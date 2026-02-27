"""
Unit tests for Captioning Agent models

Tests request and response models for transcription API.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from captioning_agent.src.models.request import (
    TranscriptionRequest,
    StreamingTranscriptionRequest,
)
from captioning_agent.src.models.response import (
    TranscriptionResponse,
    WordTimestamp,
    Segment,
    StreamingTranscriptionChunk,
    HealthResponse,
)


class TestTranscriptionRequest:
    """Tests for TranscriptionRequest model."""

    def test_valid_request_with_audio_url(self):
        """Test creating a valid request with audio URL."""
        request = TranscriptionRequest(
            audio_url="https://example.com/audio.wav",
            language="en",
            task="transcribe",
        )

        assert request.audio_url == "https://example.com/audio.wav"
        assert request.audio_data is None
        assert request.language == "en"
        assert request.task == "transcribe"
        assert request.timestamps is True
        assert request.vad_filter is False

    def test_valid_request_with_audio_data(self):
        """Test creating a valid request with base64 audio data."""
        audio_data = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
        request = TranscriptionRequest(
            audio_data=audio_data,
            language=None,  # Auto-detect
            word_timestamps=True,
        )

        assert request.audio_data == audio_data
        assert request.audio_url is None
        assert request.language is None
        assert request.word_timestamps is True

    def test_get_audio_source_url(self):
        """Test getting audio source from URL."""
        request = TranscriptionRequest(
            audio_url="https://example.com/test.mp3"
        )
        source_type, source_value = request.get_audio_source()

        assert source_type == "url"
        assert source_value == "https://example.com/test.mp3"

    def test_get_audio_source_data(self):
        """Test getting audio source from base64 data."""
        audio_data = "base64encodeddata"
        request = TranscriptionRequest(audio_data=audio_data)
        source_type, source_value = request.get_audio_source()

        assert source_type == "data"
        assert source_value == audio_data

    def test_no_audio_source_raises_error(self):
        """Test that missing both audio sources raises error."""
        request = TranscriptionRequest(
            audio_url=None,
            audio_data=None,
        )

        with pytest.raises(ValueError, match="Either audio_url or audio_data"):
            request.get_audio_source()

    def test_invalid_task_value(self):
        """Test that invalid task value raises validation error."""
        with pytest.raises(ValidationError):
            TranscriptionRequest(
                audio_data="data",
                task="invalid_task",
            )

    def test_valid_task_values(self):
        """Test that both valid task values work."""
        for task in ["transcribe", "translate"]:
            request = TranscriptionRequest(
                audio_data="data",
                task=task,
            )
            assert request.task == task


class TestStreamingTranscriptionRequest:
    """Tests for StreamingTranscriptionRequest model."""

    def test_valid_streaming_request(self):
        """Test creating a valid streaming request."""
        request = StreamingTranscriptionRequest(
            session_id="session-abc123",
            language="en",
            sample_rate=16000,
        )

        assert request.session_id == "session-abc123"
        assert request.language == "en"
        assert request.sample_rate == 16000
        assert request.channels == 1
        assert request.format == "wav"

    def test_session_id_validation(self):
        """Test session_id length validation."""
        # Too short
        with pytest.raises(ValidationError):
            StreamingTranscriptionRequest(
                session_id="",
                language="en",
            )

        # Too long
        with pytest.raises(ValidationError):
            StreamingTranscriptionRequest(
                session_id="a" * 101,
                language="en",
            )

    def test_sample_rate_validation(self):
        """Test sample rate range validation."""
        # Below minimum
        with pytest.raises(ValidationError):
            StreamingTranscriptionRequest(
                session_id="test",
                language="en",
                sample_rate=4000,
            )

        # Above maximum
        with pytest.raises(ValidationError):
            StreamingTranscriptionRequest(
                session_id="test",
                language="en",
                sample_rate=96000,
            )

        # Valid values
        for sr in [8000, 16000, 44100, 48000]:
            request = StreamingTranscriptionRequest(
                session_id="test",
                language="en",
                sample_rate=sr,
            )
            assert request.sample_rate == sr

    def test_format_validation(self):
        """Test audio format validation."""
        valid_formats = ["wav", "pcm", "flac", "ogg", "mp3"]

        for fmt in valid_formats:
            request = StreamingTranscriptionRequest(
                session_id="test",
                language="en",
                format=fmt,
            )
            assert request.format == fmt

        # Invalid format
        with pytest.raises(ValidationError):
            StreamingTranscriptionRequest(
                session_id="test",
                language="en",
                format="invalid",
            )


class TestWordTimestamp:
    """Tests for WordTimestamp model."""

    def test_valid_word_timestamp(self):
        """Test creating a valid word timestamp."""
        word = WordTimestamp(
            word="hello",
            start=0.0,
            end=0.5,
            confidence=0.95,
        )

        assert word.word == "hello"
        assert word.start == 0.0
        assert word.end == 0.5
        assert word.confidence == 0.95

    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid range
        for conf in [0.0, 0.5, 1.0]:
            word = WordTimestamp(
                word="test",
                start=0.0,
                end=0.1,
                confidence=conf,
            )
            assert word.confidence == conf

        # Out of range
        with pytest.raises(ValidationError):
            WordTimestamp(
                word="test",
                start=0.0,
                end=0.1,
                confidence=1.5,
            )

        # None is valid (optional)
        word = WordTimestamp(
            word="test",
            start=0.0,
            end=0.1,
        )
        assert word.confidence is None


class TestSegment:
    """Tests for Segment model."""

    def test_valid_segment(self):
        """Test creating a valid segment."""
        segment = Segment(
            id=0,
            text="Hello, world!",
            start=0.0,
            end=2.5,
            language="en",
            confidence=0.9,
        )

        assert segment.id == 0
        assert segment.text == "Hello, world!"
        assert segment.start == 0.0
        assert segment.end == 2.5
        assert segment.language == "en"
        assert segment.confidence == 0.9

    def test_segment_with_words(self):
        """Test creating a segment with word timestamps."""
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.3, confidence=0.95),
            WordTimestamp(word="world", start=0.4, end=0.8, confidence=0.92),
        ]

        segment = Segment(
            id=0,
            text="Hello world",
            start=0.0,
            end=0.8,
            words=words,
        )

        assert len(segment.words) == 2
        assert segment.words[0].word == "Hello"
        assert segment.words[1].word == "world"


class TestTranscriptionResponse:
    """Tests for TranscriptionResponse model."""

    def test_valid_response(self):
        """Test creating a valid transcription response."""
        segments = [
            Segment(
                id=0,
                text="Hello, world!",
                start=0.0,
                end=2.5,
                language="en",
                confidence=0.9,
            )
        ]

        response = TranscriptionResponse(
            request_id="req-123",
            text="Hello, world!",
            language="en",
            duration=2.5,
            segments=segments,
            confidence=0.9,
            processing_time_ms=450.0,
            model_version="whisper-base",
        )

        assert response.request_id == "req-123"
        assert response.text == "Hello, world!"
        assert response.language == "en"
        assert response.duration == 2.5
        assert len(response.segments) == 1
        assert response.confidence == 0.9
        assert response.processing_time_ms == 450.0
        assert response.model_version == "whisper-base"
        assert isinstance(response.timestamp, datetime)


class TestStreamingTranscriptionChunk:
    """Tests for StreamingTranscriptionChunk model."""

    def test_valid_chunk(self):
        """Test creating a valid streaming chunk."""
        chunk = StreamingTranscriptionChunk(
            session_id="session-abc",
            chunk_id=5,
            text="Hello",
            is_final=False,
            start_offset=0.0,
            confidence=0.8,
        )

        assert chunk.session_id == "session-abc"
        assert chunk.chunk_id == 5
        assert chunk.text == "Hello"
        assert chunk.is_final is False
        assert chunk.start_offset == 0.0
        assert chunk.confidence == 0.8

    def test_final_chunk(self):
        """Test creating a final result chunk."""
        chunk = StreamingTranscriptionChunk(
            session_id="session-abc",
            chunk_id=10,
            text="Hello, how are you?",
            is_final=True,
            start_offset=5.0,
        )

        assert chunk.is_final is True


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_healthy_response(self):
        """Test a healthy status response."""
        response = HealthResponse(
            status="healthy",
            model_loaded=True,
            model_name="whisper-base",
            language="en",
            uptime_seconds=123.45,
            version="0.1.0",
        )

        assert response.status == "healthy"
        assert response.model_loaded is True
        assert response.model_name == "whisper-base"
        assert response.language == "en"
        assert response.uptime_seconds == 123.45
        assert response.version == "0.1.0"

    def test_initializing_response(self):
        """Test an initializing status response."""
        response = HealthResponse(
            status="initializing",
            model_loaded=False,
            language="en",
            uptime_seconds=0.5,
            version="0.1.0",
        )

        assert response.status == "initializing"
        assert response.model_loaded is False
        assert response.model_name is None
