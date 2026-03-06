"""
Pydantic models for Lighting-Sound-Music Service.

Request and response models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional


class LightingSceneRequest(BaseModel):
    """Request model for setting a lighting scene"""
    scene_id: str = Field(..., description="Unique identifier for the lighting scene")
    channels: Dict[int, int] = Field(
        ...,
        description="DMX channel values (channel_number: value 0-255)"
    )
    fade_time_ms: Optional[int] = Field(
        0,
        description="Fade time in milliseconds (not implemented in placeholder)",
        ge=0
    )


class LightingResponse(BaseModel):
    """Response model for lighting scene operations"""
    scene_id: str = Field(..., description="Scene identifier from request")
    status: str = Field(..., description="Operation status (success/error)")
    channels_set: int = Field(..., description="Number of channels configured")
    duration_ms: int = Field(..., description="Operation duration in milliseconds")
    message: str = Field(..., description="Detailed status message")


class AudioCueRequest(BaseModel):
    """Request model for playing an audio cue"""
    cue_id: str = Field(..., description="Unique identifier for the audio cue")
    file_path: str = Field(..., description="Path to audio file")
    volume: float = Field(
        1.0,
        description="Volume level (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    loop: bool = Field(False, description="Whether to loop the audio")


class AudioResponse(BaseModel):
    """Response model for audio cue operations"""
    cue_id: str = Field(..., description="Cue identifier from request")
    status: str = Field(..., description="Playback status")
    duration_ms: int = Field(..., description="Operation duration in milliseconds")
    message: str = Field(..., description="Detailed status message")


class SyncSceneRequest(BaseModel):
    """Request model for synchronized lighting and audio scene"""
    scene_id: str = Field(..., description="Unique identifier for the synchronized scene")
    lighting_channels: Dict[int, int] = Field(
        ...,
        description="DMX channel values for lighting"
    )
    audio_file: str = Field(..., description="Path to audio file")
    audio_volume: float = Field(
        1.0,
        description="Audio volume level (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    delay_ms: int = Field(
        0,
        description="Delay before triggering scene in milliseconds",
        ge=0
    )


class SyncResponse(BaseModel):
    """Response model for synchronized scene operations"""
    scene_id: str = Field(..., description="Scene identifier from request")
    status: str = Field(..., description="Operation status (success/error)")
    lighting_triggered_at: float = Field(..., description="Timestamp when lighting was triggered")
    audio_triggered_at: float = Field(..., description="Timestamp when audio was triggered")
    duration_ms: int = Field(..., description="Total operation duration in milliseconds")
    message: str = Field(..., description="Detailed status message")


class HealthResponse(BaseModel):
    """Response model for health check endpoints"""
    status: str = Field(..., description="Health status (ready/not_ready)")
    service: str = Field(..., description="Service name")
    checks: Dict[str, bool] = Field(..., description="Individual component health checks")
