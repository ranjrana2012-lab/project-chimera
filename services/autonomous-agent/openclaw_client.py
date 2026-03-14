"""OpenClaw Client - Enables autonomous agent to call other specialized agents.

This module provides a client for the autonomous agent to communicate with
the OpenClaw Orchestrator, enabling multi-agent task execution as per the
VMAO (Verified Multi-Agent Orchestration) framework.
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AgentCapability:
    """Represents a capability/skill exposed by an agent."""
    name: str
    description: str
    endpoint: str
    method: str = "POST"
    enabled: bool = True


@dataclass
class AgentCallResult:
    """Result of calling another agent through OpenClaw."""
    success: bool
    skill_used: str
    result: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class OpenClawClient:
    """Client for autonomous agent to communicate with OpenClaw Orchestrator.

    This enables the autonomous agent to:
    1. Discover available skills/agents
    2. Delegate subtasks to specialized agents
    3. Implement VMAO-style DAG-based task decomposition
    4. Enable dependency-aware parallel execution
    """

    def __init__(self, openclaw_url: Optional[str] = None):
        """Initialize OpenClaw client.

        Args:
            openclaw_url: Base URL for OpenClaw orchestrator (default from settings)
        """
        self.openclaw_url = openclaw_url or getattr(settings, 'openclaw_url', 'http://localhost:8000')
        self.timeout = 30.0
        self._capabilities_cache: Optional[List[AgentCapability]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutes

    async def get_available_skills(self, force_refresh: bool = False) -> List[AgentCapability]:
        """Get list of available skills from OpenClaw.

        Args:
            force_refresh: Force refresh of capabilities cache

        Returns:
            List of available agent capabilities

        Raises:
            httpx.HTTPError: If request fails
        """
        # Check cache
        if not force_refresh and self._capabilities_cache:
            if self._cache_timestamp:
                age = (datetime.now() - self._cache_timestamp).total_seconds()
                if age < self._cache_ttl:
                    logger.debug(f"Using cached capabilities ({age:.0f}s old)")
                    return self._capabilities_cache

        # Fetch from OpenClaw
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.openclaw_url}/api/skills")
                response.raise_for_status()
                data = response.json()

                # Parse capabilities
                capabilities = [
                    AgentCapability(
                        name=skill["name"],
                        description=skill["description"],
                        endpoint=skill["endpoint"],
                        method=skill.get("method", "POST"),
                        enabled=skill.get("enabled", True)
                    )
                    for skill in data.get("skills", [])
                ]

                # Update cache
                self._capabilities_cache = capabilities
                self._cache_timestamp = datetime.now()

                logger.info(f"Discovered {len(capabilities)} capabilities from OpenClaw")
                return capabilities

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch capabilities from OpenClaw: {e}")
            # Return cached capabilities if available
            if self._capabilities_cache:
                logger.warning("Using stale cached capabilities due to fetch failure")
                return self._capabilities_cache
            raise

    async def call_agent(
        self,
        skill: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentCallResult:
        """Call another agent through OpenClaw orchestrator.

        This enables the autonomous agent to delegate subtasks to specialized agents,
        implementing the VMAO framework's DAG-based task decomposition.

        Args:
            skill: Name of skill to invoke
            input_data: Input data for the skill
            context: Optional additional context

        Returns:
            AgentCallResult with execution result

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If skill not found
        """
        start_time = datetime.now()

        try:
            # Prepare request payload
            payload = {
                "skill": skill,
                "input": input_data,
                "context": context or {}
            }

            logger.info(f"Calling OpenClaw with skill: {skill}")

            # Make request to OpenClaw
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.openclaw_url}/v1/orchestrate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()

                logger.info(f"Agent call completed in {execution_time:.2f}s")

                return AgentCallResult(
                    success=True,
                    skill_used=skill,
                    result=data.get("result", {}),
                    execution_time=data.get("execution_time", execution_time),
                    metadata=data.get("metadata", {})
                )

        except httpx.HTTPStatusError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Agent call failed with status {e.response.status_code}"

            logger.error(f"{error_msg}: {e}")

            return AgentCallResult(
                success=False,
                skill_used=skill,
                result={},
                execution_time=execution_time,
                error=error_msg
            )

        except httpx.HTTPError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Agent call failed: {str(e)}"

            logger.error(error_msg)

            return AgentCallResult(
                success=False,
                skill_used=skill,
                result={},
                execution_time=execution_time,
                error=error_msg
            )

    async def call_agent_parallel(
        self,
        calls: List[tuple[str, Dict[str, Any]]]
    ) -> List[AgentCallResult]:
        """Call multiple agents in parallel (dependency-aware execution).

        This implements VMAO's dependency-aware parallel execution pattern.

        Args:
            calls: List of (skill, input_data) tuples

        Returns:
            List of AgentCallResult in same order as input calls
        """
        import asyncio

        logger.info(f"Executing {len(calls)} parallel agent calls")

        # Create tasks for parallel execution
        tasks = [
            self.call_agent(skill, input_data)
            for skill, input_data in calls
        ]

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                skill = calls[i][0]
                processed_results.append(
                    AgentCallResult(
                        success=False,
                        skill_used=skill,
                        result={},
                        execution_time=0.0,
                        error=str(result)
                    )
                )
            else:
                processed_results.append(result)

        successful = sum(1 for r in processed_results if r.success)
        logger.info(f"Parallel execution complete: {successful}/{len(calls)} successful")

        return processed_results

    async def check_health(self) -> bool:
        """Check if OpenClaw orchestrator is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.openclaw_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenClaw health check failed: {e}")
            return False

    async def get_show_status(self) -> Dict[str, Any]:
        """Get current show status from OpenClaw.

        Returns:
            Show status dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.openclaw_url}/api/show/status")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get show status: {e}")
            return {
                "show_id": None,
                "state": "unknown",
                "error": str(e)
            }


# Singleton instance
_openclaw_client: Optional[OpenClawClient] = None


def get_openclaw_client() -> OpenClawClient:
    """Get or create singleton OpenClaw client instance.

    Returns:
        OpenClawClient instance
    """
    global _openclaw_client
    if _openclaw_client is None:
        _openclaw_client = OpenClawClient()
    return _openclaw_client
