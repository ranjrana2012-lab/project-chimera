"""Integration tests for WorldMonitor + Sentiment Agent integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.context_enrichment import ContextEnricher
from src.core.news_sentiment_analyzer import NewsSentimentAnalyzer
from src.core.sentiment_analyzer import SentimentAnalyzer
from src.models.context import (
    GlobalContext,
    ContextEnrichmentOptions,
    NewsSentimentRequest,
    Threat,
    ThreatLevel,
    ThreatType
)


@pytest.fixture
def sample_worldmonitor_data():
    """Create sample WorldMonitor data for testing."""
    return {
        'global_context': GlobalContext(
            global_cii=65,
            country_summary={
                "US": {
                    "country_code": "US",
                    "country_cii": 70,
                    "trend": "stable",
                    "recent_events": ["New policy announced"],
                    "news_summary": "Political stability maintained",
                    "instability_factors": {}
                }
            },
            active_threats=[
                Threat(
                    level=ThreatLevel.MEDIUM,
                    type=ThreatType.CIVIL_UNREST,
                    title="Protests in capital",
                    source="Local News",
                    location="Capital City"
                )
            ],
            major_events=[
                {"title": "International Summit", "location": "Geneva", "date": "2025-03-01"}
            ],
            last_updated=datetime.now()
        ),
        'news_articles': [
            {
                'title': 'Economic recovery continues',
                'content': 'GDP growth shows positive trend.',
                'source': 'Financial Times',
                'published_at': '2025-03-01T10:00:00Z'
            },
            {
                'title': 'Trade negotiations progress',
                'content': 'New agreements expected soon.',
                'source': 'Bloomberg',
                'published_at': '2025-03-01T09:00:00Z'
            }
        ],
        'country_context': {
            'country_code': 'US',
            'country_cii': 70,
            'trend': 'stable',
            'recent_events': ['New policy announced'],
            'news_summary': 'Political stability maintained',
            'instability_factors': {}
        }
    }


@pytest.mark.asyncio
async def test_sentiment_with_context_enrichment(sample_worldmonitor_data):
    """Test end-to-end sentiment analysis with context enrichment."""
    # Create context enricher
    context_enricher = ContextEnricher("http://localhost:3001")

    # Mock the _fetch_context method
    async def mock_fetch():
        return sample_worldmonitor_data['global_context']

    context_enricher._fetch_context = mock_fetch

    # Create sentiment analyzer
    sentiment_analyzer = AsyncMock()
    sentiment_analyzer.analyze.return_value = {
        'sentiment': {
            'label': 'positive',
            'confidence': 0.75
        }
    }

    # Create news sentiment analyzer
    news_analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=sentiment_analyzer
    )

    # Mock news fetch
    async def mock_fetch_news(request):
        return sample_worldmonitor_data['news_articles']

    news_analyzer._fetch_news = mock_fetch_news

    # Test the full flow
    # 1. Get enriched context
    options = ContextEnrichmentOptions(
        include_context=True,
        include_threats=True,
        include_events=True,
        include_cii=True
    )
    context = await context_enricher.get_context(options)

    # Verify context enrichment
    assert context is not None
    assert context.global_cii == 65
    assert len(context.active_threats) == 1
    assert len(context.major_events) == 1

    # 2. Analyze news sentiment
    news_request = NewsSentimentRequest(
        sources=['Financial Times', 'Bloomberg'],
        max_articles=100
    )
    news_result = await news_analyzer.analyze_news(news_request)

    # Verify news sentiment analysis
    assert news_result.analyzed_articles == 2
    assert news_result.average_sentiment == 'positive'
    assert news_result.sentiment_distribution['positive'] == 2

    # 3. Verify combined data
    combined_result = {
        'context': context.model_dump(),
        'news_sentiment': news_result.model_dump()
    }

    assert 'context' in combined_result
    assert 'news_sentiment' in combined_result
    assert combined_result['context']['global_cii'] == 65
    assert combined_result['news_sentiment']['analyzed_articles'] == 2


@pytest.mark.asyncio
async def test_news_sentiment_analysis_e2e(sample_worldmonitor_data):
    """Test end-to-end news sentiment analysis with WorldMonitor integration."""
    # Create sentiment analyzer
    sentiment_analyzer = MagicMock(spec=SentimentAnalyzer)
    sentiment_analyzer.analyze = AsyncMock(return_value={
        'sentiment': {'label': 'positive', 'confidence': 0.80}
    })

    # Create news sentiment analyzer
    news_analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=sentiment_analyzer
    )

    # Mock _fetch_news
    async def mock_fetch_news(request):
        return sample_worldmonitor_data['news_articles']

    news_analyzer._fetch_news = mock_fetch_news

    # Create request with filters
    request = NewsSentimentRequest(
        sources=['Financial Times', 'Bloomberg'],
        categories=['economy', 'business'],
        hours=24,
        max_articles=500
    )

    # Analyze news
    result = await news_analyzer.analyze_news(request)

    # Verify complete analysis
    assert result.analyzed_articles == 2
    assert result.average_sentiment == 'positive'
    assert 'positive' in result.sentiment_distribution
    assert result.processing_time_ms > 0

    # Verify top articles are populated
    assert len(result.top_positive) > 0
    assert 'title' in result.top_positive[0]
    assert 'source' in result.top_positive[0]
    assert 'confidence' in result.top_positive[0]


@pytest.mark.asyncio
async def test_context_global_endpoint(sample_worldmonitor_data):
    """Test the /context/global endpoint integration."""
    # Create context enricher
    context_enricher = ContextEnricher("http://localhost:3001")

    # Mock _fetch_context
    async def mock_fetch():
        return sample_worldmonitor_data['global_context']

    context_enricher._fetch_context = mock_fetch

    # Fetch global context
    options = ContextEnrichmentOptions(include_context=True)
    result = await context_enricher.get_context(options)

    # Verify result
    assert result is not None
    assert result.global_cii == 65
    assert isinstance(result.active_threats, list)
    assert isinstance(result.major_events, list)
    assert isinstance(result.country_summary, dict)

    # Test with different filtering options
    options_filtered = ContextEnrichmentOptions(
        include_context=True,
        include_threats=False,
        include_events=False,
        include_cii=True
    )
    result_filtered = await context_enricher.get_context(options_filtered)

    assert result_filtered.global_cii == 65
    assert len(result_filtered.active_threats) == 0
    assert len(result_filtered.major_events) == 0


@pytest.mark.asyncio
async def test_context_country_endpoint(sample_worldmonitor_data):
    """Test the /context/country/{code} endpoint integration."""
    # Create context enricher
    context_enricher = ContextEnricher("http://localhost:3001")

    # Create a proper mock for the response
    class MockResponse:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            pass

    # Create a mock client
    class MockClient:
        def __init__(self, data):
            self._data = data
            self.calls = []

        async def get(self, url):
            self.calls.append(url)
            return MockResponse(self._data)

    mock_client = MockClient(sample_worldmonitor_data['country_context'])

    # Mock _get_client to return our mock client
    async def mock_get_client():
        return mock_client

    context_enricher._get_client = mock_get_client

    # Fetch country context
    result = await context_enricher.get_country_context("US")

    # Verify result
    assert result is not None
    assert result['country_code'] == 'US'
    assert result['country_cii'] == 70
    assert result['trend'] == 'stable'
    assert isinstance(result['recent_events'], list)
    assert 'news_summary' in result

    # Verify correct endpoint was called
    assert len(mock_client.calls) == 1
    assert "context/country/US" in mock_client.calls[0]


@pytest.mark.asyncio
async def test_context_caching_integration(sample_worldmonitor_data):
    """Test context caching behavior in integration scenario."""
    # Create context enricher
    context_enricher = ContextEnricher("http://localhost:3001")

    # Track fetch calls
    fetch_count = [0]

    async def mock_fetch():
        fetch_count[0] += 1
        return sample_worldmonitor_data['global_context']

    context_enricher._fetch_context = mock_fetch

    # First call - should fetch from sidecar
    options = ContextEnrichmentOptions(include_context=True)
    result1 = await context_enricher.get_context(options)

    # Verify first fetch
    assert fetch_count[0] == 1
    assert result1.global_cii == 65

    # Second call - should use cache
    result2 = await context_enricher.get_context(options)

    # Verify cache was used
    assert fetch_count[0] == 1
    assert result2.global_cii == 65

    # Verify consistency
    assert result1.model_dump() == result2.model_dump()


@pytest.mark.asyncio
async def test_sentiment_with_filtered_context(sample_worldmonitor_data):
    """Test sentiment analysis with various context filtering options."""
    # Create context enricher
    context_enricher = ContextEnricher("http://localhost:3001")

    # Mock _fetch_context
    async def mock_fetch():
        return sample_worldmonitor_data['global_context']

    context_enricher._fetch_context = mock_fetch

    # Test 1: Include only CII
    options_cii_only = ContextEnrichmentOptions(
        include_context=True,
        include_cii=True,
        include_threats=False,
        include_events=False
    )
    result_cii = await context_enricher.get_context(options_cii_only)
    assert result_cii.global_cii == 65
    assert len(result_cii.active_threats) == 0
    assert len(result_cii.major_events) == 0

    # Test 2: Include only threats
    options_threats_only = ContextEnrichmentOptions(
        include_context=True,
        include_cii=False,
        include_threats=True,
        include_events=False
    )
    result_threats = await context_enricher.get_context(options_threats_only)
    assert result_threats.global_cii == 0
    assert len(result_threats.active_threats) == 1
    assert len(result_threats.major_events) == 0

    # Test 3: Include all
    options_all = ContextEnrichmentOptions(
        include_context=True,
        include_cii=True,
        include_threats=True,
        include_events=True
    )
    result_all = await context_enricher.get_context(options_all)
    assert result_all.global_cii == 65
    assert len(result_all.active_threats) == 1
    assert len(result_all.major_events) == 1


@pytest.mark.asyncio
async def test_error_handling_integration():
    """Test error handling in integration scenarios."""
    # Test 1: WorldMonitor service unavailable
    context_enricher = ContextEnricher("http://localhost:3001")

    async def mock_fetch_error():
        raise Exception("Service unavailable")

    context_enricher._fetch_context = mock_fetch_error

    options = ContextEnrichmentOptions(include_context=True)
    result = await context_enricher.get_context(options)

    # Should return None when service is unavailable and no cache
    assert result is None

    # Test 2: News fetch failure
    sentiment_analyzer = AsyncMock()
    news_analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=sentiment_analyzer
    )

    # The _fetch_news method catches exceptions internally and returns []
    # So we just mock it to return empty list to simulate that behavior
    async def mock_fetch_news_error(request):
        return []

    news_analyzer._fetch_news = mock_fetch_news_error

    request = NewsSentimentRequest()
    news_result = await news_analyzer.analyze_news(request)

    # Should return empty result on error
    assert news_result.analyzed_articles == 0
    assert news_result.average_sentiment == 'neutral'


@pytest.mark.asyncio
async def test_concurrent_requests(sample_worldmonitor_data):
    """Test handling concurrent requests for context and news."""
    import asyncio

    # Create context enricher and news analyzer
    context_enricher = ContextEnricher("http://localhost:3001")

    # Create a proper sentiment analyzer mock
    async def mock_analyze(text):
        return {'sentiment': {'label': 'positive', 'confidence': 0.75}}

    sentiment_analyzer_mock = AsyncMock()
    sentiment_analyzer_mock.analyze = mock_analyze

    news_analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=sentiment_analyzer_mock
    )

    # Mock _fetch_context
    async def mock_fetch():
        return sample_worldmonitor_data['global_context']

    context_enricher._fetch_context = mock_fetch

    # Mock _fetch_news
    async def mock_fetch_news(request):
        return sample_worldmonitor_data['news_articles']

    news_analyzer._fetch_news = mock_fetch_news

    # Make concurrent requests
    options = ContextEnrichmentOptions(include_context=True)
    news_request = NewsSentimentRequest(max_articles=100)

    context_result, news_result = await asyncio.gather(
        context_enricher.get_context(options),
        news_analyzer.analyze_news(news_request)
    )

    # Verify both requests succeeded
    assert context_result.global_cii == 65
    assert news_result.analyzed_articles == 2


@pytest.mark.asyncio
async def test_sentiment_analyzer_with_multiple_articles():
    """Test news sentiment analyzer with multiple articles of varying sentiment."""
    # Create mock sentiment analyzer with varied results
    sentiment_analyzer = AsyncMock()
    call_count = [0]

    async def varied_sentiment(text):
        call_count[0] += 1
        sentiments = [
            {'label': 'positive', 'confidence': 0.90},
            {'label': 'positive', 'confidence': 0.75},
            {'label': 'negative', 'confidence': 0.85},
            {'label': 'neutral', 'confidence': 0.60},
            {'label': 'negative', 'confidence': 0.80}
        ]
        return {'sentiment': sentiments[call_count[0] - 1]}

    sentiment_analyzer.analyze = varied_sentiment

    # Create news analyzer
    news_analyzer = NewsSentimentAnalyzer(
        sidecar_url="http://localhost:3001",
        sentiment_analyzer=sentiment_analyzer
    )

    # Mock HTTP client with multiple articles
    articles = [
        {'title': f'Article {i}', 'content': 'Content', 'source': f'Source {i}'}
        for i in range(5)
    ]

    async def mock_fetch_news(request):
        return articles

    news_analyzer._fetch_news = mock_fetch_news

    # Analyze
    request = NewsSentimentRequest(max_articles=10)
    result = await news_analyzer.analyze_news(request)

    # Verify results
    assert result.analyzed_articles == 5
    assert result.sentiment_distribution['positive'] == 2
    assert result.sentiment_distribution['negative'] == 2
    assert result.sentiment_distribution['neutral'] == 1
    assert result.average_sentiment in ['positive', 'negative', 'neutral']
