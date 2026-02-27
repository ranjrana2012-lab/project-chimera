"""Request models for Captioning Agent transcription."""

from pydantic import BaseModel, Field
from typing import Optional, List


class TranscriptionRequest(BaseModel):
    """Request for audio transcription.

    Attributes:
        audio_url: URL to audio file (alternative to audio_data)
        audio_data: Base64-encoded audio data (alternative to audio_url)
        language: Language code (e.g., 'en', 'es', 'fr'). None for auto-detect
        task: Transcription task type ('transcribe' or 'translate')
        timestamps: Whether to include word-level timestamps
        vad_filter: Whether to use voice activity detection filtering
        word_timestamps: Whether to include word-level timestamps
    """

    audio_url: Optional[str] = Field(
        default=None,
        description="URL to audio file"
    )
    audio_data: Optional[str] = Field(
        default=None,
        description="Base64-encoded audio data"
    )
    language: Optional[str] = Field(
        default="en",
        description="Language code (auto-detect if None)"
    )
    task: Optional[str] = Field(
        default="transcribe",
        pattern="^(transcribe|translate)$",
        description="Task type: transcribe or translate to English"
    )
    timestamps: Optional[bool] = Field(
        default=True,
        description="Include segment timestamps"
    )
    vad_filter: Optional[bool] = Field(
        default=False,
        description="Apply voice activity detection filtering"
    )
    word_timestamps: Optional[bool] = Field(
        default=False,
        description="Include word-level timestamps"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "audio_url": "https://example.com/audio.wav",
                    "language": "en",
                    "task": "transcribe",
                    "timestamps": True,
                    "vad_filter": False,
                    "word_timestamps": True
                },
                {
                    "audio_data": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
                    "language": None,
                    "task": "transcribe",
                    "timestamps": True,
                    "vad_filter": True,
                    "word_timestamps": False
                }
            ]
        }
    }

    def get_audio_source(self) -> tuple[str, str]:
        """Get the audio source type and value.

        Returns:
            Tuple of (source_type, source_value) where source_type is 'url' or 'data'
        """
        if self.audio_url:
            return ("url", self.audio_url)
        elif self.audio_data:
            return ("data", self.audio_data)
        else:
            raise ValueError("Either audio_url or audio_data must be provided")


class StreamingTranscriptionRequest(BaseModel):
    """Request for streaming audio transcription.

    Attributes:
        session_id: Unique session identifier for the streaming session
        language: Language code for transcription
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels
        format: Audio format (e.g., 'wav', 'pcm', 'flac')
    """

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique session identifier"
    )
    language: Optional[str] = Field(
        default="en",
        description="Language code"
    )
    sample_rate: Optional[int] = Field(
        default=16000,
        ge=8000,
        le=48000,
        description="Audio sample rate in Hz"
    )
    channels: Optional[int] = Field(
        default=1,
        ge=1,
        le=2,
        description="Number of audio channels"
    )
    format: Optional[str] = Field(
        default="wav",
        pattern="^(wav|pcm|flac|ogg|mp3)$",
        description="Audio format"
    )
    enable_vad: Optional[bool] = Field(
        default=True,
        description="Enable voice activity detection"
    )
    chunk_size_ms: Optional[int] = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Audio chunk size in milliseconds"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "session-abc123",
                    "language": "en",
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "wav",
                    "enable_vad": True,
                    "chunk_size_ms": 1000
                }
            ]
        }
    }
