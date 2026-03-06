"""
Sentiment Analyzer Module

Provides sentiment analysis using:
1. Rule-based keyword matching (current implementation)
2. DistilBERT ML model (placeholder for future integration)

The analyzer detects:
- Sentiment: positive, negative, neutral
- Score: 0.0 (negative) to 1.0 (positive)
- Emotions: joy, surprise, neutral, sadness, anger, fear
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# TODO: Replace with actual DistilBERT model when available
# from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
# import torch


class SentimentAnalyzer:
    """
    Sentiment analyzer with rule-based and ML model support.

    Currently uses rule-based keyword matching for sentiment detection.
    ML model integration is planned for future implementation.
    """

    # Positive sentiment keywords
    POSITIVE_KEYWORDS = [
        "love", "loved", "amazing", "great", "fantastic", "wonderful",
        "excellent", "brilliant", "awesome", "superb", "outstanding",
        "happy", "joy", "joyful", "delighted", "pleased", "excited",
        "beautiful", "beautifully", "perfect", "perfectly", "incredible",
        "marvelous", "spectacular", "terrific", "fabulous", "best",
        "good", "nice", "enjoyed", "enjoy", "fun", "entertaining",
        "impressed", "impressive", "recommend", "recommended"
    ]

    # Negative sentiment keywords
    NEGATIVE_KEYWORDS = [
        "hate", "hated", "terrible", "awful", "horrible", "bad",
        "worst", "boring", "bored", "disappointed", "disappointing",
        "sad", "angry", "upset", "frustrated", "annoyed", "irritated",
        "poor", "poorly", "lame", "weak", "pathetic", "ridiculous",
        "stupid", "dumb", "waste", "wasted", "regret", "unfortunate",
        "unfortunately", "failed", "failure", "mess", "disaster",
        "disgusting", "disgust", "appalling", "shocking"
    ]

    # Emotion-specific keywords
    EMOTION_KEYWORDS = {
        "joy": ["happy", "joy", "love", "excited", "delighted", "thrilled"],
        "surprise": ["wow", "surprising", "surprised", "shocking", "shocked", "unexpected"],
        "neutral": ["okay", "alright", "average", "standard", "normal", "typical"],
        "sadness": ["sad", "disappointed", "upset", "unfortunate", "regret", "depressed"],
        "anger": ["angry", "furious", "annoyed", "irritated", "frustrated", "mad"],
        "fear": ["scared", "afraid", "frightened", "terrified", "anxious", "nervous"]
    }

    # Intensity modifiers
    INTENSITY_BOOSTERS = ["very", "really", "absolutely", "completely", "totally", "extremely"]
    INTENSITY_DIMINISHERS = ["somewhat", "kind of", "sort of", "a bit", "slightly", "rather"]

    def __init__(self, use_ml_model: bool = False):
        """
        Initialize the sentiment analyzer.

        Args:
            use_ml_model: Whether to use ML model (currently placeholder only)
        """
        self.use_ml_model = use_ml_model
        self.model_available = False

        # TODO: Initialize ML model when available
        # if use_ml_model:
        #     try:
        #         self._load_ml_model()
        #         self.model_available = True
        #         logger.info("ML model loaded successfully")
        #     except Exception as e:
        #         logger.warning(f"Failed to load ML model: {e}, using rule-based")
        #         self.use_ml_model = False

        if use_ml_model and not self.model_available:
            logger.info("ML model requested but not available, using rule-based analysis")

        logger.info(f"SentimentAnalyzer initialized (ML model: {self.model_available})")

    # TODO: Implement ML model loading
    # def _load_ml_model(self):
    #     """Load DistilBERT model for sentiment analysis."""
    #     model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    #     self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    #     self.model = DistilBertForSequenceClassification.from_pretrained(model_name)
    #     self.model.eval()

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with:
                - sentiment: "positive", "negative", or "neutral"
                - score: Float from 0.0 (negative) to 1.0 (positive)
                - confidence: Float from 0.0 to 1.0
                - emotions: Dict of emotion scores
        """
        if not text or not text.strip():
            return self._neutral_result()

        # TODO: Use ML model if available
        # if self.model_available:
        #     return self._analyze_with_ml(text)

        # Use rule-based analysis
        return self._analyze_rule_based(text)

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment analysis results
        """
        if not texts:
            return []

        # Process each text
        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)

        return results

    def _analyze_rule_based(self, text: str) -> Dict:
        """
        Perform rule-based sentiment analysis using keyword matching.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result dictionary
        """
        text_lower = text.lower()

        # Count positive and negative keywords
        positive_count = 0
        negative_count = 0

        for keyword in self.POSITIVE_KEYWORDS:
            if keyword in text_lower:
                positive_count += 1

        for keyword in self.NEGATIVE_KEYWORDS:
            if keyword in text_lower:
                negative_count += 1

        # Calculate sentiment score
        total_mentions = positive_count + negative_count

        if total_mentions == 0:
            # No sentiment keywords detected
            return self._neutral_result()

        # Check for intensity modifiers
        intensity = 1.0
        for booster in self.INTENSITY_BOOSTERS:
            if booster in text_lower:
                intensity += 0.2

        for diminisher in self.INTENSITY_DIMINISHERS:
            if diminisher in text_lower:
                intensity -= 0.15

        intensity = max(0.5, min(1.5, intensity))  # Clamp between 0.5 and 1.5

        # Calculate base score
        if positive_count > negative_count:
            score = 0.5 + (positive_count / total_mentions) * 0.5 * intensity
            sentiment = "positive"
        elif negative_count > positive_count:
            score = 0.5 - (negative_count / total_mentions) * 0.5 * intensity
            sentiment = "negative"
        else:
            # Equal positive and negative - lean towards neutral
            score = 0.5
            sentiment = "neutral"

        # Clamp score
        score = max(0.0, min(1.0, score))

        # Calculate confidence based on keyword density
        confidence = min(0.95, 0.5 + (total_mentions / 10.0))

        # Calculate emotion scores
        emotions = self._calculate_emotions(text_lower, sentiment)

        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "emotions": emotions
        }

    def _calculate_emotions(self, text: str, sentiment: str) -> Dict[str, float]:
        """
        Calculate emotion scores based on keyword matching.

        Args:
            text: Lowercase text to analyze
            sentiment: Primary sentiment classification

        Returns:
            Dictionary of emotion scores
        """
        emotions = {
            "joy": 0.0,
            "surprise": 0.0,
            "neutral": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0
        }

        # Count emotion-specific keywords
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    emotions[emotion] += 0.3

        # Check for exclamation marks (indicates surprise/intensity)
        exclamations = text.count("!")
        if exclamations > 0:
            emotions["surprise"] += min(0.4, exclamations * 0.15)

        # Adjust emotions based on primary sentiment
        if sentiment == "positive":
            emotions["joy"] += 0.4
            emotions["neutral"] = max(0.0, emotions["neutral"] - 0.2)
            emotions["sadness"] = max(0.0, emotions["sadness"] - 0.2)
        elif sentiment == "negative":
            emotions["sadness"] += 0.3
            emotions["anger"] += 0.2
            emotions["neutral"] = max(0.0, emotions["neutral"] - 0.2)
            emotions["joy"] = max(0.0, emotions["joy"] - 0.2)
        else:  # neutral
            emotions["neutral"] += 0.5

        # Normalize emotions to 0-1 range
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: min(1.0, v / total * 2) for k, v in emotions.items()}

        return emotions

    def _neutral_result(self) -> Dict:
        """Return a neutral sentiment result."""
        return {
            "sentiment": "neutral",
            "score": 0.5,
            "confidence": 0.5,
            "emotions": {
                "joy": 0.0,
                "surprise": 0.0,
                "neutral": 1.0,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0
            }
        }

    # TODO: Implement ML model analysis
    # def _analyze_with_ml(self, text: str) -> Dict:
    #     """Analyze sentiment using DistilBERT model."""
    #     inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    #
    #     with torch.no_grad():
    #         outputs = self.model(**inputs)
    #         predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    #
    #     # Convert to sentiment
    #     positive_prob = predictions[0][1].item()
    #     negative_prob = predictions[0][0].item()
    #
    #     if positive_prob > 0.6:
    #         sentiment = "positive"
    #     elif negative_prob > 0.6:
    #         sentiment = "negative"
    #     else:
    #         sentiment = "neutral"
    #
    #     return {
    #         "sentiment": sentiment,
    #         "score": positive_prob,
    #         "confidence": max(positive_prob, negative_prob),
    #         "emotions": self._calculate_emotions(text.lower(), sentiment)
    #     }
