# models.py
"""Captioning Agent Pydantic Models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    loaded: bool
    version: str = "1.0.0"


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: Optional[str] = None
    version: Optional[str] = None
    checks: Optional[Dict[str, Any]] = None
    model_info: Optional[ModelInfo] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TranscriptionSegment(BaseModel):
    """Single transcription segment with timing"""
    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")


class TranscriptionRequest(BaseModel):
    """Transcription request for file upload"""
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'es')")
    task: Optional[str] = Field("transcribe", description="Task type: 'transcribe' or 'translate'")
    temperature: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Sampling temperature")


class TranscriptionResponse(BaseModel):
    """Transcription response"""
    text: str = Field(..., description="Full transcribed text")
    language: str = Field(..., description="Detected or specified language")
    segments: List[TranscriptionSegment] = Field(default_factory=list, description="Time-segmented transcription")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


class LanguageDetectionResponse(BaseModel):
    """Language detection response"""
    language: str = Field(..., description="Detected language code")
    confidence: Optional[float] = Field(None, description="Detection confidence")


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type: 'audio', 'transcription', 'error', 'status'")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketAudioChunk(BaseModel):
    """Audio chunk for WebSocket streaming"""
    audio_data: bytes = Field(..., description="Raw audio data")
    sample_rate: int = Field(16000, description="Audio sample rate")
    channels: int = Field(1, description="Number of audio channels")


class WebSocketTranscription(BaseModel):
    """Partial transcription result for WebSocket"""
    text: str = Field(..., description="Transcribed text")
    is_final: bool = Field(False, description="Whether this is a final result")
    language: Optional[str] = Field(None, description="Detected language")


class APITranscribeResponse(BaseModel):
    """E2E test compatible transcription response"""
    transcription: str = Field(..., description="Full transcribed text")
    confidence: float = Field(..., description="Overall confidence score (0-1)")
    language: Optional[str] = Field(None, description="Detected or specified language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Time-stamped transcription segments")
