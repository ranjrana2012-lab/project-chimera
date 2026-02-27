"""Configuration settings for Safety Filter service."""

from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Safety Filter service configuration.

    Attributes:
        app_name: Application name
        app_version: Application version
        host: Host to bind to
        port: Port to bind to
        debug: Debug mode
        log_level: Logging level
        cors_origins: Allowed CORS origins
    """

    # Service Configuration
    app_name: str = "safety-filter"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8006
    debug: bool = True
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    # Word Filter Configuration
    word_list_path: Optional[Path] = Field(
        default=None,
        description="Path to word list configuration file"
    )

    # ML Filter Configuration
    ml_model_path: Optional[Path] = Field(
        default=None,
        description="Path to fine-tuned ML model"
    )
    device: str = Field(
        default="cpu",
        description="Device for ML inference (cpu/cuda)"
    )

    # Policy Engine Configuration
    policy_path: Path = Field(
        default=Path("/app/configs/policies/safety-policy.yaml"),
        description="Path to policy configuration file"
    )
    default_action: str = Field(
        default="flag",
        description="Default action when no rules match"
    )

    # Audit Logging Configuration
    kafka_servers: Optional[str] = Field(
        default=None,
        description="Kafka bootstrap servers"
    )
    kafka_topic: str = Field(
        default="safety-audit",
        description="Kafka topic for audit logs"
    )
    audit_log_path: Optional[Path] = Field(
        default=Path("/app/logs/audit.log"),
        description="Fallback audit log file path"
    )
    audit_enabled: bool = Field(
        default=True,
        description="Whether audit logging is enabled"
    )

    # Review Queue Configuration
    review_queue_size: int = Field(
        default=1000,
        description="Maximum size of review queue"
    )
    review_ttl_seconds: int = Field(
        default=3600,
        description="Time to live for review queue items"
    )

    # Performance Configuration
    max_content_length: int = Field(
        default=10000,
        description="Maximum content length in characters"
    )
    batch_max_size: int = Field(
        default=100,
        description="Maximum batch size for batch checks"
    )

    # Feature Flags
    enable_ml_filter: bool = Field(
        default=True,
        description="Enable ML-based filtering"
    )
    enable_word_filter: bool = Field(
        default=True,
        description="Enable word list filtering"
    )
    enable_policy_engine: bool = Field(
        default=True,
        description="Enable policy engine"
    )

    class Config:
        env_prefix = "SAFETY_FILTER_"
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()
