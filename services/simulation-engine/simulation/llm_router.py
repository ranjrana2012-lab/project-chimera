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
