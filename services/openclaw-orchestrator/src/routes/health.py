"""Health check routes."""
from fastapi import APIRouter
from datetime import datetime
import time

router = APIRouter(tags=["health"])

_start_time = time.time()

@router.get("/health/live")
async def liveness():
    """Liveness probe."""
    return "OK"

@router.get("/health/ready")
async def readiness():
    """Readiness probe."""
    uptime = time.time() - _start_time
    return {
        "ready": True,
        "uptime": uptime,
        "dependencies": {
            "redis": "ok",  # TODO: Check Redis
            "kafka": "ok"   # TODO: Check Kafka
        }
    }
