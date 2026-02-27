"""Tests for SceneSpeak Agent routes."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import sys


# Mock torch and transformers before importing anything else
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['bitsandbytes'] = MagicMock()
sys.modules['accelerate'] = MagicMock()

# Import after mocking
from fastapi.testclient import TestClient


@pytest.fixture
def mock_engine():
    """Mock LLM engine."""
    engine = Mock()
    engine._build_prompt = Mock(return_value="test prompt")
    mock_response = Mock(
        request_id="test-123",
        dialogue="Test dialogue",
        character="Alice",
        sentiment_used=0.5,
        tokens=10,
        confidence=0.9,
        from_cache=False,
        generation_time_ms=100.0,
        model_version="v1.0",
        timestamp=datetime.now(),
    )
    mock_response.model_dump = Mock(return_value={
        "request_id": "test-123",
        "dialogue": "Test dialogue",
        "character": "Alice",
        "sentiment_used": 0.5,
        "tokens": 10,
        "confidence": 0.9,
        "from_cache": False,
        "generation_time_ms": 100.0,
        "model_version": "v1.0"
    })
    engine.generate = AsyncMock(return_value=mock_response)
    return engine


@pytest.fixture
def mock_cache():
    """Mock response cache."""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def app_with_mocks(mock_engine, mock_cache):
    """Create FastAPI app with mocked dependencies."""
    from src.main import app
    from src.routes import generation

    # Set the mocked engine and cache
    generation._engine = mock_engine
    generation._cache = mock_cache

    return app


@pytest.mark.asyncio
class TestHealthRoutes:
    """Tests for health check routes."""

    async def test_liveness_probe(self, app_with_mocks):
        """Test /health/live endpoint."""
        client = TestClient(app_with_mocks)
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.text == '"OK"'

    async def test_readiness_probe(self, app_with_mocks):
        """Test /health/ready endpoint."""
        client = TestClient(app_with_mocks)
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "uptime" in data
        assert data["ready"] is True
        assert data["uptime"] >= 0


@pytest.mark.asyncio
class TestGenerationRoutes:
    """Tests for generation routes."""

    async def test_generate_success(self, app_with_mocks):
        """Test successful generation."""
        client = TestClient(app_with_mocks)

        request_data = {
            "context": "A sunny garden",
            "character": "Alice",
            "sentiment": 0.5,
            "max_tokens": 256,
            "temperature": 0.8,
            "top_p": 0.95,
            "use_cache": False
        }

        response = client.post("/v1/generate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "dialogue" in data
        assert data["character"] == "Alice"
        assert data["from_cache"] is False

    async def test_generate_with_cache_hit(self, app_with_mocks, mock_cache):
        """Test generation with cache hit."""
        from src.routes import generation

        cached_response = {
            "request_id": "cached-123",
            "dialogue": "Cached dialogue",
            "character": "Alice",
            "sentiment_used": 0.5,
            "tokens": 10,
            "confidence": 0.9,
            "from_cache": True,
            "generation_time_ms": 50.0,
            "model_version": "v1.0",
            "timestamp": "2026-02-27T10:30:00Z"
        }
        mock_cache.get.return_value = cached_response

        client = TestClient(app_with_mocks)

        request_data = {
            "context": "A sunny garden",
            "character": "Alice",
            "sentiment": 0.5,
            "use_cache": True
        }

        response = client.post("/v1/generate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["dialogue"] == "Cached dialogue"

    async def test_generate_error(self, app_with_mocks, mock_engine):
        """Test generation error handling."""
        from src.routes import generation

        mock_engine.generate.side_effect = Exception("Generation failed")

        client = TestClient(app_with_mocks)

        request_data = {
            "context": "A sunny garden",
            "character": "Alice",
            "use_cache": False
        }

        response = client.post("/v1/generate", json=request_data)
        assert response.status_code == 500

    async def test_generate_validation_error(self, app_with_mocks):
        """Test request validation."""
        client = TestClient(app_with_mocks)

        request_data = {
            "context": "",  # Invalid: empty context
            "character": "Alice"
        }

        response = client.post("/v1/generate", json=request_data)
        assert response.status_code == 422


class TestResponseCache:
    """Tests for ResponseCache."""

    def test_make_key(self):
        """Test cache key generation."""
        from src.core.caches.response_cache import ResponseCache

        cache = ResponseCache()
        key1 = cache._make_key("prompt", {"temp": 0.5})
        key2 = cache._make_key("prompt", {"temp": 0.5})
        key3 = cache._make_key("prompt", {"temp": 0.8})

        assert key1 == key2
        assert key1 != key3
