"""Health check routes for Safety Filter service."""

from fastapi import APIRouter
from ....main import handler


router = APIRouter()


@router.get("")
@router.get("/live")
async def liveness() -> dict:
    """Liveness probe - check if service is running.

    Returns:
        Basic health status
    """
    return {"status": "healthy"}


@router.get("/ready")
async def readiness() -> dict:
    """Readiness probe - check if service is ready to handle requests.

    Returns:
        Readiness status
    """
    return {"status": "ready"}


@router.get("/detailed")
async def detailed_health() -> dict:
    """Detailed health check with component status.

    Returns:
        Detailed health status for all components
    """
    health = handler.get_health_status()
    return {
        "status": health["status"],
        "version": "0.1.0",
        "uptime_seconds": health["uptime_seconds"],
        "components": health["components"]
    }
