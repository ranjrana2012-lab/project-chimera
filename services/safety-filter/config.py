"""
Configuration for Safety Filter.

Environment-based configuration with pydantic-settings for content moderation service.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    model_config = ConfigDict(env_file=".env")

    # Service
    service_name: str = "safety-filter"
    port: int = 8005
    log_level: str = "INFO"
    environment: str = "development"

    # Content Moderation
    default_policy: str = "family"
    enable_ml_filter: bool = False  # ML enhancement for later
    enable_context_filter: bool = True
    cache_ttl: int = 3600  # 1 hour

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Audit Log
    audit_log_max_size: int = 10000
    audit_log_retention_hours: int = 24


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
