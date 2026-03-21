# services/nemoclaw-orchestrator/llm/ollama_client.py
"""Ollama client for local LLM fallback"""
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama (OpenAI-compatible local LLM)"""

    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "llama3:instruct"):
        """
        Initialize Ollama client

        Args:
            endpoint: Ollama endpoint URL
            model: Model name to use
        """
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=60.0,  # Ollama can be slow
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            client = self._get_client()
            response = client.get(f"{self.endpoint}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama

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

            # Ollama API format
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                }
            }

            response = client.post(
                f"{self.endpoint}/api/generate",
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            return {
                "text": data.get("response", ""),
                "model_used": self.model,
                "backend": "ollama_local",
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0)
                }
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
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
