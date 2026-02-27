"""Health check endpoints for Operator Console."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.core.approval_handler import ApprovalHandler
from src.core.event_aggregator import EventAggregator
from src.core.override_manager import OverrideManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

# Module-level dependencies
_aggregator: EventAggregator | None = None
_approval_handler: ApprovalHandler | None = None
_override_manager: OverrideManager | None = None


def init_health(
    aggregator: EventAggregator,
    approval_handler: ApprovalHandler,
    override_manager: OverrideManager,
) -> None:
    """Initialize health routes with dependencies.

    Args:
        aggregator: Event aggregator instance
        approval_handler: Approval handler instance
        override_manager: Override manager instance
    """
    global _aggregator, _approval_handler, _override_manager
    _aggregator = aggregator
    _approval_handler = approval_handler
    _override_manager = override_manager


@router.get("")
@router.get("/live")
async def liveness() -> dict:
    """Liveness probe - returns if service is running.

    Returns:
        Liveness status
    """
    return {
        "status": "healthy",
        "service": "operator-console",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/ready")
async def readiness() -> dict:
    """Readiness probe - returns if service is ready to handle requests.

    Returns:
        Readiness status
    """
    checks = {
        "aggregator": _aggregator is not None and _aggregator.running,
        "approval_handler": _approval_handler is not None and _approval_handler.running,
        "override_manager": _override_manager is not None and _override_manager.running,
    }

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/detailed")
async def detailed_health() -> dict:
    """Detailed health check with component status.

    Returns:
        Detailed health information
    """
    components = {}

    if _aggregator:
        components["aggregator"] = {
            "status": "running" if _aggregator.running else "stopped",
            "topics": _aggregator.topics,
            "event_count": len(_aggregator.events),
            "subscriber_count": len(_aggregator._subscribers),
        }

    if _approval_handler:
        components["approval_handler"] = {
            "status": "running" if _approval_handler.running else "stopped",
            "pending_requests": len(_approval_handler.pending_requests),
            "history_size": len(_approval_handler.approval_history),
        }

    if _override_manager:
        components["override_manager"] = {
            "status": "running" if _override_manager.running else "stopped",
            "active_overrides": len(_override_manager.active_overrides),
            "history_size": len(_override_manager.override_history),
        }

    all_healthy = all(
        c.get("status") == "running" for c in components.values()
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "operator-console",
        "components": components,
        "timestamp": datetime.now().isoformat(),
    }
