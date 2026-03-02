"""Shared data models for coordinated cues.

This module defines the data models used across lighting, sound, music,
and cues modules for coordinated theatrical scenes.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class CueState(str, Enum):
    """State of a cue execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class LightingCue(BaseModel):
    """Lighting cue parameters."""
    fixture_id: str = Field(..., description="Fixture identifier")
    intensity: float = Field(default=1.0, ge=0.0, le=1.0, description="Light intensity 0-1")
    color: Optional[str] = Field(None, description="RGB hex color (e.g., '#FF0000')")
    fade_time: float = Field(default=0.0, ge=0.0, description="Fade time in seconds")
    dmx_values: Optional[List[int]] = Field(None, description="Raw DMX values")


class SoundCue(BaseModel):
    """Sound effect cue parameters."""
    sound_name: str = Field(..., description="Sound effect name")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Volume 0-1")
    start_time: float = Field(default=0.0, ge=0.0, description="Start time relative to cue (seconds)")
    duration: Optional[float] = Field(None, description="Duration to play (seconds)")
    fade_in: float = Field(default=0.0, ge=0.0, description="Fade in time (seconds)")
    fade_out: float = Field(default=0.0, ge=0.0, description="Fade out time (seconds)")


class MusicCue(BaseModel):
    """Music cue parameters."""
    action: str = Field(..., description="Action: play, stop, pause, fade")
    track_id: Optional[str] = Field(None, description="Track ID for play action")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Volume 0-1")
    fade_time: float = Field(default=0.0, ge=0.0, description="Fade time (seconds)")
    start_time: float = Field(default=0.0, ge=0.0, description="Start time relative to cue (seconds)")


class CoordinatedCue(BaseModel):
    """A coordinated theatrical cue combining lighting, sound, and music.

    This represents a complete scene change or moment in a theatrical
    production, coordinating all audio-visual elements with precise timing.
    """
    name: str = Field(..., description="Unique cue name/identifier")
    description: Optional[str] = Field(None, description="Human-readable description")
    duration: float = Field(..., ge=0.0, description="Total cue duration in seconds")
    lighting: List[LightingCue] = Field(default_factory=list, description="Lighting cues")
    sound: List[SoundCue] = Field(default_factory=list, description="Sound effect cues")
    music: Optional[MusicCue] = Field(None, description="Music cue")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    auto_start: bool = Field(default=False, description="Start automatically on load")


class CueExecutionRequest(BaseModel):
    """Request to execute a cue."""
    cue_name: str
    background: bool = Field(default=True, description="Execute in background")
    wait_for_completion: bool = Field(default=False, description="Wait for completion")


class CueLibraryEntry(BaseModel):
    """Entry in the cue library."""
    name: str
    description: Optional[str]
    duration: float
    created_at: str
    tags: List[str]
    last_executed: Optional[str] = None
    execution_count: int = 0


class CueExecutionStatus(BaseModel):
    """Status of a running cue execution."""
    cue_name: str
    state: CueState
    started_at: Optional[str]
    completed_at: Optional[str]
    elapsed: Optional[float]
    progress: Optional[float]  # 0-1
    error: Optional[str] = None


class TimelineEvent(BaseModel):
    """An event on the execution timeline."""
    time: float = Field(..., ge=0.0, description="Time offset in seconds")
    module: str = Field(..., description="Module: lighting, sound, or music")
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
