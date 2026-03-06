"""
Pydantic models for BSL Agent.

Defines request/response models for text-to-BSL-gloss translation and avatar rendering.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


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
