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
    model_config = ConfigDict(
        env_prefix="SCENESPEAK_",
        extra="ignore"
    )

    # Service
    service_name: str = "scenespeak-agent"
    port: int = 8001
    log_level: str = "INFO"

    # GLM API
    glm_api_key: Optional[str] = None
    glm_api_base: str = "https://open.bigmodel.cn/api/paas/v4/"

    # Local LLM
    local_model_path: Optional[str] = None  # Deprecated - use local_llm settings below
    local_llm_enabled: bool = True
    local_llm_url: str = "http://host.docker.internal:8012"  # Nemotron on host
    local_llm_model: str = "nemotron-3-super-120b-a12b-nvfp4"  # DGX model
    local_llm_type: str = "openai"  # "ollama" or "openai" compatible
    glm_api_fallback: bool = True  # Use GLM API if local fails
    llm_timeout: int = 120  # Timeout for large model inference

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
