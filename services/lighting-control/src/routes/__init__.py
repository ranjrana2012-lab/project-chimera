"""Routes for Lighting Control service."""

from .health import router as health_router
from .lighting import router as lighting_router
from .cues import router as cues_router
from .presets import router as presets_router

__all__ = [
    "health_router",
    "lighting_router",
    "cues_router",
    "presets_router"
]
