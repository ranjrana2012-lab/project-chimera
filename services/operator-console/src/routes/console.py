"""Console status and control endpoints."""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from src.core.approval_handler import ApprovalHandler
from src.core.event_aggregator import EventAggregator
from src.core.override_manager import OverrideManager
from src.models.request import OverrideRequest
from src.models.response import ConsoleStatus, ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/console", tags=["console"])


# Dependency injection would happen in main.py
# For now, we'll use these as module-level variables
_aggregator: EventAggregator | None = None
_approval_handler: ApprovalHandler | None = None
_override_manager: OverrideManager | None = None
_start_time: datetime | None = None


def init_console(
    aggregator: EventAggregator,
    approval_handler: ApprovalHandler,
    override_manager: OverrideManager,
) -> None:
    """Initialize console routes with dependencies.

    Args:
        aggregator: Event aggregator instance
        approval_handler: Approval handler instance
        override_manager: Override manager instance
    """
    global _aggregator, _approval_handler, _override_manager, _start_time
    _aggregator = aggregator
    _approval_handler = approval_handler
    _override_manager = override_manager
    _start_time = datetime.now()


@router.get("/status", response_model=ConsoleStatus)
async def get_console_status() -> ConsoleStatus:
    """Get overall console status.

    Returns:
        Console status with service health, pending approvals, and alerts
    """
    if not _start_time:
        raise HTTPException(status_code=503, detail="Console not initialized")

    uptime = (datetime.now() - _start_time).total_seconds()

    # Get service statuses from event aggregator
    service_health: Dict[str, ServiceHealth] = {}

    if _aggregator:
        # In a real implementation, we'd track service health from events
        # For now, return minimal data
        service_health["script-agent"] = ServiceHealth(
            service_name="script-agent",
            status=ServiceStatus.HEALTHY,
            last_seen=datetime.now(),
            uptime_seconds=uptime,
            error_count=0,
        )
        service_health["lighting-agent"] = ServiceHealth(
            service_name="lighting-agent",
            status=ServiceStatus.HEALTHY,
            last_seen=datetime.now(),
            uptime_seconds=uptime,
            error_count=0,
        )
        service_health["audio-agent"] = ServiceHealth(
            service_name="audio-agent",
            status=ServiceStatus.HEALTHY,
            last_seen=datetime.now(),
            uptime_seconds=uptime,
            error_count=0,
        )
        service_health["stage-manager"] = ServiceHealth(
            service_name="stage-manager",
            status=ServiceStatus.HEALTHY,
            last_seen=datetime.now(),
            uptime_seconds=uptime,
            error_count=0,
        )

    # Get pending approval count
    pending_approvals = 0
    if _approval_handler:
        pending_approvals = len(_approval_handler.get_pending_requests())

    # Get active overrides
    active_overrides = []
    if _override_manager:
        active_overrides = [
            o["override_id"] for o in _override_manager.get_active_overrides()
        ]

    # Count active alerts from events
    active_alerts = 0
    if _aggregator:
        for event in _aggregator.get_recent_events():
            if event.data.get("alert_active"):
                active_alerts += 1

    return ConsoleStatus(
        services=service_health,
        pending_approvals=pending_approvals,
        active_alerts=active_alerts,
        active_overrides=active_overrides,
        system_mode="automatic" if len(active_overrides) == 0 else "manual",
        console_uptime=uptime,
    )


@router.get("/services")
async def get_services() -> Dict[str, dict]:
    """Get status of all services.

    Returns:
        Dictionary of service statuses
    """
    status = await get_console_status()
    return {
        name: {
            "status": svc.status.value,
            "last_seen": svc.last_seen.isoformat(),
            "uptime_seconds": svc.uptime_seconds,
            "error_count": svc.error_count,
            "metrics": svc.metrics,
        }
        for name, svc in status.services.items()
    }


@router.get("/mode")
async def get_system_mode() -> dict:
    """Get current system mode.

    Returns:
        System mode and active overrides
    """
    active_overrides = []
    if _override_manager:
        active_overrides = _override_manager.get_active_overrides()

    return {
        "mode": "manual" if active_overrides else "automatic",
        "active_overrides": active_overrides,
        "can_switch_to_automatic": len(active_overrides) == 0,
    }


@router.post("/trigger-override")
async def trigger_override(request: OverrideRequest, operator: str = "unknown") -> dict:
    """Trigger a manual override.

    Args:
        request: Override request
        operator: Operator initiating override

    Returns:
        Override ID and status
    """
    if not _override_manager:
        raise HTTPException(status_code=503, detail="Override manager not available")

    try:
        override_id = await _override_manager.trigger_override(request, operator)

        return {
            "status": "success",
            "override_id": override_id,
            "message": f"Override {request.override_type.value} triggered on {request.target_service}",
        }

    except Exception as e:
        logger.error(f"Error triggering override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/release-override/{override_id}")
async def release_override(override_id: str, operator: str = "unknown") -> dict:
    """Release an active override.

    Args:
        override_id: Override to release
        operator: Operator releasing override

    Returns:
        Status message
    """
    if not _override_manager:
        raise HTTPException(status_code=503, detail="Override manager not available")

    success = await _override_manager.release_override(override_id, operator)

    if not success:
        raise HTTPException(status_code=404, detail=f"Override not found: {override_id}")

    return {
        "status": "success",
        "message": f"Override {override_id} released",
    }


@router.post("/emergency-stop")
async def emergency_stop(reason: str, operator: str = "unknown") -> dict:
    """Trigger emergency stop on all services.

    Args:
        reason: Reason for emergency stop
        operator: Operator initiating stop

    Returns:
        Override ID
    """
    if not _override_manager:
        raise HTTPException(status_code=503, detail="Override manager not available")

    override_id = await _override_manager.emergency_stop_all(operator, reason)

    return {
        "status": "success",
        "override_id": override_id,
        "message": "Emergency stop triggered on all services",
    }


@router.get("/stats")
async def get_console_stats() -> dict:
    """Get console statistics.

    Returns:
        Statistics from all components
    """
    stats = {
        "uptime_seconds": (datetime.now() - _start_time).total_seconds() if _start_time else 0,
    }

    if _aggregator:
        stats["events"] = _aggregator.get_stats()

    if _approval_handler:
        stats["approvals"] = _approval_handler.get_stats()

    if _override_manager:
        stats["overrides"] = _override_manager.get_stats()

    return stats
