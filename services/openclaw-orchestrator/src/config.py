"""OpenClaw Orchestrator configuration."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service
    app_name: str = "openclaw-orchestrator"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # GPU
    gpu_enabled: bool = True
    cuda_visible_devices: str = "0"

    # Redis
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # Kafka
    kafka_bootstrap_servers: str = "kafka.shared.svc.cluster.local:9092"
    kafka_consumer_group: str = "openclaw-orchestrator"

    # Vector DB
    vector_db_host: str = "vector-db.shared.svc.cluster.local"
    vector_db_port: int = 19530

    # Skills
    skills_config_path: str = "/app/configs/skills"

    # Monitoring
    jaeger_host: str = "jaeger.shared.svc.cluster.local"
    jaeger_port: int = 6831
    jaeger_sample_rate: float = 0.1

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


settings = Settings()
