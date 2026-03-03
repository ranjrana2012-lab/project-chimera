"""
Captioning Agent - Transcription Module

Implements Whisper API integration with robust fallback logic:
- Connection timeout handling with cache fallback
- HTTP 500 error handling with retries
- Rate limit (429) handling with retry-after
- Redis caching for transcriptions
- Degraded mode when Redis unavailable
"""

import time
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional, BinaryIO
from datetime import datetime

import requests
from requests.exceptions import Timeout, HTTPError, ConnectionError


# Configure logging
logger = logging.getLogger(__name__)


# Custom Exceptions
class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    pass


class WhisperTimeoutError(TranscriptionError):
    """Whisper API timeout occurred."""
    pass


class WhisperServerError(TranscriptionError):
    """Whisper API returned server error."""
    pass


class RateLimitError(TranscriptionError):
    """Whisper API rate limit exceeded."""
    pass


# Response Models
@dataclass
class TranscriptionResponse:
    """Response model for transcription requests - matches deep dive requirements."""
    request_id: str
    text: str
    language: str
    duration: float
    confidence: float
    processing_time_ms: float
    model_version: str = "whisper-1"
    error: Optional[dict] = None
    warning: Optional[dict] = None
    from_cache: bool = False
    degraded: bool = False
    status: str = "completed"  # completed, queued, failed


@dataclass
class QueuedResponse:
    """Response for rate-limited requests."""
    request_id: str
    status: str = "queued"
    retry_after: int = 60
    error: dict = field(default_factory=lambda: {
        "code": "RATE_LIMITED",
        "message": "Request queued due to rate limit"
    })


class TranscriptionService:
    """
    Whisper API transcription service with fallback logic.

    Features:
    - Automatic retries with exponential backoff
    - Redis caching of transcriptions
    - Fallback to cache/placeholder on errors
    - Degraded mode when Redis unavailable
    """

    WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
    CACHE_TTL = 86400  # 24 hours in seconds
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds

    def __init__(self, whisper_api_key: str, redis_client=None):
        """
        Initialize transcription service.

        Args:
            whisper_api_key: OpenAI API key for Whisper
            redis_client: Optional Redis client for caching
        """
        self.whisper_api_key = whisper_api_key
        self.redis = redis_client
        self.degraded_mode = False

        if redis_client is None:
            logger.warning("No Redis client provided - caching disabled")
            self.degraded_mode = True

    def transcribe(
        self,
        audio_data: bytes,
        audio_hash: str,
        language: Optional[str] = None
    ) -> TranscriptionResponse:
        """
        Transcribe audio data using Whisper API with fallback logic.

        Args:
            audio_data: Raw audio bytes
            audio_hash: Hash of audio for caching
            language: Optional language hint (e.g., 'en')

        Returns:
            TranscriptionResponse with text or error placeholder
        """
        start_time = time.time()
        request_id = f"req_{int(time.time() * 1000)}"

        # Try cache first
        cached_result = self._get_from_cache(audio_hash)
        if cached_result:
            processing_time = (time.time() - start_time) * 1000
            return TranscriptionResponse(
                request_id=request_id,
                text=cached_result,
                language="en",
                duration=0.0,
                confidence=1.0,
                processing_time_ms=processing_time,
                from_cache=True
            )

        # Call Whisper API with retry logic
        result = self._transcribe_with_retry(
            audio_data, audio_hash, language, request_id
        )

        # Cache successful transcription (no errors, status is completed)
        if result.error is None and result.status == "completed":
            self._cache_transcription(audio_hash, result.text)

        return result

    def _get_from_cache(self, audio_hash: str) -> Optional[str]:
        """Get transcription from Redis cache."""
        if not self.redis:
            return None

        try:
            cache_key = f"caption:{audio_hash}"
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {audio_hash}")
                return cached.decode()
        except Exception as e:
            logger.warning(f"Redis get failed: {e}. Entering degraded mode.")
            self.degraded_mode = True

        return None

    def _cache_transcription(self, audio_hash: str, text: str):
        """Cache transcription in Redis."""
        if not self.redis:
            return

        try:
            cache_key = f"caption:{audio_hash}"
            self.redis.setex(cache_key, self.CACHE_TTL, text)
            logger.debug(f"Cached transcription for {audio_hash}")
        except Exception as e:
            logger.warning(f"Redis set failed: {e}. Entering degraded mode.")
            self.degraded_mode = True

    def _transcribe_with_retry(
        self,
        audio_data: bytes,
        audio_hash: str,
        language: Optional[str],
        request_id: str
    ) -> TranscriptionResponse:
        """
        Transcribe with retry logic for transient failures.

        Handles:
        - Timeouts (retry 3x with backoff)
        - 500 errors (retry 3x with backoff)
        - 429 rate limit (no retry, return queued)
        - 401 auth (no retry, critical error)
        """
        retry_count = 0
        last_error = None

        while retry_count <= self.MAX_RETRIES:
            try:
                return self._call_whisper_api(audio_data, language, request_id)

            except Timeout as e:
                last_error = e
                logger.warning(f"Timeout on attempt {retry_count + 1}")
                retry_count += 1

                if retry_count <= self.MAX_RETRIES:
                    delay = self.RETRY_DELAYS[min(retry_count - 1, 2)]
                    time.sleep(delay)

            except HTTPError as e:
                # Get status code from response if available
                status_code = None
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code

                # Handle rate limiting (429) - no retry
                if status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    logger.info(f"Rate limited, retry after {retry_after}s")
                    return TranscriptionResponse(
                        request_id=request_id,
                        text="",
                        language="",
                        duration=0.0,
                        confidence=0.0,
                        processing_time_ms=0.0,
                        error={"code": "RATE_LIMITED", "message": "Request queued"},
                        status="queued",
                        degraded=self.degraded_mode
                    )

                # Handle auth errors (401) - no retry, critical
                if status_code == 401:
                    logger.error("Whisper API authentication failed")
                    return TranscriptionResponse(
                        request_id=request_id,
                        text="",
                        language="",
                        duration=0.0,
                        confidence=0.0,
                        processing_time_ms=0.0,
                        error={"code": "AUTH_ERROR", "message": "API authentication failed"},
                        status="failed",
                        degraded=self.degraded_mode
                    )

                # Handle server errors (500, 502, 503) - retry
                if status_code and 500 <= status_code < 600:
                    last_error = e
                    logger.warning(f"Server error {status_code} on attempt {retry_count + 1}")
                    retry_count += 1

                    if retry_count <= self.MAX_RETRIES:
                        delay = self.RETRY_DELAYS[min(retry_count - 1, 2)]
                        time.sleep(delay)
                    continue

                # Other errors - don't retry
                last_error = e
                break

        # All retries exhausted - return cached or placeholder
        cached = self._get_from_cache(audio_hash)
        if cached:
            return TranscriptionResponse(
                request_id=request_id,
                text=cached,
                language="en",
                duration=0.0,
                confidence=0.0,
                processing_time_ms=0.0,
                from_cache=True,
                degraded=self.degraded_mode
            )

        # Return placeholder
        error_code = "TIMEOUT" if isinstance(last_error, Timeout) else "SERVER_ERROR"
        return TranscriptionResponse(
            request_id=request_id,
            text=f"[Transcription unavailable - connection timeout]",
            language="en",
            duration=0.0,
            confidence=0.0,
            processing_time_ms=0.0,
            error={"code": "TIMEOUT", "message": f"Whisper API failed: {error_code}"},
            status="failed",
            degraded=self.degraded_mode
        )

    def _call_whisper_api(
        self,
        audio_data: bytes,
        language: Optional[str],
        request_id: str
    ) -> TranscriptionResponse:
        """
        Call Whisper API directly.

        Raises:
            Timeout: If API call times out
            HTTPError: If API returns error status
        """
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.whisper_api_key}"
        }

        files = {
            "file": ("audio.mp3", audio_data, "audio/mpeg")
        }

        data = {
            "model": "whisper-1",
            "response_format": "verbose_json"
        }

        if language:
            data["language"] = language

        response = requests.post(
            self.WHISPER_API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()
        processing_time = (time.time() - start_time) * 1000

        return TranscriptionResponse(
            request_id=request_id,
            text=result.get("text", ""),
            language=result.get("language", "en"),
            duration=result.get("duration", 0.0),
            confidence=self._calculate_confidence(result),
            processing_time_ms=processing_time,
            degraded=self.degraded_mode
        )

    def _calculate_confidence(self, whisper_result: dict) -> float:
        """Calculate average confidence from Whisper response."""
        if "segments" not in whisper_result:
            return 0.95  # Default confidence

        segments = whisper_result["segments"]
        if not segments:
            return 0.0

        confidences = [s.get("avg_logprob", 0.0) for s in segments]
        # Convert logprob to rough confidence (0-1)
        avg_logprob = sum(confidences) / len(confidences)
        confidence = max(0.0, min(1.0, (avg_logprob + 2) / 4))

        return confidence
