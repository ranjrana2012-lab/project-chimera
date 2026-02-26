"""
Configuration for SceneSpeak Agent
"""

import os
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """SceneSpeak Agent settings."""

    # Application
    app_name: str = "scenespeak-agent"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # Model Configuration
    model_path: Path = Field(default=Path("/app/models/llama-2-7b"))
    model_name: str = "llama-2-7b-chat"
    model_cache_path: Path = Field(default=Path("/app/models/cache"))
    quantization: bool = True
    load_in_8bit: bool = True

    # Generation Parameters
    max_tokens: int = 512
    temperature: float = 0.8
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1

    # GPU Configuration
    gpu_enabled: bool = True
    gpu_device_id: int = 0
    gpu_memory_utilization: float = 0.9

    # Redis Cache
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300

    # Prompts
    prompts_path: Path = Field(default=Path("/app/models/prompts"))
    default_prompt_version: str = "v1.0.0"

    # Safety
    safety_filter_endpoint: str = "http://safety-filter.live.svc.cluster.local:8006"
    safety_enabled: bool = True

    # Monitoring
    metrics_enabled: bool = True
    tracing_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
