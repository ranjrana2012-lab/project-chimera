"""Configuration for autonomous-agent service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Service configuration
    service_name: str = "autonomous-agent"
    service_version: str = "1.0.0"
    port: int = 8008

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Git configuration
    git_repo_path: str = "/app"
    git_branch: str = "main"

    # Ralph Mode configuration
    max_retries: int = 5
    retry_delay_seconds: int = 10

    # State file paths
    state_dir: str = "state"
    requirements_file: str = "state/REQUIREMENTS.md"
    plan_file: str = "state/PLAN.md"
    state_file: str = "state/STATE.md"

    # OpenClaw Orchestrator integration
    openclaw_url: str = "http://localhost:8000"
    enable_multi_agent: bool = True


_settings = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
