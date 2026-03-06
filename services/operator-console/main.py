"""
Operator Console - FastAPI Application

Central monitoring and control dashboard for Project Chimera services.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

from config import get_settings
from models import (
    HealthResponse,
    ReadinessResponse,
    ServiceList,
    ServiceInfo,
    ServiceStatus,
    AllMetrics,
    ServiceMetrics,
    AlertList,
    ServiceControlRequest,
    ServiceControlResponse,
)
from realtime_updates import UpdateManager, UpdateType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Global update manager
update_manager: UpdateManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global update_manager
    logger.info("Operator Console starting up")

    # Initialize update manager
    update_manager = UpdateManager()

    # Start metrics polling
    await update_manager.start_metrics_polling(settings.get_all_service_urls())

    yield

    logger.info("Operator Console shutting down")
    if update_manager:
        await update_manager.stop()


# Create FastAPI app
app = FastAPI(
    title="Operator Console",
    description="Central monitoring and control dashboard for Project Chimera",
    version="1.0.0",
    lifespan=lifespan
)

# Metrics
health_checks = Counter(
    'operator_console_health_checks_total',
    'Total health checks performed',
    ['service', 'status']
)


@app.get("/health/live")
async def liveness():
    """Liveness check endpoint."""
    return HealthResponse(status="alive")


@app.get("/health/ready")
async def readiness():
    """Readiness check endpoint."""
    checks = {}

    # Check if update manager is ready
    checks["update_manager"] = update_manager is not None

    all_healthy = all(checks.values())
    status = "ready" if all_healthy else "not_ready"

    return ReadinessResponse(status=status, checks=checks)


@app.get("/api/v1/services")
async def list_services():
    """
    List all monitored services.

    Returns a list of all services with their current status and URLs.
    """
    service_urls = settings.get_all_service_urls()

    services = []
    up_count = 0
    down_count = 0
    degraded_count = 0

    for name, url in service_urls.items():
        # Get status from update manager
        status = ServiceStatus.UNKNOWN
        if update_manager:
            service_status = update_manager.get_service_status(name)
            if service_status:
                status = service_status.get("status", ServiceStatus.UNKNOWN)

        # Count statuses
        if status == ServiceStatus.UP:
            up_count += 1
        elif status == ServiceStatus.DOWN:
            down_count += 1
        elif status == ServiceStatus.DEGRADED:
            degraded_count += 1

        services.append(ServiceInfo(
            name=name,
            url=url,
            status=status,
            health_check_url=f"{url}/health/live",
            metrics_url=f"{url}/metrics"
        ))

    return ServiceList(
        services=services,
        total=len(services),
        up=up_count,
        down=down_count,
        degraded=degraded_count
    )


@app.get("/api/v1/metrics")
async def get_all_metrics():
    """
    Get metrics for all services.

    Returns current metrics including CPU, memory, request rate, and error rate.
    """
    if not update_manager:
        return AllMetrics(metrics={})

    metrics_data = update_manager.get_all_metrics()

    # Convert to ServiceMetrics objects
    service_metrics = {}
    for service_name, data in metrics_data.items():
        service_metrics[service_name] = ServiceMetrics(
            service_name=service_name,
            cpu_percent=data.get("cpu_percent"),
            memory_mb=data.get("memory_mb"),
            request_rate=data.get("request_rate"),
            error_rate=data.get("error_rate"),
            uptime_seconds=data.get("uptime_seconds")
        )

    return AllMetrics(metrics=service_metrics)


@app.get("/api/v1/alerts")
async def get_alerts():
    """
    Get current alerts.

    Returns all active alerts across all services.
    """
    if not update_manager:
        return AlertList(alerts=[], total=0)

    alerts_data = update_manager.get_all_alerts()

    # Count by severity
    critical = sum(1 for a in alerts_data if a.get("severity") == "critical")
    warning = sum(1 for a in alerts_data if a.get("severity") == "warning")
    info = sum(1 for a in alerts_data if a.get("severity") == "info")

    # Note: This would need proper Alert object conversion from the dict data
    # For now, return the basic structure
    return {
        "alerts": alerts_data,
        "total": len(alerts_data),
        "critical": critical,
        "warning": warning,
        "info": info
    }


@app.post("/api/v1/services/{service_name}/control")
async def control_service(service_name: str, request: ServiceControlRequest):
    """
    Control a service (start, stop, restart, reload).

    This is a placeholder for future service control functionality.
    Currently returns a success response for demonstration purposes.
    """
    # Validate service name
    service_urls = settings.get_all_service_urls()
    if service_name not in service_urls:
        return JSONResponse(
            status_code=404,
            content={"error": f"Service '{service_name}' not found"}
        )

    # Placeholder response
    # In production, this would integrate with Docker or a service mesh
    return ServiceControlResponse(
        service=service_name,
        action=request.action,
        status="success",
        message=f"Service control action '{request.action}' queued for '{service_name}'"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Clients can connect to receive live metrics, alerts, and status updates.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    if update_manager:
        # Register client
        update_manager.add_client(websocket)

        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        finally:
            # Unregister client
            update_manager.remove_client(websocket)
    else:
        await websocket.close()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
