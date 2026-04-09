from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Service
    service_name: str = "nemoclaw-orchestrator"
    port: int = 8000
    debug: bool = False

    # DGX Configuration (Ollama fallback)
    ollama_model: str = "llama3:instruct"  # Local Ollama model for fallback
    dgx_gpu_id: int = 0
    dgx_endpoint: str = "http://localhost:11434"  # Ollama endpoint

    # Privacy Router
    local_ratio: float = 0.95  # 95% local, 5% cloud
    cloud_fallback_enabled: bool = True

    # Z.AI Configuration (GLM-4.7 First Strategy)
    # Primary: GLM-4.7 for everything (main inference model)
    # Fallback: GLM-5-Turbo for simple/repetitive tasks only
    # Final: Local Ollama when Z.AI credits exhausted
    zai_api_key: str = ""
    zai_primary_model: str = "glm-4.7"          # GLM-4.7 - Primary inference model
    zai_programming_model: str = "glm-4.7"      # GLM-4.7 - Programming tasks
    zai_fast_model: str = "glm-5-turbo"         # GLM-5-Turbo - Fast tasks
    zai_cache_ttl: int = 3600                  # 1 hour cache
    zai_thinking_enabled: bool = False         # Thinking disabled for GLM-4.7

    # Nemotron Configuration (DISABLED - using GLM-4.7 API instead)
    nemotron_enabled: bool = False             # Disabled - GLM-4.7 is primary
    nemotron_endpoint: str = "http://localhost:8012"
    nemotron_model: str = "nemotron-3-super-120b-a12b-nvfp4"
    nemotron_timeout: int = 120
    nemotron_max_retries: int = 2

    # Agent URLs (existing agents)
    scenespeak_agent_url: str = "http://localhost:8001"
    captioning_agent_url: str = "http://localhost:8002"
    bsl_agent_url: str = "http://localhost:8003"
    sentiment_agent_url: str = "http://localhost:8004"
    lighting_sound_music_url: str = "http://localhost:8005"
    safety_filter_url: str = "http://localhost:8006"
    operator_console_url: str = "http://localhost:8007"
    music_generation_url: str = "http://localhost:8011"
    autonomous_agent_url: str = "http://localhost:8008"

    # State Store
    redis_url: str = "redis://localhost:6379"
    redis_show_state_ttl: int = 86400  # 24 hours

    # Policy
    policy_strictness: str = "medium"  # low, medium, high

    # OpenTelemetry
    otlp_endpoint: str = "http://localhost:4317"

    # Logging
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env")

def get_settings() -> Settings:
    return Settings()
