"""Pydantic models for Music Generation Service.

Request and response models for API endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Dict, Any
from enum import Enum


class ModelName(str, Enum):
    """Available model names."""
    MUSICGEN = "musicgen"
    ACESTEP = "acestep"


# ============================================================================
# E2E-Compatible API Models
# ============================================================================

class HealthResponse(BaseModel):
    """Response model for health check endpoint (E2E compatible)"""
    status: str = Field(..., description="Health status (healthy/error)")
    service: str = Field(..., description="Service name")
    model_loaded: bool = Field(..., description="Whether the model is loaded")
    model_info: Optional[Dict[str, Any]] = Field(None, description="Model information")


class ModelInfo(BaseModel):
    """Model information (E2E compatible)"""
    name: str = Field(..., description="Model name")
    loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="Model version")


class GenerateRequest(BaseModel):
    """Request to generate music (E2E compatible)"""
    prompt: str = Field(..., min_length=1, max_length=500, description="Text prompt for music generation")
    duration: int = Field(..., ge=1, le=300, description="Duration in seconds (1-300)")
    mood: Optional[str] = Field(None, description="Mood for the music")
    genre: Optional[str] = Field(None, description="Genre of the music")
    tempo: Optional[int] = Field(None, ge=40, le=240, description="Tempo in BPM (40-240)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Custom generation parameters")

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v):
        """Validate prompt is not just whitespace."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()


class GenerationMetadata(BaseModel):
    """Metadata for generated music"""
    model: str = Field(..., description="Model used for generation")
    generation_time_ms: float = Field(..., description="Generation time in milliseconds")
    timestamp: str = Field(..., description="Generation timestamp")


class GenerateResponse(BaseModel):
    """Response from music generation (E2E compatible)"""
    audio_data: Dict[str, Any] = Field(..., description="Generated audio data")
    duration: int = Field(..., description="Duration in seconds")
    format: str = Field(..., description="Audio format")
    prompt: str = Field(..., description="Original prompt")
    mood: Optional[str] = Field(None, description="Requested mood")
    genre: Optional[str] = Field(None, description="Requested genre")
    tempo: Optional[int] = Field(None, description="Requested tempo")
    metadata: Optional[GenerationMetadata] = Field(None, description="Generation metadata")


class ContinueRequest(BaseModel):
    """Request to continue existing music generation"""
    seed_music_id: str = Field(..., description="ID of the seed music to continue")
    duration: int = Field(..., ge=1, le=300, description="Additional duration in seconds")


class ContinueResponse(BaseModel):
    """Response from continue generation"""
    audio_data: Dict[str, Any] = Field(..., description="Generated audio data")
    seed_music_id: str = Field(..., description="ID of the seed music")
    duration: int = Field(..., description="Duration in seconds")
    format: str = Field(..., description="Audio format")


class BatchGenerateItem(BaseModel):
    """Single item in batch generation"""
    prompt: str = Field(..., min_length=1, description="Text prompt for this track")
    duration: int = Field(..., ge=1, le=300, description="Duration in seconds")
    mood: Optional[str] = Field(None, description="Mood for the music")
    genre: Optional[str] = Field(None, description="Genre of the music")


class BatchGenerateRequest(BaseModel):
    """Request for batch music generation"""
    prompts: List[BatchGenerateItem] = Field(..., min_items=1, max_items=10, description="List of prompts to generate")


class BatchGenerateResponse(BaseModel):
    """Response from batch generation"""
    tracks: List[GenerateResponse] = Field(..., description="Generated tracks")
    total_duration: int = Field(..., description="Total duration across all tracks")
    count: int = Field(..., description="Number of tracks generated")


class GenresResponse(BaseModel):
    """Response from genres endpoint"""
    genres: List[str] = Field(..., description="Available music genres")


class MoodsResponse(BaseModel):
    """Response from moods endpoint"""
    moods: List[str] = Field(..., description="Available music moods")


class HistoryResponse(BaseModel):
    """Response from history endpoint"""
    generations: List[Dict[str, Any]] = Field(..., description="Generation history")
    count: int = Field(..., description="Number of generations")
    limit: int = Field(..., description="Limit applied")


# Legacy models (kept for compatibility)
class GenerationRequestLegacy(BaseModel):
    """Music generation request (legacy)."""

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


class GenerationResponseLegacy(BaseModel):
    """Music generation response (legacy)."""

    success: bool
    audio_url: Optional[str] = None
    duration: float
    sample_rate: int
    format: str = "wav"
    model: str
    generation_time: float
    file_size: Optional[int] = None
    error: Optional[str] = None


class ModelInfoLegacy(BaseModel):
    """Model information (legacy)."""

    name: str
    loaded: bool
    vram_mb: Optional[int] = None
    sample_rate: int
    description: str


class HealthResponseLegacy(BaseModel):
    """Health check response (legacy)."""

    status: str  # "ok" or "error"
    service: str
    version: str = "1.0.0"
    models_loaded: List[str] = []


class ErrorResponse(BaseModel):
    """Error response."""

    error: dict


# Valid genres and moods for validation
VALID_GENRES = {
    "ambient", "classical", "dramatic", "electronic", "folk", "jazz",
    "metal", "pop", "rock", "romantic", "techno"
}

VALID_MOODS = {
    "happy", "sad", "tense", "calm", "dramatic", "energetic",
    "melancholic", "peaceful", "aggressive", "mysterious"
}

