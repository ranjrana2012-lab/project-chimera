# ============================================================================
# Security Middleware (Environment-based CORS, Security Headers, Rate Limiting)
# ============================================================================
import sys
import os

# Add shared module to path for security middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

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

# Global simulation runner instance
runner = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.service_name} v0.1.0")
    logger.info(f"Environment: {settings.environment}")

    # Initialize simulation runner
    from simulation.runner import SimulationRunner
    from simulation.llm_router import TieredLLMRouter
    from agents.persona import PersonaGenerator

    global runner
    persona_generator = PersonaGenerator(seed=42)
    runner = SimulationRunner(persona_generator, TieredLLMRouter())

    logger.info("Simulation runner initialized")

    yield

    # Shutdown
    logger.info("Shutting down simulation engine")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Chimera Simulation Engine",
    description="Multi-agent swarm intelligence simulation platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - replaced with security middleware
from shared.middleware import (
    SecurityHeadersMiddleware,
    configure_cors,
    setup_rate_limit_error_handler,
)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers (will be created in later tasks)
from api import health, graph, simulation, agents

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development"
    )
