"""vLLM client for Kimi K2.6 inference."""

import logging
import os
from typing import Dict, Any, Optional

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

load_dotenv()


class KimiClient:
    """Client for Kimi K2.6 vLLM inference."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: int = 300,
    ):
        """Initialize the KimiClient.

        Args:
            base_url: vLLM service URL (defaults to KIMI_VLLM_ENDPOINT env var)
            timeout_seconds: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("KIMI_VLLM_ENDPOINT", "http://localhost:8012")
        self.timeout = timeout_seconds
        self.model_name = os.getenv("KIMI_MODEL_NAME", "moonshotai/Kimi-K2.6")

        self.client = AsyncOpenAI(
            base_url=f"{self.base_url}/v1",
            api_key="dummy",  # vLLM doesn't require real API key
            timeout=timeout_seconds,
        )

    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate completion via vLLM.

        Args:
            request: OpenAI-compatible request dict with:
                - model: Model name (defaults to self.model_name)
                - messages: List of message dicts with role/content
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - top_p: Nucleus sampling threshold

        Returns:
            Response dict with choices containing generated messages

        Raises:
            Exception: If the vLLM request fails
        """
        response = await self.client.chat.completions.create(
            model=request.get("model", self.model_name),
            messages=request.get("messages", []),
            max_tokens=request.get("max_tokens", 32768),
            temperature=request.get("temperature", 0.7),
            top_p=request.get("top_p", 0.9),
        )

        return response.model_dump()

    async def health_check(self) -> bool:
        """Check if vLLM service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(
                "Kimi vLLM health check failed",
                extra={"url": f"{self.base_url}/health", "error": str(e)},
            )
            return False
