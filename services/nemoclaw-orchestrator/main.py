from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("Nemo Claw Orchestrator starting up")
    yield
    logger.info("Nemo Claw Orchestrator shutting down")

app = FastAPI(
    title="Nemo Claw Orchestrator",
    description="Project Chimera orchestration with Nemo Claw security and privacy",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health/live")
async def liveness():
    return {"status": "alive", "service": settings.service_name}

@app.get("/health/ready")
async def readiness():
    return {"status": "ready", "service": settings.service_name}
