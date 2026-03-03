"""Unit tests for Context Enrichment module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.context_enrichment import ContextEnricher
from src.models.context import (
    GlobalContext,
    ContextEnrichmentOptions,
    Threat,
    ThreatLevel,
    ThreatType
)


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = AsyncMock()
    return client


@pytest.fixture
def sample_global_context():
    """Create sample global context data."""
    return GlobalContext(
        global_cii=65,
        country_summary={
            "US": {
                "country_code": "US",
                "country_cii": 70,
                "trend": "stable",
                "recent_events": ["Election results announced"],
                "news_summary": "Peaceful transition of power",
                "instability_factors": {}
            },
            "FR": {
                "country_code": "FR",
                "country_cii": 85,
                "trend": "improving",
                "recent_events": [],
                "news_summary": "Economic growth continues",
                "instability_factors": {}
            }
        },
        active_threats=[
            Threat(
                level=ThreatLevel.HIGH,
                type=ThreatType.CONFLICT,
                title="Border dispute",
                source="Reuters",
                location="Eastern Europe"
            )
        ],
        major_events=[
            {"title": "Climate Summit", "location": "Geneva", "date": "2025-03-01"}
        ],
        last_updated=datetime.now()
    )


@pytest.fixture
def sample_country_context():
    """Create sample country context data."""
    return {
        "country_code": "DE",
        "country_cii": 75,
        "trend": "stable",
        "recent_events": ["New trade agreement signed"],
        "news_summary": "Economic indicators positive",
        "instability_factors": {
            "inflation": "low",
            "unemployment": "decreasing"
        }
    }


@pytest.mark.asyncio
async def test_context_fetch_success(sample_global_context):
    """Test successful context fetching from WorldMonitor sidecar."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")

    # Mock the _fetch_context method
    async def mock_fetch():
        return sample_global_context

    enricher._fetch_context = mock_fetch

    # Fetch context
    options = ContextEnrichmentOptions(include_context=True)
    result = await enricher.get_context(options)

    # Verify result
    assert result is not None
    assert result.global_cii == 65
    assert len(result.active_threats) == 1
    assert len(result.major_events) == 1


@pytest.mark.asyncio
async def test_context_caching(sample_global_context):
    """Test that context is cached and reused within TTL."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")

    # Track fetch calls
    fetch_count = [0]

    async def mock_fetch():
        fetch_count[0] += 1
        return sample_global_context

    enricher._fetch_context = mock_fetch

    # First call - should fetch from sidecar
    options = ContextEnrichmentOptions(include_context=True)
    result1 = await enricher.get_context(options)

    # Verify first call
    assert fetch_count[0] == 1
    assert result1.global_cii == 65

    # Second call within TTL - should use cache
    result2 = await enricher.get_context(options)

    # Verify cache was used (no additional fetch)
    assert fetch_count[0] == 1
    assert result2.global_cii == 65


@pytest.mark.asyncio
async def test_context_stale_fallback():
    """Test that stale context is returned when fetch fails."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")

    # Set up stale cache
    old_context = GlobalContext(
        global_cii=60,
        country_summary={},
        active_threats=[],
        major_events=[],
        last_updated=datetime.now() - timedelta(minutes=10)
    )
    enricher._context_cache = old_context

    # Mock failed fetch that raises exception
    async def mock_fetch_error():
        raise Exception("Service unavailable")

    enricher._fetch_context = mock_fetch_error

    options = ContextEnrichmentOptions(include_context=True)
    result = await enricher.get_context(options)

    # Verify stale context is returned
    assert result is not None
    assert result.global_cii == 60
    assert result.stale is True


@pytest.mark.asyncio
async def test_context_filtering_with_options(sample_global_context):
    """Test that context is filtered based on options."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")
    enricher._context_cache = sample_global_context

    # Test filtering out threats
    options_no_threats = ContextEnrichmentOptions(
        include_context=True,
        include_threats=False
    )
    result = enricher._filter_context(sample_global_context, options_no_threats)
    assert len(result.active_threats) == 0
    assert result.global_cii == 65

    # Test filtering out events
    options_no_events = ContextEnrichmentOptions(
        include_context=True,
        include_events=False
    )
    result = enricher._filter_context(sample_global_context, options_no_events)
    assert len(result.major_events) == 0
    assert len(result.active_threats) == 1

    # Test filtering out CII
    options_no_cii = ContextEnrichmentOptions(
        include_context=True,
        include_cii=False
    )
    result = enricher._filter_context(sample_global_context, options_no_cii)
    assert result.global_cii == 0

    # Test include_context=False
    with patch.object(enricher, '_fetch_context', return_value=sample_global_context):
        options_no_context = ContextEnrichmentOptions(include_context=False)
        result = await enricher.get_context(options_no_context)
        assert result is None


@pytest.mark.asyncio
async def test_get_country_context(sample_country_context):
    """Test fetching country-specific context."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")

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
        async def get(self, url):
            return MockResponse(sample_country_context)

    # Mock _get_client to return our mock client
    async def mock_get_client():
        return MockClient()

    enricher._get_client = mock_get_client

    # Fetch country context
    result = await enricher.get_country_context("DE")

    # Verify result
    assert result is not None
    assert result["country_code"] == "DE"
    assert result["country_cii"] == 75
    assert result["trend"] == "stable"


@pytest.mark.asyncio
async def test_context_fetch_failure_handling():
    """Test handling of context fetch failures."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")

    # Mock failed fetch with no cache
    with patch.object(enricher, '_fetch_context', return_value=None):
        options = ContextEnrichmentOptions(include_context=True)
        result = await enricher.get_context(options)

        # Verify None is returned
        assert result is None


@pytest.mark.asyncio
async def test_context_cache_expiry():
    """Test that cache expires after TTL."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")

    # Set up old cache (beyond TTL)
    old_context = GlobalContext(
        global_cii=55,
        country_summary={},
        active_threats=[],
        major_events=[],
        last_updated=datetime.now() - timedelta(minutes=6)  # Beyond 5 min TTL
    )
    enricher._context_cache = old_context
    enricher._cache_timestamp = datetime.now() - timedelta(minutes=6)

    # Mock new fetch
    new_context = GlobalContext(
        global_cii=70,
        country_summary={},
        active_threats=[],
        major_events=[],
        last_updated=datetime.now()
    )

    with patch.object(enricher, '_fetch_context', return_value=new_context):
        options = ContextEnrichmentOptions(include_context=True)
        result = await enricher.get_context(options)

        # Verify new context was fetched
        assert result.global_cii == 70


@pytest.mark.asyncio
async def test_close_http_client():
    """Test closing the HTTP client."""
    # Create context enricher with a mock client
    enricher = ContextEnricher("http://localhost:3001")
    mock_client = AsyncMock()
    mock_client.is_closed = False
    enricher._http_client = mock_client

    # Close the client
    await enricher.close()

    # Verify close was called
    mock_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_get_client_reuse():
    """Test that HTTP client is reused when not closed."""
    # Create context enricher
    enricher = ContextEnricher("http://localhost:3001")

    # Get client first time
    client1 = await enricher._get_client()

    # Get client second time
    client2 = await enricher._get_client()

    # Verify same client is returned
    assert client1 is client2
