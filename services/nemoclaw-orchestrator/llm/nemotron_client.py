# services/nemoclaw-orchestrator/llm/nemotron_client.py
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NemotronClient:
    """Client for local DGX Nemotron inference"""

    def __init__(self, endpoint: str, model: str = "nemotron-8b"):
        """
        Initialize Nemotron client

        Args:
            endpoint: DGX Nemotron endpoint URL
            model: Model name to use
        """
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    def is_available(self) -> bool:
        """
        Check if DGX Nemotron service is available

        Returns:
            True if service is reachable, False otherwise
        """
        try:
            client = self._get_client()
            response = client.get(f"{self.endpoint}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"DGX Nemotron health check failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using local DGX Nemotron

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Dict with generated text and metadata
        """
        try:
            client = self._get_client()

            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }

            response = client.post(
                f"{self.endpoint}/v1/completions",
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            return {
                "text": data.get("choices", [{}])[0].get("text", ""),
                "model": self.model,
                "backend": "nemotron_local",
                "usage": data.get("usage", {})
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"DGX Nemotron request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"DGX Nemotron generation error: {e}")
            raise

    def close(self):
        """Close HTTP client"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
