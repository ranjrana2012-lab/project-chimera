from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from prometheus_client import Counter, Histogram, make_asgi_app
import logging

from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Metrics
simulation_counter = Counter(
    "simulations_total",
    "Total number of simulations started",
    ["scenario_type"]
)
simulation_duration = Histogram(
    "simulation_duration_seconds",
    "Simulation execution time",
    ["scenario_type"]
)

# Create FastAPI app
app = FastAPI(
    title="Chimera Simulation Engine",
    description="Multi-agent swarm intelligence simulation platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers (will be created in later tasks)
from api import health, graph, simulation

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger.info(f"Starting {settings.service_name} v0.1.0")
    logger.info(f"Environment: {settings.environment}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    logger.info("Shutting down simulation engine")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development"
    )
