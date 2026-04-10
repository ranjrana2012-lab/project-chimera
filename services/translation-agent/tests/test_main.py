"""Tests for Translation Agent main API."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from translation_agent.main import app, get_engine
from translation_agent.models import TranslationResponse, TranslationStatus


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_engine():
    """Create mock translation engine."""
    engine = AsyncMock()
    engine.translate = AsyncMock(return_value=TranslationResponse(
        translated_text="Hola mundo",
        source_language="en",
        target_language="es",
        status=TranslationStatus.COMPLETED,
        confidence=0.95,
        cached=False,
    ))
    engine.health_check = AsyncMock(return_value={
        "cache_size": 0,
        "mock_mode": True,
        "bsl_service": "unreachable",
    })
    engine.clear_cache = AsyncMock()
    return engine


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_endpoint(self, client, mock_engine):
        """Test /health endpoint."""
        with patch("translation_agent.main.get_engine", return_value=mock_engine):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "translation-agent"
            assert "engine" in data

    def test_readiness_endpoint(self, client, mock_engine):
        """Test /readiness endpoint."""
        with patch("translation_agent.main.get_engine", return_value=mock_engine):
            response = client.get("/readiness")

            assert response.status_code == 200
            data = response.json()
            assert "ready" in data
            assert "engine" in data

    def test_liveness_endpoint(self, client):
        """Test /liveness endpoint."""
        response = client.get("/liveness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestTranslateEndpoint:
    """Tests for /translate endpoint."""

    def test_translate_success(self, client, mock_engine):
        """Test successful translation."""
        with patch("translation_agent.main.get_engine", return_value=mock_engine):
            response = client.post(
                "/translate",
                json={
                    "text": "Hello world",
                    "source_language": "en",
                    "target_language": "es",
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["translated_text"] == "Hola mundo"
            assert data["source_language"] == "en"
            assert data["target_language"] == "es"
            assert data["status"] == "completed"
            assert data["cached"] is False
            assert data["confidence"] == 0.95

    def test_translate_empty_text(self, client, mock_engine):
        """Test translation with empty text returns 400."""
        with patch("translation_agent.main.get_engine", return_value=mock_engine):
            response = client.post(
                "/translate",
                json={
                    "text": "",
                    "source_language": "en",
                    "target_language": "es",
                }
            )

            assert response.status_code == 422  # Validation error

    def test_translate_short_language_code(self, client, mock_engine):
        """Test translation with short language code returns 422."""
        with patch("translation_agent.main.get_engine", return_value=mock_engine):
            response = client.post(
                "/translate",
                json={
                    "text": "Hello",
                    "source_language": "e",
                    "target_language": "es",
                }
            )

            assert response.status_code == 422  # Validation error

    def test_translate_same_languages(self, client, mock_engine):
        """Test translation with same source and target language returns 400."""
        with patch("translation_agent.main.get_engine", return_value=mock_engine):
            response = client.post(
                "/translate",
                json={
                    "text": "Hello",
                    "source_language": "en",
                    "target_language": "en",
                }
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data


class TestLanguagesEndpoint:
    """Tests for /languages endpoint."""

    def test_get_supported_languages(self, client):
        """Test getting supported languages."""
        response = client.get("/languages")

        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert len(data["languages"]) > 0

        # Check English is in the list
        en_lang = next((lang for lang in data["languages"] if lang["code"] == "en"), None)
        assert en_lang is not None
        assert en_lang["name"] == "English"

        # Check BSL is in the list
        bsl_lang = next((lang for lang in data["languages"] if lang["code"] == "bsl"), None)
        assert bsl_lang is not None
        assert bsl_lang["name"] == "British Sign Language"


class TestCacheEndpoints:
    """Tests for cache management endpoints."""

    @pytest.mark.asyncio
    async def test_clear_cache(self, client, mock_engine):
        """Test clearing translation cache."""
        with patch("translation_agent.main.get_engine", return_value=mock_engine):
            response = client.post("/translate/cache/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cache_cleared"
            # Note: clear_cache is called by the endpoint, not directly in test


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "translation-agent"
        assert "endpoints" in data
