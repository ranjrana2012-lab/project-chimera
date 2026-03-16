from typing import Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMBackend(str, Enum):
    """Available LLM backends."""
    LOCAL_VLLM = "local_vllm"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TieredLLMRouter:
    """Route LLM calls based on cost and criticality."""

    def __init__(
        self,
        local_ratio: float = 0.95,
        local_url: str = "http://localhost:8000"
    ):
        self.local_ratio = local_ratio
        self.local_url = local_url
        self.call_count = 0
        self.local_count = 0
        self.api_count = 0

    async def route_decision(self, context: str = "") -> LLMBackend:
        """Decide which LLM to use based on context and cost ratio."""
        import random

        self.call_count += 1

        if random.random() < self.local_ratio:
            self.local_count += 1
            logger.debug(f"Routing to local LLM ({self.local_count}/{self.call_count})")
            return LLMBackend.LOCAL_VLLM
        else:
            self.api_count += 1
            logger.debug(f"Routing to API LLM ({self.api_count}/{self.call_count})")
            return LLMBackend.OPENAI if random.random() < 0.5 else LLMBackend.ANTHROPIC

    def get_stats(self) -> Dict[str, int]:
        """Get routing statistics."""
        return {
            "total_calls": self.call_count,
            "local_calls": self.local_count,
            "api_calls": self.api_count,
            "local_ratio": self.local_count / self.call_count if self.call_count > 0 else 0
        }

    async def call_llm(self, prompt: str, backend: LLMBackend = None) -> str:
        """
        Call LLM with the given prompt using the specified or routed backend.

        Args:
            prompt: The prompt to send to the LLM
            backend: Optional specific backend to use. If not provided, uses route_decision

        Returns:
            LLM response text

        Raises:
            RuntimeError: If LLM call fails
        """
        import random

        if backend is None:
            backend = await self.route_decision(prompt)

        try:
            logger.debug(f"Calling LLM with backend: {backend}")

            # In production, this would make actual API calls
            # For now, we'll simulate responses for testing
            return self._mock_llm_response(prompt, backend)

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"LLM invocation failed: {e}") from e

    def _mock_llm_response(self, prompt: str, backend: LLMBackend) -> str:
        """
        Generate mock LLM response for testing purposes.

        In production, this would be replaced with actual API calls to:
        - vLLM for LOCAL_VLLM backend
        - OpenAI API for OPENAI backend
        - Anthropic API for ANTHROPIC backend
        """
        import json
        import random

        # Simulate different response patterns based on prompt content
        prompt_lower = prompt.lower()

        if "debate" in prompt_lower or "argument" in prompt_lower:
            # Generate mock debate response
            stance = random.uniform(-0.9, 0.9)
            return json.dumps({
                "content": f"Based on my analysis, I believe this approach has merit.",
                "stance": stance,
                "reasoning": "After careful consideration of the evidence and perspectives presented."
            })

        # Default generic response
        return json.dumps({
            "content": "I understand the request and will provide a thoughtful response.",
            "stance": 0.0,
            "reasoning": "This requires further analysis."
        })
