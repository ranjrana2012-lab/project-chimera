"""
Core handler for Captioning Agent

Orchestrates transcription requests between the API layer and the
Whisper ASR engine. Provides a unified interface for both sync and
streaming transcription.
"""

import time
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

from .whisper_engine import WhisperEngine
from .stream_processor import StreamProcessor
from ..config import Settings


class CaptioningHandler:
    """Main handler for captioning operations.

    Manages the Whisper ASR engine and stream processor to provide
    both batch and real-time transcription services.
    """

    def __init__(self, settings: Settings):
        """Initialize the captioning handler.

        Args:
            settings: Application configuration
        """
        self.settings = settings
        self.whisper_engine: Optional[WhisperEngine] = None
        self.stream_processor: Optional[StreamProcessor] = None
        self._initialized = False
        self._start_time: Optional[float] = None

    async def initialize(self) -> None:
        """Initialize the handler and its components.

        Loads the Whisper model and prepares the stream processor
        for real-time transcription.
        """
        if self._initialized:
            return

        self._start_time = time.time()

        # Initialize Whisper engine
        self.whisper_engine = WhisperEngine(self.settings)
        await self.whisper_engine.load_model()

        # Initialize stream processor
        self.stream_processor = StreamProcessor(
            self.settings, self.whisper_engine
        )
        await self.stream_processor.start()

        self._initialized = True
        print("CaptioningHandler initialized successfully")

    async def transcribe(
        self,
        audio: bytes | str,
        language: Optional[str] = None,
        task: str = "transcribe",
        timestamps: bool = True,
        vad_filter: bool = False,
        word_timestamps: bool = False,
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper.

        Args:
            audio: Audio data (bytes) or URL (str)
            language: Language code (auto-detect if None)
            task: 'transcribe' or 'translate'
            timestamps: Include segment timestamps
            vad_filter: Apply voice activity detection
            word_timestamps: Include word-level timestamps

        Returns:
            Transcription response with text, segments, and metadata
        """
        if not self._initialized:
            raise RuntimeError("Handler not initialized")

        request_id = str(uuid.uuid4())

        result = await self.whisper_engine.transcribe(
            audio=audio,
            language=language or self.settings.language,
            task=task,
            timestamps=timestamps,
            vad_filter=vad_filter,
            word_timestamps=word_timestamps,
        )

        return {
            "request_id": request_id,
            **result,
        }

    async def create_stream_session(
        self,
        session_id: str,
        language: str = "en",
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a new streaming transcription session.

        Args:
            session_id: Unique session identifier
            language: Target language code
            sample_rate: Audio sample rate
            channels: Number of audio channels

        Returns:
            Session information
        """
        if not self._initialized:
            raise RuntimeError("Handler not initialized")

        session = await self.stream_processor.create_session(
            session_id=session_id,
            language=language,
            sample_rate=sample_rate,
            channels=channels,
        )

        return {
            "session_id": session.session_id,
            "language": session.language,
            "sample_rate": session.sample_rate,
            "channels": session.channels,
            "created_at": session.created_at,
        }

    async def process_stream_audio(
        self,
        session_id: str,
        audio_chunk: bytes,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process audio chunk for a streaming session.

        Args:
            session_id: Session identifier
            audio_chunk: Audio data bytes

        Yields:
            Transcription results as they become available
        """
        if not self._initialized:
            raise RuntimeError("Handler not initialized")

        async for result in self.stream_processor.process_audio_chunk(
            session_id, audio_chunk
        ):
            yield result

    async def end_stream_session(self, session_id: str) -> None:
        """
        End a streaming session.

        Args:
            session_id: Session to end
        """
        if not self._initialized:
            raise RuntimeError("Handler not initialized")

        await self.stream_processor.end_session(session_id)

    async def detect_language(self, audio: bytes) -> Dict[str, Any]:
        """
        Detect the language of audio.

        Args:
            audio: Audio data bytes (at least 1 second)

        Returns:
            Detected language and confidence
        """
        if not self._initialized:
            raise RuntimeError("Handler not initialized")

        import numpy as np

        audio_array = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

        language_code, confidence = self.whisper_engine.detect_language(audio_array)

        return {
            "language": language_code,
            "confidence": confidence,
            "language_name": WhisperEngine.LANGUAGES.get(
                language_code, language_code
            ),
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the captioning service.

        Returns:
            Health status information
        """
        uptime = time.time() - self._start_time if self._start_time else 0.0

        return {
            "status": "healthy" if self._initialized else "initializing",
            "model_loaded": self.whisper_engine.is_loaded if self.whisper_engine else False,
            "model_name": self.settings.whisper_model,
            "language": self.settings.language,
            "uptime_seconds": uptime,
            "version": self.settings.app_version,
            "active_sessions": len(self.stream_processor.get_active_sessions())
            if self.stream_processor
            else 0,
        }

    async def close(self) -> None:
        """Clean up resources."""
        if self.stream_processor:
            await self.stream_processor.stop()

        if self.whisper_engine:
            await self.whisper_engine.close()

        self._initialized = False
        print("CaptioningHandler closed")
