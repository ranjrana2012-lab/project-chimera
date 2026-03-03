"""
Core handler for Sentiment Agent.

This module provides the main handler class that coordinates
sentiment analysis and aggregation.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from .sentiment_analyzer import SentimentAnalyzer
from .aggregator import SentimentAggregator
from .context_enrichment import ContextEnricher
from .news_sentiment_analyzer import NewsSentimentAnalyzer
from ..models.context import ContextEnrichmentOptions


class SentimentHandler:
    """Main handler for Sentiment Agent operations.

    This handler coordinates the sentiment analyzer and aggregator
    to provide comprehensive sentiment analysis with trend tracking.
    """

    def __init__(self, settings):
        """Initialize the sentiment handler.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.analyzer: Optional[SentimentAnalyzer] = None
        self.aggregator: Optional[SentimentAggregator] = None
        self.context_enricher: Optional[ContextEnricher] = None
        self.news_sentiment_analyzer: Optional[NewsSentimentAnalyzer] = None
        self._initialized = False

        # Get aggregation window from settings
        self.aggregation_window = getattr(settings, 'aggregation_window', 300)

    async def initialize(self) -> None:
        """Initialize the handler and its components.

        This loads the sentiment model and sets up the aggregator.
        """
        # Initialize analyzer
        self.analyzer = SentimentAnalyzer(self.settings)
        await self.analyzer.load_model()

        # Initialize aggregator
        max_samples = getattr(self.settings, 'max_aggregation_samples', 10000)
        self.aggregator = SentimentAggregator(max_samples=max_samples)

        # Initialize context enricher if enabled
        if getattr(self.settings, 'context_enrichment_enabled', False):
            sidecar_url = getattr(self.settings, 'worldmonitor_sidecar_url', 'http://localhost:3001')
            self.context_enricher = ContextEnricher(sidecar_url)

        # Initialize news sentiment analyzer if enabled
        if getattr(self.settings, 'news_sentiment_enabled', False):
            sidecar_url = getattr(self.settings, 'worldmonitor_sidecar_url', 'http://localhost:3001')
            self.news_sentiment_analyzer = NewsSentimentAnalyzer(
                sidecar_url=sidecar_url,
                sentiment_analyzer=self.analyzer
            )

        self._initialized = True

    async def analyze(
        self,
        text: str,
        options: Optional[Dict[str, Any]] = None,
        context_options: Optional[ContextEnrichmentOptions] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment of a single text.

        Args:
            text: Text to analyze
            options: Analysis options dictionary
            context_options: Context enrichment options
            request_id: Optional request identifier

        Returns:
            Sentiment analysis response
        """
        if not self._initialized or not self.analyzer:
            raise RuntimeError("Handler not initialized. Call initialize() first.")

        # Generate request ID if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())

        start_time = time.time()

        # Parse options
        if options is None:
            options = {}

        include_emotions = options.get('include_emotions', True)
        include_trend = options.get('include_trend', False)
        min_confidence = options.get('min_confidence', 0.5)

        # Run analysis
        result = await self.analyzer.analyze(
            text=text,
            include_emotions=include_emotions,
            min_confidence=min_confidence
        )

        # Add sample to aggregator
        if self.aggregator:
            sentiment = result['sentiment']
            await self.aggregator.add_sample(
                label=sentiment['label'],
                confidence=sentiment['confidence'],
                emotions=result.get('emotions')
            )

        # Add trend if requested
        trend = None
        if include_trend:
            aggregation_window = options.get('aggregation_window', self.aggregation_window)
            trend = await self.analyzer.get_trend(window_seconds=aggregation_window)

        # Get context if enricher is available and options provided
        context = None
        if self.context_enricher and context_options:
            context = await self.context_enricher.get_context(context_options)

        processing_time = (time.time() - start_time) * 1000

        # Build response
        from ..models.response import SentimentResponse, SentimentScore, EmotionScores

        sentiment_score = SentimentScore(
            label=result['sentiment']['label'],
            confidence=result['sentiment']['confidence'],
            positive_score=result['sentiment']['positive_score'],
            negative_score=result['sentiment']['negative_score']
        )

        emotions = None
        if result.get('emotions'):
            emotions = EmotionScores(**result['emotions'])

        return {
            'request_id': request_id,
            'text': text,
            'sentiment': sentiment_score,
            'emotions': emotions,
            'trend': trend,
            'context': context,
            'processing_time_ms': processing_time,
            'model_version': getattr(self.settings, 'model_version', 'distilbert-sst-2-v0.1.0'),
            'timestamp': datetime.now()
        }

    async def analyze_batch(
        self,
        texts: List[str],
        options: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze
            options: Analysis options dictionary
            request_id: Optional request identifier

        Returns:
            Batch sentiment analysis response
        """
        if not self._initialized or not self.analyzer:
            raise RuntimeError("Handler not initialized. Call initialize() first.")

        # Generate request ID if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())

        start_time = time.time()

        # Parse options
        if options is None:
            options = {}

        include_emotions = options.get('include_emotions', True)

        # Run batch analysis
        raw_results = await self.analyzer.analyze_batch(
            texts=texts,
            include_emotions=include_emotions
        )

        # Add samples to aggregator
        if self.aggregator:
            await self.aggregator.add_batch(raw_results)

        # Build individual results
        results = []
        for i, result in enumerate(raw_results):
            from ..models.response import SentimentScore, EmotionScores

            sentiment_score = SentimentScore(
                label=result['sentiment']['label'],
                confidence=result['sentiment']['confidence'],
                positive_score=result['sentiment']['positive_score'],
                negative_score=result['sentiment']['negative_score']
            )

            emotions = None
            if result.get('emotions'):
                emotions = EmotionScores(**result['emotions'])

            results.append({
                'request_id': f"{request_id}-{i}",
                'text': texts[i],
                'sentiment': sentiment_score,
                'emotions': emotions,
                'processing_time_ms': result['processing_time_ms'],
                'model_version': getattr(self.settings, 'model_version', 'distilbert-sst-2-v0.1.0'),
                'timestamp': datetime.now()
            })

        # Compute aggregate statistics
        aggregate = await self._compute_aggregate_stats(raw_results)

        processing_time = (time.time() - start_time) * 1000

        return {
            'request_id': request_id,
            'results': results,
            'aggregate': aggregate,
            'total_processing_time_ms': processing_time,
            'model_version': getattr(self.settings, 'model_version', 'distilbert-sst-2-v0.1.0'),
            'timestamp': datetime.now()
        }

    async def get_aggregate(
        self,
        window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get aggregated sentiment statistics.

        Args:
            window_seconds: Time window in seconds (None = default window)

        Returns:
            Aggregated sentiment statistics
        """
        if not self._initialized or not self.aggregator:
            raise RuntimeError("Handler not initialized. Call initialize() first.")

        if window_seconds is None:
            window_seconds = self.aggregation_window

        return await self.aggregator.get_aggregate(window_seconds=window_seconds)

    async def get_time_series(
        self,
        window_seconds: int,
        interval_seconds: int = 30
    ) -> List[Dict[str, Any]]:
        """Get time-series sentiment data.

        Args:
            window_seconds: Total time window to analyze
            interval_seconds: Size of each interval in the series

        Returns:
            List of time-series data points
        """
        if not self._initialized or not self.aggregator:
            raise RuntimeError("Handler not initialized. Call initialize() first.")

        return await self.aggregator.get_time_series(
            window_seconds=window_seconds,
            interval_seconds=interval_seconds
        )

    async def get_emotion_aggregate(
        self,
        window_seconds: Optional[int] = None
    ) -> Dict[str, float]:
        """Get aggregated emotion scores.

        Args:
            window_seconds: Time window in seconds (None = default window)

        Returns:
            Dictionary with average emotion scores
        """
        if not self._initialized or not self.aggregator:
            raise RuntimeError("Handler not initialized. Call initialize() first.")

        if window_seconds is None:
            window_seconds = self.aggregation_window

        return await self.aggregator.get_emotion_aggregate(window_seconds=window_seconds)

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the service.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy" if self._initialized else "initializing",
            "model_loaded": self.analyzer is not None and self.analyzer.pipeline is not None,
            "aggregator_ready": self.aggregator is not None,
            "device": str(self.analyzer.device) if self.analyzer else "unknown"
        }

    async def close(self) -> None:
        """Clean up resources."""
        if self.analyzer:
            await self.analyzer.close()

        if self.aggregator:
            await self.aggregator.clear()

        if self.context_enricher:
            await self.context_enricher.close()

        if self.news_sentiment_analyzer:
            await self.news_sentiment_analyzer.close()

        self._initialized = False

    async def _compute_aggregate_stats(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute aggregate statistics from batch results.

        Args:
            results: List of sentiment analysis results

        Returns:
            Aggregate statistics dictionary
        """
        total = len(results)
        if total == 0:
            return {
                'overall_label': 'neutral',
                'average_confidence': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'average_score': 0.0
            }

        label_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_confidence = 0.0
        total_score = 0.0

        for result in results:
            sentiment = result['sentiment']
            label = sentiment['label']
            if label in label_counts:
                label_counts[label] += 1

            total_confidence += sentiment['confidence']

            # Calculate normalized score (-1 to 1)
            if label == 'positive':
                total_score += sentiment['positive_score']
            elif label == 'negative':
                total_score -= sentiment['negative_score']

        dominant_label = max(label_counts, key=label_counts.get)

        return {
            'overall_label': dominant_label,
            'average_confidence': round(total_confidence / total, 4),
            'positive_count': label_counts['positive'],
            'negative_count': label_counts['negative'],
            'neutral_count': label_counts['neutral'],
            'average_score': round(total_score / total, 4)
        }
