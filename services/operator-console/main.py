"""
Operator Console - FastAPI Application

Central monitoring and control dashboard for Project Chimera services.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient, ConnectError
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

from config import get_settings
from tracing import setup_telemetry, instrument_fastapi
from metrics import (
    init_service_info,
    record_service_status,
    record_service_metrics,
    record_alert,
    acknowledge_alert,
    record_metrics_collection_duration,
    record_collection_error,
    record_websocket_message,
    update_websocket_connections,
    get_metrics_text,
    CONTENT_TYPE_LATEST
)
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
    AlertSeverity,
)
from websocket_manager import manager
from metrics_collector import MetricsCollector
from alert_manager import AlertManager, AlertThreshold

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize telemetry
tracer = setup_telemetry(settings.service_name, settings.otlp_endpoint)
init_service_info(settings.service_name, "1.0.0")

# Global components
metrics_collector: Optional[MetricsCollector] = None
alert_manager: Optional[AlertManager] = None
_collection_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global metrics_collector, alert_manager, _collection_task

    logger.info("Operator Console starting up")

    # Initialize metrics collector
    service_urls = settings.get_all_service_urls()
    metrics_collector = MetricsCollector(
        service_urls=service_urls,
        poll_interval=settings.metrics_poll_interval
    )
    await metrics_collector.start()
    logger.info(f"Metrics collector started for {len(service_urls)} services")

    # Initialize alert manager with default thresholds
    alert_manager = AlertManager()

    # Set up default thresholds for each service
    for service_name in service_urls.keys():
        alert_manager.set_threshold(
            service_name,
            AlertThreshold(
                metric_name="cpu_percent",
                warning_threshold=70.0,
                critical_threshold=settings.alert_cpu_threshold,
                comparison="greater_than"
            )
        )
        alert_manager.set_threshold(
            service_name,
            AlertThreshold(
                metric_name="memory_mb",
                warning_threshold=1500.0,
                critical_threshold=settings.alert_memory_threshold,
                comparison="greater_than"
            )
        )
        alert_manager.set_threshold(
            service_name,
            AlertThreshold(
                metric_name="error_rate",
                warning_threshold=0.01,
                critical_threshold=settings.alert_error_rate_threshold,
                comparison="greater_than"
            )
        )

    # Subscribe to alerts for WebSocket broadcasting
    async def alert_subscriber(alert):
        await manager.broadcast_alert(
            alert_id=alert.id,
            severity=alert.severity.value,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            metadata=alert.metadata
        )

    alert_manager.subscribe(alert_subscriber)

    # Start metrics broadcast and alert checking task
    async def broadcast_and_check_loop():
        while True:
            try:
                # Collect metrics
                all_metrics = metrics_collector.get_all_metrics()

                # Check each service's metrics against thresholds
                for service_name, metrics in all_metrics.items():
                    # Broadcast metrics via WebSocket
                    for metric_name, value in metrics.items():
                        await manager.broadcast_metric(
                            service_name=service_name,
                            metric_name=metric_name,
                            value=value,
                            unit=""
                        )

                    # Check for alerts
                    await alert_manager.check_metrics(service_name, metrics)

                    # Update Prometheus metrics
                    status = metrics_collector.get_service_status(service_name)
                    record_service_status(service_name, status == "up")

                    # Record service metrics
                    cpu = metrics.get("cpu_percent")
                    memory = metrics.get("memory_mb")
                    request_rate = metrics.get("request_rate")
                    error_rate = metrics.get("error_rate")

                    record_service_metrics(
                        service_name,
                        cpu_percent=cpu,
                        memory_mb=memory,
                        request_rate=request_rate,
                        error_rate=error_rate
                    )

                # Update WebSocket connection count
                update_websocket_connections(manager.get_connection_count())

            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")

            await asyncio.sleep(settings.metrics_poll_interval)

    _collection_task = asyncio.create_task(broadcast_and_check_loop())
    logger.info("Metrics broadcast and alert checking loop started")

    yield

    # Shutdown
    logger.info("Operator Console shutting down")

    if _collection_task:
        _collection_task.cancel()
        try:
            await _collection_task
        except asyncio.CancelledError:
            pass

    if metrics_collector:
        await metrics_collector.stop()


# Create FastAPI app
app = FastAPI(
    title="Operator Console",
    description="Central monitoring and control dashboard for Project Chimera",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI
instrument_fastapi(app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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

    if metrics_collector:
        service_urls = settings.get_all_service_urls()
        async with AsyncClient(timeout=5.0) as client:
            for service_name, service_url in service_urls.items():
                try:
                    response = await client.get(f"{service_url}/health/live")
                    checks[service_name] = response.status_code == 200
                except Exception:
                    checks[service_name] = False
    else:
        # Return not ready if collector not initialized
        return ReadinessResponse(
            status="not_ready",
            checks={},
        )

    all_ready = all(checks.values())
    status = "ready" if all_ready else "not_ready"

    return ReadinessResponse(status=status, checks=checks)


@app.get("/", response_class=RedirectResponse)
async def dashboard():
    """Redirect to the static dashboard."""
    return RedirectResponse(url="/static/dashboard.html")



@app.get("/api/services", response_model=ServiceList)
async def list_services():
    """List all services with their status."""
    service_urls = settings.get_all_service_urls()
    services = []

    for service_name, service_url in service_urls.items():
        status = metrics_collector.get_service_status(service_name) if metrics_collector else ServiceStatus.UNKNOWN

        service_info = ServiceInfo(
            name=service_name,
            url=service_url,
            status=ServiceStatus(status) if status in ["up", "down", "degraded"] else ServiceStatus.UNKNOWN,
            health_check_url=f"{service_url}/health/live",
            metrics_url=f"{service_url}/metrics"
        )
        services.append(service_info)

    up_count = sum(1 for s in services if s.status == ServiceStatus.UP)
    down_count = sum(1 for s in services if s.status == ServiceStatus.DOWN)
    degraded_count = sum(1 for s in services if s.status == ServiceStatus.DEGRADED)

    return ServiceList(
        services=services,
        total=len(services),
        up=up_count,
        down=down_count,
        degraded=degraded_count
    )


@app.get("/api/metrics", response_model=AllMetrics)
async def get_metrics():
    """Get current metrics from all services."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    all_metrics = metrics_collector.get_all_metrics()
    metrics_dict = {}

    for service_name, service_metrics in all_metrics.items():
        # Extract relevant metrics
        cpu = service_metrics.get("cpu_percent")
        memory = service_metrics.get("memory_mb")
        request_rate = service_metrics.get("request_rate")
        error_rate = service_metrics.get("error_rate")

        metrics_dict[service_name] = ServiceMetrics(
            service_name=service_name,
            cpu_percent=cpu,
            memory_mb=memory,
            request_rate=request_rate,
            error_rate=error_rate
        )

    return AllMetrics(metrics=metrics_dict)


@app.post("/api/control/{service_name}", response_model=ServiceControlResponse)
async def control_service(service_name: str, request: ServiceControlRequest):
    """Manually control a service (start, stop, restart, reload)."""
    service_urls = settings.get_all_service_urls()

    if service_name not in service_urls:
        raise HTTPException(status_code=404, detail=f"Service not found: {service_name}")

    service_url = service_urls[service_name]
    control_url = f"{service_url}/api/control"

    try:
        async with AsyncClient(timeout=10.0) as client:
            response = await client.post(
                control_url,
                json={"action": request.action, "reason": request.reason}
            )

            if response.status_code == 200:
                return ServiceControlResponse(
                    service=service_name,
                    action=request.action,
                    status="success",
                    message=f"Service {service_name} {request.action} successful"
                )
            else:
                return ServiceControlResponse(
                    service=service_name,
                    action=request.action,
                    status="failed",
                    message=f"Service {service_name} {request.action} failed: {response.text}"
                )

    except ConnectError:
        raise HTTPException(status_code=503, detail=f"Service {service_name} is unreachable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error controlling service: {str(e)}")


@app.get("/api/alerts", response_model=AlertList)
async def get_alerts():
    """Get all active alerts."""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not available")

    active_alerts = alert_manager.get_active_alerts()
    critical_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL)
    warning_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.WARNING)
    info_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.INFO)

    return AlertList(
        alerts=active_alerts,
        total=len(active_alerts),
        critical=critical_count,
        warning=warning_count,
        info=info_count
    )


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert_endpoint(alert_id: str):
    """Acknowledge an alert."""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not available")

    success = alert_manager.acknowledge_alert(alert_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

    # Record metric
    alert = next((a for a in alert_manager.get_alert_history() if a.id == alert_id), None)
    if alert:
        acknowledge_alert(alert.severity.value)

    return {"message": f"Alert {alert_id} acknowledged"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    connection_id = f"conn_{id(websocket)}"
    await manager.connect(websocket, connection_id)

    try:
        while True:
            # Receive and handle incoming messages
            data = await websocket.receive_json()

            # Handle subscriptions
            if "action" in data and data["action"] == "subscribe":
                channel = data.get("channel", "all")
                if channel == "all":
                    manager.subscribe(connection_id, "metrics")
                    manager.subscribe(connection_id, "alerts")
                    manager.subscribe(connection_id, "status")
                else:
                    manager.subscribe(connection_id, channel)

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics_text(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
