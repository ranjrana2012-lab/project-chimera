"""
Configuration for Sentiment Agent

This module defines the configuration settings for the Sentiment Agent service,
using Pydantic for validation and environment variable loading.
"""

import os
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Sentiment Agent settings.

    Attributes:
        app_name: Application name
        app_version: Application version
        app_env: Environment (development/staging/production)
        host: Server host address
        port: Server port (default: 8004 for sentiment-agent)
        debug: Debug mode flag
        log_level: Logging level
        cors_origins: CORS allowed origins
    """

    # Application
    app_name: str = "sentiment-agent"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8004
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # Model Configuration
    model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"
    model_version: str = "distilbert-sst-2-v0.1.0"
    model_cache_dir: Path = Field(default=Path("/app/models/cache"))

    # Sentiment Analysis Configuration
    aggregation_window: int = Field(
        default=300,
        description="Default time window for sentiment aggregation (seconds)"
    )
    max_aggregation_samples: int = Field(
        default=10000,
        description="Maximum number of samples to store for aggregation"
    )

    # Redis Configuration (for future caching)
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    cache_enabled: bool = False
    cache_ttl_seconds: int = 30

    # Text Processing
    max_text_length: int = Field(
        default=5000,
        description="Maximum text length for analysis"
    )
    max_batch_size: int = Field(
        default=100,
        description="Maximum number of texts in a batch request"
    )

    # Observability
    metrics_enabled: bool = True
    tracing_enabled: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
