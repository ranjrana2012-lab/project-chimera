"""Visual Core Service - Main FastAPI Application.

LTX-2 video generation integration hub for Project Chimera.
Serves as the central service for AI-powered video generation.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config import settings
from tracing import setup_tracing, instrument_fastapi, shutdown_tracing
from metrics import request_latency


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
        service_version="1.0.0",
        otlp_endpoint=settings.otlp_endpoint,
        environment="production"
    )
    logger.info("Tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize tracing: {e}")
    tracer = None


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Visual Core Service...")
    try:
        # Instrument FastAPI with OpenTelemetry
        instrument_fastapi(app)

        logger.info("Visual Core Service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Visual Core Service...")
    shutdown_tracing()
    logger.info("Visual Core Service stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Visual Core Service",
    description="LTX-2 video generation integration hub for Project Chimera",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Metrics Endpoints
# ============================================================================

@app.get("/health/live", response_model=Dict[str, str])
async def liveness_probe():
    """Liveness probe endpoint."""
    return {"status": "alive"}


@app.get("/health/ready", response_model=Dict[str, object])
async def readiness_probe():
    """Readiness probe endpoint."""
    dependencies = {}
    all_ready = True

    # Check LTX API connectivity
    try:
        # TODO: Add actual LTX API health check
        dependencies["ltx_api"] = True
    except Exception as e:
        dependencies["ltx_api"] = False
        all_ready = False

    return {
        "status": "ready" if all_ready else "not_ready",
        "service": settings.service_name,
        "dependencies": dependencies
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Video Generation Endpoints
# ============================================================================

@app.post("/api/v1/generate/text")
async def generate_video_from_text():
    """
    Generate video from text prompt.

    This endpoint is a placeholder and will be implemented in Task 2.
    """
    with track_request_latency("generate_text"):
        raise HTTPException(
            status_code=501,
            detail="Text-to-video generation not yet implemented. See Task 2 of the integration plan."
        )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
