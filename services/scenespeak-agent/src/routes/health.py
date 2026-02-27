"""Health check routes."""
from fastapi import APIRouter
import time

router = APIRouter(tags=["health"])
_start_time = time.time()


@router.get("/live")
async def liveness():
    """Liveness probe - returns OK if service is alive."""
    return "OK"


@router.get("/ready")
async def readiness():
    """Readiness probe - returns ready status and uptime."""
    uptime = time.time() - _start_time
    return {"ready": True, "uptime": uptime}
