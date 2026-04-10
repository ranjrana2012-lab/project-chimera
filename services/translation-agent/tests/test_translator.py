"""Tests for Translation Engine."""

import pytest
from unittest.mock import AsyncMock, patch

from translation_agent.models import TranslationRequest, TranslationStatus
from translation_agent.translator import (
    TranslationCache,
    MockTranslator,
    BSLTranslator,
    TranslationEngine,
)


class TestTranslationCache:
    """Tests for TranslationCache."""

    @pytest.fixture
    def cache(self):
        """Create cache instance with short TTL."""
        return TranslationCache(ttl=1)

    @pytest.fixture
    def sample_request(self):
        """Create sample translation request."""
        return TranslationRequest(
            text="Hello world",
            source_language="en",
            target_language="es",
        )

    def test_cache_miss(self, cache, sample_request):
        """Test cache miss returns None."""
        result = cache.get(sample_request)
        assert result is None

    def test_cache_hit(self, cache, sample_request):
        """Test cache hit returns cached response."""
        from translation_agent.models import TranslationResponse

        response = TranslationResponse(
            translated_text="Hola mundo",
            source_language="en",
            target_language="es",
            status=TranslationStatus.COMPLETED,
        )

        cache.set(sample_request, response)
        result = cache.get(sample_request)

        assert result is not None
        assert result.translated_text == "Hola mundo"
        assert result.cached is True

    def test_cache_expiry(self, cache, sample_request):
        """Test cache expires after TTL."""
        import time

        from translation_agent.models import TranslationResponse

        response = TranslationResponse(
            translated_text="Hola mundo",
            source_language="en",
            target_language="es",
            status=TranslationStatus.COMPLETED,
        )

        cache.set(sample_request, response)
        time.sleep(1.1)  # Wait for TTL to expire

        result = cache.get(sample_request)
        assert result is None

    def test_cache_clear(self, cache, sample_request):
        """Test clearing cache."""
        from translation_agent.models import TranslationResponse

        response = TranslationResponse(
            translated_text="Hola mundo",
            source_language="en",
            target_language="es",
            status=TranslationStatus.COMPLETED,
        )

        cache.set(sample_request, response)
        cache.clear()

        result = cache.get(sample_request)
        assert result is None


class TestMockTranslator:
    """Tests for MockTranslator."""

    @pytest.mark.asyncio
    async def test_translate_adds_prefix(self):
        """Test mock translation adds language prefix."""
        request = TranslationRequest(
            text="Hello world",
            source_language="en",
            target_language="es",
        )

        response = await MockTranslator.translate(request)

        assert response.status == TranslationStatus.COMPLETED
        assert response.translated_text == "[ES] Hello world"
        assert response.confidence == 0.95

    @pytest.mark.asyncio
    async def test_translate_unknown_language(self):
        """Test translation with unknown language code."""
        request = TranslationRequest(
            text="Hello",
            source_language="en",
            target_language="xx",
        )

        response = await MockTranslator.translate(request)

        assert response.status == TranslationStatus.COMPLETED
        assert response.translated_text == "[XX] Hello"


class TestTranslationEngine:
    """Tests for TranslationEngine."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        class MockSettings:
            service_name = "translation-agent"
            use_mock = True
            cache_ttl = 3600
            bsl_service_url = "http://localhost:8005"

        return MockSettings()

    @pytest.fixture
    def engine(self, mock_settings):
        """Create translation engine with mock settings."""
        return TranslationEngine(mock_settings)

    @pytest.mark.asyncio
    async def test_translate_with_cache(self, engine):
        """Test translation uses cache."""
        request = TranslationRequest(
            text="Hello world",
            source_language="en",
            target_language="es",
        )

        # First call - cache miss
        response1 = await engine.translate(request)
        assert response1.cached is False

        # Second call - cache hit
        response2 = await engine.translate(request)
        assert response2.cached is True
        assert response2.translated_text == response1.translated_text

    @pytest.mark.asyncio
    async def test_translate_bsl_routes_to_bsl_translator(self, engine):
        """Test BSL translation routes to BSL translator."""
        request = TranslationRequest(
            text="Hello",
            source_language="en",
            target_language="bsl",
        )

        with patch.object(
            engine._bsl_translator,
            "translate",
            new_callable=AsyncMock,
        ) as mock_bsl:
            from translation_agent.models import TranslationResponse

            mock_bsl.return_value = TranslationResponse(
                translated_text="[BSL] Hello",
                source_language="en",
                target_language="bsl",
                status=TranslationStatus.COMPLETED,
            )

            response = await engine.translate(request)

            mock_bsl.assert_called_once()
            assert response.target_language == "bsl"

    @pytest.mark.asyncio
    async def test_clear_cache(self, engine):
        """Test clearing cache."""
        request = TranslationRequest(
            text="Hello",
            source_language="en",
            target_language="es",
        )

        # Populate cache
        await engine.translate(request)
        assert engine._cache.get(request) is not None

        # Clear cache
        engine.clear_cache()
        assert engine._cache.get(request) is None

    @pytest.mark.asyncio
    async def test_health_check(self, engine):
        """Test health check returns engine status."""
        health = await engine.health_check()

        assert "cache_size" in health
        assert "mock_mode" in health
        assert "bsl_service" in health
        assert health["mock_mode"] is True
