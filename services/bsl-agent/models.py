"""
Pydantic models for BSL Agent.

Defines request/response models for text-to-BSL-gloss translation and avatar rendering.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class TranslateRequest(BaseModel):
    """Request for text-to-BSL-gloss translation"""
    text: str = Field(..., min_length=1, description="English text to translate")
    include_nmm: Optional[bool] = Field(True, description="Include non-manual markers")
    context: Optional[dict] = Field(None, description="Additional context")


class TranslateResponse(BaseModel):
    """Response from BSL gloss translation"""
    gloss: str
    breakdown: List[str]
    duration_estimate: float
    confidence: float
    non_manual_markers: Optional[List[str]] = None
    translation_time_ms: float


class SignMetadata(BaseModel):
    """Metadata for individual BSL signs"""
    gloss: str = Field(..., description="BSL gloss notation for this sign")
    handshape: str = Field(..., description="Hand shape used")
    location: str = Field(..., description="Location of the sign relative to body")


class APITranslateRequest(BaseModel):
    """Request for /api/translate endpoint"""
    text: str = Field(..., min_length=1, description="English text to translate")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for translation")


class APITranslateResponse(BaseModel):
    """Response from /api/translate endpoint"""
    gloss: str = Field(..., description="BSL gloss notation")
    duration: float = Field(..., description="Estimated signing duration in seconds")
    signs: List[SignMetadata] = Field(default_factory=list, description="Individual sign metadata")


class RenderRequest(BaseModel):
    """Request for avatar rendering"""
    gloss: str = Field(..., min_length=1, description="BSL gloss to render")
    session_id: Optional[str] = Field(None, description="Session ID for avatar instance")
    include_nmm: Optional[bool] = Field(True, description="Include non-manual markers in animation")


class RenderResponse(BaseModel):
    """Response from avatar rendering"""
    success: bool
    animation_data: dict
    gestures_queued: int
    session_id: Optional[str] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    translator_ready: bool
    avatar_ready: bool
    renderer: Optional[Dict[str, Any]] = None


# E2E Avatar Endpoint Models

class APIAvatarGenerateRequest(BaseModel):
    """Request for /api/avatar/generate endpoint"""
    text: str = Field(..., min_length=1, description="Text to generate avatar animation for")
    expression: Optional[str] = Field(None, description="Optional expression to apply (e.g., 'happy', 'sad')")


class AnimationMetadata(BaseModel):
    """Metadata for generated animation"""
    duration_ms: float = Field(..., description="Animation duration in milliseconds")
    fps: int = Field(..., description="Frames per second")


class APIAvatarGenerateResponse(BaseModel):
    """Response from /api/avatar/generate endpoint"""
    animation_data: Dict[str, Any] = Field(..., description="Generated animation data with frames")
    metadata: Optional[AnimationMetadata] = None


class APIAvatarExpressionRequest(BaseModel):
    """Request for /api/avatar/expression endpoint"""
    expression: str = Field(..., description="Expression to apply (e.g., 'happy', 'sad', 'neutral')")


class APIAvatarExpressionResponse(BaseModel):
    """Response from /api/avatar/expression endpoint"""
    expression: str = Field(..., description="Expression that was requested")
    applied: bool = Field(..., description="Whether the expression was successfully applied")


class APIAvatarHandshapeRequest(BaseModel):
    """Request for /api/avatar/handshape endpoint"""
    handshape: str = Field(..., description="Handshape to apply (e.g., 'wave', 'point')")
    hand: str = Field(..., description="Which hand ('left' or 'right')")


class APIAvatarHandshapeResponse(BaseModel):
    """Response from /api/avatar/handshape endpoint"""
    handshape: str = Field(..., description="Handshape that was requested")
    hand: str = Field(..., description="Hand that was specified")
    applied: bool = Field(..., description="Whether the handshape was successfully applied")


# Valid expressions for validation
VALID_EXPRESSIONS = {"happy", "sad", "neutral", "angry", "surprised", "confused"}

# Valid handshapes for validation
VALID_HANDSHAPES = {"wave", "point", "fist", "open", "peace", "thumbs_up"}
