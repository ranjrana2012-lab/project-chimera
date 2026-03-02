"""Configuration for Lighting Control service."""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for Lighting Control service."""

    # Service configuration
    app_name: str = "lighting-control"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8005
    debug: bool = True
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # sACN Configuration
    sacn_universe: int = 1
    sacn_priority: int = 100
    sacn_source_name: str = "Project Chimera Lighting"
    sacn_enabled: bool = True

    # DMX Configuration (for legacy/raw DMX)
    dmx_host: str = "192.168.1.100"
    dmx_port: int = 6454
    dmx_channels: int = 512

    # OSC Configuration
    osc_server_host: str = "0.0.0.0"
    osc_server_port: int = 9000
    osc_client_host: str = "127.0.0.1"
    osc_client_port: int = 9000
    osc_enabled: bool = True

    # Fixture Configuration
    fixture_config_path: Path = Field(
        default=Path("/etc/lighting-control/fixtures.json")
    )

    # Preset Configuration
    preset_path: Path = Field(
        default=Path("/var/lib/lighting-control/presets.json")
    )

    # Approval Gates
    require_scene_change_approval: bool = False

    # Default fixture configuration
    default_fixtures: dict = Field(
        default={
            "stage_left": {"address": 1, "channels": 3},
            "stage_center": {"address": 5, "channels": 3},
            "stage_right": {"address": 9, "channels": 3}
        }
    )

    # Timing defaults
    default_fade_time: float = 0.0
    default_delay_time: float = 0.0

    # Cue configuration
    default_cue_list: str = "main"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_prefix = "LIGHTING_"
        env_file = ".env"
        case_sensitive = False


settings = Settings()
