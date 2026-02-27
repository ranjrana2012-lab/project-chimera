"""
Safety Filter Service - Content Moderation for Project Chimera

This FastAPI service provides real-time content safety filtering using
multi-layer analysis including word list filtering, ML-based classification,
and configurable policy evaluation.

Features:
- Word list-based profanity and offensive content filtering
- ML-based BERT safety classification
- Configurable safety policies and strictness levels
- Kafka-based audit logging
- Content flagging with detailed explanations
- Batch processing support
- OpenClaw skill invocation support
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from .config import settings
from .core.handler import SafetyHandler


# Global handler instance
handler: SafetyHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.

    Handles startup and shutdown events for the safety filter service.
    """
    global handler

    print(f"Starting {settings.app_name} v{settings.app_version}...")

    # Initialize handler
    handler = SafetyHandler(settings)
    await handler.initialize()

    print(f"{settings.app_name} started successfully on port {settings.port}")
    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    await handler.close()
    print(f"{settings.app_name} shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Content moderation and safety filtering using word lists and ML",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# Routes
from .routes.health import router as health_router
from .routes.safety import router as safety_router
from .routes.policies import router as policies_router

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(safety_router, prefix="/api/v1", tags=["Safety"])
app.include_router(policies_router, prefix="/api/v1/policies", tags=["Policies"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> dict:
    """Root endpoint with service information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Content moderation and safety filtering",
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health",
        "api": "/api/v1"
    }


@app.get("/stats")
async def statistics() -> dict:
    """Get operational statistics."""
    if handler is None:
        return {"error": "Handler not initialized"}

    stats = handler.get_statistics()
    return {
        "uptime_seconds": stats["uptime_seconds"],
        "audit": stats["audit_stats"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "safety_filter.src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
