"""Request routing to skills."""
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
import aiohttp
import redis.asyncio as redis

from ..models.request import OrchestrationRequest, SkillRequest
from ..models.response import OrchestrationResponse, SkillResponse, Status
from .skill_registry import SkillRegistry
from .gpu_scheduler import GPUScheduler


class Router:
    """Routes requests to skills."""

    def __init__(
        self,
        registry: SkillRegistry,
        gpu_scheduler: GPUScheduler,
        redis_client: redis.Redis
    ):
        self.registry = registry
        self.gpu_scheduler = gpu_scheduler
        self.redis = redis_client
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """Orchestrate a request through multiple skills."""
        request_id = request.request_id or str(uuid.uuid4())
        start_time = time.time()

        results = {}
        errors = {}
        gpu_used = False

        # Allocate GPU if needed
        gpu_id = None
        if request.gpu_required:
            gpu_id = await self.gpu_scheduler.allocate_gpu(
                service="orchestrate",
                memory_mb=4000,
                timeout=request.timeout
            )
            if gpu_id is not None:
                gpu_used = True

        try:
            # Execute skills in sequence
            for skill_name in request.skills:
                skill = self.registry.get_skill(skill_name)
                if not skill:
                    errors[skill_name] = "Skill not found"
                    continue

                try:
                    skill_response = await self._invoke_skill(
                        skill,
                        request.input_data,
                        timeout=request.timeout
                    )
                    results[skill_name] = skill_response.output

                except asyncio.TimeoutError:
                    errors[skill_name] = "Timeout"
                except Exception as e:
                    errors[skill_name] = str(e)

        finally:
            if gpu_id is not None:
                await self.gpu_scheduler.release_gpu("orchestrate")

        execution_time = (time.time() - start_time) * 1000

        status = Status.SUCCESS if not errors else Status.ERROR

        return OrchestrationResponse(
            request_id=request_id,
            status=status,
            results=results,
            execution_time_ms=execution_time,
            gpu_used=gpu_used,
            errors=errors if errors else None
        )

    async def _invoke_skill(
        self,
        skill: 'Skill',
        input_data: Dict[str, Any],
        timeout: int
    ) -> SkillResponse:
        """Invoke a single skill."""
        start_time = time.time()

        async with self.session.post(
            f"{skill.endpoint}/v1/invoke",
            json={"input_data": input_data},
            timeout=aiohttp.ClientTimeout(total=timeout / 1000)
        ) as response:
            output = await response.json()
            execution_time = (time.time() - start_time) * 1000

            return SkillResponse(
                skill=skill.name,
                status=Status.SUCCESS,
                output=output,
                execution_time_ms=execution_time
            )
