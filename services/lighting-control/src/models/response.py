"""Response models for Lighting Control service."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class LightingStatus(str, Enum):
    """Lighting operation status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


class LightingResponse(BaseModel):
    """Response from lighting operations.

    Attributes:
        status: Operation status
        affected_fixtures: List of fixture IDs affected
        timing: Timing information
        universe: Universe number used
        channels_updated: Number of channels updated
    """
    status: LightingStatus = Field(
        ...,
        description="Operation status"
    )
    affected_fixtures: List[str] = Field(
        default_factory=list,
        description="Affected fixture IDs"
    )
    timing: Dict[str, float] = Field(
        default_factory=dict,
        description="Timing information (seconds)"
    )
    universe: int = Field(
        ...,
        description="Universe used"
    )
    channels_updated: int = Field(
        default=0,
        ge=0,
        description="Number of channels updated"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "affected_fixtures": ["stage_left", "stage_right"],
                    "timing": {"fade": 2.5, "total": 2.52},
                    "universe": 1,
                    "channels_updated": 6
                }
            ]
        }
    }


class FixtureState(BaseModel):
    """Current fixture state.

    Attributes:
        fixture_id: Fixture identifier
        dmx_address: Base DMX address
        channel_values: Current channel values
        last_update: Last update timestamp
        intensity: Current calculated intensity
    """
    fixture_id: str = Field(
        ...,
        description="Fixture identifier"
    )
    dmx_address: int = Field(
        ...,
        ge=1,
        le=512,
        description="Base DMX address"
    )
    channel_values: List[int] = Field(
        default_factory=list,
        description="Current channel values"
    )
    last_update: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    intensity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Calculated intensity"
    )


class LightingState(BaseModel):
    """Current lighting system state.

    Attributes:
        universe: Current universe
        dmx_values: All 512 DMX channel values
        fixtures: Dictionary of fixture states
        active_preset: Currently active preset
        active_cue: Currently active cue
        sACN_active: Whether sACN sender is active
        OSC_active: Whether OSC sender is active
    """
    universe: int = Field(
        ...,
        description="Current universe"
    )
    dmx_values: List[int] = Field(
        default_factory=lambda: [0] * 512,
        description="All 512 DMX values"
    )
    fixtures: Dict[str, FixtureState] = Field(
        default_factory=dict,
        description="Fixture states"
    )
    active_preset: Optional[str] = Field(
        default=None,
        description="Active preset name"
    )
    active_cue: Optional[str] = Field(
        default=None,
        description="Active cue number"
    )
    sACN_active: bool = Field(
        default=False,
        description="sACN sender status"
    )
    OSC_active: bool = Field(
        default=False,
        description="OSC sender status"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "universe": 1,
                    "dmx_values": [255, 200, 180, 0, 255, 200],
                    "fixtures": {
                        "stage_left": {
                            "fixture_id": "stage_left",
                            "dmx_address": 1,
                            "channel_values": [255, 200, 180],
                            "intensity": 0.9
                        }
                    },
                    "active_preset": "warm_intimate",
                    "active_cue": "1",
                    "sACN_active": True,
                    "OSC_active": True
                }
            ]
        }
    }


class PresetResponse(BaseModel):
    """Response for preset operations.

    Attributes:
        name: Preset name
        saved: Whether operation succeeded
        values: Channel values in preset
        fixtures: Fixture configurations
        fade_time: Default fade time
        timestamp: When preset was created/updated
    """
    name: str = Field(
        ...,
        description="Preset name"
    )
    saved: bool = Field(
        ...,
        description="Operation successful"
    )
    values: Dict[int, int] = Field(
        default_factory=dict,
        description="Channel values"
    )
    fixtures: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Fixture configurations"
    )
    fade_time: float = Field(
        default=0.0,
        description="Default fade time"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Creation/update timestamp"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class CueResponse(BaseModel):
    """Response for cue execution.

    Attributes:
        cue_number: Cue identifier
        executed: Whether cue was executed
        status: Execution status
        preset_used: Preset that was applied
        timing: Execution timing
        follow_triggered: Whether follow cue was triggered
    """
    cue_number: str = Field(
        ...,
        description="Cue identifier"
    )
    executed: bool = Field(
        ...,
        description="Cue executed successfully"
    )
    status: str = Field(
        ...,
        description="Status message"
    )
    preset_used: Optional[str] = Field(
        default=None,
        description="Preset applied"
    )
    timing: Dict[str, float] = Field(
        default_factory=dict,
        description="Timing information"
    )
    follow_triggered: bool = Field(
        default=False,
        description="Follow cue triggered"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cue_number": "1",
                    "executed": True,
                    "status": "completed",
                    "preset_used": "warm_intimate",
                    "timing": {"delay": 0.5, "fade": 2.0, "total": 2.5},
                    "follow_triggered": False
                }
            ]
        }
    }


class OSCResponse(BaseModel):
    """Response for OSC operations.

    Attributes:
        sent: Whether message was sent
        address: OSC address used
        host: Target host
        port: Target port
        timestamp: When message was sent
    """
    sent: bool = Field(
        ...,
        description="Message sent successfully"
    )
    address: str = Field(
        ...,
        description="OSC address"
    )
    host: Optional[str] = Field(
        default=None,
        description="Target host"
    )
    port: int = Field(
        ...,
        description="Target port"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Send timestamp"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class HealthResponse(BaseModel):
    """Health check response.

    Attributes:
        status: Overall health status
        sACN_connected: sACN connection status
        OSC_connected: OSC connection status
        uptime_seconds: Service uptime
        active_fixtures: Number of active fixtures
        active_presets: Number of loaded presets
    """
    status: str = Field(
        ...,
        description="Health status"
    )
    sACN_connected: bool = Field(
        default=False,
        description="sACN connection status"
    )
    OSC_connected: bool = Field(
        default=False,
        description="OSC connection status"
    )
    uptime_seconds: float = Field(
        default=0.0,
        description="Service uptime"
    )
    active_fixtures: int = Field(
        default=0,
        ge=0,
        description="Number of active fixtures"
    )
    active_presets: int = Field(
        default=0,
        ge=0,
        description="Number of loaded presets"
    )
