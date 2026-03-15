from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/live", response_model=HealthResponse)
async def liveness():
    """Liveness probe - check if service is running."""
    return HealthResponse(
        status="healthy",
        service="simulation-engine",
        version="0.1.0"
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness():
    """Readiness probe - check if service can accept requests."""
    return HealthResponse(
        status="ready",
        service="simulation-engine",
        version="0.1.0"
    )
