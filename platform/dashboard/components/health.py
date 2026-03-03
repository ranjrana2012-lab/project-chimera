"""
Health monitoring component for dashboard.

Tracks service health status, response times, and test results.
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


@dataclass
class ServiceHealth:
    """
    Health status of a single service.

    Attributes:
        name: Service name
        status: Health status (up, down, degraded)
        last_check: When health was last checked
        response_time_ms: Response time in milliseconds
        passed_tests: Number of passing tests
        total_tests: Total number of tests
    """
    name: str
    status: str = "unknown"  # up, down, degraded, unknown
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_time_ms: Optional[float] = None
    passed_tests: int = 0
    total_tests: int = 0
    error_message: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == "up"

    @property
    def time_since_check_seconds(self) -> float:
        """Get seconds since last health check."""
        return (datetime.now(timezone.utc) - self.last_check).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "passed_tests": self.passed_tests,
            "total_tests": self.total_tests,
            "success_rate": self.success_rate,
            "is_healthy": self.is_healthy,
            "time_since_check_seconds": self.time_since_check_seconds,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceHealth":
        """Create from dictionary."""
        last_check = data.get("last_check")
        if isinstance(last_check, str):
            last_check = datetime.fromisoformat(last_check)
        elif last_check is None:
            last_check = datetime.now(timezone.utc)

        return cls(
            name=data["name"],
            status=data.get("status", "unknown"),
            last_check=last_check,
            response_time_ms=data.get("response_time_ms"),
            passed_tests=data.get("passed_tests", 0),
            total_tests=data.get("total_tests", 0),
            error_message=data.get("error_message")
        )


@dataclass
class HealthConfig:
    """
    Configuration for health monitoring.

    Attributes:
        check_interval_seconds: How often to check health
        timeout_seconds: Request timeout
        healthy_threshold: Consecutive checks before marking healthy
        unhealthy_threshold: Consecutive checks before marking unhealthy
    """
    check_interval_seconds: int = 10
    timeout_seconds: int = 5
    healthy_threshold: int = 3
    unhealthy_threshold: int = 2


@dataclass
class ServiceDefinition:
    """
    Definition of a service to monitor.

    Attributes:
        name: Service name
        host: Service hostname
        port: Service port
        health_path: HTTP path for health endpoint
    """
    name: str
    host: str = "localhost"
    port: int = 8000
    health_path: str = "/health"

    @property
    def health_url(self) -> str:
        """Get full health check URL."""
        return f"http://{self.host}:{self.port}{self.health_path}"


class HealthMonitor:
    """
    Monitors health of multiple services.

    Tracks service status, handles health checks, and provides
    aggregated health information.
    """

    def __init__(self, config: Optional[HealthConfig] = None):
        """
        Initialize health monitor.

        Args:
            config: Health monitoring configuration
        """
        self.config = config or HealthConfig()
        self.services: Dict[str, ServiceDefinition] = {}
        self.health_status: Dict[str, ServiceHealth] = {}
        self._consecutive_failures: Dict[str, int] = {}
        self._consecutive_successes: Dict[str, int] = {}

        logger.info("HealthMonitor initialized")

    def register_service(self, service: ServiceDefinition) -> None:
        """
        Register a service for monitoring.

        Args:
            service: Service definition
        """
        self.services[service.name] = service
        self._consecutive_failures[service.name] = 0
        self._consecutive_successes[service.name] = 0

        logger.debug(f"Registered service: {service.name}")

    def unregister_service(self, name: str) -> None:
        """
        Unregister a service from monitoring.

        Args:
            name: Service name
        """
        if name in self.services:
            del self.services[name]
        if name in self.health_status:
            del self.health_status[name]
        if name in self._consecutive_failures:
            del self._consecutive_failures[name]
        if name in self._consecutive_successes:
            del self._consecutive_successes[name]

        logger.debug(f"Unregistered service: {name}")

    def update_health_status(self, health: ServiceHealth) -> None:
        """
        Update health status for a service.

        Args:
            health: Service health status
        """
        self.health_status[health.name] = health

        # Update consecutive counters
        if health.is_healthy:
            self._consecutive_successes[health.name] += 1
            self._consecutive_failures[health.name] = 0
        else:
            self._consecutive_failures[health.name] += 1
            self._consecutive_successes[health.name] = 0

        logger.debug(f"Updated health for {health.name}: {health.status}")

    def get_service_health(self, name: str) -> Optional[ServiceHealth]:
        """
        Get health status for a service.

        Args:
            name: Service name

        Returns:
            Service health status or None if not found
        """
        return self.health_status.get(name)

    def get_all_health(self) -> Dict[str, ServiceHealth]:
        """
        Get health status for all services.

        Returns:
            Dictionary mapping service names to health status
        """
        return self.health_status.copy()

    def get_service_count(self) -> int:
        """Get total number of registered services."""
        return len(self.services)

    def get_healthy_count(self) -> int:
        """Get number of healthy services."""
        return sum(1 for h in self.health_status.values() if h.is_healthy)

    def get_unhealthy_count(self) -> int:
        """Get number of unhealthy services."""
        return sum(1 for h in self.health_status.values() if not h.is_healthy)


class HealthAggregator:
    """
    Aggregates health information across all services.

    Provides summary statistics and filtered views of service health.
    """

    def __init__(self, services: Optional[List[ServiceDefinition]] = None):
        """
        Initialize health aggregator.

        Args:
            services: List of services to monitor
        """
        self.monitor = HealthMonitor()

        if services:
            for service in services:
                self.monitor.register_service(service)

        logger.info(f"HealthAggregator initialized with {len(services or [])} services")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get health summary across all services.

        Returns:
            Summary dictionary with counts and percentages
        """
        total = self.monitor.get_service_count()
        healthy = self.monitor.get_healthy_count()
        unhealthy = self.monitor.get_unhealthy_count()

        return {
            "total_services": total,
            "healthy_count": healthy,
            "unhealthy_count": unhealthy,
            "unknown_count": total - healthy - unhealthy,
            "health_percentage": (healthy / total * 100) if total > 0 else 0
        }

    def get_services_by_status(self, status: str) -> List[ServiceHealth]:
        """
        Get services filtered by status.

        Args:
            status: Status filter (up, down, degraded)

        Returns:
            List of service health with matching status
        """
        return [
            h for h in self.monitor.health_status.values()
            if h.status == status
        ]

    def get_all_health_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all health status as dictionaries.

        Returns:
            Dictionary mapping service names to health dictionaries
        """
        return {
            name: health.to_dict()
            for name, health in self.monitor.get_all_health().items()
        }

    def update_service(self, health: ServiceHealth) -> None:
        """
        Update health status for a service.

        Args:
            health: Service health status
        """
        self.monitor.update_health_status(health)


def get_default_services() -> List[ServiceDefinition]:
    """
    Get default service definitions for Project Chimera.

    Returns:
        List of default services
    """
    return [
        ServiceDefinition("scenespeak-agent", "localhost", 8001, "/health"),
        ServiceDefinition("captioning-agent", "localhost", 8002, "/health"),
        ServiceDefinition("bsl-agent", "localhost", 8003, "/health"),
        ServiceDefinition("sentiment-agent", "localhost", 8004, "/health"),
        ServiceDefinition("lighting-service", "localhost", 8005, "/health"),
        ServiceDefinition("safety-filter", "localhost", 8006, "/health"),
        ServiceDefinition("operator-console", "localhost", 8007, "/health"),
        ServiceDefinition("openclaw-orchestrator", "localhost", 8000, "/health"),
    ]
