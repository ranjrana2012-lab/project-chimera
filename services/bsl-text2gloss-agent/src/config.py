"""Configuration for BSL Text2Gloss Agent"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "bsl-text2gloss-agent"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8003
    debug: bool = True
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    cache_ttl_seconds: int = 300


settings = Settings()
