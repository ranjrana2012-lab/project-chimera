"""Health check routes"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
@router.get("/live")
async def liveness():
    """Liveness probe."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness():
    """Readiness probe."""
    from ....main import handler
    if handler:
        health = await handler.health_check()
        return health
    return {"status": "initializing"}
