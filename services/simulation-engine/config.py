from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    service_name: str = "simulation-engine"
    log_level: str = "INFO"
    port: int = 8016
    environment: str = "development"

    # Graph Database
    graph_db_url: str = "bolt://localhost:7687"
    graph_db_user: str = "neo4j"
    graph_db_password: str = "chimera_graph_2026"

    # Vector Database
    vector_db_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/chimera"

    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    local_llm_url: str = "http://localhost:8000"

    # Cost Control
    enable_tiered_routing: bool = True
    local_llm_ratio: float = 0.95
    max_tokens_per_simulation: int = 100000

    # Simulation Constraints
    max_agents: int = 1000
    max_rounds: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()
