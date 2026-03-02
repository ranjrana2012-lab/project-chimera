"""Request models for Lighting Control service."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class LightingRequest(BaseModel):
    """Request for lighting control operations.

    Attributes:
        universe: sACN universe number (1-63999)
        fixture_addresses: Dictionary mapping fixture IDs to DMX addresses
        values: Dictionary mapping channel numbers to DMX values (0-255)
        fade_time: Fade transition time in seconds
        priority: Priority level for conflicting sACN data (0-200, 100=default)
    """
    universe: int = Field(
        default=1,
        ge=1,
        le=63999,
        description="sACN universe number"
    )
    fixture_addresses: Dict[str, int] = Field(
        default_factory=dict,
        description="Fixture ID to DMX address mapping"
    )
    values: Dict[int, int] = Field(
        ...,
        description="Channel to DMX value mapping (0-255)"
    )
    fade_time: float = Field(
        default=0.0,
        ge=0.0,
        le=3600.0,
        description="Fade time in seconds"
    )
    priority: int = Field(
        default=100,
        ge=0,
        le=200,
        description="sACN priority (0-200, 100=default)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "universe": 1,
                    "fixture_addresses": {"stage_left": 1, "stage_right": 5},
                    "values": {1: 255, 2: 200, 3: 180, 5: 255, 6: 200},
                    "fade_time": 2.5,
                    "priority": 100
                }
            ]
        }
    }


class FixtureValues(BaseModel):
    """Per-fixture value specification.

    Attributes:
        fixture_id: Fixture identifier
        channels: Channel values for this fixture (indexed from fixture base)
        intensity: Overall intensity modifier (0.0-1.0)
    """
    fixture_id: str = Field(
        ...,
        description="Fixture identifier"
    )
    channels: List[int] = Field(
        default_factory=list,
        description="Channel values (DMX 0-255)"
    )
    intensity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Intensity modifier"
    )


class PresetRequest(BaseModel):
    """Request for lighting preset operations.

    Attributes:
        name: Preset name
        description: Preset description
        values: Channel values for this preset
        fixtures: List of fixture configurations
        fade_time: Default fade time for this preset
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Preset name"
    )
    description: Optional[str] = Field(
        default="",
        max_length=500,
        description="Preset description"
    )
    values: Dict[int, int] = Field(
        default_factory=dict,
        description="Channel values"
    )
    fixtures: List[FixtureValues] = Field(
        default_factory=list,
        description="Fixture configurations"
    )
    fade_time: float = Field(
        default=0.0,
        ge=0.0,
        le=3600.0,
        description="Default fade time"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "warm_intimate",
                    "description": "Warm intimate scene",
                    "values": {1: 200, 2: 180, 5: 200},
                    "fixtures": [
                        {
                            "fixture_id": "stage_left",
                            "channels": [255, 200, 180],
                            "intensity": 0.8
                        }
                    ],
                    "fade_time": 3.0
                }
            ]
        }
    }


class CueRequest(BaseModel):
    """Request for cue execution.

    Attributes:
        cue_number: Cue identifier (numeric or string)
        cue_list: Cue list identifier
        preset_name: Preset to apply
        values: Override channel values
        fade_time: Override fade time
        delay_secs: Delay before execution
        follow_on: Automatically trigger next cue
    """
    cue_number: str = Field(
        ...,
        description="Cue identifier"
    )
    cue_list: str = Field(
        default="main",
        description="Cue list identifier"
    )
    preset_name: Optional[str] = Field(
        default=None,
        description="Preset to apply"
    )
    values: Optional[Dict[int, int]] = Field(
        default=None,
        description="Override channel values"
    )
    fade_time: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=3600.0,
        description="Override fade time"
    )
    delay_secs: float = Field(
        default=0.0,
        ge=0.0,
        le=3600.0,
        description="Delay before execution"
    )
    follow_on: bool = Field(
        default=False,
        description="Auto-trigger next cue"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cue_number": "1",
                    "cue_list": "main",
                    "preset_name": "warm_intimate",
                    "fade_time": 2.0,
                    "delay_secs": 0.5,
                    "follow_on": False
                }
            ]
        }
    }


class OSCMessageRequest(BaseModel):
    """Request for OSC message sending.

    Attributes:
        address: OSC address pattern (e.g., /lighting/fixture/1/intensity)
        arguments: OSC arguments (int, float, or string)
        host: Target host (None for broadcast)
        port: Target port
    """
    address: str = Field(
        ...,
        description="OSC address pattern"
    )
    arguments: List[Any] = Field(
        default_factory=list,
        description="OSC arguments"
    )
    host: Optional[str] = Field(
        default=None,
        description="Target host"
    )
    port: int = Field(
        default=9000,
        ge=1,
        le=65535,
        description="Target port"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "address": "/lighting/fixture/1/intensity",
                    "arguments": [0.8],
                    "port": 9000
                }
            ]
        }
    }
