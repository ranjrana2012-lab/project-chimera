"""Configuration for Translation Agent using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Translation Agent configuration.

    Environment variables:
        TRANSLATION_AGENT_NAME: Service name (default: translation-agent)
        TRANSLATION_AGENT_PORT: Service port (default: 8006)
        TRANSLATION_AGENT_OTLP_ENDPOINT: OpenTelemetry endpoint
        TRANSLATION_AGENT_USE_MOCK: Use mock translation (default: True for development)
        TRANSLATION_AGENT_CACHE_TTL: Translation cache TTL in seconds (default: 3600)
        TRANSLATION_AGENT_BSL_SERVICE_URL: BSL avatar service URL
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TRANSLATION_AGENT_",
        extra="ignore",
    )

    # Service identification
    service_name: str = "translation-agent"
    port: int = 8006
    host: str = "0.0.0.0"

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Translation settings
    use_mock: bool = True
    cache_ttl: int = 3600

    # BSL Service integration
    bsl_service_url: str = "http://localhost:8005"

    # Supported languages
    supported_languages: list[str] = [
        "en",  # English
        "es",  # Spanish
        "fr",  # French
        "de",  # German
        "it",  # Italian
        "pt",  # Portuguese
        "nl",  # Dutch
        "pl",  # Polish
        "ru",  # Russian
        "zh",  # Chinese
        "ja",  # Japanese
        "ko",  # Korean
        "ar",  # Arabic
        "hi",  # Hindi
        "bsl",  # British Sign Language
    ]


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
