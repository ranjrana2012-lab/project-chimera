"""Configuration for Safety Filter"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "safety-filter"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8006
    debug: bool = True
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # Policy Configuration
    policy_path: Path = Field(default=Path("/app/configs/policies"))
    default_action: str = "flag"  # block, flag, warn

    # Review Queue
    review_queue_size: int = 1000
    review_ttl_seconds: int = 3600


settings = Settings()
