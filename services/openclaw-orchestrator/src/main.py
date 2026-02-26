"""
OpenClaw Orchestrator - FastAPI Entry Point
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import make_asgi_app
from pydantic import ValidationError

from .config import settings, Settings
from .core.health import HealthChecker
from .core.skill_registry import SkillRegistry
from .core.pipeline_executor import PipelineExecutor
from .core.metrics import metrics_registry


# Global state
skill_registry: SkillRegistry | None = None
pipeline_executor: PipelineExecutor | None = None
health_checker: HealthChecker | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    global skill_registry, pipeline_executor, health_checker

    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}...")

    # Initialize components
    skill_registry = SkillRegistry(settings.skills_path)
    await skill_registry.load_skills()

    pipeline_executor = PipelineExecutor(
        skill_registry=skill_registry,
        settings=settings
    )

    health_checker = HealthChecker(
        settings=settings,
        skill_registry=skill_registry
    )

    # Setup OpenTelemetry
    if settings.tracing_enabled:
        tracer_provider = TracerProvider()
        trace.set_tracer_provider(tracer_provider)
        # Add span processor here (e.g., Jaeger)
        print("OpenTelemetry tracing enabled")

    print(f"{settings.app_name} started successfully")
    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    await skill_registry.close()
    print(f"{settings.app_name} shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="OpenClaw Orchestrator - Central Control Plane for Project Chimera",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

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
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# Routes
from .routes.health import router as health_router
from .routes.orchestration import router as orchestration_router
from .routes.skills import router as skills_router
from .routes.pipelines import router as pipelines_router

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(orchestration_router, prefix="/api/v1/orchestration", tags=["Orchestration"])
app.include_router(skills_router, prefix="/api/v1/skills", tags=["Skills"])
app.include_router(pipelines_router, prefix="/api/v1/pipelines", tags=["Pipelines"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "OpenClaw Orchestrator - Central Control Plane for Project Chimera",
        "docs": "/docs",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "openclaw_orchestrator.src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
