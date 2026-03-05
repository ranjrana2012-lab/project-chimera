from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    service_name: str = "openclaw-orchestrator"
    port: int = 8000
    debug: bool = False

    # Agent URLs (use localhost for development, service names for K8s)
    scenespeak_agent_url: str = "http://localhost:8001"
    captioning_agent_url: str = "http://localhost:8002"
    bsl_agent_url: str = "http://localhost:8003"
    sentiment_agent_url: str = "http://localhost:8004"
    lighting_sound_music_url: str = "http://localhost:8005"
    safety_filter_url: str = "http://localhost:8006"

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Logging
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env")

def get_settings() -> Settings:
    return Settings()
