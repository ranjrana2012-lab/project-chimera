"""Lighting Control Service - sACN/OSC stage lighting control."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from .config import settings
from .core.handler import LightingHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global handler instance
handler: LightingHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    global handler

    logger.info(f"Starting {settings.app_name} v{settings.app_version}...")

    # Initialize handler
    handler = LightingHandler(settings)
    await handler.initialize()

    logger.info(f"{settings.app_name} started successfully")
    yield

    logger.info(f"Shutting down {settings.app_name}...")
    if handler:
        await handler.close()
    logger.info(f"{settings.app_name} shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="sACN/OSC stage lighting control for Project Chimera",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
from .routes.health import router as health_router
from .routes.lighting import router as lighting_router
from .routes.cues import router as cues_router
from .routes.presets import router as presets_router

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(lighting_router, tags=["Lighting"])
app.include_router(cues_router, tags=["Cues"])
app.include_router(presets_router, tags=["Presets"])

# Mount Prometheus metrics
app.mount("/metrics", make_asgi_app())


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "sACN/OSC stage lighting control",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "metrics": "/metrics",
            "lighting": "/v1/lighting/*",
            "cues": "/v1/cues/*",
            "presets": "/v1/presets/*"
        }
    }


@app.get("/info")
async def info():
    """Detailed service information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "config": {
            "sACN": {
                "universe": settings.sacn_universe,
                "priority": settings.sacn_priority,
                "enabled": settings.sacn_enabled
            },
            "OSC": {
                "server_port": settings.osc_server_port,
                "enabled": settings.osc_enabled
            },
            "fixtures": settings.default_fixtures
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
