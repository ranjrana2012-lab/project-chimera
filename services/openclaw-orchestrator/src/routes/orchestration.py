"""Orchestration routes for OpenClaw Orchestrator"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...models.requests import SkillInvokeRequest
from ...models.responses import SkillInvokeResponse
from ...core.orchestrator import Orchestrator
from ...config import Settings

router = APIRouter()


async def get_orchestrator() -> Orchestrator:
    """Dependency to get orchestrator instance."""
    from ....main import pipeline_executor
    # Create orchestrator from pipeline executor
    return Orchestrator(pipeline_executor=pipeline_executor)  # type: ignore


@router.post("/invoke", response_model=SkillInvokeResponse)
async def invoke_skill(
    request: SkillInvokeRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
) -> SkillInvokeResponse:
    """
    Invoke a single skill.

    This endpoint invokes a single skill with the provided input data.
    The skill is executed and the result is returned.
    """
    try:
        response = await orchestrator.invoke_skill(
            skill_name=request.skill_name,
            input_data=request.input,
            config=request.config,
            timeout_ms=request.timeout_ms,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill not found: {request.skill_name}"
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Skill invocation timed out: {request.skill_name}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill invocation failed: {str(e)}"
        )
