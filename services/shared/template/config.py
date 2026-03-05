# config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Service configuration from environment variables"""

    # Service
    service_name: str = "service-template"
    service_version: str = "1.0.0"
    port: int = 8000
    debug: bool = False

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Kafka
    kafka_brokers: str = "localhost:9092"
    kafka_topic: str = "chimera-events"

    # AI Models
    glm_api_key: Optional[str] = None
    glm_api_base: str = "https://open.bigmodel.cn/api/paas/v4/"
    local_model_path: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get service settings"""
    return Settings()
