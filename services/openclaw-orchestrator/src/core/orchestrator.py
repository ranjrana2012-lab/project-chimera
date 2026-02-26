"""Orchestrator for coordinating skill invocations"""

import time
from typing import Any, Dict, Optional

import httpx

from ..config import Settings
from ..models.responses import SkillInvokeResponse
from .skill_registry import SkillRegistry
from .pipeline_executor import PipelineExecutor


class Orchestrator:
    """Orchestrator for skill invocations."""

    def __init__(
        self,
        skill_registry: SkillRegistry,
        settings: Settings,
    ):
        self.skill_registry = skill_registry
        self.settings = settings

    async def invoke_skill(
        self,
        skill_name: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        timeout_ms: int = 3000,
    ) -> SkillInvokeResponse:
        """Invoke a single skill."""
        start_time = time.time()

        try:
            # Get skill metadata
            skill = await self.skill_registry.get_skill(skill_name)

            if not skill.enabled:
                raise ValueError(f"Skill is disabled: {skill_name}")

            # Check cache
            if skill.cache_enabled:
                cache_key = self.skill_registry.get_cache_key(skill_name, input_data)
                cached_result = await self.skill_registry.get_cached_result(cache_key)
                if cached_result is not None:
                    latency_ms = (time.time() - start_time) * 1000
                    return SkillInvokeResponse(
                        skill_name=skill_name,
                        success=True,
                        output=cached_result,
                        latency_ms=latency_ms,
                        cached=True,
                    )

            # Invoke the skill
            output = await self._invoke_service(
                skill_name, input_data, config or {}, timeout_ms
            )

            # Cache result if enabled
            if skill.cache_enabled:
                cache_key = self.skill_registry.get_cache_key(skill_name, input_data)
                await self.skill_registry.cache_result(
                    cache_key, output, skill.cache_ttl_seconds
                )

            latency_ms = (time.time() - start_time) * 1000

            return SkillInvokeResponse(
                skill_name=skill_name,
                success=True,
                output=output,
                latency_ms=latency_ms,
                cached=False,
                metadata={
                    "skill_version": skill.version,
                    "category": skill.category,
                },
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            return SkillInvokeResponse(
                skill_name=skill_name,
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )

    async def _invoke_service(
        self,
        skill_name: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any],
        timeout_ms: int,
    ) -> Dict[str, Any]:
        """Invoke a skill service via HTTP."""
        endpoint = self._get_service_endpoint(skill_name)

        timeout_sec = timeout_ms / 1000.0

        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            response = await client.post(
                f"{endpoint}/invoke",
                json={
                    "input": input_data,
                    "config": config,
                },
            )
            response.raise_for_status()

            data = response.json()

            # Extract output from response
            if isinstance(data, dict) and "output" in data:
                return data["output"]
            return data

    def _get_service_endpoint(self, skill_name: str) -> str:
        """Get the service endpoint for a skill."""
        # Map skill names to service endpoints
        skill_to_service = {
            "scenespeak": self.settings.scenespeak_endpoint,
            "captioning": self.settings.captioning_endpoint,
            "bsl-text2gloss": self.settings.bsl_text2gloss_endpoint,
            "sentiment": self.settings.sentiment_endpoint,
            "lighting-control": self.settings.lighting_endpoint,
            "safety-filter": self.settings.safety_endpoint,
            "operator-console": self.settings.operator_endpoint,
        }

        if skill_name in skill_to_service:
            return skill_to_service[skill_name]

        # Default to skill name as service name
        return f"http://{skill_name}.live.svc.cluster.local:8000"
