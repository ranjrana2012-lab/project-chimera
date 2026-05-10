# services/nemoclaw-orchestrator/llm/privacy_router.py
import time
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from llm.nemotron_client import NemotronClient
from llm.ollama_client import OllamaClient
from llm.gguf_client import GGUFClient
from llm.zai_client import ZAIClient, ZAIModel
from llm.credit_cache import CreditStatusCache

logger = logging.getLogger(__name__)


class LLMBackend(str, Enum):
    """Available LLM backends"""
    ZAI_PRIMARY = "zai_primary"
    ZAI_PROGRAMMING = "zai_programming"
    ZAI_FAST = "zai_fast"
    NEMOTRON_LOCAL = "nemotron_local"
    OLLAMA_LOCAL = "ollama_local"
    GGUF_LLAMA = "gguf_llama"           # Meta-Llama-3.1-8B-Instruct-Q4_K_M
    GGUF_BSL7 = "gguf_bsl_phase7"       # BSL Phase 7
    GGUF_BSL8 = "gguf_bsl_phase8"       # BSL Phase 8
    GGUF_BSL9 = "gguf_bsl_phase9"       # BSL Phase 9
    GGUF_DIRECTOR_V4 = "gguf_director_v4"  # Director v4
    GGUF_DIRECTOR_V5 = "gguf_director_v5"  # Director v5
    GGUF_SCENESPEAK = "gguf_scenespeak"    # SceneSpeak QueryD


@dataclass
class RouterConfig:
    """Configuration for privacy router"""
    dgx_endpoint: str
    ollama_model: str = "llama3:instruct"     # Local Ollama fallback model

    # Z.AI Configuration - GLM-4.7 First Strategy
    zai_api_key: str = ""
    zai_primary_model: str = "glm-4.7"          # GLM-4.7 - Primary inference model
    zai_programming_model: str = "glm-4.7"      # GLM-4.7 - Programming tasks
    zai_fast_model: str = "glm-5-turbo"         # GLM-5-Turbo - Fast tasks
    zai_cache_ttl: int = 3600                   # 1 hour cache
    zai_thinking_enabled: bool = False          # Thinking disabled for GLM-4.7

    # Nemotron Configuration (DISABLED - GLM-4.7 API is primary)
    nemotron_enabled: bool = False
    nemotron_endpoint: str = "http://localhost:8012"
    nemotron_model_120b: str = "nemotron-3-super-120b-a12b-nvfp4"
    nemotron_timeout: int = 120
    nemotron_max_retries: int = 2

    # GGUF Model Configuration
    gguf_base_path: str = field(
        default_factory=lambda: os.getenv(
            "CHIMERA_GGUF_BASE",
            str(Path.home() / "Project_Chimera_Downloads" / "LLM Models" / "gguf"),
        )
    )
    gguf_models: Dict[str, str] = None  # Map of backend to GGUF file path

    def __post_init__(self):
        if self.gguf_models is None:
            self.gguf_models = {
                "gguf_llama": "other/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                "gguf_bsl_phase7": "bsl-phases/bsl_phase7.Q4_K_M.gguf",
                "gguf_bsl_phase8": "bsl-phases/bsl_phase8.Q4_K_M.gguf",
                "gguf_bsl_phase9": "bsl-phases/bsl_phase9.Q4_K_M.gguf",
                "gguf_director_v4": "directors/director_v4.Q4_K_M.gguf",
                "gguf_director_v5": "directors/director_v5.Q4_K_M.gguf",
                "gguf_scenespeak": "scene-speak/scenespeak_queryd.Q4_K_M.gguf",
            }

    # Legacy config (kept for backward compatibility)
    local_ratio: float = 0.0  # No longer used (Z.AI-first with cascade)
    cloud_fallback_enabled: bool = True  # Now means Ollama fallback only


class PrivacyRouter:
    """
    Routes LLM requests with Z.AI GLM-4.7 first priority

    GLM-4.7 FIRST Strategy:
    - Primary: GLM-4.7 (glm-4.7) for everything
    - Fallback 1: GLM-4.7-FlashX (glm-4.7-flashx) for simple tasks
    - Final: Local Ollama when Z.AI credits exhausted (Nemotron disabled)
    """

    def __init__(self, config: RouterConfig):
        """
        Initialize privacy router with Z.AI-first routing

        Args:
            config: Router configuration
        """
        self.config = config

        # Z.AI clients
        self.zai_client = ZAIClient(
            api_key=config.zai_api_key or None
        )
        self.credit_cache = CreditStatusCache(
            ttl=config.zai_cache_ttl
        )

        # Local Nemotron client (DISABLED - GLM-4.7 is primary)
        if config.nemotron_enabled:
            self.nemotron_client = NemotronClient(
                endpoint=config.nemotron_endpoint,
                model=config.nemotron_model_120b,
                timeout=config.nemotron_timeout
            )
        else:
            self.nemotron_client = None

        # Local Ollama client (final fallback - llama3:instruct)
        self.local_client = OllamaClient(
            endpoint=config.dgx_endpoint,
            model=config.ollama_model
        )

        # GGUF clients for specialized models
        self.gguf_clients: Dict[LLMBackend, GGUFClient] = {}
        self._init_gguf_clients()

    def _init_gguf_clients(self):
        """Initialize GGUF clients for configured models"""
        gguf_model_configs = {
            LLMBackend.GGUF_LLAMA: ("llama-3.1-8b-instruct", self.config.gguf_models["gguf_llama"]),
            LLMBackend.GGUF_BSL7: ("bsl-phase7", self.config.gguf_models["gguf_bsl_phase7"]),
            LLMBackend.GGUF_BSL8: ("bsl-phase8", self.config.gguf_models["gguf_bsl_phase8"]),
            LLMBackend.GGUF_BSL9: ("bsl-phase9", self.config.gguf_models["gguf_bsl_phase9"]),
            LLMBackend.GGUF_DIRECTOR_V4: ("director-v4", self.config.gguf_models["gguf_director_v4"]),
            LLMBackend.GGUF_DIRECTOR_V5: ("director-v5", self.config.gguf_models["gguf_director_v5"]),
            LLMBackend.GGUF_SCENESPEAK: ("scenespeak-queryd", self.config.gguf_models["gguf_scenespeak"]),
        }

        for backend, (model_name, gguf_path) in gguf_model_configs.items():
            self.gguf_clients[backend] = GGUFClient(
                endpoint=self.config.dgx_endpoint,
                gguf_base_path=self.config.gguf_base_path,
                model_name=model_name,
                gguf_relative_path=gguf_path
            )

    def _select_zai_model(self, task_type: str) -> LLMBackend:
        """
        Select Z.AI model based on task type

        CASCADE: GLM-4.7 → GLM-4.7-FlashX → Local
        - Simple/repetitive tasks: Skip directly to GLM-4.7-FlashX (fastest)
        - Programming/complex tasks: GLM-4.7 (primary)
        - Everything else: GLM-4.7 (default, most capable)

        Args:
            task_type: Type of task (tool_invocation, programming, simple, etc.)

        Returns:
            LLMBackend for the selected Z.AI model (initial choice - fallback happens in generate())
        """
        # Use FlashX directly for explicitly simple/repetitive tasks (for speed)
        if task_type in ["simple", "repetitive", "quick", "classification"]:
            return LLMBackend.ZAI_FAST

        # For all other tasks, use GLM-4.7 (primary)
        return LLMBackend.ZAI_PRIMARY

    def route(self, prompt: str, task_type: str = "default") -> LLMBackend:
        """
        Determine which backend to use for a request (Z.AI-first)

        Args:
            prompt: Input prompt
            task_type: Type of task for model selection

        Returns:
            LLMBackend to use
        """
        # Check if Z.AI is available (not marked as exhausted)
        if not self.credit_cache.is_available():
            logger.debug("Z.AI marked exhausted, routing to local Ollama")
            return LLMBackend.OLLAMA_LOCAL

        # Select Z.AI model based on task type
        return self._select_zai_model(task_type)

    def _is_nemotron_available(self) -> bool:
        """Check if Nemotron service is available"""
        try:
            import httpx
            response = httpx.get(f"{self.config.nemotron_endpoint}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        force_backend: Optional[LLMBackend] = None,
        task_type: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using appropriate backend (Z.AI-first)

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            force_backend: Force specific backend (for testing)
            task_type: Type of task for model selection
            **kwargs: Additional parameters

        Returns:
            Dict with generated text and metadata
        """
        start_time = time.time()
        backend = force_backend or self.route(prompt, task_type)

        try:
            # Z.AI backends
            if backend in (LLMBackend.ZAI_PRIMARY, LLMBackend.ZAI_PROGRAMMING, LLMBackend.ZAI_FAST):
                return self._generate_with_zai(
                    prompt=prompt,
                    backend=backend,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

            # Nemotron fallback
            elif backend == LLMBackend.NEMOTRON_LOCAL:
                return self._generate_with_nemotron(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

            # GGUF models
            elif backend in self.gguf_clients:
                return self._generate_with_gguf(
                    prompt=prompt,
                    backend=backend,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

            # Local Ollama fallback
            elif backend == LLMBackend.OLLAMA_LOCAL:
                return self._generate_with_ollama(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

            else:
                raise ValueError(f"Unknown backend: {backend}")

        except Exception as e:
            backend_value = backend.value if isinstance(backend, LLMBackend) else backend
            logger.error(f"Generation failed with backend {backend_value}: {e}")

            # Z.AI-to-Z.AI fallback cascade
            if backend == LLMBackend.ZAI_PRIMARY:
                # GLM-4.7 failed, try FlashX
                logger.info("GLM-4.7 failed, attempting fallback to GLM-4.7-FlashX")
                try:
                    return self._generate_with_zai(
                        prompt=prompt,
                        backend=LLMBackend.ZAI_FAST,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                except Exception as e2:
                    logger.warning(f"GLM-4.7-FlashX fallback also failed: {e2}")

            elif backend == LLMBackend.ZAI_PROGRAMMING:
                # GLM-4.7 failed, try FlashX
                logger.info("GLM-4.7 failed, attempting fallback to GLM-4.7-FlashX")
                try:
                    return self._generate_with_zai(
                        prompt=prompt,
                        backend=LLMBackend.ZAI_FAST,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                except Exception as e2:
                    logger.warning(f"GLM-4.7-FlashX fallback failed: {e2}")

            # Final fallback to Ollama (local model)
            if self.config.cloud_fallback_enabled:
                logger.info("Attempting final fallback to Ollama (local)")
                return self._generate_with_ollama(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

            raise

    def _generate_with_zai(
        self,
        prompt: str,
        backend: LLMBackend,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate using Z.AI client"""
        # Map backend to model
        model_map = {
            LLMBackend.ZAI_PRIMARY: ZAIModel.PRIMARY,
            LLMBackend.ZAI_PROGRAMMING: ZAIModel.PROGRAMMING,
            LLMBackend.ZAI_FAST: ZAIModel.FAST,
        }

        model = model_map[backend]
        logger.debug(f"Routing to Z.AI model: {model.value}")

        result = self.zai_client.generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            thinking=self.config.zai_thinking_enabled,
            **kwargs
        )

        # Check for credit exhaustion
        if "error" in result and result["error"] == "credit_exhausted":
            logger.warning("Z.AI credits exhausted, marking and falling back")
            self.credit_cache.mark_exhausted()

            # Retry with Ollama (local fallback)
            return self._generate_with_ollama(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

        result["backend"] = backend.value
        return result

    def _generate_with_nemotron(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate using local Nemotron client"""
        logger.debug("Routing to local Nemotron")

        for attempt in range(self.config.nemotron_max_retries + 1):
            try:
                result = self.nemotron_client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                result["backend"] = LLMBackend.NEMOTRON_LOCAL.value
                return result
            except Exception as e:
                if attempt < self.config.nemotron_max_retries:
                    logger.warning(f"Nemotron attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                logger.error(f"Nemotron generation failed after {self.config.nemotron_max_retries} retries: {e}")
                raise

    def _generate_with_ollama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate using local Ollama client"""
        logger.debug("Routing to local Ollama")

        result = self.local_client.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        result["backend"] = LLMBackend.OLLAMA_LOCAL.value
        return result

    def _generate_with_gguf(
        self,
        prompt: str,
        backend: LLMBackend,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate using local GGUF client"""
        gguf_client = self.gguf_clients.get(backend)
        if not gguf_client:
            raise ValueError(f"No GGUF client configured for backend: {backend}")

        logger.debug(f"Routing to GGUF model: {backend.value}")

        result = gguf_client.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        result["backend"] = backend.value
        return result

    def close(self):
        """Close all clients"""
        self.zai_client.close()
        if hasattr(self, 'nemotron_client') and self.nemotron_client:
            self.nemotron_client.close()
        self.local_client.close()
        for gguf_client in self.gguf_clients.values():
            gguf_client.close()
        self.credit_cache.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
