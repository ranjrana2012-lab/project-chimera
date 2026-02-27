"""
Unit tests for Sentiment Aggregator.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from services.sentiment_agent.src.core.aggregator import (
    SentimentAggregator,
    SentimentSample
)


@pytest.mark.unit
class TestSentimentSample:
    """Test cases for SentimentSample dataclass."""

    def test_create_sample(self):
        """Test creating a sentiment sample."""
        sample = SentimentSample(
            timestamp=datetime.now(),
            label='positive',
            confidence=0.95,
            score=0.95,
            emotions={'joy': 0.85, 'sadness': 0.05}
        )

        assert sample.label == 'positive'
        assert sample.confidence == 0.95
        assert sample.score == 0.95
        assert sample.emotions is not None


@pytest.mark.unit
class TestSentimentAggregator:
    """Test cases for SentimentAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create an aggregator instance."""
        return SentimentAggregator(max_samples=100)

    @pytest.mark.asyncio
    async def test_add_sample(self, aggregator):
        """Test adding a single sample."""
        await aggregator.add_sample(
            label='positive',
            confidence=0.95,
            emotions={'joy': 0.85}
        )

        count = await aggregator.get_sample_count()
        assert count == 1

    @pytest.mark.asyncio
    async def test_add_batch(self, aggregator):
        """Test adding batch samples."""
        results = [
            {
                'sentiment': {
                    'label': 'positive',
                    'confidence': 0.95
                },
                'emotions': {'joy': 0.85}
            },
            {
                'sentiment': {
                    'label': 'negative',
                    'confidence': 0.80
                },
                'emotions': {'anger': 0.60}
            }
        ]

        await aggregator.add_batch(results)

        count = await aggregator.get_sample_count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_aggregate_empty(self, aggregator):
        """Test getting aggregate when empty."""
        aggregate = await aggregator.get_aggregate()

        assert aggregate['total_count'] == 0
        assert aggregate['overall_label'] == 'neutral'

    @pytest.mark.asyncio
    async def test_get_aggregate_with_samples(self, aggregator):
        """Test getting aggregate with samples."""
        # Add multiple samples
        await aggregator.add_sample('positive', 0.95)
        await aggregator.add_sample('positive', 0.90)
        await aggregator.add_sample('negative', 0.80)

        aggregate = await aggregator.get_aggregate()

        assert aggregate['total_count'] == 3
        assert aggregate['positive_count'] == 2
        assert aggregate['negative_count'] == 1
        assert aggregate['overall_label'] == 'positive'
        assert aggregate['average_score'] > 0  # Should be positive overall

    @pytest.mark.asyncio
    async def test_get_aggregate_with_window(self, aggregator):
        """Test getting aggregate with time window."""
        now = datetime.now()

        # Add sample outside window
        old_sample = SentimentSample(
            timestamp=now - timedelta(seconds=400),
            label='positive',
            confidence=0.95,
            score=0.95
        )
        aggregator._samples.append(old_sample)

        # Add sample within window
        await aggregator.add_sample('negative', 0.80)

        # Get aggregate for 300 second window
        aggregate = await aggregator.get_aggregate(window_seconds=300)

        # Should only include the recent sample
        assert aggregate['total_count'] == 1
        assert aggregate['negative_count'] == 1

    @pytest.mark.asyncio
    async def test_get_time_series(self, aggregator):
        """Test getting time series data."""
        # Add samples spread over time
        now = datetime.now()
        for i in range(5):
            timestamp = now - timedelta(seconds=(4 - i) * 30)
            await aggregator.add_sample(
                'positive' if i % 2 == 0 else 'negative',
                0.8 + (i * 0.02)
            )

        time_series = await aggregator.get_time_series(
            window_seconds=300,
            interval_seconds=60
        )

        assert len(time_series) > 0
        assert 'timestamp' in time_series[0]
        assert 'average_score' in time_series[0]
        assert 'positive_count' in time_series[0]

    @pytest.mark.asyncio
    async def test_get_emotion_aggregate(self, aggregator):
        """Test getting emotion aggregate."""
        await aggregator.add_sample(
            'positive',
            0.95,
            emotions={'joy': 0.85, 'sadness': 0.05, 'anger': 0.02,
                      'fear': 0.03, 'surprise': 0.30, 'disgust': 0.01}
        )
        await aggregator.add_sample(
            'positive',
            0.90,
            emotions={'joy': 0.75, 'sadness': 0.10, 'anger': 0.02,
                      'fear': 0.03, 'surprise': 0.20, 'disgust': 0.01}
        )

        emotions = await aggregator.get_emotion_aggregate()

        assert 'joy' in emotions
        assert 'sadness' in emotions
        assert emotions['joy'] > 0  # Should have positive joy

    @pytest.mark.asyncio
    async def test_clear(self, aggregator):
        """Test clearing the aggregator."""
        await aggregator.add_sample('positive', 0.95)
        await aggregator.add_sample('negative', 0.80)

        assert await aggregator.get_sample_count() == 2

        await aggregator.clear()

        assert await aggregator.get_sample_count() == 0

    @pytest.mark.asyncio
    async def test_max_samples_limit(self, aggregator):
        """Test that aggregator respects max_samples limit."""
        # Set a small max_samples
        small_aggregator = SentimentAggregator(max_samples=5)

        # Add more samples than max
        for i in range(10):
            await small_aggregator.add_sample('positive', 0.8 + (i * 0.01))

        # Should only keep the most recent 5
        count = await small_aggregator.get_sample_count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_intensity_calculation(self, aggregator):
        """Test intensity calculation in aggregate."""
        # Add samples where positive dominates
        for _ in range(8):
            await aggregator.add_sample('positive', 0.9)
        for _ in range(2):
            await aggregator.add_sample('negative', 0.8)

        aggregate = await aggregator.get_aggregate()

        # Intensity should be ratio of dominant sentiment
        assert aggregate['positive_count'] == 8
        assert aggregate['negative_count'] == 2
        assert aggregate['intensity'] == 0.8  # 8/10
