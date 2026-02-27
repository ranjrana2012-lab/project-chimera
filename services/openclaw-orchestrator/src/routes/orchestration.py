"""Orchestration API routes."""
from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram

from ..models.request import OrchestrationRequest
from ..models.response import OrchestrationResponse
from ..core.router import Router
from ..core.skill_registry import SkillRegistry
from ..core.gpu_scheduler import GPUScheduler

router = APIRouter(prefix="/v1", tags=["orchestration"])

# Metrics
orchestration_counter = Counter(
    'orchestration_requests_total',
    'Total orchestration requests',
    ['status']
)
orchestration_duration = Histogram(
    'orchestration_duration_seconds',
    'Orchestration duration'
)

# Dependencies (simplified for now)
_router = None

async def get_router():
    global _router
    return _router

@router.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(
    request: OrchestrationRequest,
    router: Router = Depends(get_router)
):
    """Execute orchestration through specified skills."""
    with orchestration_duration.time():
        try:
            response = await router.orchestrate(request)

            if response.status.value == "success":
                orchestration_counter.labels(status="success").inc()
            else:
                orchestration_counter.labels(status="error").inc()

            return response

        except Exception as e:
            orchestration_counter.labels(status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))
