"""SceneSpeak Agent configuration."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Service
    app_name: str = "scenespeak-agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # Model
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"
    device: str = "cuda"
    quantization_enabled: bool = True
    model_download_path: str = "/app/models"
    model_cache_enabled: bool = True

    # Generation
    max_tokens_default: int = 256
    temperature_default: float = 0.8
    top_p_default: float = 0.95

    # Cache
    cache_enabled: bool = True
    cache_ttl: int = 3600

    # Redis
    redis_host: str = "redis.shared.svc.cluster.local"
    redis_port: int = 6379
    redis_password: str = ""

    # Kafka
    kafka_bootstrap_servers: str = "kafka.shared.svc.cluster.local:9092"

    # Monitoring
    jaeger_host: str = "jaeger.shared.svc.cluster.local"
    jaeger_port: int = 6831

    class Config:
        env_file = ".env"

settings = Settings()
