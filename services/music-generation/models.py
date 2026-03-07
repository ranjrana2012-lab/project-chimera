"""Pydantic models for Music Generation Service."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from enum import Enum


class ModelName(str, Enum):
    """Available model names."""
    MUSICGEN = "musicgen"
    ACESTEP = "acestep"


class GenerationRequest(BaseModel):
    """Music generation request."""

    prompt: str = Field(..., min_length=1, max_length=500, description="Text prompt for music generation")
    model: ModelName = Field(default=ModelName.MUSICGEN, description="Model to use")
    duration: float = Field(default=5.0, ge=1.0, le=30.0, description="Duration in seconds")
    sample_rate: int = Field(default=44100, ge=16000, le=48000, description="Sample rate in Hz")

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v):
        """Validate prompt is not just whitespace."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()


class GenerationResponse(BaseModel):
    """Music generation response."""

    success: bool
    audio_url: Optional[str] = None
    duration: float
    sample_rate: int
    format: str = "wav"
    model: str
    generation_time: float
    file_size: Optional[int] = None
    error: Optional[str] = None


class ModelInfo(BaseModel):
    """Model information."""

    name: str
    loaded: bool
    vram_mb: Optional[int] = None
    sample_rate: int
    description: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str  # "ok" or "error"
    service: str
    version: str = "1.0.0"
    models_loaded: List[str] = []


class ErrorResponse(BaseModel):
    """Error response."""

    error: dict
