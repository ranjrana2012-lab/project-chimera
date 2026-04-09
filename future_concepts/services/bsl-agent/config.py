"""
Configuration for BSL Agent.

Environment-based configuration with pydantic-settings for BSL translation service.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    model_config = ConfigDict(env_file=".env")

    # Service
    service_name: str = "bsl-agent"
    port: int = 8003
    log_level: str = "INFO"
    environment: str = "development"

    # Avatar Rendering
    avatar_model_path: str = "/models/bsl_avatar"
    avatar_resolution: str = "1920x1080"
    avatar_fps: int = 30
    enable_facial_expressions: bool = True
    enable_body_language: bool = True

    # Translation
    cache_ttl: int = 86400  # 24 hours

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
