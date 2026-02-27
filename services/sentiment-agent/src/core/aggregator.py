"""
Sentiment Aggregation Module.

This module provides functionality to aggregate sentiment analysis results
over time windows, useful for tracking audience sentiment trends during
live performances.
"""

import asyncio
from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class SentimentSample:
    """A single sentiment sample for aggregation.

    Attributes:
        timestamp: When the sample was collected
        label: Sentiment label (positive/negative/neutral)
        confidence: Confidence score (0.0-1.0)
        score: Normalized score (-1.0 to 1.0)
        emotions: Optional emotion scores
    """
    timestamp: datetime
    label: str
    confidence: float
    score: float
    emotions: Optional[Dict[str, float]] = None


class SentimentAggregator:
    """Aggregates sentiment data over time windows.

    This class maintains a rolling window of sentiment samples and provides
    aggregated statistics for different time periods.
    """

    def __init__(self, max_samples: int = 10000):
        """Initialize the aggregator.

        Args:
            max_samples: Maximum number of samples to store in memory
        """
        self.max_samples = max_samples
        self._samples: List[SentimentSample] = []
        self._lock = asyncio.Lock()

    async def add_sample(
        self,
        label: str,
        confidence: float,
        timestamp: Optional[datetime] = None,
        emotions: Optional[Dict[str, float]] = None
    ) -> None:
        """Add a sentiment sample to the aggregator.

        Args:
            label: Sentiment label (positive/negative/neutral)
            confidence: Confidence score (0.0-1.0)
            timestamp: When the sample was collected (defaults to now)
            emotions: Optional emotion scores
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Convert label to normalized score
        label_to_score = {
            'positive': 1.0,
            'neutral': 0.0,
            'negative': -1.0
        }

        score = label_to_score.get(label.lower(), 0.0) * confidence

        sample = SentimentSample(
            timestamp=timestamp,
            label=label,
            confidence=confidence,
            score=score,
            emotions=emotions
        )

        async with self._lock:
            self._samples.append(sample)

            # Prune old samples if we exceed max
            if len(self._samples) > self.max_samples:
                # Remove oldest samples
                self._samples = self._samples[-self.max_samples:]

    async def add_batch(
        self,
        results: List[Dict[str, Any]]
    ) -> None:
        """Add multiple sentiment samples from batch results.

        Args:
            results: List of sentiment analysis results
        """
        for result in results:
            sentiment = result.get('sentiment', {})
            emotions = result.get('emotions')

            await self.add_sample(
                label=sentiment.get('label', 'neutral'),
                confidence=sentiment.get('confidence', 0.5),
                emotions=emotions
            )

    async def get_aggregate(
        self,
        window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get aggregated sentiment statistics.

        Args:
            window_seconds: Time window in seconds (None = all samples)

        Returns:
            Dictionary with aggregated statistics
        """
        async with self._lock:
            if not self._samples:
                return self._empty_aggregate()

            # Filter by time window if specified
            if window_seconds:
                cutoff = datetime.now() - timedelta(seconds=window_seconds)
                samples = [s for s in self._samples if s.timestamp >= cutoff]
            else:
                samples = self._samples

            if not samples:
                return self._empty_aggregate()

            return self._compute_aggregate(samples)

    async def get_time_series(
        self,
        window_seconds: int,
        interval_seconds: int = 30
    ) -> List[Dict[str, Any]]:
        """Get time-series data for sentiment over a window.

        Args:
            window_seconds: Total time window to analyze
            interval_seconds: Size of each interval in the series

        Returns:
            List of time-series data points
        """
        async with self._lock:
            if not self._samples:
                return []

            cutoff = datetime.now() - timedelta(seconds=window_seconds)
            samples = [s for s in self._samples if s.timestamp >= cutoff]

            if not samples:
                return []

            # Group samples into intervals
            intervals = defaultdict(list)

            for sample in samples:
                # Calculate which interval this sample belongs to
                seconds_from_start = int((sample.timestamp - cutoff).total_seconds())
                interval_index = seconds_from_start // interval_seconds
                intervals[interval_index].append(sample)

            # Compute aggregate for each interval
            time_series = []

            for i in sorted(intervals.keys()):
                interval_samples = intervals[i]
                aggregate = self._compute_aggregate(interval_samples)

                # Calculate the timestamp for the middle of the interval
                interval_start = cutoff + timedelta(seconds=i * interval_seconds)
                interval_mid = interval_start + timedelta(seconds=interval_seconds // 2)

                time_series.append({
                    'timestamp': interval_mid,
                    'interval_seconds': interval_seconds,
                    **aggregate
                })

            return time_series

    async def get_emotion_aggregate(
        self,
        window_seconds: Optional[int] = None
    ) -> Dict[str, float]:
        """Get aggregated emotion scores.

        Args:
            window_seconds: Time window in seconds (None = all samples)

        Returns:
            Dictionary with average emotion scores
        """
        async with self._lock:
            if not self._samples:
                return {
                    'joy': 0.0,
                    'sadness': 0.0,
                    'anger': 0.0,
                    'fear': 0.0,
                    'surprise': 0.0,
                    'disgust': 0.0
                }

            # Filter by time window if specified
            if window_seconds:
                cutoff = datetime.now() - timedelta(seconds=window_seconds)
                samples = [s for s in self._samples if s.timestamp >= cutoff and s.emotions]
            else:
                samples = [s for s in self._samples if s.emotions]

            if not samples:
                return {
                    'joy': 0.0,
                    'sadness': 0.0,
                    'anger': 0.0,
                    'fear': 0.0,
                    'surprise': 0.0,
                    'disgust': 0.0
                }

            # Average each emotion
            emotion_totals = defaultdict(float)
            count = 0

            for sample in samples:
                if sample.emotions:
                    for emotion, score in sample.emotions.items():
                        emotion_totals[emotion] += score
                    count += 1

            if count == 0:
                return {e: 0.0 for e in emotion_totals.keys()}

            return {
                emotion: round(total / count, 4)
                for emotion, total in emotion_totals.items()
            }

    async def clear(self) -> None:
        """Clear all stored samples."""
        async with self._lock:
            self._samples.clear()

    async def get_sample_count(self, window_seconds: Optional[int] = None) -> int:
        """Get the number of samples stored.

        Args:
            window_seconds: Time window in seconds (None = all samples)

        Returns:
            Number of samples in the window
        """
        async with self._lock:
            if not self._samples:
                return 0

            if window_seconds:
                cutoff = datetime.now() - timedelta(seconds=window_seconds)
                return len([s for s in self._samples if s.timestamp >= cutoff])

            return len(self._samples)

    def _empty_aggregate(self) -> Dict[str, Any]:
        """Return an empty aggregate result."""
        return {
            'overall_label': 'neutral',
            'average_score': 0.0,
            'average_confidence': 0.0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'total_count': 0,
            'positive_ratio': 0.0,
            'negative_ratio': 0.0,
            'neutral_ratio': 0.0,
            'intensity': 0.0
        }

    def _compute_aggregate(self, samples: List[SentimentSample]) -> Dict[str, Any]:
        """Compute aggregate statistics from a list of samples.

        Args:
            samples: List of sentiment samples

        Returns:
            Dictionary with aggregated statistics
        """
        total = len(samples)

        # Count labels
        label_counts = defaultdict(int)
        total_score = 0.0
        total_confidence = 0.0

        for sample in samples:
            label_counts[sample.label] += 1
            total_score += sample.score
            total_confidence += sample.confidence

        # Determine dominant label
        dominant_label = max(label_counts, key=label_counts.get) if label_counts else 'neutral'

        # Calculate ratios
        positive_count = label_counts.get('positive', 0)
        negative_count = label_counts.get('negative', 0)
        neutral_count = label_counts.get('neutral', 0)

        # Intensity = ratio of dominant sentiment
        intensity = max(label_counts.values()) / total if total > 0 else 0.0

        return {
            'overall_label': dominant_label,
            'average_score': round(total_score / total, 4) if total > 0 else 0.0,
            'average_confidence': round(total_confidence / total, 4) if total > 0 else 0.0,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'total_count': total,
            'positive_ratio': round(positive_count / total, 4) if total > 0 else 0.0,
            'negative_ratio': round(negative_count / total, 4) if total > 0 else 0.0,
            'neutral_ratio': round(neutral_count / total, 4) if total > 0 else 0.0,
            'intensity': round(intensity, 4)
        }
