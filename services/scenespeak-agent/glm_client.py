"""
GLM 4.7 API client with local fallback for SceneSpeak Agent.

This module provides dialogue generation using the GLM 4.7 API with automatic
fallback to local LLM (Ollama) when the API is unavailable or fails.
"""

import httpx
import logging
import time
from typing import Optional
from dataclasses import dataclass

from config import get_settings
from local_llm import LocalLLMClient, LocalLLMResponse

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DialogueResponse:
    """Response from dialogue generation"""
    text: str
    tokens_used: int
    model: str
    source: str  # "api" or "local"
    duration_ms: int


class GLMClient:
    """GLM 4.7 API client with local fallback"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GLM client.

        Args:
            api_key: Optional API key for GLM 4.7 API. If not provided,
                    will use the value from settings.
        """
        self.api_key = api_key or settings.glm_api_key
        self.api_base = settings.glm_api_base
        self.local_model_path = settings.local_model_path
        self.local_llm_client: Optional[LocalLLMClient] = None
        self._local_llm_initialized = False

    async def _ensure_local_llm(self) -> Optional[LocalLLMClient]:
        """
        Ensure local LLM client is initialized and available.

        Returns:
            LocalLLMClient if available, None otherwise
        """
        if not settings.local_llm_enabled:
            return None

        if self._local_llm_initialized and self.local_llm_client:
            if await self.local_llm_client.is_available():
                return self.local_llm_client
            else:
                logger.warning("Local LLM was available but is now disconnected")
                self._local_llm_initialized = False
                return None

        # Try to initialize local LLM
        try:
            self.local_llm_client = LocalLLMClient(
                base_url=settings.local_llm_url,
                model=settings.local_llm_model
            )
            success = await self.local_llm_client.connect()
            if success:
                self._local_llm_initialized = True
                logger.info(f"Local LLM initialized: {settings.local_llm_url}")
                return self.local_llm_client
            else:
                logger.warning("Failed to connect to local LLM")
                return None
        except Exception as e:
            logger.warning(f"Failed to initialize local LLM: {e}")
            return None

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        prefer_local: bool = False
    ) -> DialogueResponse:
        """
        Generate dialogue with local LLM or GLM 4.7 API.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate (default: 500)
            temperature: Sampling temperature (default: 0.7)
            prefer_local: If True, try local LLM first (default: False)

        Returns:
            DialogueResponse with generated text and metadata
        """
        # Try local LLM first if preferred or if no API key
        if prefer_local or not self.api_key:
            local_client = await self._ensure_local_llm()
            if local_client:
                try:
                    local_response = await local_client.generate(
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    return DialogueResponse(
                        text=local_response.text,
                        tokens_used=local_response.tokens_used,
                        model=local_response.model,
                        source="local",
                        duration_ms=local_response.duration_ms
                    )
                except Exception as e:
                    logger.warning(f"Local LLM generation failed: {e}")
                    if not self.api_key:
                        # No fallback available
                        raise RuntimeError(
                            "Local LLM failed and no GLM API key configured"
                        ) from e
                    # Fall through to API if available
            elif not self.api_key:
                raise RuntimeError(
                    "Local LLM unavailable and no GLM API key configured"
                )

        # Try GLM 4.7 API
        if self.api_key:
            try:
                return await self._call_glm_api(prompt, max_tokens, temperature)
            except Exception as e:
                logger.warning(f"GLM API failed: {e}")

                # Try local LLM as fallback if enabled
                if settings.glm_api_fallback:
                    local_client = await self._ensure_local_llm()
                    if local_client:
                        try:
                            logger.info("Falling back to local LLM")
                            local_response = await local_client.generate(
                                prompt=prompt,
                                max_tokens=max_tokens,
                                temperature=temperature
                            )
                            return DialogueResponse(
                                text=local_response.text,
                                tokens_used=local_response.tokens_used,
                                model=local_response.model,
                                source="local-fallback",
                                duration_ms=local_response.duration_ms
                            )
                        except Exception as local_e:
                            logger.warning(f"Local LLM fallback also failed: {local_e}")

                # Re-raise original API error if no fallback worked
                raise

        # Should not reach here, but just in case
        raise RuntimeError("No dialogue generation method available")

    async def _call_glm_api(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> DialogueResponse:
        """
        Call GLM 4.7 API for dialogue generation.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            DialogueResponse with API-generated text and metadata
        """
        payload = {
            "model": "glm-4",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        start_time = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

        duration_ms = int((time.time() - start_time) * 1000)

        return DialogueResponse(
            text=data["choices"][0]["message"]["content"],
            tokens_used=data["usage"]["total_tokens"],
            model="glm-4",
            source="api",
            duration_ms=duration_ms
        )

    async def _call_local_model(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> DialogueResponse:
        """
        Call local LLM for dialogue generation.

        This method is kept for backward compatibility but now uses
        the LocalLLMClient internally.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            DialogueResponse with locally-generated text and metadata
        """
        local_client = await self._ensure_local_llm()
        if not local_client:
            logger.warning("Local LLM not available, returning error response")
            return DialogueResponse(
                text="[Local LLM not available - please configure Ollama]",
                tokens_used=0,
                model="local",
                source="error",
                duration_ms=0
            )

        try:
            local_response = await local_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return DialogueResponse(
                text=local_response.text,
                tokens_used=local_response.tokens_used,
                model=local_response.model,
                source="local",
                duration_ms=local_response.duration_ms
            )
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            return DialogueResponse(
                text=f"[Local LLM error: {str(e)}]",
                tokens_used=0,
                model="local",
                source="error",
                duration_ms=0
            )

    async def get_local_llm_health(self) -> dict:
        """
        Get health status of local LLM.

        Returns:
            Dictionary with health information
        """
        if self.local_llm_client:
            return await self.local_llm_client.health_check()
        return {
            "connected": False,
            "status": "not_initialized",
            "base_url": settings.local_llm_url,
            "model": settings.local_llm_model
        }
