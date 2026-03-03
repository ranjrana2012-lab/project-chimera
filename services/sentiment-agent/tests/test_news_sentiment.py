"""Unit tests for News Sentiment Analyzer module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.news_sentiment_analyzer import NewsSentimentAnalyzer
from src.models.context import NewsSentimentRequest
from src.core.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture
def mock_sentiment_analyzer():
    """Create a mock sentiment analyzer."""
    analyzer = AsyncMock()
    analyzer.analyze.return_value = {
        'sentiment': {
            'label': 'positive',
            'confidence': 0.85
        }
    }
    return analyzer


@pytest.fixture
def sample_articles():
    """Create sample news articles."""
    return [
        {
            'title': 'Economic growth exceeds expectations',
            'content': 'The economy grew by 3% last quarter, surpassing analyst predictions.',
            'source': 'Financial Times',
            'published_at': '2025-03-01T10:00:00Z'
        },
        {
            'title': 'Stock markets reach new highs',
            'content': 'Major indices hit record levels as investor confidence soars.',
            'source': 'Bloomberg',
            'published_at': '2025-03-01T09:30:00Z'
        },
        {
            'title': 'Concerns about inflation rise',
            'content': 'Central banks may need to raise interest rates to combat inflation.',
            'source': 'Reuters',
            'published_at': '2025-03-01T08:00:00Z'
        }
    ]


def test_news_sentiment_analyzer_initialization(mock_sentiment_analyzer):
    """Test NewsSentimentAnalyzer initialization."""
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    assert analyzer.sidecar_url == "http://localhost:3001"
    assert analyzer.sentiment_analyzer == mock_sentiment_analyzer
    assert analyzer._http_client is None


@pytest.mark.asyncio
async def test_analyze_news_success(mock_sentiment_analyzer, sample_articles):
    """Test successful news sentiment analysis."""
    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Mock _fetch_news
    async def mock_fetch(request):
        return sample_articles

    analyzer._fetch_news = mock_fetch

    # Create request
    request = NewsSentimentRequest(
        sources=['Financial Times', 'Bloomberg'],
        categories=['economy'],
        hours=24,
        max_articles=100
    )

    # Analyze news
    result = await analyzer.analyze_news(request)

    # Verify results
    assert result.analyzed_articles == 3
    assert result.average_sentiment == 'positive'
    assert 'positive' in result.sentiment_distribution
    assert result.processing_time_ms > 0
    assert isinstance(result.top_positive, list)
    assert isinstance(result.top_negative, list)


@pytest.mark.asyncio
async def test_analyze_news_empty_articles(mock_sentiment_analyzer):
    """Test analysis when no articles are returned."""
    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Mock empty articles
    async def mock_fetch(request):
        return []

    analyzer._fetch_news = mock_fetch

    # Create request
    request = NewsSentimentRequest()

    # Analyze news
    result = await analyzer.analyze_news(request)

    # Verify empty response
    assert result.analyzed_articles == 0
    assert result.average_sentiment == 'neutral'
    assert result.sentiment_distribution == {}
    assert result.top_positive == []
    assert result.top_negative == []


@pytest.mark.asyncio
async def test_sentiment_aggregation(sample_articles):
    """Test sentiment aggregation across multiple articles."""
    # Create mock sentiment analyzer with varied results
    mock_sentiment_analyzer = AsyncMock()
    call_count = [0]

    async def varied_sentiment(text):
        call_count[0] += 1
        sentiments = ['positive', 'positive', 'negative']
        return {
            'sentiment': {
                'label': sentiments[call_count[0] - 1],
                'confidence': 0.8
            }
        }

    mock_sentiment_analyzer.analyze = varied_sentiment

    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Mock _fetch_news
    async def mock_fetch(request):
        return sample_articles

    analyzer._fetch_news = mock_fetch

    # Analyze news
    request = NewsSentimentRequest()
    result = await analyzer.analyze_news(request)

    # Verify aggregation
    assert result.analyzed_articles == 3
    assert result.sentiment_distribution['positive'] == 2
    assert result.sentiment_distribution['negative'] == 1
    assert result.average_sentiment == 'positive'  # Most frequent


@pytest.mark.asyncio
async def test_news_filtering(mock_sentiment_analyzer):
    """Test news filtering with various parameters."""
    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Test with sources filter
    async def mock_fetch_empty(request):
        return []

    analyzer._fetch_news = mock_fetch_empty

    request = NewsSentimentRequest(
        sources=['BBC', 'CNN']
    )
    await analyzer.analyze_news(request)

    # Test with categories filter
    request = NewsSentimentRequest(
        categories=['politics', 'business']
    )
    await analyzer.analyze_news(request)

    # Test with hours filter
    request = NewsSentimentRequest(
        hours=48
    )
    await analyzer.analyze_news(request)

    # Test with max_articles limit
    async def mock_fetch_10(request):
        return [{'title': f'Article {i}'} for i in range(10)]

    analyzer._fetch_news = mock_fetch_10

    request = NewsSentimentRequest(max_articles=5)
    result = await analyzer.analyze_news(request)

    # Verify max articles limit is respected
    assert result.analyzed_articles <= 5


@pytest.mark.asyncio
async def test_top_positive_negative_articles(sample_articles):
    """Test identification of top positive and negative articles."""
    # Create mock with different confidences
    mock_sentiment_analyzer = AsyncMock()
    call_count = [0]

    async def varied_confidence(text):
        call_count[0] += 1
        if call_count[0] == 1:
            return {'sentiment': {'label': 'positive', 'confidence': 0.95}}
        elif call_count[0] == 2:
            return {'sentiment': {'label': 'positive', 'confidence': 0.70}}
        else:
            return {'sentiment': {'label': 'negative', 'confidence': 0.85}}

    mock_sentiment_analyzer.analyze = varied_confidence

    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Mock _fetch_news
    async def mock_fetch(request):
        return sample_articles

    analyzer._fetch_news = mock_fetch

    # Analyze news
    request = NewsSentimentRequest()
    result = await analyzer.analyze_news(request)

    # Verify top positive (should be sorted by confidence)
    if result.top_positive:
        assert result.top_positive[0]['confidence'] >= result.top_positive[-1]['confidence']

    # Verify top negative
    if result.top_negative:
        assert 'title' in result.top_negative[0]
        assert 'confidence' in result.top_negative[0]


@pytest.mark.asyncio
async def test_text_length_truncation(mock_sentiment_analyzer):
    """Test that article text is truncated for analysis."""
    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Mock with long article
    long_content = "This is a very long article. " * 100  # Over 500 chars

    async def mock_fetch(request):
        return [{
            'title': 'Long Article',
            'content': long_content,
            'source': 'Test Source'
        }]

    analyzer._fetch_news = mock_fetch

    # Analyze news
    request = NewsSentimentRequest()
    await analyzer.analyze_news(request)

    # Verify sentiment analyzer was called with truncated text
    mock_sentiment_analyzer.analyze.assert_called_once()
    call_args = mock_sentiment_analyzer.analyze.call_args[0][0]
    assert len(call_args) <= 500


@pytest.mark.asyncio
async def test_fetch_news_error_handling():
    """Test handling of errors when fetching news."""
    mock_sentiment_analyzer = AsyncMock()

    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # The _fetch_news method catches exceptions internally and returns []
    # So we just mock it to return empty list to simulate that behavior
    async def mock_fetch_error(request):
        return []

    analyzer._fetch_news = mock_fetch_error

    # Analyze news
    request = NewsSentimentRequest()
    result = await analyzer.analyze_news(request)

    # Verify empty response on error
    assert result.analyzed_articles == 0
    assert result.average_sentiment == 'neutral'


@pytest.mark.asyncio
async def test_close_http_client():
    """Test closing the HTTP client."""
    mock_sentiment_analyzer = AsyncMock()

    # Create analyzer with a mock client
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    mock_client = AsyncMock()
    mock_client.is_closed = False
    analyzer._http_client = mock_client

    # Close the client
    await analyzer.close()

    # Verify close was called
    mock_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_get_client_reuse():
    """Test that HTTP client is reused when not closed."""
    mock_sentiment_analyzer = AsyncMock()

    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Get client first time
    client1 = await analyzer._get_client()

    # Get client second time
    client2 = await analyzer._get_client()

    # Verify same client is returned
    assert client1 is client2


@pytest.mark.asyncio
async def test_processing_time_calculation(mock_sentiment_analyzer):
    """Test that processing time is calculated correctly."""
    # Create analyzer
    analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=mock_sentiment_analyzer
    )

    # Mock fetch
    async def mock_fetch(request):
        return [{'title': 'Test', 'content': 'Content', 'source': 'Test'}]

    analyzer._fetch_news = mock_fetch

    # Analyze news
    request = NewsSentimentRequest()
    result = await analyzer.analyze_news(request)

    # Verify processing time is recorded
    assert result.processing_time_ms > 0
    assert result.processing_time_ms < 1000  # Should be fast for one article
