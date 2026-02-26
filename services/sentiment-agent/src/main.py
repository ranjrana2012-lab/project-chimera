"""
Sentiment Agent - Audience sentiment analysis
FastAPI entry point
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from .config import settings
from .core.handler import SentimentHandler


handler: SentimentHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global handler
    print(f"Starting {settings.app_name}...")
    handler = SentimentHandler(settings)
    await handler.initialize()
    print(f"{settings.app_name} started")
    yield
    print(f"Shutting down {settings.app_name}...")
    await handler.close()


app = FastAPI(
    title=settings.app_name,
    description="Audience sentiment analysis from social media",
    version=settings.app_version,
    lifespan=lifespan,
)

from .routes.health import router as health_router
from .routes.sentiment import router as sentiment_router

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(sentiment_router, prefix="/api/v1", tags=["Sentiment"])
app.mount("/metrics", make_asgi_app())


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": settings.app_version}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
