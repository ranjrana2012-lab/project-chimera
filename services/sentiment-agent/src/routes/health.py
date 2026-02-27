"""Health check routes for Sentiment Agent."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
@router.get("/live")
async def liveness():
    """Liveness probe - returns if service is running."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness():
    """Readiness probe - returns if service is ready to handle requests."""
    from ....main import handler

    if handler:
        health = await handler.health_check()
        return {
            "status": "ready" if health.get("status") == "healthy" else "initializing",
            **health
        }
    return {"status": "initializing", "model_loaded": False}
