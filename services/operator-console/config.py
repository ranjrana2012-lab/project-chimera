"""
Configuration for Operator Console.

Environment-based configuration with pydantic-settings for the operator console service.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    model_config = ConfigDict(env_file=".env")

    # Service
    service_name: str = "operator-console"
    port: int = 8007
    log_level: str = "INFO"
    environment: str = "development"

    # Service URLs (for health checks and metrics collection)
    openclaw_orchestrator_url: str = "http://localhost:8000"
    nemoclaw_orchestrator_url: str = "http://nemoclaw-orchestrator:8000"
    scenespeak_agent_url: str = "http://localhost:8001"
    captioning_agent_url: str = "http://localhost:8002"
    bsl_agent_url: str = "http://localhost:8003"
    sentiment_agent_url: str = "http://localhost:8004"
    lighting_sound_music_url: str = "http://localhost:8005"
    safety_filter_url: str = "http://localhost:8006"

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Metrics Collection
    metrics_poll_interval: float = 5.0

    # Alert Thresholds
    alert_cpu_threshold: float = 80.0
    alert_memory_threshold: float = 2000.0
    alert_error_rate_threshold: float = 0.05
    alert_request_rate_minimum: float = 0.1

    def get_all_service_urls(self) -> dict[str, str]:
        """Get all service URLs as a dictionary."""
        return {
            "openclaw-orchestrator": self.openclaw_orchestrator_url,
            "nemoclaw-orchestrator": self.nemoclaw_orchestrator_url,
            "scenespeak-agent": self.scenespeak_agent_url,
            "captioning-agent": self.captioning_agent_url,
            "bsl-agent": self.bsl_agent_url,
            "sentiment-agent": self.sentiment_agent_url,
            "lighting-sound-music": self.lighting_sound_music_url,
            "safety-filter": self.safety_filter_url,
        }


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
