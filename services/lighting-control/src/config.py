"""Configuration for Lighting Control"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "lighting-control"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8005
    debug: bool = True
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # DMX Configuration
    dmx_host: str = "192.168.1.100"
    dmx_port: int = 6454
    dmx_universe: int = 1
    dmx_channels: int = 512

    # OSC Configuration
    osc_host: str = "127.0.0.1"
    osc_port: int = 9000

    # Approval Gates
    require_scene_change_approval: bool = True


settings = Settings()
