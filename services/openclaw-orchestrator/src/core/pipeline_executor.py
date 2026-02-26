"""Pipeline Executor for OpenClaw Orchestrator"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from ..config import Settings
from ..models.requests import PipelineStep
from ..models.responses import (
    PipelineExecuteResponse,
    PipelineStepResult,
    PipelineStatus,
)
from .skill_registry import SkillRegistry


class PipelineExecutor:
    """Executor for skill pipelines."""

    def __init__(
        self,
        skill_registry: SkillRegistry,
        settings: Settings,
    ):
        self.skill_registry = skill_registry
        self.settings = settings
        self._pipelines: Dict[str, List[PipelineStep]] = {}
        self._running_pipelines: Dict[str, PipelineStatus] = {}

    async def execute(
        self,
        pipeline_id: Optional[str] = None,
        steps: Optional[List[PipelineStep]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        parallel: bool = False,
        timeout_ms: int = 10000,
    ) -> PipelineExecuteResponse:
        """Execute a pipeline."""
        start_time = time.time()

        # Get pipeline steps
        if pipeline_id:
            if pipeline_id not in self._pipelines:
                raise ValueError(f"Pipeline not found: {pipeline_id}")
            steps = self._pipelines[pipeline_id]
        elif not steps:
            raise ValueError("Either pipeline_id or steps must be provided")

        input_data = input_data or {}
        execution_id = str(uuid.uuid4())

        # Create pipeline status
        status = PipelineStatus(
            pipeline_id=execution_id,
            status="running",
            current_step=0,
            total_steps=len(steps),
            started_at=datetime.now().isoformat(),
        )
        self._running_pipelines[execution_id] = status

        try:
            # Execute steps
            if parallel:
                results = await self._execute_parallel(steps, input_data)
            else:
                results = await self._execute_sequential(steps, input_data)

            # Aggregate final output
            final_output = {}
            for result in results:
                if result.success:
                    final_output.update(result.output)

            total_latency = (time.time() - start_time) * 1000

            # Update status
            status.status = "completed"
            status.completed_at = datetime.now().isoformat()

            return PipelineExecuteResponse(
                pipeline_id=pipeline_id,
                success=all(r.success for r in results),
                output=final_output,
                steps=results,
                total_latency_ms=total_latency,
                metadata={"execution_id": execution_id},
            )

        except Exception as e:
            status.status = "failed"
            status.error = str(e)
            status.completed_at = datetime.now().isoformat()

            raise

        finally:
            # Clean up old statuses
            await self._cleanup_old_statuses()

    async def _execute_sequential(
        self, steps: List[PipelineStep], initial_input: Dict[str, Any]
    ) -> List[PipelineStepResult]:
        """Execute steps sequentially."""
        results = []
        current_input = initial_input.copy()

        for i, step in enumerate(steps):
            step_result = await self._execute_step(step, current_input, i + 1)
            results.append(step_result)

            if step_result.success:
                # Update input for next step
                if step.input_mapping:
                    mapped_input = {}
                    for output_key, input_key in step.input_mapping.items():
                        if output_key in step_result.output:
                            mapped_input[input_key] = step_result.output[output_key]
                    current_input.update(mapped_input)
                else:
                    current_input.update(step_result.output)
            else:
                # Stop pipeline on failure
                break

        return results

    async def _execute_parallel(
        self, steps: List[PipelineStep], input_data: Dict[str, Any]
    ) -> List[PipelineStepResult]:
        """Execute steps in parallel."""
        tasks = [
            self._execute_step(step, input_data, i + 1)
            for i, step in enumerate(steps)
        ]
        return await asyncio.gather(*tasks)

    async def _execute_step(
        self, step: PipelineStep, input_data: Dict[str, Any], step_number: int
    ) -> PipelineStepResult:
        """Execute a single pipeline step."""
        start_time = time.time()

        try:
            skill = await self.skill_registry.get_skill(step.skill_name)

            if not skill.enabled:
                raise ValueError(f"Skill is disabled: {step.skill_name}")

            # Invoke skill
            output = await self._invoke_skill(
                step.skill_name, input_data, step.config or {}
            )

            latency_ms = (time.time() - start_time) * 1000

            return PipelineStepResult(
                step_number=step_number,
                skill_name=step.skill_name,
                success=True,
                output=output,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            return PipelineStepResult(
                step_number=step_number,
                skill_name=step.skill_name,
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )

    async def _invoke_skill(
        self, skill_name: str, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke a skill via HTTP."""
        skill = await self.skill_registry.get_skill(skill_name)

        # Get service endpoint
        endpoint = self._get_service_endpoint(skill_name)

        # Call service
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{endpoint}/invoke",
                json={"input": input_data, "config": config},
            )
            response.raise_for_status()
            return response.json()

    def _get_service_endpoint(self, skill_name: str) -> str:
        """Get the service endpoint for a skill."""
        endpoints = {
            "scenespeak": self.settings.scenespeak_endpoint,
            "captioning": self.settings.captioning_endpoint,
            "bsl-text2gloss": self.settings.bsl_text2gloss_endpoint,
            "sentiment": self.settings.sentiment_endpoint,
            "lighting-control": self.settings.lighting_endpoint,
            "safety-filter": self.settings.safety_endpoint,
            "operator-console": self.settings.operator_endpoint,
        }

        return endpoints.get(skill_name, f"http://{skill_name}:8000")

    async def define_pipeline(self, pipeline_id: str, steps: List[Dict]) -> None:
        """Define a new pipeline."""
        pipeline_steps = [PipelineStep(**step) for step in steps]
        self._pipelines[pipeline_id] = pipeline_steps

    async def delete_pipeline(self, pipeline_id: str) -> None:
        """Delete a pipeline definition."""
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        del self._pipelines[pipeline_id]

    async def get_status(self, pipeline_id: str) -> PipelineStatus:
        """Get the status of a running pipeline."""
        if pipeline_id not in self._running_pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        return self._running_pipelines[pipeline_id]

    async def _cleanup_old_statuses(self) -> None:
        """Clean up old pipeline statuses."""
        cutoff = datetime.now() - timedelta(hours=1)
        keys_to_delete = [
            k for k, v in self._running_pipelines.items()
            if datetime.fromisoformat(v.started_at) < cutoff
        ]
        for key in keys_to_delete:
            del self._running_pipelines[key]
