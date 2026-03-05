"""
Configuration for SceneSpeak Agent.

Environment-based configuration with pydantic-settings for GLM 4.7 API integration
and local LLM fallback support.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    model_config = ConfigDict(env_file=".env")

    # Service
    service_name: str = "scenespeak-agent"
    port: int = 8001
    log_level: str = "INFO"

    # GLM API
    glm_api_key: Optional[str] = None
    glm_api_base: str = "https://open.bigmodel.cn/api/paas/v4/"

    # Local LLM
    local_model_path: Optional[str] = None  # To be provided tomorrow

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
