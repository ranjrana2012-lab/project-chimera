"""Translation engine with caching and BSL integration.

Iteration 35: Added Google Translate API support for real translations.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any

import httpx

from .config import get_settings
from .models import TranslationRequest, TranslationResponse, TranslationStatus

logger = logging.getLogger(__name__)


class TranslationCache:
    """Simple in-memory cache for translations."""

    def __init__(self, ttl: int = 3600):
        """Initialize cache with TTL in seconds."""
        self._cache: dict[str, tuple[TranslationResponse, float]] = {}
        self._ttl = ttl

    def _generate_key(self, request: TranslationRequest) -> str:
        """Generate cache key from request."""
        content = f"{request.text}:{request.source_language}:{request.target_language}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, request: TranslationRequest) -> TranslationResponse | None:
        """Get cached translation if available and not expired."""
        key = self._generate_key(request)
        if key not in self._cache:
            return None

        response, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None

        return response

    def set(self, request: TranslationRequest, response: TranslationResponse) -> None:
        """Cache translation response."""
        key = self._generate_key(request)
        # Create a new response with cached=True
        cached_response = TranslationResponse(
            translated_text=response.translated_text,
            source_language=response.source_language,
            target_language=response.target_language,
            status=response.status,
            confidence=response.confidence,
            cached=True,
            error=response.error,
        )
        self._cache[key] = (cached_response, time.time())

    def clear(self) -> None:
        """Clear all cached translations."""
        self._cache.clear()


class GoogleTranslator:
    """Google Cloud Translation API integration (Iteration 35).

    Provides real translations using Google Cloud Translation API v2.
    Falls back to mock if API key is not configured or on errors.
    """

    def __init__(self, api_key: str, project_id: str, api_url: str):
        """Initialize Google translator.

        Args:
            api_key: Google Cloud API key
            project_id: Google Cloud project ID
            api_url: Google Translate API endpoint
        """
        self.api_key = api_key
        self.project_id = project_id
        self.api_url = api_url
        self._client = httpx.AsyncClient(timeout=30.0)

    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """Translate text using Google Cloud Translation API.

        Args:
            request: Translation request with text and language codes

        Returns:
            TranslationResponse with translated text

        Falls back to mock translation on API errors.
        """
        try:
            # Prepare API request
            params = {
                "key": self.api_key,
                "q": request.text,
                "source": request.source_language,
                "target": request.target_language,
                "format": "text"
            }

            # Call Google Translate API
            response = await self._client.get(
                self.api_url,
                params=params
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            translations = data.get("data", {}).get("translations", [])
            if not translations:
                logger.error("No translations in API response")
                return await MockTranslator.translate(request)

            translated_text = translations[0].get("translatedText", request.text)
            detected_source = translations[0].get("detectedSourceLanguage", request.source_language)

            logger.info(
                f"Google Translate: {request.source_language} -> {request.target_language}"
            )

            return TranslationResponse(
                translated_text=translated_text,
                source_language=detected_source,
                target_language=request.target_language,
                status=TranslationStatus.COMPLETED,
                confidence=0.98,  # Google Translate has high accuracy
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning("Google Translate API quota exceeded or invalid key")
            else:
                logger.warning(f"Google Translate API error: {e.response.status_code}")
            # Fallback to mock
            return await MockTranslator.translate(request)

        except Exception as e:
            logger.warning(f"Google Translate failed: {e}")
            # Fallback to mock
            return await MockTranslator.translate(request)

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class MockTranslator:
    """Mock translation service for development/testing."""

    # Simple prefix-based mock translations
    _mock_prefixes: dict[str, str] = {
        "es": "[ES] ",
        "fr": "[FR] ",
        "de": "[DE] ",
        "it": "[IT] ",
        "pt": "[PT] ",
        "nl": "[NL] ",
        "pl": "[PL] ",
        "ru": "[RU] ",
        "zh": "[ZH] ",
        "ja": "[JA] ",
        "ko": "[KO] ",
        "ar": "[AR] ",
        "hi": "[HI] ",
        "bsl": "[BSL] ",
    }

    @classmethod
    async def translate(cls, request: TranslationRequest) -> TranslationResponse:
        """Mock translation that adds language prefix."""
        await asyncio.sleep(0.01)  # Simulate API delay

        prefix = cls._mock_prefixes.get(request.target_language, f"[{request.target_language.upper()}] ")
        translated = prefix + request.text

        return TranslationResponse(
            translated_text=translated,
            source_language=request.source_language,
            target_language=request.target_language,
            status=TranslationStatus.COMPLETED,
            confidence=0.95,
        )


class BSLTranslator:
    """British Sign Language translation via BSL avatar service."""

    def __init__(self, bsl_service_url: str):
        """Initialize BSL translator with service URL."""
        self._bsl_service_url = bsl_service_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=10.0)

    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """Translate to BSL using avatar service."""
        try:
            # Check if BSL service is available
            response = await self._client.get(f"{self._bsl_service_url}/health")
            if response.status_code != 200:
                logger.warning(f"BSL service unhealthy: {response.status_code}")
                # Fall back to mock translation
                return await MockTranslator.translate(request)

            # Call BSL translation endpoint
            payload = {"text": request.text}
            response = await self._client.post(
                f"{self._bsl_service_url}/translate",
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                return TranslationResponse(
                    translated_text=data.get("translated_text", request.text),
                    source_language=request.source_language,
                    target_language=request.target_language,
                    status=TranslationStatus.COMPLETED,
                    confidence=0.90,
                )
            else:
                logger.error(f"BSL translation failed: {response.status_code}")
                return await MockTranslator.translate(request)

        except httpx.ConnectError:
            logger.warning("BSL service unavailable, using mock translation")
            return await MockTranslator.translate(request)
        except Exception as e:
            logger.exception(f"BSL translation error: {e}")
            return TranslationResponse(
                translated_text=request.text,
                source_language=request.source_language,
                target_language=request.target_language,
                status=TranslationStatus.FAILED,
                error=str(e),
            )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class TranslationEngine:
    """
    Main translation engine with caching (Iteration 35).

    Routes to Google Translate API when configured, otherwise uses mock.
    """

    def __init__(self, settings: Any | None = None):
        """Initialize translation engine."""
        self._settings = settings or get_settings()
        self._cache = TranslationCache(ttl=self._settings.cache_ttl)
        self._bsl_translator = BSLTranslator(self._settings.bsl_service_url)

        # Initialize Google translator if API key is configured (Iteration 35)
        self._google_translator = None
        if self._settings.has_google_api_key:
            self._google_translator = GoogleTranslator(
                api_key=self._settings.google_translate_api_key,
                project_id=self._settings.google_translate_project_id,
                api_url=self._settings.google_api_url
            )
            logger.info("Google Translate API configured")

    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """Translate text with caching."""
        # Check cache first
        cached = self._cache.get(request)
        if cached:
            logger.debug(f"Cache hit for translation: {request.text[:50]}...")
            return cached

        # Route to appropriate translator
        if request.target_language == "bsl":
            response = await self._bsl_translator.translate(request)
        elif self._google_translator and not self._settings.use_mock:
            # Use real Google Translate API (Iteration 35)
            response = await self._google_translator.translate(request)
        else:
            # Use mock translation
            response = await MockTranslator.translate(request)

        # Cache successful translations
        if response.status == TranslationStatus.COMPLETED:
            self._cache.set(request, response)

        return response

    def clear_cache(self) -> None:
        """Clear translation cache."""
        self._cache.clear()

    async def health_check(self) -> dict[str, Any]:
        """Check health of translation services."""
        status = {
            "cache_size": len(self._cache._cache),
            "mock_mode": self._settings.use_mock,
            "google_api_configured": self._settings.has_google_api_key,
            "bsl_service": "unknown",
        }

        # Check BSL service health
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self._settings.bsl_service_url}/health")
                status["bsl_service"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception:
            status["bsl_service"] = "unreachable"

        return status

    async def close(self) -> None:
        """Close resources."""
        await self._bsl_translator.close()
        if self._google_translator:
            await self._google_translator.close()
