"""Health check routes for Captioning Agent"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
@router.get("/live")
async def liveness():
    """Liveness probe - checks if service is running."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness():
    """Readiness probe - checks if service is ready to handle requests."""
    from ....main import handler

    if handler:
        health = await handler.health_check()
        return health
    return {"status": "initializing"}
