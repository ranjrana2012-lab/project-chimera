"""
Local LLM integration for SceneSpeak Agent.

Supports Ollama for local model serving with ARM64 GB10 GPU compatibility.
Provides fallback to GLM API when local LLM is unavailable.
"""

import httpx
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LocalLLMResponse:
    """Response from local LLM generation"""
    text: str
    tokens_used: int
    model: str
    source: str
    duration_ms: int


class LocalLLMClient:
    """Local LLM client supporting Ollama and direct model loading."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: float = 30.0
    ):
        """
        Initialize the local LLM client.

        Args:
            base_url: Base URL for Ollama API (default: localhost:11434)
            model: Model name to use (default: llama3.2)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._available_models: Optional[list[str]] = None

    async def connect(self) -> bool:
        """
        Connect to local LLM server and verify availability.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
            # Test connection and get available models
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            # Extract available models
            self._available_models = [
                model["name"] for model in data.get("models", [])
            ]
            self._connected = True

            logger.info(
                f"Connected to local LLM: {self.base_url}, "
                f"available models: {self._available_models}"
            )
            return True

        except httpx.ConnectError as e:
            logger.warning(f"Failed to connect to local LLM at {self.base_url}: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.warning(f"Local LLM unavailable: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Close the HTTP client connection."""
        if self.client:
            await self.client.aclose()
            self._connected = False
            logger.info("Disconnected from local LLM")

    async def is_available(self) -> bool:
        """
        Check if local LLM is available and connected.

        Returns:
            True if available, False otherwise
        """
        return self._connected and self.client is not None

    async def get_available_models(self) -> list[str]:
        """
        Get list of available models from Ollama.

        Returns:
            List of model names, or empty list if unavailable
        """
        if not self._connected or not self._available_models:
            return []
        return self._available_models

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LocalLLMResponse:
        """
        Generate dialogue using local LLM.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 2.0)
            **kwargs: Additional generation parameters

        Returns:
            LocalLLMResponse with generated text and metadata

        Raises:
            RuntimeError: If not connected to local LLM
            httpx.HTTPError: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Not connected to local LLM")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": kwargs.get("top_p", 0.9),
                "top_k": kwargs.get("top_k", 40),
            }
        }

        start_time = time.time()

        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            return LocalLLMResponse(
                text=result.get("response", ""),
                tokens_used=result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                model=self.model,
                source="local",
                duration_ms=duration_ms
            )

        except httpx.HTTPError as e:
            logger.error(f"Local LLM generation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of local LLM service.

        Returns:
            Dictionary with health status information
        """
        health = {
            "connected": self._connected,
            "base_url": self.base_url,
            "model": self.model,
            "available_models": []
        }

        if self._connected and self.client:
            try:
                response = await self.client.get("/api/tags")
                response.raise_for_status()
                data = response.json()
                health["available_models"] = [
                    model["name"] for model in data.get("models", [])
                ]
                health["status"] = "healthy"
            except Exception as e:
                health["status"] = "unhealthy"
                health["error"] = str(e)
        else:
            health["status"] = "disconnected"

        return health

    async def ensure_model(self, model: str) -> bool:
        """
        Ensure a specific model is available.

        Args:
            model: Model name to check

        Returns:
            True if model is available, False otherwise
        """
        if not self._connected:
            return False

        available = await self.get_available_models()
        return any(model in m for m in available)


# Legacy LocalLLM class for backward compatibility
class LocalLLM:
    """Legacy interface for local LLM inference (deprecated)."""

    def __init__(self, model_path: Optional[str] = None, base_url: str = "http://localhost:11434"):
        """
        Initialize the local LLM interface.

        Args:
            model_path: Deprecated - Path to the local model file
            base_url: Base URL for Ollama API
        """
        if model_path:
            logger.warning("model_path parameter is deprecated. Using Ollama instead.")

        self.client = LocalLLMClient(base_url=base_url)
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the local model connection.

        Returns:
            True if initialization successful
        """
        self._initialized = await self.client.connect()
        return self._initialized

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> dict:
        """
        Generate text using local model.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dictionary with generation results
        """
        if not self._initialized:
            success = await self.initialize()
            if not success:
                return {
                    "text": "[Local model not available]",
                    "tokens_used": 0,
                    "duration_ms": 0
                }

        try:
            response = await self.client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                "text": response.text,
                "tokens_used": response.tokens_used,
                "duration_ms": response.duration_ms
            }
        except Exception as e:
            logger.error(f"Local model generation failed: {e}")
            return {
                "text": f"[Local model error: {str(e)}]",
                "tokens_used": 0,
                "duration_ms": 0
            }
