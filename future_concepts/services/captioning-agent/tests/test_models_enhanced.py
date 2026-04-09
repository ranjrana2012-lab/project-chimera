"""
Enhanced tests for Captioning Agent Pydantic models.

Tests request/response models for transcription and health checks.
"""

import pytest
from pydantic import ValidationError
from models import (
    HealthResponse,
    TranscriptionResponse,
    TranscriptionSegment,
    ErrorResponse,
    LanguageDetectionResponse
)


class TestHealthResponse:
    """Test HealthResponse model"""

    def test_health_response_minimal(self):
        """Test minimal health response"""
        response = HealthResponse(status="alive")
        assert response.status == "alive"
        assert response.checks is None

    def test_health_response_with_checks(self):
        """Test health response with checks"""
        checks = {"whisper_model": "loaded"}
        response = HealthResponse(status="ready", checks=checks)
        assert response.status == "ready"
        assert response.checks == checks

    def test_health_response_statuses(self):
        """Test various health statuses"""
        statuses = ["alive", "ready", "not_ready"]
        for status in statuses:
            response = HealthResponse(status=status)
            assert response.status == status

    def test_health_response_empty_checks(self):
        """Test health response with empty checks"""
        response = HealthResponse(status="alive", checks={})
        assert response.checks == {}


class TestTranscriptionSegment:
    """Test TranscriptionSegment model"""

    def test_segment_minimal(self):
        """Test minimal segment"""
        segment = TranscriptionSegment(start=0.0, end=1.0, text="Hello")
        assert segment.start == 0.0
        assert segment.end == 1.0
        assert segment.text == "Hello"
        assert segment.confidence is None

    def test_segment_with_confidence(self):
        """Test segment with confidence score"""
        segment = TranscriptionSegment(
            start=0.0,
            end=1.0,
            text="Hello",
            confidence=0.95
        )
        assert segment.confidence == 0.95

    def test_segment_timing_validation(self):
        """Test segment timing values"""
        segment = TranscriptionSegment(
            start=10.5,
            end=15.7,
            text="Test"
        )
        assert segment.start == 10.5
        assert segment.end == 15.7

    def test_segment_empty_text(self):
        """Test segment with empty text"""
        segment = TranscriptionSegment(
            start=0.0,
            end=1.0,
            text=""
        )
        assert segment.text == ""

    def test_segment_unicode_text(self):
        """Test segment with unicode text"""
        segment = TranscriptionSegment(
            start=0.0,
            end=1.0,
            text="Hello 世界 🌍"
        )
        assert "世界" in segment.text


class TestTranscriptionResponse:
    """Test TranscriptionResponse model"""

    def test_response_minimal(self):
        """Test minimal transcription response"""
        response = TranscriptionResponse(
            text="Hello world",
            language="en",
            segments=[],
            duration=5.0,
            processing_time_ms=1000
        )
        assert response.text == "Hello world"
        assert response.language == "en"
        assert response.segments == []

    def test_response_with_segments(self):
        """Test response with segments"""
        segments = [
            TranscriptionSegment(start=0.0, end=1.0, text="Hello"),
            TranscriptionSegment(start=1.0, end=2.0, text="world")
        ]
        response = TranscriptionResponse(
            text="Hello world",
            language="en",
            segments=segments,
            duration=2.0,
            processing_time_ms=500
        )
        assert len(response.segments) == 2
        assert response.segments[0].text == "Hello"

    def test_response_language_codes(self):
        """Test various language codes"""
        languages = ["en", "es", "fr", "de", "it", "pt", "zh", "ja"]
        for lang in languages:
            response = TranscriptionResponse(
                text="Test",
                language=lang,
                segments=[],
                duration=1.0,
                processing_time_ms=100
            )
            assert response.language == lang

    def test_response_duration_values(self):
        """Test various duration values"""
        durations = [0.5, 1.0, 10.0, 100.0, 3600.0]
        for duration in durations:
            response = TranscriptionResponse(
                text="Test",
                language="en",
                segments=[],
                duration=duration,
                processing_time_ms=100
            )
            assert response.duration == duration

    def test_response_processing_time(self):
        """Test processing time values"""
        times = [100, 500, 1000, 5000, 10000]
        for time_ms in times:
            response = TranscriptionResponse(
                text="Test",
                language="en",
                segments=[],
                duration=1.0,
                processing_time_ms=time_ms
            )
            assert response.processing_time_ms == time_ms

    def test_response_with_long_text(self):
        """Test response with long transcription text"""
        long_text = "word " * 1000
        response = TranscriptionResponse(
            text=long_text,
            language="en",
            segments=[],
            duration=100.0,
            processing_time_ms=5000
        )
        assert len(response.text) == len(long_text)

    def test_response_with_unicode(self):
        """Test response with unicode characters"""
        response = TranscriptionResponse(
            text="Hello 世界 🌍",
            language="en",
            segments=[],
            duration=5.0,
            processing_time_ms=1000
        )
        assert "世界" in response.text


class TestErrorResponse:
    """Test ErrorResponse model"""

    def test_error_response_minimal(self):
        """Test minimal error response"""
        response = ErrorResponse(error="Test error")
        assert response.error == "Test error"
        assert response.detail is None

    def test_error_response_with_detail(self):
        """Test error response with detail"""
        response = ErrorResponse(
            error="Test error",
            detail="Additional error details"
        )
        assert response.error == "Test error"
        assert response.detail == "Additional error details"

    def test_error_response_with_timestamp(self):
        """Test error response has timestamp"""
        response = ErrorResponse(error="Test error")
        assert response.timestamp is not None

    def test_error_response_empty_error(self):
        """Test error response with empty error"""
        response = ErrorResponse(error="")
        assert response.error == ""


class TestLanguageDetectionResponse:
    """Test LanguageDetectionResponse model"""

    def test_language_detection_minimal(self):
        """Test minimal language detection response"""
        response = LanguageDetectionResponse(
            language="en",
            confidence=0.95
        )
        assert response.language == "en"
        assert response.confidence == 0.95

    def test_language_detection_without_confidence(self):
        """Test language detection without confidence"""
        response = LanguageDetectionResponse(language="en")
        assert response.language == "en"
        assert response.confidence is None

    def test_language_detection_confidence_range(self):
        """Test confidence values in valid range"""
        for conf in [0.0, 0.5, 0.95, 1.0]:
            response = LanguageDetectionResponse(
                language="en",
                confidence=conf
            )
            assert response.confidence == conf


class TestModelSerialization:
    """Test model serialization/deserialization"""

    def test_health_response_to_dict(self):
        """Test HealthResponse serialization"""
        response = HealthResponse(status="ready", checks={"model": "loaded"})
        data = response.model_dump()
        assert data["status"] == "ready"
        assert data["checks"] == {"model": "loaded"}

    def test_transcription_response_to_dict(self):
        """Test TranscriptionResponse serialization"""
        segment = TranscriptionSegment(start=0.0, end=1.0, text="Hello")
        response = TranscriptionResponse(
            text="Hello",
            language="en",
            segments=[segment],
            duration=1.0,
            processing_time_ms=100
        )
        data = response.model_dump()
        assert data["text"] == "Hello"
        assert len(data["segments"]) == 1

    def test_segment_to_dict(self):
        """Test TranscriptionSegment serialization"""
        segment = TranscriptionSegment(
            start=0.0,
            end=1.0,
            text="Hello",
            confidence=0.95
        )
        data = segment.model_dump()
        assert data["start"] == 0.0
        assert data["end"] == 1.0
        assert data["text"] == "Hello"
        assert data["confidence"] == 0.95


class TestModelValidation:
    """Test model validation scenarios"""

    def test_segment_negative_timing(self):
        """Test segment with negative timing"""
        segment = TranscriptionSegment(
            start=-1.0,
            end=0.0,
            text="Test"
        )
        # Model should accept negative values (validation might be application-level)
        assert segment.start == -1.0

    def test_response_zero_duration(self):
        """Test response with zero duration"""
        response = TranscriptionResponse(
            text="Test",
            language="en",
            segments=[],
            duration=0.0,
            processing_time_ms=0
        )
        assert response.duration == 0.0

    def test_response_negative_processing_time(self):
        """Test response with negative processing time"""
        response = TranscriptionResponse(
            text="Test",
            language="en",
            segments=[],
            duration=1.0,
            processing_time_ms=-100
        )
        # Model should accept negative values
        assert response.processing_time_ms == -100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
