"""
Unit tests for Captioning Agent Handler

Tests the main handler that orchestrates transcription requests.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from captioning_agent.src.config import Settings
from captioning_agent.src.core.handler import CaptioningHandler
from captioning_agent.src.core.whisper_engine import WhisperEngine
from captioning_agent.src.core.stream_processor import StreamProcessor


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        app_name="captioning-agent-test",
        app_version="0.1.0-test",
        whisper_model="base",
        language="en",
        enable_streaming=True,
    )


@pytest.fixture
def mock_whisper_engine():
    """Create a mock Whisper engine."""
    engine = MagicMock(spec=WhisperEngine)
    engine.is_loaded = False
    engine.load_model = AsyncMock()
    engine.transcribe = AsyncMock(return_value={
        "text": "Test transcription",
        "language": "en",
        "duration": 2.5,
        "segments": [
            {
                "id": 0,
                "text": "Test transcription",
                "start": 0.0,
                "end": 2.5,
            }
        ],
        "confidence": 0.9,
        "processing_time_ms": 500.0,
        "model_version": "whisper-base",
    })
    engine.detect_language = MagicMock(return_value=("en", 0.95))
    engine.close = AsyncMock()
    return engine


@pytest.fixture
def mock_stream_processor():
    """Create a mock stream processor."""
    processor = MagicMock(spec=StreamProcessor)
    processor.start = AsyncMock()
    processor.stop = AsyncMock()
    processor.create_session = AsyncMock(return_value={
        "session_id": "test-session",
        "language": "en",
        "sample_rate": 16000,
        "channels": 1,
        "created_at": 1234567890.0,
    })
    processor.process_audio_chunk = AsyncMock()
    processor.end_session = AsyncMock()
    processor.get_active_sessions = MagicMock(return_value=set())
    return processor


@pytest.fixture
def captioning_handler(settings, mock_whisper_engine, mock_stream_processor):
    """Create a CaptioningHandler with mocked dependencies."""
    handler = CaptioningHandler(settings)
    handler.whisper_engine = mock_whisper_engine
    handler.stream_processor = mock_stream_processor
    return handler


@pytest.mark.unit
class TestCaptioningHandler:
    """Tests for CaptioningHandler class."""

    def test_initialization(self, settings):
        """Test handler initialization."""
        handler = CaptioningHandler(settings)

        assert handler.settings is not None
        assert handler.whisper_engine is None
        assert handler.stream_processor is None
        assert handler._initialized is False

    @pytest.mark.asyncio
    async def test_initialize(self, captioning_handler):
        """Test handler initialization."""
        captioning_handler._initialized = False
        await captioning_handler.initialize()

        assert captioning_handler._initialized is True
        captioning_handler.whisper_engine.load_model.assert_called_once()
        captioning_handler.stream_processor.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, captioning_handler):
        """Test initializing an already initialized handler is idempotent."""
        captioning_handler._initialized = True

        # Should not raise
        await captioning_handler.initialize()

    @pytest.mark.asyncio
    async def test_transcribe(self, captioning_handler):
        """Test transcribe method."""
        captioning_handler._initialized = True

        result = await captioning_handler.transcribe(
            audio=b"fake audio data",
            language="en",
        )

        assert "request_id" in result
        assert result["text"] == "Test transcription"
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_transcribe_not_initialized(self, captioning_handler):
        """Test transcribe fails when handler not initialized."""
        captioning_handler._initialized = False

        with pytest.raises(RuntimeError, match="not initialized"):
            await captioning_handler.transcribe(audio=b"audio")

    @pytest.mark.asyncio
    async def test_create_stream_session(self, captioning_handler):
        """Test creating a streaming session."""
        captioning_handler._initialized = True

        result = await captioning_handler.create_stream_session(
            session_id="test-session",
            language="en",
        )

        assert result["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_end_stream_session(self, captioning_handler):
        """Test ending a streaming session."""
        captioning_handler._initialized = True

        await captioning_handler.end_stream_session("test-session")

        captioning_handler.stream_processor.end_session.assert_called_once_with("test-session")

    @pytest.mark.asyncio
    async def test_detect_language(self, captioning_handler):
        """Test language detection."""
        captioning_handler._initialized = True

        result = await captioning_handler.detect_language(b"audio data")

        assert result["language"] == "en"
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, captioning_handler):
        """Test health check returns healthy status."""
        captioning_handler._initialized = True
        captioning_handler._start_time = 1234567890.0
        captioning_handler.whisper_engine.is_loaded = True

        result = await captioning_handler.health_check()

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_close(self, captioning_handler):
        """Test closing the handler."""
        captioning_handler._initialized = True

        await captioning_handler.close()

        captioning_handler.stream_processor.stop.assert_called_once()
        captioning_handler.whisper_engine.close.assert_called_once()
        assert captioning_handler._initialized is False


@pytest.mark.asyncio
async def test_captioning_handler_full_workflow(settings):
    """Test a complete workflow with the handler."""
    handler = CaptioningHandler(settings)

    # Mock the dependencies
    mock_engine = MagicMock(spec=WhisperEngine)
    mock_engine.is_loaded = False
    mock_engine.load_model = AsyncMock()
    mock_engine.transcribe = AsyncMock(return_value={
        "text": "Hello world",
        "language": "en",
        "duration": 1.0,
        "segments": [],
        "confidence": 0.95,
        "processing_time_ms": 300.0,
        "model_version": "whisper-base",
    })
    mock_engine.detect_language = MagicMock(return_value=("en", 0.9))
    mock_engine.close = AsyncMock()

    mock_processor = MagicMock(spec=StreamProcessor)
    mock_processor.start = AsyncMock()
    mock_processor.stop = AsyncMock()
    mock_processor.create_session = AsyncMock(return_value={
        "session_id": "test",
        "language": "en",
        "sample_rate": 16000,
        "channels": 1,
        "created_at": 0.0,
    })
    mock_processor.process_audio_chunk = AsyncMock()
    mock_processor.end_session = AsyncMock()
    mock_processor.get_active_sessions = MagicMock(return_value=set())

    handler.whisper_engine = mock_engine
    handler.stream_processor = mock_processor

    # Initialize
    await handler.initialize()
    assert handler._initialized is True

    # Transcribe
    result = await handler.transcribe(audio=b"audio data", language="en")
    assert result["text"] == "Hello world"

    # Health check
    health = await handler.health_check()
    assert health["status"] == "healthy"

    # Close
    await handler.close()
    assert handler._initialized is False

