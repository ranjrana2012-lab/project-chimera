from .health import router as health_router
from .safety import router as safety_router

__all__ = ["health_router", "safety_router"]
