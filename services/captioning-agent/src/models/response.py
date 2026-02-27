"""Response models for Captioning Agent transcription."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WordTimestamp(BaseModel):
    """Word-level timestamp.

    Attributes:
        word: The transcribed word
        start: Start time in seconds
        end: End time in seconds
        confidence: Confidence score for this word (0.0-1.0)
    """

    word: str = Field(..., description="Transcribed word")
    start: float = Field(..., ge=0.0, description="Start time in seconds")
    end: float = Field(..., ge=0.0, description="End time in seconds")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Word confidence score"
    )


class Segment(BaseModel):
    """Transcribed segment with timestamps.

    Attributes:
        id: Segment identifier
        text: Transcribed text for this segment
        start: Start time in seconds
        end: End time in seconds
        language: Detected or specified language
        words: Optional word-level timestamps
        confidence: Confidence score for this segment
    """

    id: int = Field(..., ge=0, description="Segment ID")
    text: str = Field(..., description="Transcribed text")
    start: float = Field(..., ge=0.0, description="Start time in seconds")
    end: float = Field(..., ge=0.0, description="End time in seconds")
    language: Optional[str] = Field(default=None, description="Language code")
    words: Optional[List[WordTimestamp]] = Field(
        default=None,
        description="Word-level timestamps"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Segment confidence score"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 0,
                    "text": "Hello, how are you today?",
                    "start": 0.0,
                    "end": 2.5,
                    "language": "en",
                    "confidence": 0.95
                }
            ]
        }
    }


class TranscriptionResponse(BaseModel):
    """Response from audio transcription.

    Attributes:
        request_id: Unique identifier for the transcription request
        text: Full transcribed text
        language: Detected or specified language
        duration: Audio duration in seconds
        segments: List of transcribed segments
        words: Optional word-level timestamps
        confidence: Overall confidence score
        processing_time_ms: Time taken to process in milliseconds
        model_version: Version of the Whisper model used
        timestamp: When the response was generated
    """

    request_id: str = Field(..., description="Unique request identifier")
    text: str = Field(..., description="Full transcribed text")
    language: str = Field(..., description="Language code")
    duration: float = Field(..., ge=0.0, description="Audio duration in seconds")
    segments: List[Segment] = Field(default_factory=list, description="Transcribed segments")
    words: Optional[List[WordTimestamp]] = Field(
        default=None,
        description="Word-level timestamps"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score"
    )
    processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Processing time in milliseconds"
    )
    model_version: str = Field(..., description="Whisper model version")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "req-abc123",
                    "text": "Hello, how are you today? I hope you're having a wonderful day.",
                    "language": "en",
                    "duration": 4.2,
                    "segments": [
                        {
                            "id": 0,
                            "text": "Hello, how are you today?",
                            "start": 0.0,
                            "end": 2.5,
                            "language": "en",
                            "confidence": 0.95
                        },
                        {
                            "id": 1,
                            "text": " I hope you're having a wonderful day.",
                            "start": 2.5,
                            "end": 4.2,
                            "language": "en",
                            "confidence": 0.92
                        }
                    ],
                    "confidence": 0.94,
                    "processing_time_ms": 450.5,
                    "model_version": "whisper-base",
                    "timestamp": "2026-02-27T10:30:00Z"
                }
            ]
        }
    }


class StreamingTranscriptionChunk(BaseModel):
    """Chunk of streaming transcription.

    Attributes:
        session_id: Session identifier
        chunk_id: Sequential chunk identifier
        text: Transcribed text for this chunk
        is_final: Whether this is the final result for this segment
        start_offset: Start offset in seconds from session start
        confidence: Confidence score for this chunk
        language: Detected language
        timestamp: When this chunk was generated
    """

    session_id: str = Field(..., description="Session identifier")
    chunk_id: int = Field(..., ge=0, description="Chunk ID")
    text: str = Field(..., description="Transcribed text")
    is_final: bool = Field(..., description="Is this a final result")
    start_offset: float = Field(..., ge=0.0, description="Start offset in seconds")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score"
    )
    language: Optional[str] = Field(default=None, description="Language code")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Chunk timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "session-abc123",
                    "chunk_id": 5,
                    "text": "Hello, how are you",
                    "is_final": False,
                    "start_offset": 0.0,
                    "confidence": 0.85,
                    "language": "en",
                    "timestamp": "2026-02-27T10:30:05Z"
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Health check response.

    Attributes:
        status: Health status (healthy, initializing, unhealthy)
        model_loaded: Whether the Whisper model is loaded
        model_name: Name of the loaded model
        language: Default language setting
        uptime_seconds: Service uptime in seconds
        version: Service version
    """

    status: str = Field(..., description="Health status")
    model_loaded: bool = Field(..., description="Model loaded status")
    model_name: Optional[str] = Field(default=None, description="Model name")
    language: str = Field(..., description="Default language")
    uptime_seconds: float = Field(..., ge=0.0, description="Uptime in seconds")
    version: str = Field(..., description="Service version")
