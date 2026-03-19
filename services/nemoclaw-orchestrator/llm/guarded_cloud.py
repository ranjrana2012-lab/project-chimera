# services/nemoclaw-orchestrator/llm/guarded_cloud.py
import httpx
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class GuardedCloudClient:
    """Client for Anthropic API with PII stripping"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307"
    ):
        """
        Initialize Guarded Cloud client

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set - cloud client will fail")

        self.model = model
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=60.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    def _strip_pii(self, text: str) -> str:
        """
        Strip PII from text using OutputFilter

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        from policy.filters import OutputFilter

        output_filter = OutputFilter()

        # Use the existing filter to remove PII
        result = {"text": text}
        import asyncio

        # Run async filter in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            filtered = loop.run_until_complete(
                output_filter.filter(result, "guarded_cloud")
            )
            return filtered["text"]
        finally:
            loop.close()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        strip_pii: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Anthropic API with PII stripping

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            strip_pii: Whether to strip PII from prompt
            **kwargs: Additional parameters

        Returns:
            Dict with generated text and metadata
        """
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        try:
            client = self._get_client()

            # Strip PII from prompt if enabled
            sanitized_prompt = self._strip_pii(prompt) if strip_pii else prompt

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": sanitized_prompt}
                ],
                **kwargs
            }

            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            generated_text = data.get("content", [{}])[0].get("text", "")

            return {
                "text": generated_text,
                "model": self.model,
                "backend": "cloud_guarded",
                "usage": data.get("usage", {}),
                "pii_stripped": strip_pii
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Guarded cloud generation error: {e}")
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
