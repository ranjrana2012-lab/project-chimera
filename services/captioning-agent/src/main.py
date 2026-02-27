"""
Captioning Agent - Speech-to-text with accessibility
FastAPI entry point
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from .config import settings
from .core.handler import CaptioningHandler


# Global state
handler: CaptioningHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    global handler

    print(f"Starting {settings.app_name} v{settings.app_version}...")

    # Initialize handler
    handler = CaptioningHandler(settings)
    await handler.initialize()

    print(f"{settings.app_name} started successfully")
    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    if handler:
        await handler.close()
    print(f"{settings.app_name} shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Real-time speech-to-text transcription using OpenAI Whisper",
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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# Routes
from .routes.health import router as health_router
from .routes.captioning import router as captioning_router

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(captioning_router, prefix="/api/v1", tags=["Captioning"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Real-time speech-to-text transcription using OpenAI Whisper",
        "docs": "/docs",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "captioning_agent.src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
