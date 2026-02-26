"""Health check routes for OpenClaw Orchestrator"""

import time
from typing import Dict

from fastapi import APIRouter, Depends, status

from ...models.responses import HealthResponse
from ...core.health import HealthChecker

router = APIRouter()


async def get_health_checker() -> HealthChecker:
    """Dependency to get health checker instance."""
    # In a real implementation, this would return a singleton instance
    from ....main import health_checker
    return health_checker  # type: ignore


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@router.get("/live", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def liveness(
    health_checker: HealthChecker = Depends(get_health_checker)
) -> HealthResponse:
    """Liveness probe - checks if the service is running."""
    return await health_checker.check_liveness()


@router.get("/ready", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def readiness(
    health_checker: HealthChecker = Depends(get_health_checker)
) -> HealthResponse:
    """Readiness probe - checks if the service is ready to accept traffic."""
    return await health_checker.check_readiness()


@router.get("/startup", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def startup(
    health_checker: HealthChecker = Depends(get_health_checker)
) -> HealthResponse:
    """Startup probe - checks if the service has started successfully."""
    return await health_checker.check_startup()
