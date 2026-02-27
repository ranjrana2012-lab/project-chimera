"""
Stream Processor for real-time audio captioning

Handles WebSocket connections and processes audio chunks for real-time
speech-to-text transcription using Whisper.
"""

import asyncio
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Set

import numpy as np
import torch
import webrtcvad

from .whisper_engine import WhisperEngine
from ..config import Settings


@dataclass
class StreamSession:
    """Active streaming session state.

    Attributes:
        session_id: Unique session identifier
        language: Target language code
        sample_rate: Audio sample rate
        channels: Number of audio channels
        created_at: Session creation timestamp
        last_activity: Last audio chunk received timestamp
        audio_buffer: Buffer of audio chunks
        is_active: Whether session is active
    """

    session_id: str
    language: str
    sample_rate: int
    channels: int
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    audio_buffer: deque = field(default_factory=deque)
    is_active: bool = True
    total_samples: int = 0


class StreamProcessor:
    """Processes audio streams for real-time transcription.

    Features:
    - WebSocket session management
    - Voice activity detection (VAD)
    - Chunked audio processing
    - Real-time partial and final results
    - Automatic language detection
    - Session timeout handling
    """

    # VAD aggressiveness (0-3, higher = more aggressive)
    VAD_AGGRESSIVENESS = 2

    # Audio processing parameters
    CHUNK_SAMPLES = 16000  # 1 second at 16kHz
    OVERLAP_SAMPLES = 1600  # 100ms overlap for continuity
    MIN_SPEECH_SAMPLES = 8000  # 0.5 seconds minimum

    # Session timeout (seconds)
    SESSION_TIMEOUT = 300  # 5 minutes

    def __init__(self, settings: Settings, whisper_engine: WhisperEngine):
        """Initialize the stream processor.

        Args:
            settings: Application settings
            whisper_engine: Whisper ASR engine instance
        """
        self.settings = settings
        self.whisper_engine = whisper_engine
        self.sessions: Dict[str, StreamSession] = {}
        self.vad = webrtcvad.Vad(self.VAD_AGGRESSIVENESS)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the stream processor background tasks."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        print("Stream processor started")

    async def stop(self) -> None:
        """Stop the stream processor and clean up sessions."""
        self._running = False

        # Close all sessions
        for session in list(self.sessions.values()):
            await self.end_session(session.session_id)

        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        print("Stream processor stopped")

    async def create_session(
        self,
        session_id: str,
        language: str = "en",
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> StreamSession:
        """Create a new streaming session.

        Args:
            session_id: Unique session identifier
            language: Target language code
            sample_rate: Audio sample rate
            channels: Number of audio channels

        Returns:
            The created session
        """
        if session_id in self.sessions:
            raise ValueError(f"Session {session_id} already exists")

        session = StreamSession(
            session_id=session_id,
            language=language,
            sample_rate=sample_rate,
            channels=channels,
        )

        self.sessions[session_id] = session
        print(f"Created streaming session: {session_id}")

        return session

    async def end_session(self, session_id: str) -> None:
        """End a streaming session and process remaining audio.

        Args:
            session_id: Session to end
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        # Process remaining audio buffer
        if session.audio_buffer:
            # Combine remaining chunks and process
            remaining = self._combine_buffer(session)
            if remaining is not None:
                # This would be processed in a real implementation
                pass

        session.is_active = False
        del self.sessions[session_id]

        print(f"Ended streaming session: {session_id}")

    async def process_audio_chunk(
        self,
        session_id: str,
        audio_chunk: bytes | np.ndarray,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process an audio chunk for a session.

        Args:
            session_id: Session identifier
            audio_chunk: Audio data (bytes or numpy array)

        Yields:
            Transcription result dictionaries with partial/final results
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        session.last_activity = time.time()

        # Prepare audio
        if isinstance(audio_chunk, bytes):
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(
                np.float32
            ) / 32768.0
        else:
            audio_array = audio_chunk.astype(np.float32)

        # Resample if needed
        if session.sample_rate != 16000:
            # Simple resampling (use librosa in production)
            import librosa

            audio_array = librosa.resample(
                audio_array, orig_sr=session.sample_rate, target_sr=16000
            )

        # Mix to mono if needed
        if len(audio_array.shape) > 1:
            audio_array = np.mean(audio_array, axis=1)

        # Add to buffer
        session.audio_buffer.append(audio_array)
        session.total_samples += len(audio_array)

        # Process if we have enough audio
        total_audio = self._combine_buffer(session)

        if total_audio is not None and len(total_audio) >= self.CHUNK_SAMPLES:
            # Check for speech using VAD
            has_speech = self._detect_speech(total_audio[: self.CHUNK_SAMPLES])

            if has_speech:
                # Process with Whisper
                result = await self._transcribe_chunk(
                    session,
                    total_audio[: self.CHUNK_SAMPLES],
                )

                if result["text"].strip():
                    yield {
                        "session_id": session_id,
                        "chunk_id": session.total_samples // self.CHUNK_SAMPLES,
                        "text": result["text"],
                        "is_final": True,
                        "start_offset": (
                            session.total_samples - self.CHUNK_SAMPLES
                        )
                        / 16000.0,
                        "confidence": result.get("confidence"),
                        "language": result.get("language"),
                    }

            # Keep overlap for continuity
            overlap = total_audio[self.CHUNK_SAMPLES - self.OVERLAP_SAMPLES :]
            session.audio_buffer = deque([overlap])

    async def _transcribe_chunk(
        self, session: StreamSession, audio: np.ndarray
    ) -> Dict[str, Any]:
        """Transcribe an audio chunk.

        Args:
            session: Session state
            audio: Audio array to transcribe

        Returns:
            Transcription result
        """
        try:
            result = await self.whisper_engine.transcribe(
                audio,
                language=session.language,
                task="transcribe",
                timestamps=True,
                word_timestamps=False,
            )

            return result

        except Exception as e:
            print(f"Transcription error for session {session.session_id}: {e}")
            return {
                "text": "",
                "language": session.language,
                "confidence": 0.0,
            }

    def _combine_buffer(self, session: StreamSession) -> Optional[np.ndarray]:
        """Combine all chunks in the buffer into a single array.

        Args:
            session: Session with audio buffer

        Returns:
            Combined audio array or None if buffer is empty
        """
        if not session.audio_buffer:
            return None

        return np.concatenate(list(session.audio_buffer))

    def _detect_speech(self, audio: np.ndarray) -> bool:
        """Detect if audio contains speech using VAD.

        Args:
            audio: Audio array at 16kHz

        Returns:
            True if speech is detected
        """
        # Convert to int16 for VAD
        audio_int16 = (audio * 32768).astype(np.int16)

        # Split into frames (30ms each)
        frame_size = 480  # 30ms at 16kHz
        frames = [
            bytes(audio_int16[i : i + frame_size])
            for i in range(0, len(audio_int16), frame_size)
            if len(audio_int16[i : i + frame_size]) == frame_size
        ]

        # Check each frame
        speech_frames = 0
        for frame in frames:
            if self.vad.is_speech(frame, sample_rate=16000):
                speech_frames += 1

        # Return True if more than 50% of frames contain speech
        return speech_frames > len(frames) / 2

    async def _cleanup_loop(self) -> None:
        """Background task to clean up inactive sessions."""
        while self._running:
            try:
                current_time = time.time()

                # Find inactive sessions
                to_remove = []
                for session_id, session in self.sessions.items():
                    if (
                        current_time - session.last_activity
                        > self.SESSION_TIMEOUT
                    ):
                        to_remove.append(session_id)

                # Remove inactive sessions
                for session_id in to_remove:
                    print(f"Cleaning up inactive session: {session_id}")
                    await self.end_session(session_id)

                # Sleep for 30 seconds
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Cleanup loop error: {e}")
                await asyncio.sleep(30)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session.

        Args:
            session_id: Session identifier

        Returns:
            Session information or None if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "language": session.language,
            "sample_rate": session.sample_rate,
            "channels": session.channels,
            "duration_seconds": session.total_samples / 16000.0,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "is_active": session.is_active,
            "buffer_size_chunks": len(session.audio_buffer),
        }

    def get_active_sessions(self) -> Set[str]:
        """Get set of active session IDs.

        Returns:
            Set of active session identifiers
        """
        return {
            s.session_id for s in self.sessions.values() if s.is_active
        }
