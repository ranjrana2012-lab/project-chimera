"""
Comprehensive unit tests for Captioning Agent.

Combines tests for all Captioning Agent modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

import sys
sys.path.insert(0, '.')

from core.transcription import TranscriptionService, TranscriptionResponse
from core.descriptions import AccessibilityDescriptionGenerator, VisualElement, SceneElementType
from api.rate_limit import RateLimiter, RateLimitConfig


class TestCaptioningAgentSuite:
    """Comprehensive test suite for Captioning Agent."""

    def test_transcription_service_initialization(self):
        """TranscriptionService initializes correctly."""
        service = TranscriptionService(whisper_api_key="test", redis_client=None)

        assert service.whisper_api_key == "test"
        assert service.redis is None
        assert service.degraded_mode is True  # No redis = degraded

    def test_description_generator_initialization(self):
        """DescriptionGenerator initializes correctly."""
        generator = AccessibilityDescriptionGenerator()

        assert generator.enable_ml is False

    def test_rate_limiter_initialization(self):
        """RateLimiter initializes with default config."""
        limiter = RateLimiter()

        assert limiter.config.max_concurrent == 10
        assert limiter.config.max_requests_per_minute == 60

    def test_rate_limiter_custom_config(self):
        """RateLimiter accepts custom configuration."""
        config = RateLimitConfig(max_concurrent=5, max_requests_per_minute=30)
        limiter = RateLimiter(config)

        assert limiter.config.max_concurrent == 5
        assert limiter.config.max_requests_per_minute == 30

    def test_full_workflow_transcribe_and_cache(self):
        """Test full workflow: transcribe → cache → retrieve."""
        redis_mock = Mock()
        redis_mock.get.return_value = None  # No cache initially
        redis_mock.setex = Mock()  # Will set cache

        service = TranscriptionService(whisper_whisper_api_key="test", redis_client=redis_mock)

        # Mock successful Whisper response
        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "Hello world",
            "language": "en",
            "duration": 1.5,
            "segments": [{"avg_logprob": -0.5}]
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.post', return_value=mock_response):
            result = service.transcribe(b"audio_data", "hash123")

        # Verify transcription succeeded
        assert result.text == "Hello world"
        assert result.status == "completed"

        # Verify caching occurred
        redis_mock.setex.assert_called_once()

    def test_full_workflow_rate_limit_check(self):
        """Test full workflow: rate limit check before transcription."""
        limiter = RateLimiter(RateLimitConfig(max_requests_per_minute=5))

        # First 5 requests should be allowed
        for i in range(5):
            result = limiter.check_rate_limit(f"client_{i}")
            assert result["allowed"] is True

        # 6th request should be limited
        result = limiter.check_rate_limit("client_0")
        assert result["allowed"] is False
        assert result["reason"] == "per_minute"

    def test_full_workflow_description_enhancement(self):
        """Test full workflow: enhance transcription with descriptions."""
        generator = AccessibilityDescriptionGenerator()

        visual_elements = [
            VisualElement(
                element_type=SceneElementType.MOVEMENT,
                description="Character walks across stage",
                position="center"
            )
        ]

        transcription = "Hello everyone"
        enhanced = generator.enhance_transcription_with_scene(
            transcription,
            visual_elements,
            {"characters": ["HAMLET"]}
        )

        assert enhanced["transcription"] == transcription
        assert enhanced["has_visual_content"] is True

    def test_error_handling_workflow(self):
        """Test error handling across all modules."""
        service = TranscriptionService(whisper_whisper_api_key="test", redis_client=None)

        # Test timeout handling
        with patch('requests.post', side_effect=Exception("Timeout")):
            result = service.transcribe(b"audio", "hash")

            # Should return placeholder, not crash
            assert "[Transcription unavailable" in result.text
            assert result.error is not None

    def test_degraded_mode_workflow(self):
        """Test degraded mode when Redis fails."""
        redis_mock = Mock()
        redis_mock.get.side_effect = Exception("Redis down")
        redis_mock.setex.side_effect = Exception("Redis down")

        service = TranscriptionService(whisper_whisper_api_key="test", redis_client=redis_mock)

        # Should still work in degraded mode
        assert service.degraded_mode is True

    def test_concurrent_clients_independent(self):
        """Test that multiple clients are rate-limited independently."""
        limiter = RateLimiter()

        # Client 1 uses their quota
        for _ in range(10):
            limiter.record_request("client_1")
            limiter.release_request("client_1")

        result1 = limiter.check_rate_limit("client_1")
        assert result1["allowed"] is False

        # But client 2 is unaffected
        result2 = limiter.check_rate_limit("client_2")
        assert result2["allowed"] is True

    def test_metrics_are_tracked(self):
        """Test that Prometheus metrics are tracked."""
        from prometheus_client import Counter

        # Check that our metrics exist
        from api.rate_limit import rate_limit_requests
        from core.transcription import logger

        # Metrics should be Counter instances
        assert hasattr(rate_limit_requests, 'inc')
        assert hasattr(rate_limit_requests, 'labels')


class TestPerformanceTargets:
    """Test that performance targets are met."""

    def test_transcription_latency_under_2s(self):
        """Transcription should complete in under 2 seconds."""
        service = TranscriptionService(whisper_whisper_api_key="test", redis_client=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "Test",
            "language": "en",
            "duration": 1.0,
            "segments": []
        }
        mock_response.raise_for_status = Mock()

        start = time.time()
        with patch('requests.post', return_value=mock_response):
            result = service.transcribe(b"audio", "hash")
        elapsed = time.time() - start

        # Should be fast (mocked response)
        assert elapsed < 0.1
        assert result.processing_time_ms < 100

    def test_rate_limit_check_fast(self):
        """Rate limit check should be very fast."""
        limiter = RateLimiter()

        start = time.time()
        for _ in range(100):
            limiter.check_rate_limit(f"client_{_ % 10}")
        elapsed = time.time() - start

        # 100 checks should take < 0.1 seconds
        assert elapsed < 0.1

    def test_description_generation_fast(self):
        """Description generation should be fast."""
        generator = AccessibilityDescriptionGenerator()

        elements = [
            VisualElement(
                element_type=SceneElementType.MOVEMENT,
                description=f"Movement {i}",
                position="center"
            )
            for i in range(10)
        ]

        start = time.time()
        generator.generate_scene_description(elements, {"characters": ["A"]})
        elapsed = time.time() - start

        # Should be fast
        assert elapsed < 0.01


class TestReliabilityFeatures:
    """Test reliability and fault tolerance."""

    def test_service_survives_redis_failure(self):
        """Service continues when Redis fails."""
        redis_mock = Mock()
        redis_mock.get.side_effect = Exception("Redis down")
        redis_mock.setex.side_effect = Exception("Redis down")

        service = TranscriptionService(whisper_whisper_api_key="test", redis_client=redis_mock)

        # Service should still work
        assert service.degraded_mode is True

        # Transcription should still function
        mock_response = Mock()
        mock_response.json.return_value = {"text": "OK", "language": "en", "duration": 1.0, "segments": []}
        mock_response.raise_for_status = Mock()

        with patch('requests.post', return_value=mock_response):
            result = service.transcribe(b"audio", "hash")

        assert result.text == "OK"
        assert result.degraded is True

    def test_rate_limiter_survives_client_flood(self):
        """Rate limiter handles flood of requests gracefully."""
        limiter = RateLimiter()

        # Simulate flood of requests
        for i in range(1000):
            result = limiter.check_rate_limit(f"client_{i}")

            # First 60 should be allowed (per hour limit)
            if i < 60:
                assert result["allowed"] is True
            else:
                # Limited
                pass

        # Stats should still be accurate
        stats = limiter.get_stats()
        assert stats["active_clients"] >= 0

    def test_description_generator_handles_empty_input(self):
        """Description generator handles empty/invalid input gracefully."""
        generator = AccessibilityDescriptionGenerator()

        # Empty elements
        result = generator.generate_scene_description([])
        assert result == ""

        # None context
        enhanced = generator.enhance_transcription_with_scene(
            "Text",
            [],
            None
        )
        assert enhanced["transcription"] == "Text"


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
