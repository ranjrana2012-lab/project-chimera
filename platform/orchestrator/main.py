"""Test Orchestrator FastAPI application."""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from orchestrator.routes import router
from shared.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Startup
    # Don't create tables in test mode
    import os
    if os.getenv("TESTING") != "true":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await engine.dispose()


orchestrator_app = FastAPI(
    title="Chimera Test Orchestrator",
    description="Orchestrates test execution for Project Chimera",
    version="0.1.0",
    lifespan=lifespan
)

orchestrator_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

orchestrator_app.include_router(router)


@orchestrator_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "orchestrator"}
