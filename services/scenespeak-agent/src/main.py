"""SceneSpeak Agent main application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import make_asgi_app
import redis.asyncio as redis

from .routes import generation, health
from .core.llm_engine import LLMEngine
from .core.caches import ResponseCache

_engine = None
_cache = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Initializes the LLM engine and cache on startup,
    and cleans up resources on shutdown.
    """
    global _engine, _cache

    # Initialize LLM Engine
    _engine = LLMEngine()
    await _engine.load()
    generation.set_engine(_engine)

    # Initialize ResponseCache
    _cache = ResponseCache(
        host="localhost",
        port=6379,
        db=0,
        password=None,
    )
    await _cache.connect()
    generation.set_cache(_cache)

    yield

    # Shutdown - clean up resources
    if _cache:
        await _cache.close()


app = FastAPI(title="SceneSpeak Agent", version="1.0.0", lifespan=lifespan)
app.include_router(generation.router)
app.include_router(health.router, prefix="/health")
app.mount("/metrics", make_asgi_app())


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {"service": "scenespeak-agent", "version": "1.0.0"}
