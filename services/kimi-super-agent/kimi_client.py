"""Kimi K2.6 vLLM client for inference."""

import logging
import os
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)


class KimiClient:
    """Client for Kimi K2.6 vLLM inference API."""

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.base_url = base_url or os.getenv("KIMI_VLLM_ENDPOINT", "http://localhost:8000")
        self.model_name = model_name or os.getenv("KIMI_MODEL_NAME", "moonshotai/Kimi-K2.6")
        self.timeout = timeout_seconds or int(os.getenv("KIMI_REQUEST_TIMEOUT", "300"))
        logger.info(f"KimiClient initialized with {self.base_url}")

    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send generation request to vLLM server.

        Args:
            request: Generation request with messages and parameters

        Returns:
            vLLM response with generated text
        """
        url = f"{self.base_url}/v1/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = dict(request)
            payload.setdefault("model", self.model_name)
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Check if vLLM server is healthy."""
        try:
            url = f"{self.base_url}/health"
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
