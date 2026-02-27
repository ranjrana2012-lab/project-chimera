"""
Unit tests for Sentiment Handler.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from services.sentiment_agent.src.core.handler import SentimentHandler
from services.sentiment_agent.src.models.request import SentimentRequest, SentimentBatchRequest


@pytest.mark.unit
class TestSentimentHandler:
    """Test cases for SentimentHandler."""

    @pytest.fixture
    def settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        settings.aggregation_window = 300
        settings.max_aggregation_samples = 10000
        settings.model_version = "distilbert-sst-2-v0.1.0"
        return settings

    @pytest.fixture
    def handler(self, settings):
        """Create a handler instance."""
        return SentimentHandler(settings)

    @pytest.mark.asyncio
    async def test_initialize(self, handler):
        """Test handler initialization."""
        # Mock the SentimentAnalyzer.load_model method
        with patch('services.sentiment_agent.src.core.sentiment_analyzer.SentimentAnalyzer.load_model', new_callable=AsyncMock):
            await handler.initialize()
            assert handler._initialized is True
            assert handler.aggregator is not None

    @pytest.mark.asyncio
    async def test_analyze_uninitialized(self, handler):
        """Test analysis fails when handler is not initialized."""
        handler._initialized = False

        with pytest.raises(RuntimeError, match="not initialized"):
            await handler.analyze("Test text")

    @pytest.mark.asyncio
    async def test_analyze_success(self, handler):
        """Test successful sentiment analysis."""
        # Mock the analyzer
        handler._initialized = True
        handler.analyzer = Mock()
        handler.analyzer.analyze = AsyncMock(return_value={
            'sentiment': {
                'label': 'positive',
                'confidence': 0.95,
                'positive_score': 0.98,
                'negative_score': 0.02
            },
            'emotions': {
                'joy': 0.85,
                'sadness': 0.05,
                'anger': 0.02,
                'fear': 0.03,
                'surprise': 0.30,
                'disgust': 0.01
            },
            'processing_time_ms': 50.0
        })

        # Mock aggregator
        handler.aggregator = Mock()
        handler.aggregator.add_sample = AsyncMock()

        result = await handler.analyze("This is amazing!")

        assert result['sentiment'].label == 'positive'
        assert result['sentiment'].confidence == 0.95
        assert result['emotions'].joy == 0.85
        assert 'request_id' in result

    @pytest.mark.asyncio
    async def test_analyze_with_options(self, handler):
        """Test analysis with custom options."""
        handler._initialized = True
        handler.analyzer = Mock()
        handler.analyzer.analyze = AsyncMock(return_value={
            'sentiment': {
                'label': 'negative',
                'confidence': 0.85,
                'positive_score': 0.15,
                'negative_score': 0.85
            },
            'emotions': None,
            'processing_time_ms': 45.0
        })

        handler.aggregator = Mock()
        handler.aggregator.add_sample = AsyncMock()

        options = {
            'include_emotions': False,
            'min_confidence': 0.7
        }

        result = await handler.analyze(
            "This is terrible!",
            options=options
        )

        assert result['sentiment'].label == 'negative'
        assert result['emotions'] is None

    @pytest.mark.asyncio
    async def test_analyze_batch(self, handler):
        """Test batch sentiment analysis."""
        handler._initialized = True
        handler.analyzer = Mock()
        handler.analyzer.analyze_batch = AsyncMock(return_value=[
            {
                'sentiment': {
                    'label': 'positive',
                    'confidence': 0.95,
                    'positive_score': 0.98,
                    'negative_score': 0.02
                },
                'emotions': {'joy': 0.85, 'sadness': 0.05, 'anger': 0.02,
                             'fear': 0.03, 'surprise': 0.30, 'disgust': 0.01},
                'processing_time_ms': 20.0
            },
            {
                'sentiment': {
                    'label': 'positive',
                    'confidence': 0.90,
                    'positive_score': 0.95,
                    'negative_score': 0.05
                },
                'emotions': {'joy': 0.75, 'sadness': 0.10, 'anger': 0.02,
                             'fear': 0.03, 'surprise': 0.20, 'disgust': 0.01},
                'processing_time_ms': 18.0
            }
        ])

        handler.aggregator = Mock()
        handler.aggregator.add_batch = AsyncMock()

        texts = ["Great!", "Amazing!"]
        result = await handler.analyze_batch(texts)

        assert len(result['results']) == 2
        assert 'aggregate' in result
        assert result['aggregate']['positive_count'] == 2

    @pytest.mark.asyncio
    async def test_get_aggregate(self, handler):
        """Test getting aggregated sentiment."""
        handler._initialized = True
        handler.aggregator = Mock()
        handler.aggregator.get_aggregate = AsyncMock(return_value={
            'overall_label': 'positive',
            'average_score': 0.75,
            'positive_count': 10,
            'negative_count': 2,
            'neutral_count': 1
        })

        result = await handler.get_aggregate(window_seconds=300)

        assert result['overall_label'] == 'positive'
        assert result['positive_count'] == 10

    @pytest.mark.asyncio
    async def test_health_check(self, handler):
        """Test health check endpoint."""
        handler._initialized = True
        handler.analyzer = Mock()
        handler.analyzer.pipeline = Mock()
        handler.aggregator = Mock()

        result = await handler.health_check()

        assert result['status'] == 'healthy'
        assert result['model_loaded'] is True
        assert result['aggregator_ready'] is True

    @pytest.mark.asyncio
    async def test_close(self, handler):
        """Test closing the handler."""
        handler._initialized = True
        handler.analyzer = Mock()
        handler.analyzer.close = AsyncMock()
        handler.aggregator = Mock()
        handler.aggregator.clear = AsyncMock()

        await handler.close()

        handler.analyzer.close.assert_called_once()
        handler.aggregator.clear.assert_called_once()
        assert handler._initialized is False
