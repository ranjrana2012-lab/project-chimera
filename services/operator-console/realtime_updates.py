"""
Real-time updates system for Operator Console.

Provides WebSocket-based live metrics, alert notifications, and interactive dashboard updates.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class UpdateType(Enum):
    """Real-time update types."""
    METRIC = "metric"
    ALERT = "alert"
    STATUS = "status"
    CHAT = "chat"
    CONTROL = "control"


@dataclass
class MetricUpdate:
    """Real-time metric update."""
    service_name: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": UpdateType.METRIC.value,
            "service": self.service_name,
            "metric": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class AlertUpdate:
    """Alert notification update."""
    id: str
    severity: str  # critical, warning, info
    title: str
    message: str
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": UpdateType.ALERT.value,
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "metadata": self.metadata
        }


@dataclass
class StatusUpdate:
    """Service status update."""
    service_name: str
    status: str  # up, down, degraded
    health_check: str
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": UpdateType.STATUS.value,
            "service": self.service_name,
            "status": self.status,
            "health_check": self.health_check,
            "last_check": self.last_check.isoformat(),
            "metadata": self.metadata
        }


class WebSocketConnection:
    """WebSocket connection manager."""

    def __init__(self, websocket_id: str, queue: asyncio.Queue):
        self.id = websocket_id
        self.queue = queue
        self.subscriptions: Set[str] = set()
        self.connected = True
        self.last_ping = datetime.now(timezone.utc)

    def subscribe(self, channel: str):
        """Subscribe to updates channel."""
        self.subscriptions.add(channel)

    def unsubscribe(self, channel: str):
        """Unsubscribe from updates channel."""
        self.subscriptions.discard(channel)

    def is_subscribed(self, channel: str) -> bool:
        """Check if subscribed to channel."""
        return channel in self.subscriptions

    def send(self, message: Dict[str, Any]) -> bool:
        """Send message to connection."""
        if not self.connected:
            return False

        try:
            self.queue.put_nowait(json.dumps(message))
            return True
        except asyncio.QueueFull:
            logger.warning(f"Queue full for connection {self.id}")
            return False

    async def send_async(self, message: Dict[str, Any]) -> bool:
        """Send message to connection asynchronously."""
        if not self.connected:
            return False

        try:
            await self.queue.put(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Send error for {self.id}: {e}")
            return False


class MetricsCollector:
    """Collects metrics from all services."""

    def __init__(self, services: List[str], poll_interval: float = 5.0):
        self.services = services
        self.poll_interval = poll_interval
        self._latest_metrics: Dict[str, Dict[str, float]] = {}
        self._running = False

    async def start(self):
        """Start metrics collection."""
        self._running = True

        async def collect():
            while self._running:
                for service in self.services:
                    # Simulate metric collection
                    # In production, would query service /metrics endpoint
                    metrics = await self._collect_service_metrics(service)
                    self._latest_metrics[service] = metrics

                await asyncio.sleep(self.poll_interval)

        asyncio.create_task(collect())

    async def _collect_service_metrics(self, service: str) -> Dict[str, float]:
        """Collect metrics from a service."""
        # Simulated metrics
        import random
        return {
            "cpu_percent": random.uniform(10, 80),
            "memory_mb": random.uniform(100, 2000),
            "request_rate": random.uniform(1, 100),
            "error_rate": random.uniform(0, 0.05)
        }

    async def stop(self):
        """Stop metrics collection."""
        self._running = False

    def get_metrics(self, service: str) -> Optional[Dict[str, float]]:
        """Get latest metrics for a service."""
        return self._latest_metrics.get(service)

    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get all collected metrics."""
        return self._latest_metrics.copy()


class AlertManager:
    """Manages alert notifications."""

    def __init__(self):
        self._active_alerts: Dict[str, AlertUpdate] = {}
        self._alert_history: List[AlertUpdate] = []
        self._subscribers: List[Callable] = []

    def subscribe(self, callback: Callable[[AlertUpdate], None]):
        """Subscribe to new alerts."""
        self._subscribers.append(callback)

    async def create_alert(
        self,
        severity: str,
        title: str,
        message: str,
        source: str
    ) -> AlertUpdate:
        """Create a new alert."""
        alert = AlertUpdate(
            id=f"alert_{hashlib.md5(f"{title}{message}".encode()).hexdigest()[:8]}",
            severity=severity,
            title=title,
            message=message,
            source=source
        )

        self._active_alerts[alert.id] = alert
        self._alert_history.append(alert)

        # Keep history limited
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-1000:]

        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert subscriber error: {e}")

        return alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].acknowledged = True
            return True
        return False

    def get_active_alerts(self) -> List[AlertUpdate]:
        """Get all active alerts."""
        return list(self._active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[AlertUpdate]:
        """Get alert history."""
        return self._alert_history[-limit:]


class RealTimeUpdateService:
    """Service for managing real-time updates to operator console."""

    def __init__(
        self,
        services: List[str],
        websocket_port: int = 8080
    ):
        self.services = services
        self.websocket_port = websocket_port
        self._connections: Dict[str, WebSocketConnection] = {}
        self.metrics_collector = MetricsCollector(services)
        self.alert_manager = AlertManager()
        self._running = False

    async def start(self):
        """Start the real-time update service."""
        if self._running:
            return

        self._running = True

        # Start metrics collection
        await self.metrics_collector.start()

        # Start broadcasting loop
        asyncio.create_task(self._broadcast_loop())

        logger.info("Real-time update service started")

    async def stop(self):
        """Stop the service."""
        self._running = False
        await self.metrics_collector.stop()
        logger.info("Real-time update service stopped")

    async def register_connection(
        self,
        connection_id: str,
        queue: asyncio.Queue
    ) -> WebSocketConnection:
        """Register a new WebSocket connection."""
        connection = WebSocketConnection(connection_id, queue)
        self._connections[connection_id] = connection

        # Send initial state
        await self._send_initial_state(connection)

        return connection

    async def unregister_connection(self, connection_id: str) -> bool:
        """Unregister a WebSocket connection."""
        if connection_id in self._connections:
            del self._connections[connection_id]
            logger.info(f"Connection {connection_id} unregistered")
            return True
        return False

    async def _send_initial_state(self, connection: WebSocketConnection):
        """Send initial state to newly connected client."""
        # Send all service statuses
        for service in self.services:
            metrics = self.metrics_collector.get_metrics(service)
            if metrics:
                update = StatusUpdate(
                    service_name=service,
                    status="up",
                    health_check="healthy",
                    metadata=metrics
                )
                await connection.send_async(update.to_dict())

        # Send active alerts
        for alert in self.alert_manager.get_active_alerts():
            await connection.send_async(alert.to_dict())

    async def _broadcast_loop(self):
        """Broadcast updates to all connected clients."""
        while self._running:
            start_time = time.time()

            # Broadcast metrics to all subscribed connections
            for service in self.services:
                metrics = self.metrics_collector.get_metrics(service)
                if metrics:
                    await self._broadcast_metric(service, metrics)

            # Broadcast any new alerts
            for alert in self.alert_manager.get_active_alerts():
                await self._broadcast_alert(alert)

            # Sleep to maintain target rate (30 FPS)
            elapsed = time.time() - start_time
            sleep_time = max(0, (1.0 / 30) - elapsed)
            await asyncio.sleep(sleep_time)

    async def _broadcast_metric(self, service: str, metrics: Dict[str, float]):
        """Broadcast metric update to subscribers."""
        for metric_name, value in metrics.items():
            update = MetricUpdate(
                service_name=service,
                metric_name=metric_name,
                value=value,
                unit=self._get_unit(metric_name)
            )

            for connection in self._connections.values():
                if connection.is_subscribed(f"metrics:{service}"):
                    await connection.send_async(update.to_dict())

    async def _broadcast_alert(self, alert: AlertUpdate):
        """Broadcast alert to all connections."""
        for connection in self._connections.values():
            if connection.is_subscribed("alerts"):
                await connection.send_async(alert.to_dict())

    def _get_unit(self, metric_name: str) -> str:
        """Get unit for metric name."""
        units = {
            "cpu_percent": "%",
            "memory_mb": "MB",
            "request_rate": "req/s",
            "error_rate": "%"
        }
        return units.get(metric_name, "")

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)

    def get_service_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get all service metrics."""
        return self.metrics_collector.get_all_metrics()

    async def create_alert(
        self,
        severity: str,
        title: str,
        message: str,
        source: str
    ) -> AlertUpdate:
        """Create and broadcast a new alert."""
        alert = await self.alert_manager.create_alert(severity, title, message, source)
        await self._broadcast_alert(alert)
        return alert


# Global real-time update service
realtime_service = RealTimeUpdateService(
    services=[
        "scenespeak-agent",
        "captioning-agent",
        "bsl-agent",
        "sentiment-agent",
        "lighting-service",
        "safety-filter"
    ]
)


__all__ = [
    "UpdateType",
    "MetricUpdate",
    "AlertUpdate",
    "StatusUpdate",
    "WebSocketConnection",
    "MetricsCollector",
    "AlertManager",
    "RealTimeUpdateService",
    "realtime_service"
]
