# services/nemoclaw-orchestrator/llm/privacy_router.py
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import logging

from llm.nemotron_client import NemotronClient
from llm.zai_client import ZAIClient, ZAIModel
from llm.credit_cache import CreditStatusCache

logger = logging.getLogger(__name__)


class LLMBackend(str, Enum):
    """Available LLM backends"""
    ZAI_PRIMARY = "zai_primary"
    ZAI_PROGRAMMING = "zai_programming"
    ZAI_FAST = "zai_fast"
    NEMOTRON_LOCAL = "nemotron_local"


@dataclass
class RouterConfig:
    """Configuration for privacy router"""
    dgx_endpoint: str
    nemotron_model: str = "nemotron-8b"

    # Z.AI Configuration
    zai_api_key: str = ""
    zai_primary_model: str = "glm-5-turbo"
    zai_programming_model: str = "glm-4.7"
    zai_fast_model: str = "glm-4.7-flashx"
    zai_cache_ttl: int = 3600
    zai_thinking_enabled: bool = True

    # Legacy config (kept for backward compatibility)
    local_ratio: float = 0.0  # No longer used (Z.AI-first)
    cloud_fallback_enabled: bool = True  # Now means Nemotron fallback


class PrivacyRouter:
    """
    Routes LLM requests with Z.AI-first priority

    Implements Z.AI-first routing with:
    - Primary Z.AI models for orchestration and tool invocation
    - Programming Z.AI model for code generation
    - Fast Z.AI model for simple tasks
    - Automatic fallback to local DGX Nemotron on credit exhaustion
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

        # Local Nemotron client (fallback)
        self.local_client = NemotronClient(
            endpoint=config.dgx_endpoint,
            model=config.nemotron_model
        )

    def _select_zai_model(self, task_type: str) -> LLMBackend:
        """
        Select Z.AI model based on task type

        Args:
            task_type: Type of task (tool_invocation, programming, simple, etc.)

        Returns:
            LLMBackend for the selected Z.AI model
        """
        if task_type in ["tool_invocation", "persistent", "orchestration", "default"]:
            return LLMBackend.ZAI_PRIMARY
        elif task_type in ["programming", "code_generation", "debugging"]:
            return LLMBackend.ZAI_PROGRAMMING
        elif task_type in ["simple", "repetitive", "quick", "classification"]:
            return LLMBackend.ZAI_FAST
        else:
            return LLMBackend.ZAI_PRIMARY  # Default to primary

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
            logger.debug("Z.AI marked exhausted, routing to local Nemotron")
            return LLMBackend.NEMOTRON_LOCAL

        # Select Z.AI model based on task type
        return self._select_zai_model(task_type)

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

            # Local Nemotron fallback
            elif backend == LLMBackend.NEMOTRON_LOCAL:
                return self._generate_with_nemotron(
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

            # Attempt fallback to Nemotron
            if backend != LLMBackend.NEMOTRON_LOCAL and self.config.cloud_fallback_enabled:
                logger.info("Attempting fallback to local Nemotron")
                return self._generate_with_nemotron(
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

            # Retry with Nemotron
            return self._generate_with_nemotron(
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
        logger.debug("Routing to local DGX Nemotron")

        result = self.local_client.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        result["backend"] = LLMBackend.NEMOTRON_LOCAL.value
        return result

    def close(self):
        """Close all clients"""
        self.zai_client.close()
        self.local_client.close()
        self.credit_cache.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
