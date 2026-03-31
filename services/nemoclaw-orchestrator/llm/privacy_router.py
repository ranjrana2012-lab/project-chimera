# services/nemoclaw-orchestrator/llm/privacy_router.py
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import logging

from llm.nemotron_client import NemotronClient
from llm.ollama_client import OllamaClient
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


@dataclass
class RouterConfig:
    """Configuration for privacy router"""
    dgx_endpoint: str
    nemotron_model: str = "nemotron-8b"

    # Z.AI Configuration - GLM-5.1 Turbo First Strategy
    zai_api_key: str = ""
    zai_primary_model: str = "glm-5-turbo"      # GLM-5.1 Turbo - Primary
    zai_programming_model: str = "glm-4.7"      # GLM-4.7 - Fallback
    zai_fast_model: str = "glm-4.7-flashx"      # GLM-4.7-FlashX - Last Z.AI option
    zai_cache_ttl: int = 1800                   # Max plan: 1800s (30min), Standard: 3600s (1hr)
    zai_thinking_enabled: bool = True           # Enable extended reasoning for best intelligence

    # Nemotron Configuration (local fallback after Z.AI)
    nemotron_enabled: bool = True
    nemotron_endpoint: str = "http://localhost:8000"
    nemotron_model_120b: str = "nemotron-3-super-120b-a12b-nvfp4"
    nemotron_timeout: int = 120
    nemotron_max_retries: int = 2

    # Legacy config (kept for backward compatibility)
    local_ratio: float = 0.0  # No longer used (Z.AI-first with cascade)
    cloud_fallback_enabled: bool = True  # Now means Nemotron/Ollama fallback


class PrivacyRouter:
    """
    Routes LLM requests with Z.AI GLM-5.1 Turbo first priority

    GLM-5.1 TURBO FIRST Strategy:
    - Primary: GLM-5.1 Turbo (glm-5-turbo) for everything
    - Fallback 1: GLM-4.7 (glm-4.7) if GLM-5.1 Turbo fails
    - Fallback 2: GLM-4.7-FlashX (glm-4.7-flashx) for simple tasks
    - Final: Local LLM (Nemotron → Ollama) when all Z.AI options exhausted
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

        # Local Nemotron client (fallback before Ollama)
        if config.nemotron_enabled:
            self.nemotron_client = NemotronClient(
                endpoint=config.nemotron_endpoint,
                model=config.nemotron_model_120b,
                timeout=config.nemotron_timeout
            )
        else:
            self.nemotron_client = None

        # Local Ollama client (final fallback)
        self.local_client = OllamaClient(
            endpoint=config.dgx_endpoint,
            model=config.nemotron_model
        )

    def _select_zai_model(self, task_type: str) -> LLMBackend:
        """
        Select Z.AI model based on task type

        CASCADE: GLM-5.1 Turbo → GLM-4.7 → GLM-4.7-FlashX → Local
        - Simple/repetitive tasks: Skip directly to GLM-4.7-FlashX (fastest)
        - Programming/complex tasks: GLM-5.1 Turbo (can fallback to GLM-4.7)
        - Everything else: GLM-5.1 Turbo (default, most capable)

        Args:
            task_type: Type of task (tool_invocation, programming, simple, etc.)

        Returns:
            LLMBackend for the selected Z.AI model (initial choice - fallback happens in generate())
        """
        # Use FlashX directly for explicitly simple/repetitive tasks (skip GLM-5.1 for speed)
        if task_type in ["simple", "repetitive", "quick", "classification"]:
            return LLMBackend.ZAI_FAST

        # For complex programming tasks, prefer GLM-4.7 (can still start with GLM-5.1)
        # The router will fallback from GLM-5.1 → GLM-4.7 if needed
        if task_type in ["programming", "code_generation", "debugging", "complex"]:
            return LLMBackend.ZAI_PROGRAMMING

        # Default to GLM-5.1 Turbo (fastest, most capable)
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
            logger.debug("Z.AI marked exhausted, routing to local Nemotron/Ollama")
            # Try Nemotron first, then Ollama
            if self.nemotron_client and self._is_nemotron_available():
                return LLMBackend.NEMOTRON_LOCAL
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
                # GLM-5.1 Turbo failed, try GLM-4.7
                logger.info("GLM-5.1 Turbo failed, attempting fallback to GLM-4.7")
                try:
                    return self._generate_with_zai(
                        prompt=prompt,
                        backend=LLMBackend.ZAI_PROGRAMMING,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                except Exception as e2:
                    logger.warning(f"GLM-4.7 fallback also failed: {e2}")
                    # Try FlashX as last Z.AI option
                    logger.info("Attempting fallback to GLM-4.7-FlashX")
                    try:
                        return self._generate_with_zai(
                            prompt=prompt,
                            backend=LLMBackend.ZAI_FAST,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            **kwargs
                        )
                    except Exception as e3:
                        logger.warning(f"GLM-4.7-FlashX fallback also failed: {e3}")

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

            # Attempt fallback to Nemotron, then Ollama (local models)
            if self.config.nemotron_enabled and self.nemotron_client:
                logger.info("Attempting fallback to Nemotron (local)")
                try:
                    return self._generate_with_nemotron(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                except Exception as e:
                    logger.warning(f"Nemotron fallback failed: {e}")

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

            # Retry with Nemotron, then Ollama
            if self.nemotron_client:
                try:
                    return self._generate_with_nemotron(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                except Exception as e:
                    logger.warning(f"Nemotron fallback failed: {e}")
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

    def close(self):
        """Close all clients"""
        self.zai_client.close()
        if hasattr(self, 'nemotron_client') and self.nemotron_client:
            self.nemotron_client.close()
        self.local_client.close()
        self.credit_cache.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
