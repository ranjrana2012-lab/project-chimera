"""
Configuration for Lighting-Sound-Music Service.

Environment-based configuration with pydantic-settings for DMX control,
audio playback, and telemetry integration.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    model_config = ConfigDict(env_file=".env")

    # Service
    service_name: str = "lighting-sound-music"
    port: int = 8005
    log_level: str = "INFO"

    # DMX Configuration
    dmx_enabled: bool = True
    dmx_universe: int = 1
    dmx_interface: str = "placeholder"  # Will be configured when hardware is available

    # Audio Configuration
    audio_enabled: bool = True
    audio_sample_rate: int = 44100
    audio_channels: int = 2
    audio_buffer_size: int = 1024

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Synchronization
    sync_tolerance_ms: int = 50  # Tolerance for lighting/audio sync in milliseconds


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
