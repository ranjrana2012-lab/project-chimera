"""Visual Core Service Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings for visual core."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        protected_namespaces=('settings_',)  # Fix Pydantic warning
    )

    # Service
    service_name: str = "visual-core"
    port: int = 8014
    log_level: str = "INFO"

    # LTX API Configuration
    ltx_api_key: str  # Required
    ltx_api_base: str = "https://api.ltx.video/v1"
    ltx_model_default: str = "ltx-2-3-pro"
    ltx_model_fast: str = "ltx-2-fast"
    max_concurrent_requests: int = 5

    # Storage Paths
    cache_path: str = "/app/cache/videos"
    lora_storage_path: str = "/app/models/lora"

    # External Dependencies
    ffmpeg_path: str = "ffmpeg"
    sentiment_agent_url: str = "http://sentiment-agent:8004"
    simulation_engine_url: str = "http://simulation-engine:8016"

    # OpenTelemetry
    otlp_endpoint: str = "http://jaeger:4317"


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()


# Global settings instance for easy import
settings = get_settings()
