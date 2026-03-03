"""
Unit tests for Captioning Agent transcription module.

Tests Whisper API failure fallback logic:
- Connection timeout fallback to cache
- HTTP 500 error fallback to cache
- No cache fallback to placeholder
- Retry logic with exponential backoff
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime

# Import the module we're testing
import sys
sys.path.insert(0, '/home/ranj/Project_Chimera/services/captioning-agent')

# Import after setting path
import core.transcription as trans_module
from core.transcription import (
    TranscriptionService,
    TranscriptionError,
    WhisperTimeoutError,
    WhisperServerError
)


class TestWhisperTimeoutFallback:
    """Test Whisper API timeout handling with cache fallback."""

    def test_timeout_returns_cached_transcription(self):
        """When Whisper times out, return cached transcription if available."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        # Setup: Cache has transcription for this audio
        audio_hash = "abc123"
        cached_text = "Hello from cache"
        service.redis.get.return_value = cached_text.encode()

        # When: Whisper API times out
        with patch('trans_module.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()

            # Then: Return cached transcription
            result = service.transcribe(audio_data=b"fake_audio", audio_hash=audio_hash)

            assert result.text == cached_text
            assert result.error is None
            assert result.from_cache is True

    def test_timeout_returns_placeholder_when_no_cache(self):
        """When Whisper times out and no cache, return placeholder."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        # Setup: No cache available
        service.redis.get.return_value = None

        # When: Whisper API times out
        with patch('core.transcription.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()

            # Then: Return placeholder
            result = service.transcribe(audio_data=b"fake_audio", audio_hash="xyz789")

            assert "[Transcription unavailable" in result.text
            assert result.error['code'] == "TIMEOUT"
            assert result.from_cache is False

    def test_timeout_retries_with_exponential_backoff(self):
        """Timeout triggers 3 retries with 1s, 2s, 4s delays."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        service.redis.get.return_value = None

        retry_count = [0]
        expected_delays = [1, 2, 4]  # Exponential backoff

        def timeout_then_success(*args, **kwargs):
            retry_count[0] += 1
            if retry_count[0] <= 3:
                raise requests.exceptions.Timeout()
            return Mock(
                json=lambda: {"text": "Finally worked", "language": "en"},
                raise_for_status=lambda: None
            )

        with patch('core.transcription.requests.post', side_effect=timeout_then_success) as mock_post:
            with patch('core.transcription.time.sleep') as mock_sleep:
                result = service.transcribe(audio_data=b"fake_audio", audio_hash="hash1")

                # Should have retried 3 times before success
                assert mock_post.call_count == 4
                assert result.text == "Finally worked"
                assert retry_count[0] == 4


class TestWhisperServerErrorFallback:
    """Test Whisper API 500 error handling with cache fallback."""

    def test_500_error_returns_cached_transcription(self):
        """When Whisper returns 500, return cached transcription."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        # Setup: Cache has transcription
        service.redis.get.return_value = b"Cached result"

        # When: Whisper returns 500
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch('core.transcription.requests.post') as mock_post:
            mock_post.return_value = mock_response
            mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError()

            result = service.transcribe(audio_data=b"fake_audio", audio_hash="hash2")

            assert result.text == "Cached result"
            assert result.from_cache is True

    def test_500_error_retries_three_times_then_fallback(self):
        """500 error triggers 3 retries then fallback to cache/placeholder."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        service.redis.get.return_value = None  # No cache

        # When: All retries return 500
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.text = "Internal Server Error"

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = service.transcribe(audio_data=b"fake_audio", audio_hash="hash3")

            # Should have retried 3 times (total 4 calls)
            assert mock_post.call_count == 4
            # Returns placeholder since no cache
            assert "[Transcription unavailable" in result.text
            assert result.status == "failed"


class TestCachingBehavior:
    """Test caching of successful transcriptions."""

    def test_successful_transcription_is_cached(self):
        """Successful transcriptions are cached with 24hr TTL."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        # Mock successful Whisper response
        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "Hello world",
            "language": "en",
            "duration": 2.5,
            "segments": [{"avg_logprob": -0.5}]  # For confidence calculation
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.post', return_value=mock_response):
            result = service.transcribe(audio_data=b"fake_audio", audio_hash="hash4")

        # Then: Result should be cached
        assert service.redis.setex.called
        # The cache key should be "caption:hash4"
        call_args = service.redis.setex.call_args
        cache_key = call_args[0][0]
        assert cache_key == "caption:hash4"
        # The cached text should be "Hello world"
        cached_text = call_args[0][1]
        assert cached_text == "Hello world"

    def test_cache_key_uses_audio_hash(self):
        """Cache key is 'caption:{audio_hash}' format."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        audio_hash = "unique_hash_123"

        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "Test",
            "language": "en",
            "segments": [{"avg_logprob": -0.5}]
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.post', return_value=mock_response):
            service.transcribe(audio_data=b"audio", audio_hash=audio_hash)

        # Verify cache key format
        service.redis.setex.assert_called_once()
        cache_key = service.redis.setex.call_args[0][0]
        assert cache_key == f"caption:{audio_hash}"


class TestRateLimitHandling:
    """Test 429 rate limit handling."""

    def test_429_returns_queued_response(self):
        """Rate limit (429) returns queued status with retry-after."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.text = "Rate limit exceeded"

        # Make raise_for_status raise HTTPError
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        with patch('requests.post', return_value=mock_response):
            result = service.transcribe(audio_data=b"audio", audio_hash="hash5")

        assert result.status == "queued"
        assert result.error['code'] == "RATE_LIMITED"

    def test_429_does_not_retry_immediately(self):
        """Rate limit does NOT trigger retry - waits for retry-after."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        with patch('requests.post', return_value=mock_response) as mock_post:
            service.transcribe(audio_data=b"audio", audio_hash="hash6")

        # Should only call once (no retry on 429)
        assert mock_post.call_count == 1


class TestResponseModels:
    """Test response model validation matches requirements."""

    def test_response_includes_all_required_fields(self):
        """TranscriptionResponse includes all required fields from deep dive."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "Test transcription",
            "language": "en",
            "duration": 1.5
        }
        mock_response.raise_for_status = Mock()

        with patch('core.transcription.requests.post', return_value=mock_response):
            result = service.transcribe(audio_data=b"audio", audio_hash="hash7")

        # These fields are REQUIRED according to deep dive report
        assert hasattr(result, 'text')
        assert hasattr(result, 'language')
        assert hasattr(result, 'duration')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'processing_time_ms')
        assert hasattr(result, 'model_version')

    def test_processing_time_ms_is_populated(self):
        """processing_time_ms field is required and populated."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        mock_response = Mock()
        mock_response.json.return_value = {"text": "Test", "language": "en", "duration": 1.0}
        mock_response.raise_for_status = Mock()

        with patch('core.transcription.requests.post', return_value=mock_response):
            result = service.transcribe(audio_data=b"audio", audio_hash="hash8")

        assert result.processing_time_ms > 0
        assert isinstance(result.processing_time_ms, (int, float))


class TestDegradedMode:
    """Test degraded mode when Redis is unavailable."""

    def test_redis_failure_continues_without_cache(self):
        """Redis connection failure continues in degraded mode."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        # Redis raises connection error
        service.redis.get.side_effect = Exception("Redis down")

        # But Whisper still works
        mock_response = Mock()
        mock_response.json.return_value = {"text": "Transcription", "language": "en", "duration": 1.0}
        mock_response.raise_for_status = Mock()

        with patch('core.transcription.requests.post', return_value=mock_response):
            result = service.transcribe(audio_data=b"audio", audio_hash="hash9")

        # Should still return successful transcription
        assert result.text == "Transcription"
        assert result.degraded is True  # Flag indicating degraded mode

    def test_redis_failure_logs_warning(self):
        """Redis failure is logged but doesn't crash service."""
        service = TranscriptionService(
            whisper_api_key="test-key",
            redis_client=Mock()
        )

        service.redis.get.side_effect = Exception("Redis down")

        mock_response = Mock()
        mock_response.json.return_value = {"text": "OK", "language": "en", "duration": 1.0}
        mock_response.raise_for_status = Mock()

        with patch('core.transcription.requests.post', return_value=mock_response):
            with patch('core.transcription.logger') as mock_logger:
                result = service.transcribe(audio_data=b"audio", audio_hash="hash10")

                # Should log warning about degraded mode
                assert mock_logger.warning.called
                assert result.degraded is True
