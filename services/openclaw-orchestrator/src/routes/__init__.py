"""API routes for OpenClaw Orchestrator"""

from .health import router as health_router
from .orchestration import router as orchestration_router
from .skills import router as skills_router

__all__ = [
    "health_router",
    "orchestration_router",
    "skills_router",
]
