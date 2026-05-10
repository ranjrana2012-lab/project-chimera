# main.py
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service Template",
    description="Reusable service template for Project Chimera service experiments",
    version="1.0.0"
)


@app.get("/health/live")
async def liveness():
    """Basic liveness check - is the process running?"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness check - can we handle requests?"""
    # Override in implementations to check dependencies
    return {"status": "ready", "checks": {}}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
async def startup_event():
    logger.info("Service starting up")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Service shutting down")
