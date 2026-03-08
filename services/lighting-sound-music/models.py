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


# E2E-compatible Lighting API Models

class DMXInfo(BaseModel):
    """DMX connection information"""
    connected: bool = Field(..., description="Whether DMX is connected")
    universe: int = Field(..., description="DMX universe number")


class ExtendedHealthResponse(BaseModel):
    """Extended health response with DMX info for E2E tests"""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    dmx_info: DMXInfo = Field(..., description="DMX connection information")


class SetLightingRequest(BaseModel):
    """Request to set lighting scene"""
    scene: str = Field(..., description="Scene identifier")
    mood: Optional[str] = Field(None, description="Mood for the scene")


class SetLightingResponse(BaseModel):
    """Response from set lighting scene"""
    success: bool = Field(..., description="Whether the operation succeeded")
    scene: str = Field(..., description="Scene that was set")


class SetColorRequest(BaseModel):
    """Request to set lighting color"""
    color: str = Field(..., description="Hex color code (#RRGGBB)")
    intensity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Intensity level (0.0 to 1.0)"
    )


class SetColorResponse(BaseModel):
    """Response from set color"""
    applied: bool = Field(..., description="Whether color was applied")
    color: str = Field(..., description="Color that was set")


class SetIntensityRequest(BaseModel):
    """Request to set lighting intensity"""
    intensity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Intensity level (0.0 to 1.0)"
    )


class SetIntensityResponse(BaseModel):
    """Response from set intensity"""
    applied: bool = Field(..., description="Whether intensity was applied")
    intensity: float = Field(..., description="Intensity that was set")


class TransitionState(BaseModel):
    """State for transition"""
    color: str = Field(..., description="Hex color code")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Intensity level")


class TransitionRequest(BaseModel):
    """Request to transition between states"""
    from_state: TransitionState = Field(..., alias="from", description="Starting state")
    to_state: TransitionState = Field(..., alias="to", description="Target state")
    duration: int = Field(..., description="Transition duration in milliseconds")


class TransitionResponse(BaseModel):
    """Response from transition"""
    started: bool = Field(..., description="Whether transition started")
    duration: int = Field(..., description="Transition duration in milliseconds")


class LightingStateResponse(BaseModel):
    """Current lighting state"""
    color: str = Field(..., description="Current color (hex)")
    intensity: float = Field(..., description="Current intensity")
    scene: str = Field(..., description="Current scene")


class PresetScene(BaseModel):
    """Preset scene definition"""
    name: str = Field(..., description="Preset name")
    description: Optional[str] = Field(None, description="Preset description")


class PresetsResponse(BaseModel):
    """Response from presets endpoint"""
    presets: list[PresetScene] = Field(..., description="Available presets")


class ApplyPresetRequest(BaseModel):
    """Request to apply a preset"""
    preset: str = Field(..., description="Preset name to apply")


class ApplyPresetResponse(BaseModel):
    """Response from apply preset"""
    applied: bool = Field(..., description="Whether preset was applied")
    preset: str = Field(..., description="Preset that was applied")


class ZoneRequest(BaseModel):
    """Request for zone-specific lighting"""
    zone: str = Field(..., description="Zone identifier")
    color: str = Field(..., description="Hex color code")
    intensity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Intensity level (0.0 to 1.0)"
    )


class ZoneResponse(BaseModel):
    """Response from zone control"""
    zone: str = Field(..., description="Zone that was controlled")
    applied: bool = Field(..., description="Whether settings were applied")


class EffectParams(BaseModel):
    """Parameters for lighting effect"""
    speed: Optional[int] = Field(None, description="Effect speed")
    duration: Optional[int] = Field(None, description="Effect duration in ms")


class EffectRequest(BaseModel):
    """Request to apply lighting effect"""
    effect: str = Field(..., description="Effect name (e.g., 'strobe')")
    params: Optional[EffectParams] = Field(None, description="Effect parameters")


class EffectResponse(BaseModel):
    """Response from effect endpoint"""
    effect: str = Field(..., description="Effect that was started")
    started: bool = Field(..., description="Whether effect started")


class BatchUpdate(BaseModel):
    """Single update in batch operation"""
    zone: str = Field(..., description="Zone identifier")
    color: str = Field(..., description="Hex color code")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Intensity level")


class BatchRequest(BaseModel):
    """Request for batch lighting updates"""
    updates: list[BatchUpdate] = Field(..., description="List of updates to apply")


class BatchResponse(BaseModel):
    """Response from batch operation"""
    updated: list[str] = Field(..., description="List of zones that were updated")


class ResetResponse(BaseModel):
    """Response from reset operation"""
    reset: bool = Field(..., description="Whether reset was successful")
