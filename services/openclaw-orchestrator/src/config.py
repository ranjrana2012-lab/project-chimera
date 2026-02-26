"""
Configuration Management for OpenClaw Orchestrator
"""

import os
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "openclaw-orchestrator"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # Paths
    skills_path: Path = Field(default=Path("/app/skills"))
    models_path: Path = Field(default=Path("/app/models"))
    config_path: Path = Field(default=Path("/app/configs"))

    # GPU Configuration
    gpu_enabled: bool = True
    gpu_device_id: int = 0
    model_cache_path: Path = Field(default=Path("/app/models/cache"))

    # Redis
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_max_connections: int = 50

    # Kafka
    kafka_bootstrap_servers: str = "kafka.shared.svc.cluster.local:9092"
    kafka_consumer_group: str = "openclaw-orchestrator"
    kafka_auto_offset_reset: str = "latest"

    # Vector Database
    vector_db_host: str = "vector-db.shared.svc.cluster.local"
    vector_db_port: int = 19530
    vector_db_index: str = "chimera-skills"

    # OpenTelemetry
    tracing_enabled: bool = True
    jaeger_host: str = "jaeger.shared.svc.cluster.local"
    jaeger_port: int = 6831

    # Prometheus
    metrics_enabled: bool = True
    prometheus_host: str = "prometheus.shared.svc.cluster.local"
    prometheus_port: int = 9090

    # Kubernetes
    k8s_namespace: str = "live"
    k8s_pod_name: str = Field(default_factory=lambda: os.getenv("POD_NAME", "localhost"))
    k8s_pod_ip: str = Field(default_factory=lambda: os.getenv("POD_IP", "127.0.0.1"))

    # Service Endpoints
    scenespeak_endpoint: str = "http://scenespeak-agent.live.svc.cluster.local:8001"
    captioning_endpoint: str = "http://captioning-agent.live.svc.cluster.local:8002"
    bsl_text2gloss_endpoint: str = "http://bsl-text2gloss-agent.live.svc.cluster.local:8003"
    sentiment_endpoint: str = "http://sentiment-agent.live.svc.cluster.local:8004"
    lighting_endpoint: str = "http://lighting-control.live.svc.cluster.local:8005"
    safety_endpoint: str = "http://safety-filter.live.svc.cluster.local:8006"
    operator_endpoint: str = "http://operator-console.live.svc.cluster.local:8007"

    # Pipeline Configuration
    pipeline_timeout_ms: int = 10000
    pipeline_max_retries: int = 3
    pipeline_parallelism: int = 4

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


# Global settings instance
settings = Settings()
