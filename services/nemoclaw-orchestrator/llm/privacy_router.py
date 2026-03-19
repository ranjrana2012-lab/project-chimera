# services/nemoclaw-orchestrator/llm/privacy_router.py
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import logging

from llm.nemotron_client import NemotronClient
from llm.guarded_cloud import GuardedCloudClient

logger = logging.getLogger(__name__)


class LLMBackend(str, Enum):
    """Available LLM backends"""
    NEMOTRON_LOCAL = "nemotron_local"
    CLOUD_GUARDED = "cloud_guarded"
    FALLBACK = "fallback"


@dataclass
class RouterConfig:
    """Configuration for privacy router"""
    dgx_endpoint: str
    local_ratio: float = 0.95  # 95% local, 5% cloud
    cloud_fallback_enabled: bool = True
    nemotron_model: str = "nemotron-8b"
    cloud_model: str = "claude-3-haiku-20240307"

    def __post_init__(self):
        """Validate configuration"""
        if not 0 <= self.local_ratio <= 1:
            raise ValueError("local_ratio must be between 0 and 1")


class PrivacyRouter:
    """
    Routes LLM requests between local DGX and guarded cloud

    Implements privacy-preserving routing with:
    - 95% local processing on DGX Nemotron
    - 5% cloud fallback with PII stripping
    - Automatic fallback on local failure
    """

    def __init__(self, config: RouterConfig):
        """
        Initialize privacy router

        Args:
            config: Router configuration
        """
        self.config = config

        self.local_client = NemotronClient(
            endpoint=config.dgx_endpoint,
            model=config.nemotron_model
        )
        self.cloud_client = GuardedCloudClient(
            model=config.cloud_model
        )

    def route(self, prompt: str) -> LLMBackend:
        """
        Determine which backend to use for a request

        Args:
            prompt: Input prompt

        Returns:
            LLMBackend to use
        """
        # Check if local is available
        if not self.local_client.is_available():
            logger.warning("Local DGX unavailable, routing to cloud")
            return LLMBackend.CLOUD_GUARDED

        # Route based on configured ratio
        if random.random() < self.config.local_ratio:
            return LLMBackend.NEMOTRON_LOCAL
        else:
            return LLMBackend.CLOUD_GUARDED

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        force_backend: Optional[LLMBackend] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using appropriate backend

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            force_backend: Force specific backend (for testing)
            **kwargs: Additional parameters

        Returns:
            Dict with generated text and metadata
        """
        # Determine backend
        backend = force_backend or self.route(prompt)

        # Try selected backend
        try:
            if backend == LLMBackend.NEMOTRON_LOCAL:
                logger.debug("Routing to local DGX Nemotron")
                return self.local_client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

            elif backend == LLMBackend.CLOUD_GUARDED:
                logger.debug("Routing to guarded cloud")
                return self.cloud_client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    strip_pii=True,
                    **kwargs
                )

            else:
                # Fallback - try cloud if enabled
                if self.config.cloud_fallback_enabled:
                    logger.debug("Using fallback to guarded cloud")
                    return self.cloud_client.generate(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        strip_pii=True,
                        **kwargs
                    )
                else:
                    raise ValueError("No backend available and cloud fallback disabled")

        except Exception as e:
            logger.error(f"Backend {backend.value} failed: {e}")

            # Attempt fallback to cloud if enabled
            if backend != LLMBackend.CLOUD_GUARDED and self.config.cloud_fallback_enabled:
                logger.info("Attempting fallback to guarded cloud")
                try:
                    return self.cloud_client.generate(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        strip_pii=True,
                        **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"Cloud fallback also failed: {fallback_error}")
                    raise

            raise

    def close(self):
        """Close all clients"""
        self.local_client.close()
        self.cloud_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
