"""
Music Generation Service - Main FastAPI Application
Project Chimera v0.5.0
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

from .api.models import router as models_router
from .api.generate import router as generate_router
from .config import settings
from .model_manager import ModelManager


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Prometheus metrics
request_counter = Counter(
    'music_generation_requests_total',
    'Total number of generation requests',
    ['model', 'status']
)
model_load_time = Gauge(
    'music_generation_model_load_seconds',
    'Time taken to load models',
    ['model']
)
active_generations = Gauge(
    'music_generation_active',
    'Number of active generation tasks'
)


# Global model manager
model_manager: ModelManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Music Generation Service...")
    global model_manager

    try:
        model_manager = ModelManager(model_path=settings.model_path)
        logger.info(f"Model manager initialized with path: {settings.model_path}")
        logger.info("Music Generation Service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model manager: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Music Generation Service...")
    if model_manager:
        model_manager.cleanup()
    logger.info("Music Generation Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Music Generation Service",
    description="AI-powered music generation service for Project Chimera",
    version="0.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# Include routers
app.include_router(models_router, prefix="/api/v1", tags=["models"])
app.include_router(generate_router, prefix="/api/v1", tags=["generate"])


@app.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Liveness probe endpoint.
    Returns service status indicating if the service is running.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_probe() -> Dict[str, str]:
    """
    Readiness probe endpoint.
    Returns service status indicating if the service is ready to handle requests.
    """
    if model_manager is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
