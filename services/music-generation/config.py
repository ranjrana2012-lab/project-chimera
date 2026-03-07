"""Music Generation Service Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""  # Moved from removed Config class
    )

    # Service
    service_name: str = "music-generation"
    port: int = 8011
    log_level: str = "INFO"
    environment: str = "development"

    # Model Paths
    musicgen_model_path: str = "/models/musicgen"
    acestep_model_path: str = "/models/acestep"
    huggingface_cache_dir: str = "/models/cache"

    # Model Settings
    default_model: str = "musicgen"  # or "acestep"
    max_vram_mb: int = 8192  # GB10 GPU VRAM limit
    model_offload: bool = True  # Offload to CPU when not in use

    # Generation Settings
    default_duration: float = 5.0  # seconds
    max_duration: float = 30.0
    sample_rate: int = 44100
    normalize_db: float = -1.0
    trim_silence: bool = True

    # GPU Settings
    device: str = "cuda"  # or "cpu" for testing
    torch_threads: int = 4

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
