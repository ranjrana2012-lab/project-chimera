"""OpenClaw Orchestrator main application."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from .routes import orchestration, skills, health
from .core.skill_registry import SkillRegistry
from .core.gpu_scheduler import GPUScheduler
from .core.router import Router
from .core.kafka_producer import KafkaProducer
import redis.asyncio as redis

# Global instances
registry = SkillRegistry
gpu_scheduler = GPUScheduler()
kafka_producer = KafkaProducer("kafka.shared.svc.cluster.local:9092")

# Global router instance for dependency injection
_router = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    await kafka_producer.start()

    # Initialize router with dependencies
    global _router
    _router = Router(
        registry=registry,
        gpu_scheduler=gpu_scheduler,
        redis_client=redis.Redis(host="redis.shared.svc.cluster.local", port=6379)
    )
    await _router.__aenter__()

    yield

    # Shutdown
    await _router.__aexit__()
    await kafka_producer.stop()

app = FastAPI(
    title="OpenClaw Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(orchestration.router)
app.include_router(skills.router)
app.include_router(health.router)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "openclaw-orchestrator",
        "version": "1.0.0",
        "status": "running"
    }
