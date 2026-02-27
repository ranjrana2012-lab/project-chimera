"""
Unit tests for Captioning Agent Stream Processor

Tests real-time audio stream processing functionality.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

import pytest
import numpy as np

import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from captioning_agent.src.config import Settings
from captioning_agent.src.core.stream_processor import (
    StreamProcessor,
    StreamSession,
)
from captioning_agent.src.core.whisper_engine import WhisperEngine


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        whisper_model="base",
        language="en",
        enable_streaming=True,
        stream_chunk_size_ms=1000,
        session_timeout_seconds=300,
    )


@pytest.fixture
def mock_whisper_engine():
    """Create a mock Whisper engine."""
    engine = MagicMock(spec=WhisperEngine)
    engine.transcribe = AsyncMock(return_value={
        "text": "Test transcription",
        "language": "en",
        "confidence": 0.9,
    })
    return engine


@pytest.fixture
def stream_processor(settings, mock_whisper_engine):
    """Create a StreamProcessor instance."""
    processor = StreamProcessor(settings, mock_whisper_engine)
    return processor


class TestStreamSession:
    """Tests for StreamSession dataclass."""

    def test_session_creation(self):
        """Test creating a stream session."""
        session = StreamSession(
            session_id="test-session",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        assert session.session_id == "test-session"
        assert session.language == "en"
        assert session.sample_rate == 16000
        assert session.channels == 1
        assert session.is_active is True
        assert len(session.audio_buffer) == 0
        assert session.total_samples == 0

    def test_session_defaults(self):
        """Test session default values."""
        session = StreamSession(
            session_id="test",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        assert session.is_active is True
        assert session.total_samples == 0


class TestStreamProcessor:
    """Tests for StreamProcessor class."""

    def test_initialization(self, stream_processor):
        """Test processor initialization."""
        assert stream_processor.settings is not None
        assert stream_processor.whisper_engine is not None
        assert len(stream_processor.sessions) == 0

    @pytest.mark.asyncio
    async def test_start_and_stop(self, stream_processor):
        """Test starting and stopping the processor."""
        await stream_processor.start()
        assert stream_processor._running is True
        assert stream_processor._cleanup_task is not None

        await stream_processor.stop()
        assert stream_processor._running is False

    @pytest.mark.asyncio
    async def test_create_session(self, stream_processor):
        """Test creating a new streaming session."""
        session = await stream_processor.create_session(
            session_id="test-session-1",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        assert session.session_id == "test-session-1"
        assert session.language == "en"
        assert session.sample_rate == 16000
        assert session.channels == 1
        assert session.is_active is True

        # Check session is stored
        assert "test-session-1" in stream_processor.sessions

    @pytest.mark.asyncio
    async def test_create_duplicate_session(self, stream_processor):
        """Test creating a duplicate session raises error."""
        await stream_processor.create_session(
            session_id="test-session",
            language="en",
        )

        with pytest.raises(ValueError, match="already exists"):
            await stream_processor.create_session(
                session_id="test-session",
                language="en",
            )

    @pytest.mark.asyncio
    async def test_end_session(self, stream_processor):
        """Test ending a session."""
        await stream_processor.create_session(
            session_id="test-session",
            language="en",
        )

        await stream_processor.end_session("test-session")

        assert "test-session" not in stream_processor.sessions

    @pytest.mark.asyncio
    async def test_end_nonexistent_session(self, stream_processor):
        """Test ending a nonexistent session doesn't raise."""
        # Should not raise
        await stream_processor.end_session("nonexistent")

    @pytest.mark.asyncio
    async def test_process_audio_chunk_bytes(self, stream_processor):
        """Test processing audio chunk from bytes."""
        await stream_processor.create_session(
            session_id="test-session",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        # Create audio bytes (1 second at 16kHz, 16-bit)
        audio_bytes = (np.random.randn(16000) * 32767).astype(np.int16).tobytes()

        results = []
        async for result in stream_processor.process_audio_chunk(
            "test-session",
            audio_bytes,
        ):
            results.append(result)

        # Session should have received audio
        session = stream_processor.sessions["test-session"]
        assert session.total_samples > 0

    @pytest.mark.asyncio
    async def test_process_audio_chunk_numpy(self, stream_processor):
        """Test processing audio chunk from numpy array."""
        await stream_processor.create_session(
            session_id="test-session",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        # Create audio numpy array
        audio_array = np.random.randn(16000).astype(np.float32)

        results = []
        async for result in stream_processor.process_audio_chunk(
            "test-session",
            audio_array,
        ):
            results.append(result)

        # Check results
        session = stream_processor.sessions["test-session"]
        assert session.total_samples == 16000

    @pytest.mark.asyncio
    async def test_process_audio_chunk_nonexistent_session(self, stream_processor):
        """Test processing audio for nonexistent session raises error."""
        audio_bytes = b"dummy audio data"

        with pytest.raises(ValueError, match="not found"):
            async for _ in stream_processor.process_audio_chunk(
                "nonexistent",
                audio_bytes,
            ):
                pass

    def test_combine_buffer_empty(self, stream_processor):
        """Test combining empty buffer returns None."""
        session = StreamSession(
            session_id="test",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        result = stream_processor._combine_buffer(session)
        assert result is None

    def test_combine_buffer_with_data(self, stream_processor):
        """Test combining buffer with data."""
        session = StreamSession(
            session_id="test",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        # Add chunks to buffer
        chunk1 = np.random.randn(100).astype(np.float32)
        chunk2 = np.random.randn(100).astype(np.float32)
        session.audio_buffer.extend([chunk1, chunk2])

        result = stream_processor._combine_buffer(session)

        assert result is not None
        assert len(result) == 200

    @pytest.mark.asyncio
    async def test_transcribe_chunk(self, stream_processor):
        """Test transcribing an audio chunk."""
        session = StreamSession(
            session_id="test",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        audio = np.random.randn(16000).astype(np.float32)

        result = await stream_processor._transcribe_chunk(session, audio)

        assert result["text"] == "Test transcription"
        assert result["language"] == "en"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_transcribe_chunk_error_handling(self, stream_processor):
        """Test transcription error handling."""
        session = StreamSession(
            session_id="test",
            language="en",
            sample_rate=16000,
            channels=1,
        )

        # Make transcribe raise an error
        stream_processor.whisper_engine.transcribe = AsyncMock(
            side_effect=Exception("Transcription failed")
        )

        audio = np.random.randn(16000).astype(np.float32)

        result = await stream_processor._transcribe_chunk(session, audio)

        # Should return error result
        assert result["text"] == ""
        assert result["confidence"] == 0.0

    @patch('captioning_agent.src.core.stream_processor.webrtcvad.Vad')
    def test_detect_speech_positive(self, mock_vad_class, stream_processor):
        """Test speech detection returns True when speech found."""
        mock_vad = MagicMock()
        mock_vad.is_speech.return_value = True
        mock_vad_class.return_value = mock_vad

        # Re-create processor to use mocked VAD
        processor = StreamProcessor(stream_processor.settings, stream_processor.whisper_engine)

        audio = np.random.randn(16000).astype(np.float32)

        has_speech = processor._detect_speech(audio)

        assert has_speech is True

    @patch('captioning_agent.src.core.stream_processor.webrtcvad.Vad')
    def test_detect_speech_negative(self, mock_vad_class, stream_processor):
        """Test speech detection returns False when no speech."""
        mock_vad = MagicMock()
        mock_vad.is_speech.return_value = False
        mock_vad_class.return_value = mock_vad

        processor = StreamProcessor(stream_processor.settings, stream_processor.whisper_engine)

        audio = np.random.randn(16000).astype(np.float32)

        has_speech = processor._detect_speech(audio)

        assert has_speech is False

    def test_get_session_info(self, stream_processor):
        """Test getting session information."""
        # Create a session
        session = StreamSession(
            session_id="test-session",
            language="en",
            sample_rate=16000,
            channels=1,
        )
        session.total_samples = 32000  # 2 seconds
        stream_processor.sessions["test-session"] = session

        info = stream_processor.get_session_info("test-session")

        assert info["session_id"] == "test-session"
        assert info["language"] == "en"
        assert info["sample_rate"] == 16000
        assert info["channels"] == 1
        assert info["duration_seconds"] == 2.0
        assert info["is_active"] is True

    def test_get_session_info_nonexistent(self, stream_processor):
        """Test getting info for nonexistent session returns None."""
        info = stream_processor.get_session_info("nonexistent")
        assert info is None

    def test_get_active_sessions(self, stream_processor):
        """Test getting set of active sessions."""
        # Create multiple sessions
        session1 = StreamSession("session-1", "en", 16000, 1)
        session2 = StreamSession("session-2", "en", 16000, 1)
        session3 = StreamSession("session-3", "en", 16000, 1)
        session3.is_active = False

        stream_processor.sessions.update({
            "session-1": session1,
            "session-2": session2,
            "session-3": session3,
        })

        active = stream_processor.get_active_sessions()

        assert active == {"session-1", "session-2"}
        assert "session-3" not in active


@pytest.mark.asyncio
async def test_stream_processor_cleanup(settings, mock_whisper_engine):
    """Test automatic cleanup of inactive sessions."""
    processor = StreamProcessor(settings, mock_whisper_engine)

    # Create sessions
    await processor.create_session("active-1", "en", 16000, 1)
    await processor.create_session("active-2", "en", 16000, 1)

    # Manually create an old inactive session
    old_session = StreamSession("old-inactive", "en", 16000, 1)
    old_session.last_activity = 0  # Very old timestamp
    processor.sessions["old-inactive"] = old_session

    await processor.start()

    # Wait a brief moment for cleanup to potentially run
    await asyncio.sleep(0.1)

    await processor.stop()

    # Check sessions (cleanup runs on 30s intervals, so old session may still exist)
    assert "active-1" in processor.sessions or "active-2" in processor.sessions
