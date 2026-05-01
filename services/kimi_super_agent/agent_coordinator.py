"""Chimera agent coordination for Kimi super-agent."""

import os
import asyncio
import time
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for a Chimera agent."""
    endpoint: str
    timeout_seconds: int


class AgentCoordinator:
    """Coordinates calls to Chimera agents."""

    # Default agent configurations
    DEFAULT_AGENTS = {
        "sentiment": AgentConfig(
            endpoint=os.getenv("SENTIMENT_AGENT_ENDPOINT", "http://sentiment-agent:8004"),
            timeout_seconds=int(os.getenv("SENTIMENT_AGENT_TIMEOUT", "10"))
        ),
        "translation": AgentConfig(
            endpoint=os.getenv("TRANSLATION_AGENT_ENDPOINT", "http://translation-agent:8002"),
            timeout_seconds=int(os.getenv("TRANSLATION_AGENT_TIMEOUT", "15"))
        ),
        "scenespeak": AgentConfig(
            endpoint=os.getenv("SCENESPEAK_AGENT_ENDPOINT", "http://scenespeak-agent:8001"),
            timeout_seconds=int(os.getenv("SCENESPEAK_AGENT_TIMEOUT", "30"))
        ),
        "safety": AgentConfig(
            endpoint=os.getenv("SAFETY_FILTER_ENDPOINT", "http://safety-filter:8006"),
            timeout_seconds=int(os.getenv("SAFETY_FILTER_TIMEOUT", "5"))
        ),
    }

    def __init__(self, agents: Dict[str, AgentConfig] = None):
        self.agents = agents or self.DEFAULT_AGENTS
        self.client = httpx.AsyncClient(timeout=30.0)

    async def call_agent(
        self,
        agent_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a single Chimera agent.

        Args:
            agent_name: Name of agent to call
            data: Request data

        Returns:
            Agent response dict

        Raises:
            ValueError: If agent not found
            httpx.HTTPError: If request fails
        """
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        start_time = time.time()

        try:
            response = await self.client.post(
                agent.endpoint,
                json=data,
                timeout=agent.timeout_seconds
            )
            response.raise_for_status()

            result = response.json()
            result["_timing_ms"] = int((time.time() - start_time) * 1000)
            result["_agent"] = agent_name
            result["_success"] = True

            return result

        except httpx.HTTPError as e:
            return {
                "_agent": agent_name,
                "_success": False,
                "_error": str(e),
                "_timing_ms": int((time.time() - start_time) * 1000)
            }

    async def coordinate_agents(
        self,
        agent_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Coordinate multiple agent calls in parallel.

        Args:
            agent_calls: List of {agent, data} dicts

        Returns:
            List of agent responses
        """
        tasks = [
            self.call_agent(call["agent"], call["data"])
            for call in agent_calls
        ]

        return await asyncio.gather(*tasks)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
