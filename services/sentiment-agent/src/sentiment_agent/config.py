"""
Configuration for Sentiment Agent.

Environment-based configuration with pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    model_config = ConfigDict(env_file=".env")

    # Service
    service_name: str = "sentiment-agent"
    port: int = 8004
    log_level: str = "INFO"
    host: str = "0.0.0.0"

    # Model Configuration
    use_ml_model: bool = False  # Set to True when ML model is available
    model_path: Optional[str] = None  # Path to DistilBERT model
    model_cache_dir: Optional[str] = "./models_cache"

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"
    enable_tracing: bool = True

    # Processing
    max_text_length: int = 10000  # Maximum text length to process
    batch_size: int = 32  # Maximum batch size for processing


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
