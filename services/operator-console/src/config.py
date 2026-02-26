"""Configuration for Operator Console"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "operator-console"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8007
    debug: bool = True
    cors_origins: List[str] = Field(default=["*"])

    # Service Endpoints
    safety_filter_endpoint: str = "http://safety-filter.live.svc.cluster.local:8006"
    lighting_endpoint: str = "http://lighting-control.live.svc.cluster.local:8005"

    # Alerting
    alert_retention_hours: int = 24


settings = Settings()
