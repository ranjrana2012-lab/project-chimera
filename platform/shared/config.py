"""Configuration settings for Chimera Quality Platform."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/chimera_quality"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # GitHub
    github_webhook_secret: Optional[str] = None
    github_token: Optional[str] = None

    # GitLab
    gitlab_webhook_secret: Optional[str] = None
    gitlab_token: Optional[str] = None

    # Dashboard
    dashboard_url: str = "http://localhost:8000"

    # Test Execution
    max_workers: int = 16
    test_timeout_seconds: int = 300

    # Coverage
    min_coverage_threshold: float = 95.0

    # Mutation
    max_mutation_survival: float = 2.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
