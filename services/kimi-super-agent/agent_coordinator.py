"""Agent coordinator for managing sub-agents."""

import logging
import os
import asyncio
import time
from typing import Dict, Any, List

import httpx

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Coordinates delegation to specialized agents."""

    def __init__(self):
        self.agents_enabled = os.getenv("CHIMERA_SUB_AGENTS_ENABLED", "false").lower() == "true"
        self.client = httpx.AsyncClient(timeout=float(os.getenv("CHIMERA_AGENT_TIMEOUT", "30")))
        self.agent_urls = {
            "sentiment": os.getenv("SENTIMENT_AGENT_URL", "http://sentiment-agent:8004"),
            "safety": os.getenv("SAFETY_FILTER_URL", "http://safety-filter:8006"),
            "translation": os.getenv("TRANSLATION_AGENT_URL", "http://translation-agent:8002"),
            "scenespeak": os.getenv("SCENESPEAK_AGENT_URL", "http://scenespeak-agent:8001"),
        }
        logger.info(f"AgentCoordinator initialized (sub-agents: {self.agents_enabled})")

    async def call_agent(self, agent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call a configured Chimera agent and annotate the result."""
        if agent not in self.agent_urls:
            raise ValueError(f"Unknown agent: {agent}")

        start = time.perf_counter()
        response = await self.client.post(self.agent_urls[agent], json=data)
        response.raise_for_status()
        result = response.json()
        result["_success"] = True
        result["_agent"] = agent
        result["_timing_ms"] = int((time.perf_counter() - start) * 1000)
        return result

    async def coordinate_agents(self, agent_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run several agent calls concurrently."""
        tasks = [
            self.call_agent(call["agent"], call.get("data", {}))
            for call in agent_calls
        ]
        return await asyncio.gather(*tasks)

    async def coordinate(
        self,
        request: Dict[str, Any],
        capability_hint: int
    ) -> Dict[str, Any]:
        """
        Coordinate request handling with agents if needed.

        Args:
            request: Internal request format
            capability_hint: Detected capability requirement

        Returns:
            Coordination result with agent invocations
        """
        # For now, return empty - sub-agent delegation to be implemented
        return {
            "agents_used": [],
            "delegated": False
        }
