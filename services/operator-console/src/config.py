"""Configuration for Operator Console service."""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Operator Console service settings."""

    # Service settings
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

    # Kafka settings
    kafka_brokers: str = "localhost:9092"
    kafka_topics: List[str] = [
        "chimera.events",
        "chimera.approvals",
        "chimera.overrides",
        "chimera.health",
    ]
    consumer_group: str = "operator-console"

    # Event aggregator settings
    max_events: int = 1000
    event_buffer_size: int = 1000

    # Approval handler settings
    approval_request_topic: str = "chimera.approvals"
    approval_response_topic: str = "chimera.approvals"
    default_expiry_minutes: int = 30
    max_pending_approvals: int = 1000

    # Override manager settings
    override_topic: str = "chimera.overrides"
    max_active_overrides: int = 100

    # UI settings
    ui_title: str = "Project Chimera - Operator Console"
    ui_refresh_interval_ms: int = 1000
    max_displayed_events: int = 100

    # WebSocket settings
    ws_ping_interval: int = 20
    ws_ping_timeout: int = 30
    max_ws_connections: int = 100


settings = Settings()
