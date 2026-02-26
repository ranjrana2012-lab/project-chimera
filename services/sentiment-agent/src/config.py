"""Configuration for Sentiment Agent"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "sentiment-agent"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8004
    debug: bool = True
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    model_name: str = "cardiffnlp/twitter-roberta-base-sentiment"
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    cache_ttl_seconds: int = 30


settings = Settings()
