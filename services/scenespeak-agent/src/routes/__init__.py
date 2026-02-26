"""API routes for SceneSpeak Agent"""

from .health import router as health_router
from .dialogue import router as dialogue_router

__all__ = ["health_router", "dialogue_router"]
