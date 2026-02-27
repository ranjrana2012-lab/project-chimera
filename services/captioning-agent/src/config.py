"""
Configuration for Captioning Agent
"""

import os
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Captioning Agent settings."""

    # Application
    app_name: str = "captioning-agent"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # Whisper Model Configuration
    whisper_model: str = "base"  # tiny, base, small, medium, large
    model_path: Path = Field(default=Path("/app/models/whisper"))
    language: str = "en"  # Default language
    task: str = "transcribe"  # transcribe or translate

    # Transcription Options
    enable_word_timestamps: bool = False
    enable_vad: bool = False
    chunk_size_seconds: int = 30  # Process audio in chunks

    # Streaming Configuration
    enable_streaming: bool = True
    stream_chunk_size_ms: int = 1000  # 1 second chunks for streaming
    stream_overlap_ms: int = 100  # Overlap between chunks
    session_timeout_seconds: int = 300  # 5 minutes

    # Audio Processing
    sample_rate: int = 16000  # Whisper requires 16kHz
    audio_channels: int = 1  # Mono audio
    supported_formats: List[str] = Field(
        default=["wav", "pcm", "flac", "ogg", "mp3"]
    )

    # GPU Configuration
    gpu_enabled: bool = False  # Whisper runs well on CPU
    gpu_device_id: int = 0

    # Redis Cache (optional for caching results)
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    cache_enabled: bool = False
    cache_ttl_seconds: int = 3600  # 1 hour

    # Monitoring
    metrics_enabled: bool = True
    tracing_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("whisper_model")
    @classmethod
    def validate_whisper_model(cls, v: str) -> str:
        valid_models = ["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"]
        if v not in valid_models:
            raise ValueError(f"Invalid whisper_model: {v}. Must be one of {valid_models}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        # Basic validation - Whisper supports 99+ languages
        if len(v) < 2 or len(v) > 3:
            raise ValueError(f"Invalid language code: {v}. Use ISO 639-1 or 639-2 format")
        return v.lower()


settings = Settings()
