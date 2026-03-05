"""
GLM 4.7 API client with local fallback for SceneSpeak Agent.

This module provides dialogue generation using the GLM 4.7 API with automatic
fallback to local LLM when the API is unavailable or fails.
"""

import httpx
import logging
import time
from typing import Optional
from dataclasses import dataclass

from config import get_settings

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

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> DialogueResponse:
        """
        Generate dialogue with GLM 4.7, fallback to local model.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate (default: 500)
            temperature: Sampling temperature (default: 0.7)

        Returns:
            DialogueResponse with generated text and metadata
        """
        # Try GLM 4.7 API first
        if self.api_key:
            try:
                return await self._call_glm_api(prompt, max_tokens, temperature)
            except Exception as e:
                logger.warning(f"GLM API failed: {e}, falling back to local")

        # Fallback to local model
        return await self._call_local_model(prompt, max_tokens, temperature)

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

        Currently a placeholder until model paths are provided.
        Will be implemented with actual local model loading tomorrow.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            DialogueResponse with locally-generated text and metadata
        """
        if not self.local_model_path:
            logger.warning("Local model path not configured, using placeholder")
            return DialogueResponse(
                text=f"[Local model placeholder - model path not configured] {prompt[:50]}...",
                tokens_used=0,
                model="local",
                source="placeholder",
                duration_ms=0
            )

        # TODO: Implement local model loading when paths provided tomorrow
        logger.info(f"Local model path configured: {self.local_model_path}")
        logger.warning("Local model loading not yet implemented")

        # Placeholder response
        return DialogueResponse(
            text=f"[Local model placeholder] {prompt[:100]}...",
            tokens_used=0,
            model="local",
            source="local",
            duration_ms=0
        )
