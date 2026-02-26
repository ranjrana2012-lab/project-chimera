from .health import router as health_router
from .alerts import router as alerts_router
from .approvals import router as approvals_router

__all__ = ["health_router", "alerts_router", "approvals_router"]
