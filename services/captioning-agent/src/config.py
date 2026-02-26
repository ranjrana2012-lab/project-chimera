"""Configuration for Captioning Agent"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "captioning-agent"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = True
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    whisper_model: str = "base"
    language: str = "en"
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379


settings = Settings()
