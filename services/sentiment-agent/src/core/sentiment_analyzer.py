"""
Sentiment Analyzer using DistilBERT SST-2 model.

This module provides sentiment analysis using the Hugging Face
transformers library with the distilbert-base-uncased-finetuned-sst-2-english model.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime, timedelta

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline as hf_pipeline


class SentimentAnalyzer:
    """Sentiment analyzer using DistilBERT SST-2 model."""

    def __init__(self, settings):
        """Initialize the sentiment analyzer.

        Args:
            settings: Application settings containing model configuration
        """
        self.settings = settings
        self.model_name = getattr(settings, 'model_name', 'distilbert-base-uncased-finetuned-sst-2-english')
        self.device = self._get_device()
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self._history = deque(maxlen=1000)  # Store recent analyses for trending
        self._lock = asyncio.Lock()

    def _get_device(self) -> torch.device:
        """Determine the best device for model inference."""
        if torch.cuda.is_available():
            return torch.device("cuda:0")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    async def load_model(self) -> None:
        """Load the sentiment analysis model.

        This loads both the tokenizer and model for the DistilBERT SST-2 model.
        The model is loaded on the best available device.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model_sync)
        print(f"Sentiment model '{self.model_name}' loaded on {self.device}")

    def _load_model_sync(self) -> None:
        """Synchronously load the model (run in executor)."""
        # Load pipeline with sentiment analysis
        self.pipeline = hf_pipeline(
            "sentiment-analysis",
            model=self.model_name,
            tokenizer=self.model_name,
            device=self.device,
            top_k=None  # Get all labels with scores
        )

        # Also load tokenizer and model separately for more control
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

    async def analyze(
        self,
        text: str,
        include_emotions: bool = True,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """Analyze sentiment of a single text.

        Args:
            text: Text to analyze
            include_emotions: Whether to include emotion detection
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary containing sentiment analysis results
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.time()

        # Truncate text if too long (DistilBERT max is 512 tokens)
        truncated_text = self._truncate_text(text, max_length=512)

        # Run sentiment analysis
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._analyze_sync,
            truncated_text
        )

        # Add emotions if requested
        emotions = None
        if include_emotions:
            emotions = self._detect_emotions(truncated_text, result)

        # Store in history for trending
        async with self._lock:
            self._history.append({
                'timestamp': datetime.now(),
                'score': result['score'],
                'label': result['label']
            })

        processing_time = (time.time() - start_time) * 1000

        return {
            'sentiment': result,
            'emotions': emotions,
            'processing_time_ms': processing_time
        }

    def _analyze_sync(self, text: str) -> Dict[str, Any]:
        """Synchronously analyze text sentiment (run in executor)."""
        outputs = self.pipeline(text)

        # The SST-2 model returns POSITIVE and NEGATIVE labels
        # Convert to our format
        if isinstance(outputs, list):
            output = outputs[0]
        else:
            output = outputs

        # Extract scores
        positive_score = 0.0
        negative_score = 0.0

        for item in output:
            if item['label'].upper() == 'POSITIVE':
                positive_score = item['score']
            elif item['label'].upper() == 'NEGATIVE':
                negative_score = item['score']

        # Determine label based on higher score
        if positive_score > negative_score:
            label = 'positive'
            confidence = positive_score
        else:
            label = 'negative'
            confidence = negative_score

        # Check for neutral (when scores are close)
        if abs(positive_score - negative_score) < 0.1:
            label = 'neutral'
            confidence = max(positive_score, negative_score)

        return {
            'label': label,
            'confidence': confidence,
            'positive_score': positive_score,
            'negative_score': negative_score
        }

    def _detect_emotions(
        self,
        text: str,
        sentiment_result: Dict[str, Any]
    ) -> Dict[str, float]:
        """Detect emotions based on sentiment and text analysis.

        This is a heuristic-based emotion detection since we're using
        a binary sentiment model. For production, you might want to use
        a dedicated emotion model.

        Args:
            text: The analyzed text
            sentiment_result: Results from sentiment analysis

        Returns:
            Dictionary of emotion scores
        """
        text_lower = text.lower()

        # Emotion keyword lists (simplified)
        joy_keywords = ['happy', 'joy', 'love', 'great', 'amazing', 'wonderful',
                       'excellent', 'fantastic', 'best', 'beautiful', 'excited',
                       'thrilled', 'delighted', 'pleased']
        sadness_keywords = ['sad', 'disappointed', 'unhappy', 'sorry', 'regret',
                           'miss', 'tragic', 'depressed', 'lonely', 'grief']
        anger_keywords = ['angry', 'furious', 'mad', 'hate', 'terrible', 'awful',
                         'worst', 'annoyed', 'frustrated', 'irritated', 'rage']
        fear_keywords = ['scared', 'afraid', 'frightened', 'terrified', 'anxious',
                        'worried', 'nervous', 'panic', 'fear', 'dread']
        surprise_keywords = ['surprised', 'shocked', 'amazed', 'astonished',
                           'unexpected', 'wow', 'incredible', 'unbelievable']
        disgust_keywords = ['disgusting', 'gross', 'revolting', 'sick', 'awful',
                           'repulsive', 'nasty', 'horrible']

        # Count keyword matches
        word_count = len(text.split())

        def get_emotion_score(keywords: List[str]) -> float:
            count = sum(1 for kw in keywords if kw in text_lower)
            base_score = min(count / max(word_count, 1), 1.0)
            # Adjust based on sentiment
            if sentiment_result['label'] == 'positive':
                return base_score * sentiment_result['confidence']
            else:
                return base_score * 0.5

        return {
            'joy': get_emotion_score(joy_keywords),
            'sadness': get_emotion_score(sadness_keywords),
            'anger': get_emotion_score(anger_keywords),
            'fear': get_emotion_score(fear_keywords),
            'surprise': get_emotion_score(surprise_keywords),
            'disgust': get_emotion_score(disgust_keywords)
        }

    async def analyze_batch(
        self,
        texts: List[str],
        include_emotions: bool = True
    ) -> List[Dict[str, Any]]:
        """Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze
            include_emotions: Whether to include emotion detection

        Returns:
            List of sentiment analysis results
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Process in parallel chunks
        chunk_size = 10
        results = []

        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            chunk_results = await asyncio.gather(
                *[self.analyze(text, include_emotions) for text in chunk],
                return_exceptions=True
            )
            results.extend(chunk_results)

        return results

    async def get_trend(
        self,
        window_seconds: int = 300
    ) -> Dict[str, Any]:
        """Get sentiment trend over a time window.

        Args:
            window_seconds: Time window to analyze (default: 5 minutes)

        Returns:
            Trend analysis data
        """
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

            # Filter data within window
            window_data = [
                item for item in self._history
                if item['timestamp'] >= cutoff_time
            ]

            if not window_data:
                return {
                    'current_score': 0.0,
                    'direction': 'stable',
                    'change_percent': 0.0,
                    'data_points': []
                }

            # Calculate average sentiment score
            # Convert labels to scores: positive=1, neutral=0, negative=-1
            label_to_score = {'positive': 1.0, 'neutral': 0.0, 'negative': -1.0}

            # Create data points (group by 30-second intervals)
            interval_seconds = 30
            intervals = {}

            for item in window_data:
                interval_key = item['timestamp'].replace(
                    second=(item['timestamp'].second // interval_seconds) * interval_seconds,
                    microsecond=0
                )

                if interval_key not in intervals:
                    intervals[interval_key] = []

                score = label_to_score.get(item['label'], 0.0) * item['score']
                intervals[interval_key].append(score)

            # Create trend data points
            data_points = []
            for timestamp in sorted(intervals.keys()):
                scores = intervals[timestamp]
                avg_score = sum(scores) / len(scores) if scores else 0.0
                data_points.append({
                    'timestamp': timestamp,
                    'score': avg_score,
                    'count': len(scores)
                })

            # Calculate current score and trend
            current_score = data_points[-1]['score'] if data_points else 0.0

            # Determine direction
            direction = 'stable'
            change_percent = 0.0

            if len(data_points) >= 2:
                prev_score = data_points[-2]['score']
                if abs(current_score - prev_score) > 0.05:
                    if current_score > prev_score:
                        direction = 'rising'
                    else:
                        direction = 'falling'

                    # Calculate percent change
                    if prev_score != 0:
                        change_percent = ((current_score - prev_score) / abs(prev_score)) * 100
                    else:
                        change_percent = current_score * 100

            return {
                'current_score': current_score,
                'direction': direction,
                'change_percent': round(change_percent, 2),
                'data_points': [
                    {
                        'timestamp': dp['timestamp'],
                        'score': round(dp['score'], 4),
                        'count': dp['count']
                    }
                    for dp in data_points
                ]
            }

    def _truncate_text(self, text: str, max_length: int = 512) -> str:
        """Truncate text to fit within model's maximum sequence length.

        Args:
            text: Text to truncate
            max_length: Maximum length in tokens

        Returns:
            Truncated text
        """
        # Approximate token count (roughly 4 chars per token)
        max_chars = max_length * 4

        if len(text) <= max_chars:
            return text

        # Truncate intelligently - try to end at a sentence boundary
        truncated = text[:max_chars]

        # Find last sentence ending
        for ending in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
            last_idx = truncated.rfind(ending)
            if last_idx > max_chars // 2:  # Ensure we don't cut too much
                return truncated[:last_idx + len(ending)]

        return truncated + '...'

    async def close(self) -> None:
        """Clean up resources.

        This method unloads the model from memory to free up resources.
        """
        if self.model:
            del self.model
            self.model = None

        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        if self.pipeline:
            del self.pipeline
            self.pipeline = None

        # Clear GPU cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Clear history
        async with self._lock:
            self._history.clear()
