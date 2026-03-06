# config.py
"""Captioning Agent Configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Captioning Agent configuration from environment variables"""

    # Service
    service_name: str = "captioning-agent"
    service_version: str = "1.0.0"
    port: int = 8002
    debug: bool = False

    # Whisper Model
    whisper_model_size: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu or cuda
    whisper_compute_type: str = "float32"  # float32, float16, int8

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"
    enable_tracing: bool = True

    # File Upload
    max_file_size: int = 25 * 1024 * 1024  # 25MB
    allowed_audio_formats: list = [".wav", ".mp3", ".ogg", ".flac", ".m4a"]

    # WebSocket
    websocket_chunk_size: int = 4096
    websocket_sample_rate: int = 16000

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


def get_settings() -> Settings:
    """Get captioning agent settings"""
    return Settings()


# Global settings instance
settings = get_settings()
