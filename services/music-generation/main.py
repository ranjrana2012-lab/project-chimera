"""
Music Generation Service - Main FastAPI Application
Project Chimera v0.5.0
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .config import settings
from .model_manager import ModelManager
from .metrics import (
    request_counter,
    model_load_time,
    active_generations
)
from .tracing import (
    setup_tracing,
    instrument_fastapi,
    get_tracer,
    trace_model_loading,
    shutdown_tracing
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize OpenTelemetry tracing
try:
    tracer = setup_tracing(
        service_name=settings.service_name,
        service_version="0.5.0",
        otlp_endpoint=settings.otlp_endpoint,
        environment=settings.environment
    )
    logger.info("Tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize tracing: {e}")
    tracer = None


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
        # Instrument FastAPI with OpenTelemetry
        instrument_fastapi(app)

        # Load models with tracing
        with trace_model_loading("model_manager", settings.model_path):
            model_manager = ModelManager(model_path=settings.model_path)

        logger.info(f"Model manager initialized with path: {settings.model_path}")
        logger.info("Music Generation Service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model manager: {e}")
        model_load_time.labels(model="model_manager", status="error").set(0)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Music Generation Service...")
    if model_manager:
        model_manager.cleanup()
    shutdown_tracing()
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


# Include routers (when they are created, they will be included here)
# app.include_router(models_router, prefix="/api/v1", tags=["models"])
# app.include_router(generate_router, prefix="/api/v1", tags=["generate"])


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
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )
