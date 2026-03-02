"""Health check routes."""

from fastapi import APIRouter
import time

from ..models.response import HealthResponse

router = APIRouter()

# Track service start time
_start_time = time.time()


def _get_handler():
    """Get the lighting handler instance."""
    from ....main import handler
    return handler


@router.get("", status_code=200)
async def liveness() -> dict:
    """Liveness probe - service is running."""
    return {"status": "healthy"}


@router.get("/live", status_code=200)
async def liveness_alt() -> dict:
    """Alternative liveness endpoint."""
    return {"status": "healthy"}


@router.get("/ready", status_code=200)
async def readiness() -> dict:
    """Readiness probe - service is ready to handle requests."""
    handler = _get_handler()

    ready = (
        handler is not None
        and handler.sacn.is_active
    )

    return {
        "status": "ready" if ready else "not_ready",
        "sACN_connected": handler.sacn.is_active if handler else False,
        "OSC_connected": handler.osc.client_connected if handler else False
    }


@router.get("/health", status_code=200)
async def health() -> HealthResponse:
    """Detailed health check."""
    handler = _get_handler()

    uptime = time.time() - _start_time

    return HealthResponse(
        status="healthy" if handler and handler.sacn.is_active else "degraded",
        sACN_connected=handler.sacn.is_active if handler else False,
        OSC_connected=handler.osc.client_connected if handler else False,
        uptime_seconds=uptime,
        active_fixtures=len(handler.fixture_manager.get_all_fixtures()) if handler else 0,
        active_presets=len(handler.fixture_manager.get_all_presets()) if handler else 0
    )


@router.get("/health/detailed", status_code=200)
async def health_detailed() -> dict:
    """Detailed health information with subsystem status."""
    handler = _get_handler()

    uptime = time.time() - _start_time

    status_info = {
        "status": "healthy",
        "uptime_seconds": uptime,
        "subsystems": {
            "sACN": {
                "status": "up" if handler and handler.sacn.is_active else "down",
                "universe": handler.sacn.universe if handler else None,
                "priority": handler.sacn.priority if handler else None
            },
            "OSC": {
                "status": "up" if handler and handler.osc.client_connected else "down",
                "client_connected": handler.osc.client_connected if handler else False,
                "server_running": handler.osc.server_running if handler else False
            },
            "fixtures": {
                "status": "up",
                "count": len(handler.fixture_manager.get_all_fixtures()) if handler else 0
            },
            "presets": {
                "status": "up",
                "count": len(handler.fixture_manager.get_all_presets()) if handler else 0,
                "active": handler.fixture_manager.get_active_preset() if handler else None
            },
            "cues": {
                "status": "up",
                "current": handler.cue_executor.get_current_cue() if handler else None
            }
        }
    }

    # Overall status
    all_up = all(s["status"] == "up" for s in status_info["subsystems"].values())
    status_info["status"] = "healthy" if all_up else "degraded"

    return status_info
