"""Dashboard FastAPI application."""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dashboard.routes import router as dashboard_router
from shared.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Startup
    import os
    if os.getenv("TESTING") != "true":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await engine.dispose()


dashboard_app = FastAPI(
    title="Chimera Quality Dashboard",
    description="Real-time testing dashboard for Project Chimera",
    version="0.1.0",
    lifespan=lifespan
)

dashboard_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

dashboard_app.include_router(dashboard_router)


@dashboard_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dashboard"}
