"""
OpenAI-compatible LLM client for SceneSpeak Agent.

Supports Nemotron and other OpenAI-compatible endpoints.
Works with host.docker.internal for Docker container to host communication.
"""

import httpx
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OpenAIResponse:
    """Response from OpenAI-compatible LLM generation"""
    text: str
    tokens_used: int
    model: str
    source: str
    duration_ms: int
    backend: str = "openai_compatible"


class OpenAILLMClient:
    """OpenAI-compatible LLM client supporting Nemotron and other APIs."""

    def __init__(
        self,
        base_url: str = "http://host.docker.internal:8012",
        model: str = "nemotron-3-super-120b-a12b-nvfp4",
        timeout: float = 120.0
    ):
        """
        Initialize the OpenAI-compatible LLM client.

        Args:
            base_url: Base URL for OpenAI-compatible API (default: host.docker.internal:8012)
            model: Model name to use (default: nemotron-3-super-120b-a12b-nvfp4)
            timeout: Request timeout in seconds (default: 120s for large models)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Connect to OpenAI-compatible LLM server and verify availability.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
            # Test connection with health check
            response = await self.client.get("/health", timeout=5.0)
            if response.status_code == 200:
                self._connected = True
                logger.info(f"Connected to OpenAI-compatible LLM: {self.base_url}")
                return True
            else:
                logger.warning(f"LLM health check returned {response.status_code}")
                return False

        except httpx.ConnectError as e:
            logger.warning(f"Failed to connect to LLM at {self.base_url}: {e}")
            # For MVP, allow connection to fail gracefully
            # Service will still start but use fallback
            self._connected = False
            return False
        except Exception as e:
            logger.warning(f"LLM unavailable: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Close the HTTP client connection."""
        if self.client:
            await self.client.aclose()
            self._connected = False
            logger.info("Disconnected from OpenAI-compatible LLM")

    async def is_available(self) -> bool:
        """
        Check if OpenAI-compatible LLM is available and connected.

        Returns:
            True if available, False otherwise
        """
        return self._connected and self.client is not None

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> OpenAIResponse:
        """
        Generate dialogue using OpenAI-compatible API.

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 2.0)
            **kwargs: Additional generation parameters

        Returns:
            OpenAIResponse with generated text and metadata

        Raises:
            RuntimeError: If not connected to LLM
            httpx.HTTPError: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Not connected to OpenAI-compatible LLM")

        # OpenAI-compatible chat format
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        start_time = time.time()

        try:
            response = await self.client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            result = response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract response from OpenAI format
            text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)

            return OpenAIResponse(
                text=text,
                tokens_used=tokens_used,
                model=self.model,
                source="openai_local",
                duration_ms=duration_ms,
                backend="openai_compatible"
            )

        except httpx.HTTPError as e:
            logger.error(f"OpenAI-compatible LLM generation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of OpenAI-compatible LLM service.

        Returns:
            Dictionary with health status information
        """
        health = {
            "connected": self._connected,
            "base_url": self.base_url,
            "model": self.model,
            "format": "openai_compatible"
        }

        if self._connected and self.client:
            try:
                response = await self.client.get("/health")
                if response.status_code == 200:
                    health["status"] = "healthy"
                else:
                    health["status"] = f"unhealthy (status {response.status_code})"
            except Exception as e:
                health["status"] = "unhealthy"
                health["error"] = str(e)
        else:
            health["status"] = "disconnected"

        return health

    def sync_is_available(self) -> bool:
        """
        Synchronous check if LLM is available (for non-async contexts).

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    def sync_generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous generate using httpx.Client (for non-async contexts).

        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters

        Returns:
            Dictionary with generation results
        """
        client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout
        )

        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }

            start_time = time.time()
            response = client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            result = response.json()
            duration_ms = int((time.time() - start_time) * 1000)

            text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            return {
                "text": text,
                "tokens_used": usage.get("total_tokens", 0),
                "model": self.model,
                "source": "openai_local",
                "duration_ms": duration_ms,
                "backend": "openai_compatible"
            }
        except Exception as e:
            logger.error(f"Sync generation failed: {e}")
            raise
        finally:
            client.close()
