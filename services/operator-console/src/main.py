"""Main application for Operator Console service."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.core.approval_handler import ApprovalHandler
from src.core.event_aggregator import EventAggregator
from src.core.override_manager import OverrideManager
from src.routes import console, events, approvals, health

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize core components (will be set in lifespan)
aggregator: EventAggregator | None = None
approval_handler: ApprovalHandler | None = None
override_manager: OverrideManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application lifecycle."""
    global aggregator, approval_handler, override_manager

    logger.info(f"Starting {settings.app_name}...")

    try:
        # Initialize core components
        aggregator = EventAggregator(
            kafka_brokers="localhost:9092",
            topics=["chimera.events", "chimera.approvals", "chimera.overrides", "chimera.health"],
            max_events=1000,
        )

        approval_handler = ApprovalHandler(
            kafka_brokers="localhost:9092",
            request_topic="chimera.approvals",
            response_topic="chimera.approvals",
            default_expiry_minutes=30,
        )

        override_manager = OverrideManager(
            kafka_brokers="localhost:9092",
            override_topic="chimera.overrides",
        )

        # Start components
        await aggregator.start()
        await approval_handler.start()
        await override_manager.start()

        # Initialize routes with dependencies
        console.init_console(aggregator, approval_handler, override_manager)
        events.init_events(aggregator)
        approvals.init_approvals(approval_handler)
        health.init_health(aggregator, approval_handler, override_manager)

        logger.info(f"{settings.app_name} started successfully")
        yield

    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise

    finally:
        logger.info(f"Shutting down {settings.app_name}...")

        if aggregator:
            await aggregator.stop()
        if approval_handler:
            await approval_handler.stop()
        if override_manager:
            await override_manager.stop()

        logger.info(f"{settings.app_name} shut down successfully")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Human oversight and manual override console for Project Chimera",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from src.routes.console import router as console_router
from src.routes.events import router as events_router
from src.routes.approvals import router as approvals_router
from src.routes.health import router as health_router

app.include_router(console_router)
app.include_router(events_router)
app.include_router(approvals_router)
app.include_router(health_router)

# Mount static files for dashboard UI
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        with open(index_path) as f:
            return f.read()
    return """
    <html>
        <head><title>Operator Console</title></head>
        <body>
            <h1>Operator Console</h1>
            <p>Dashboard UI not found. Please ensure static files are available.</p>
            <p><a href="/docs">API Documentation</a></p>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Simple health check."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
