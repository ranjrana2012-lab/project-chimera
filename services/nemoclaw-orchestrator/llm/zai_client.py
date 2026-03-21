# services/nemoclaw-orchestrator/llm/zai_client.py
from openai import OpenAI
from enum import Enum
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class ZAIModel(str, Enum):
    """Z.AI model options"""
    PRIMARY = "glm-5-turbo"      # OpenClaw-optimized, tool invocation
    PROGRAMMING = "glm-4.7"      # Enhanced programming, reasoning
    FAST = "glm-4.7-flashx"      # Simple, repetitive tasks


class ZAIClient:
    """Client for Z.AI API using OpenAI SDK with custom base_url"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.z.ai/api/paas/v4/"
    ):
        """
        Initialize Z.AI client

        Args:
            api_key: Z.AI API key (defaults to ZAI_API_KEY env var)
            base_url: Z.AI API base URL
        """
        self.api_key = api_key or os.getenv("ZAI_API_KEY", "")
        self.base_url = base_url
        self._client: Optional[OpenAI] = None

        if not self.api_key:
            logger.warning("ZAI_API_KEY not set - Z.AI client will fail")

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def _is_credit_error(self, error: Exception) -> bool:
        """
        Check if error indicates credit exhaustion

        Args:
            error: Exception to check

        Returns:
            True if error is credit exhaustion, False otherwise
        """
        error_str = str(error).lower()
        error_status = getattr(error, "status_code", None)

        # Check status code
        if error_status in (402, 403):
            return True

        # Check error message for credit-related keywords
        credit_keywords = [
            "insufficient credits",
            "quota exceeded",
            "credit exhausted",
            "billing",
            "payment required"
        ]
        return any(keyword in error_str for keyword in credit_keywords)

    def generate(
        self,
        prompt: str,
        model: ZAIModel = ZAIModel.PRIMARY,
        max_tokens: int = 512,
        temperature: float = 0.7,
        thinking: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Z.AI API

        Args:
            prompt: Input prompt
            model: Z.AI model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            thinking: Whether to enable thinking parameter
            **kwargs: Additional parameters

        Returns:
            Dict with generated text and metadata
        """
        try:
            client = self._get_client()

            # Build request
            request_params = {
                "model": model.value,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }

            # Note: thinking parameter not supported by current Z.AI API version
            # if thinking:
            #     request_params["thinking"] = {"type": "enabled"}

            response = client.chat.completions.create(**request_params)

            return {
                "text": response.choices[0].message.content,
                "model_used": model.value,
                "credits_exhausted": False,
                "usage": getattr(response, "usage", {})
            }

        except Exception as e:
            # Check for credit exhaustion
            if self._is_credit_error(e):
                logger.warning(f"Z.AI credit exhaustion detected: {e}")
                return {
                    "error": "credit_exhausted",
                    "details": str(e),
                    "model_used": model.value
                }

            # Re-raise other errors
            logger.error(f"Z.AI generation error: {e}")
            raise

    def close(self):
        """Close OpenAI client"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
