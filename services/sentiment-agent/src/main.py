"""
Sentiment Agent - Audience Sentiment Analysis Service

This FastAPI service provides real-time sentiment analysis for audience
feedback using the DistilBERT SST-2 model.

Features:
- Single and batch text sentiment analysis
- Emotion detection (joy, sadness, anger, fear, surprise, disgust)
- Trend analysis over time windows
- Aggregated sentiment statistics
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
from .core.handler import SentimentHandler


# Global handler instance
handler: SentimentHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.

    Handles startup and shutdown events for the sentiment agent service.
    """
    global handler

    print(f"Starting {settings.app_name} v{settings.app_version}...")

    # Initialize handler
    handler = SentimentHandler(settings)
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
    description="Audience sentiment analysis using DistilBERT SST-2",
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
from .routes.analysis import router as analysis_router
from .routes.context import router as context_router

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(context_router, prefix="/api/v1/context", tags=["Context"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> dict:
    """Root endpoint with service information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Audience sentiment analysis using DistilBERT SST-2",
        "model": settings.model_name,
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "sentiment_agent.src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
