"""Health check endpoints for BSL Text2Gloss Agent."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
@router.get("/live")
async def liveness():
    """Liveness check - returns healthy if service is running."""
    return {
        "status": "healthy",
        "service": "bsl-text2gloss-agent",
        "check": "live"
    }


@router.get("/ready")
async def readiness():
    """Readiness check - returns ready if service can handle requests."""
    from ....main import handler

    is_ready = handler is not None and handler.translator is not None

    return {
        "status": "ready" if is_ready else "not_ready",
        "service": "bsl-text2gloss-agent",
        "check": "ready",
        "model_loaded": is_ready
    }
