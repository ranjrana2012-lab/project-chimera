"""Educational Platform Service Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings for educational platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        protected_namespaces=('settings_',)  # Fix Pydantic warning
    )

    # Service
    service_name: str = "educational-platform"
    port: int = 8012
    log_level: str = "INFO"
    environment: str = "development"

    # Database
    database_url: str = "sqlite:///./educational_platform.db"
    use_sqlite: bool = True

    # Integration Services
    bsl_agent_url: str = "http://localhost:8003"
    captioning_agent_url: str = "http://localhost:8002"
    sentiment_agent_url: str = "http://localhost:8004"

    # Educational Settings
    default_learning_objectives: int = 5  # per lesson
    max_assessment_questions: int = 20
    passing_score_threshold: float = 0.7  # 70%
    retry_attempts_allowed: int = 3

    # Accessibility Settings
    enable_bsl: bool = True
    enable_captions: bool = True
    enable_sentiment: bool = True
    auto_adapt_content: bool = True

    # Session Settings
    session_timeout_minutes: int = 60
    max_active_sessions: int = 1000

    # Analytics Settings
    analytics_retention_days: int = 365
    anonymous_analytics: bool = True

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"
    enable_tracing: bool = True

    # Educator Interface
    educator_dashboard_enabled: bool = True
    content_review_required: bool = False


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()


# Global settings instance for easy import
settings = get_settings()
