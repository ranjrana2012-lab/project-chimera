"""Configuration for Operator Console service."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class ConsoleConfig:
    """Operator Console service configuration."""

    # Service settings
    service_name: str = "operator-console"
    service_version: str = "0.1.0"
    host: str = field(default_factory=lambda: os.getenv("CONSOLE_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("CONSOLE_PORT", "8007")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Kafka settings
    kafka_brokers: str = field(
        default_factory=lambda: os.getenv("KAFKA_BROKERS", "localhost:9092")
    )
    kafka_topics: List[str] = field(
        default_factory=lambda: [
            "chimera.events",
            "chimera.approvals",
            "chimera.overrides",
            "chimera.health",
        ]
    )
    consumer_group: str = "operator-console"

    # Event aggregator settings
    max_events: int = field(default_factory=lambda: int(os.getenv("MAX_EVENTS", "1000")))
    event_buffer_size: int = 1000

    # Approval handler settings
    approval_request_topic: str = "chimera.approvals"
    approval_response_topic: str = "chimera.approvals"
    default_expiry_minutes: int = field(
        default_factory=lambda: int(os.getenv("APPROVAL_EXPIRY_MINUTES", "30"))
    )
    max_pending_approvals: int = 1000

    # Override manager settings
    override_topic: str = "chimera.overrides"
    max_active_overrides: int = 100

    # UI settings
    ui_title: str = "Project Chimera - Operator Console"
    ui_refresh_interval_ms: int = field(
        default_factory=lambda: int(os.getenv("UI_REFRESH_MS", "1000"))
    )
    max_displayed_events: int = field(
        default_factory=lambda: int(os.getenv("MAX_DISPLAYED_EVENTS", "100"))
    )
    alert_sound_enabled: bool = field(
        default_factory=lambda: os.getenv("ALERT_SOUND", "true").lower() == "true"
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS settings
    cors_origins: List[str] = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS", "http://localhost:8007,http://localhost:3000"
        ).split(",")
    )

    # WebSocket settings
    ws_ping_interval: int = 20
    ws_ping_timeout: int = 30
    max_ws_connections: int = 100


# Global config instance
config = ConsoleConfig()
