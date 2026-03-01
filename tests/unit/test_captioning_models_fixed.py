"""Test to verify Captioning Agent response model has required fields.

This test verifies that the TranscriptionResponse model includes:
- processing_time_ms: Processing time in milliseconds
- model_version: Version of the Whisper model used

These fields are required for proper API response tracking and monitoring.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


def test_transcription_response_has_processing_time_ms():
    """Test that TranscriptionResponse has processing_time_ms field."""
    from services.captioning_agent.src.models.response import TranscriptionResponse

    # Create a minimal valid TranscriptionResponse
    response = TranscriptionResponse(
        request_id="test-req-001",
        text="Hello world",
        language="en",
        duration=1.5,
        confidence=0.95,
        processing_time_ms=250.0,
        model_version="whisper-base"
    )

    assert response.processing_time_ms == 250.0
    assert response.processing_time_ms > 0


def test_transcription_response_has_model_version():
    """Test that TranscriptionResponse has model_version field."""
    from services.captioning_agent.src.models.response import TranscriptionResponse

    response = TranscriptionResponse(
        request_id="test-req-002",
        text="Testing model version",
        language="en",
        duration=2.0,
        confidence=0.92,
        processing_time_ms=350.0,
        model_version="whisper-small"
    )

    assert response.model_version == "whisper-small"
    assert isinstance(response.model_version, str)


def test_transcription_response_fails_without_processing_time_ms():
    """Test that TranscriptionResponse requires processing_time_ms field."""
    from services.captioning_agent.src.models.response import TranscriptionResponse

    with pytest.raises(ValidationError) as exc_info:
        TranscriptionResponse(
            request_id="test-req-003",
            text="Missing field test",
            language="en",
            duration=1.0,
            confidence=0.90,
            # processing_time_ms is intentionally missing
            model_version="whisper-base"
        )

    errors = exc_info.value.errors()
    error_fields = [e["loc"][0] for e in errors]
    assert "processing_time_ms" in error_fields


def test_transcription_response_fails_without_model_version():
    """Test that TranscriptionResponse requires model_version field."""
    from services.captioning_agent.src.models.response import TranscriptionResponse

    with pytest.raises(ValidationError) as exc_info:
        TranscriptionResponse(
            request_id="test-req-004",
            text="Missing model version test",
            language="en",
            duration=1.0,
            confidence=0.88,
            processing_time_ms=200.0
            # model_version is intentionally missing
        )

    errors = exc_info.value.errors()
    error_fields = [e["loc"][0] for e in errors]
    assert "model_version" in error_fields


def test_transcription_response_complete_example():
    """Test TranscriptionResponse with all fields including segments."""
    from services.captioning_agent.src.models.response import (
        TranscriptionResponse,
        Segment,
        WordTimestamp
    )

    response = TranscriptionResponse(
        request_id="req-complete-001",
        text="Complete example with all fields",
        language="en",
        duration=5.0,
        confidence=0.94,
        processing_time_ms=450.5,
        model_version="whisper-medium",
        segments=[
            Segment(
                id=0,
                text="Complete example with all fields",
                start=0.0,
                end=5.0,
                language="en",
                confidence=0.94,
                words=[
                    WordTimestamp(
                        word="Complete",
                        start=0.0,
                        end=0.5,
                        confidence=0.98
                    )
                ]
            )
        ]
    )

    assert response.request_id == "req-complete-001"
    assert response.processing_time_ms == 450.5
    assert response.model_version == "whisper-medium"
    assert len(response.segments) == 1
    assert response.segments[0].words is not None
    assert len(response.segments[0].words) == 1


def test_transcription_response_serialization():
    """Test that TranscriptionResponse with required fields serializes correctly."""
    from services.captioning_agent.src.models.response import TranscriptionResponse
    import json

    response = TranscriptionResponse(
        request_id="test-serialize-001",
        text="Serialization test",
        language="en",
        duration=1.2,
        confidence=0.93,
        processing_time_ms=180.75,
        model_version="whisper-tiny"
    )

    # Serialize to dict
    response_dict = response.model_dump()
    assert "processing_time_ms" in response_dict
    assert "model_version" in response_dict
    assert response_dict["processing_time_ms"] == 180.75
    assert response_dict["model_version"] == "whisper-tiny"

    # Serialize to JSON
    response_json = response.model_dump_json()
    parsed = json.loads(response_json)
    assert "processing_time_ms" in parsed
    assert "model_version" in parsed
    assert parsed["processing_time_ms"] == 180.75
    assert parsed["model_version"] == "whisper-tiny"


def test_transcription_response_field_validation():
    """Test field validation for processing_time_ms."""
    from services.captioning_agent.src.models.response import TranscriptionResponse
    import pytest

    # Test negative processing_time_ms is rejected
    with pytest.raises(ValidationError):
        TranscriptionResponse(
            request_id="test-validation-001",
            text="Negative time test",
            language="en",
            duration=1.0,
            confidence=0.90,
            processing_time_ms=-10.0,
            model_version="whisper-base"
        )

    # Test zero is accepted (minimum boundary)
    response = TranscriptionResponse(
        request_id="test-validation-002",
        text="Zero time test",
        language="en",
        duration=1.0,
        confidence=0.90,
        processing_time_ms=0.0,
        model_version="whisper-base"
    )
    assert response.processing_time_ms == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
