"""Operator Console - Human oversight and approval interface"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .config import settings
from .core.handler import OperatorHandler


handler: OperatorHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global handler
    print(f"Starting {settings.app_name}...")
    handler = OperatorHandler(settings)
    await handler.initialize()
    print(f"{settings.app_name} started")
    yield
    print(f"Shutting down {settings.app_name}...")
    await handler.close()


app = FastAPI(
    title=settings.app_name,
    description="Human oversight and approval interface",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes.health import router as health_router
from .routes.alerts import router as alerts_router
from .routes.approvals import router as approvals_router

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(alerts_router, prefix="/api/v1", tags=["Alerts"])
app.include_router(approvals_router, prefix="/api/v1", tags=["Approvals"])
app.mount("/metrics", make_asgi_app())


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": settings.app_version}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
