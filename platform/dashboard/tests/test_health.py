"""
Unit tests for health monitoring component.

Tests service health status tracking and aggregation.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add dashboard to path
dashboard_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(dashboard_path))


class TestServiceHealth:
    """Test ServiceHealth dataclass."""

    @pytest.fixture
    def health(self):
        """Create a service health instance."""
        from components.health import ServiceHealth
        return ServiceHealth(
            name="test-service",
            status="up",
            last_check=datetime.now(timezone.utc),
            response_time_ms=50,
            passed_tests=10,
            total_tests=10
        )

    def test_service_health_creation(self, health):
        """Test creating service health."""
        assert health.name == "test-service"
        assert health.status == "up"
        assert health.response_time_ms == 50
        assert health.passed_tests == 10
        assert health.total_tests == 10

    def test_service_health_success_rate(self, health):
        """Test success rate calculation."""
        rate = health.success_rate
        assert rate == 100.0

    def test_service_health_success_rate_partial(self):
        """Test success rate with failures."""
        from components.health import ServiceHealth
        health = ServiceHealth(
            name="test-service",
            status="degraded",
            passed_tests=8,
            total_tests=10,
            last_check=datetime.now(timezone.utc)
        )
        assert health.success_rate == 80.0

    def test_service_health_is_healthy(self, health):
        """Test is_healthy check."""
        assert health.is_healthy is True

    def test_service_health_is_healthy_false(self):
        """Test is_healthy when down."""
        from components.health import ServiceHealth
        health = ServiceHealth(
            name="test-service",
            status="down",
            passed_tests=0,
            total_tests=10,
            last_check=datetime.now(timezone.utc)
        )
        assert health.is_healthy is False

    def test_service_health_is_healthy_degraded(self):
        """Test is_healthy when degraded."""
        from components.health import ServiceHealth
        health = ServiceHealth(
            name="test-service",
            status="degraded",
            passed_tests=8,
            total_tests=10,
            last_check=datetime.now(timezone.utc)
        )
        assert health.is_healthy is False

    def test_service_health_time_since_check(self, health):
        """Test time since last check."""
        # Should be very recent
        seconds = health.time_since_check_seconds
        assert seconds < 1.0

    def test_service_health_time_since_check_old(self):
        """Test time since check with old timestamp."""
        from components.health import ServiceHealth
        old_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        health = ServiceHealth(
            name="test-service",
            status="up",
            passed_tests=10,
            total_tests=10,
            last_check=old_time
        )
        seconds = health.time_since_check_seconds
        assert 29 <= seconds <= 31  # Allow for test execution time


class TestHealthConfig:
    """Test HealthConfig dataclass."""

    def test_health_config_defaults(self):
        """Test default health config."""
        from components.health import HealthConfig
        config = HealthConfig()
        assert config.check_interval_seconds == 10
        assert config.timeout_seconds == 5
        assert config.healthy_threshold == 3
        assert config.unhealthy_threshold == 2

    def test_health_config_custom(self):
        """Test custom health config."""
        from components.health import HealthConfig
        config = HealthConfig(
            check_interval_seconds=30,
            timeout_seconds=10,
            healthy_threshold=5,
            unhealthy_threshold=3
        )
        assert config.check_interval_seconds == 30
        assert config.timeout_seconds == 10
        assert config.healthy_threshold == 5
        assert config.unhealthy_threshold == 3


class TestServiceDefinition:
    """Test ServiceDefinition dataclass."""

    def test_service_definition(self):
        """Test service definition."""
        from components.health import ServiceDefinition
        service = ServiceDefinition(
            name="test-service",
            host="localhost",
            port=8000,
            health_path="/health"
        )
        assert service.name == "test-service"
        assert service.host == "localhost"
        assert service.port == 8000
        assert service.health_path == "/health"

    def test_service_definition_url(self):
        """Test service URL generation."""
        from components.health import ServiceDefinition
        service = ServiceDefinition(
            name="test-service",
            host="localhost",
            port=8000,
            health_path="/health"
        )
        assert service.health_url == "http://localhost:8000/health"

    def test_service_definition_url_custom_path(self):
        """Test service URL with custom path."""
        from components.health import ServiceDefinition
        service = ServiceDefinition(
            name="test-service",
            host="localhost",
            port=8000,
            health_path="/api/v1/health"
        )
        assert service.health_url == "http://localhost:8000/api/v1/health"


class TestHealthMonitor:
    """Test HealthMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create health monitor."""
        from components.health import HealthMonitor
        return HealthMonitor()

    def test_monitor_init(self, monitor):
        """Test monitor initialization."""
        assert len(monitor.services) == 0
        assert len(monitor.health_status) == 0

    def test_register_service(self, monitor):
        """Test registering a service."""
        from components.health import ServiceDefinition
        service = ServiceDefinition(
            name="test-service",
            host="localhost",
            port=9999,
            health_path="/health"
        )
        monitor.register_service(service)
        assert "test-service" in monitor.services
        assert monitor.services["test-service"].name == "test-service"

    def test_register_multiple_services(self, monitor):
        """Test registering multiple services."""
        from components.health import ServiceDefinition
        services = [
            ServiceDefinition(f"service-{i}", "localhost", 8000 + i, "/health")
            for i in range(3)
        ]
        for service in services:
            monitor.register_service(service)
        assert len(monitor.services) == 3

    def test_get_all_health_empty(self, monitor):
        """Test getting health status when no services."""
        status = monitor.get_all_health()
        assert status == {}

    def test_get_service_health_unknown(self, monitor):
        """Test getting health for unknown service."""
        status = monitor.get_service_health("unknown")
        assert status is None

    def test_get_service_count(self, monitor):
        """Test getting service count."""
        assert monitor.get_service_count() == 0

        from components.health import ServiceDefinition
        monitor.register_service(ServiceDefinition("s1", "localhost", 8001, "/health"))
        monitor.register_service(ServiceDefinition("s2", "localhost", 8002, "/health"))

        assert monitor.get_service_count() == 2

    def test_get_healthy_count(self, monitor):
        """Test getting healthy service count."""
        from components.health import ServiceDefinition, ServiceHealth

        # Register services
        monitor.register_service(ServiceDefinition("s1", "localhost", 8001, "/health"))
        monitor.register_service(ServiceDefinition("s2", "localhost", 8002, "/health"))
        monitor.register_service(ServiceDefinition("s3", "localhost", 8003, "/health"))

        # Set health status manually for testing
        monitor.health_status["s1"] = ServiceHealth(
            name="s1", status="up", passed_tests=10, total_tests=10,
            last_check=datetime.now(timezone.utc)
        )
        monitor.health_status["s2"] = ServiceHealth(
            name="s2", status="down", passed_tests=0, total_tests=10,
            last_check=datetime.now(timezone.utc)
        )
        monitor.health_status["s3"] = ServiceHealth(
            name="s3", status="up", passed_tests=10, total_tests=10,
            last_check=datetime.now(timezone.utc)
        )

        assert monitor.get_healthy_count() == 2

    def test_get_unhealthy_count(self, monitor):
        """Test getting unhealthy service count."""
        from components.health import ServiceDefinition, ServiceHealth

        monitor.register_service(ServiceDefinition("s1", "localhost", 8001, "/health"))
        monitor.register_service(ServiceDefinition("s2", "localhost", 8002, "/health"))

        monitor.health_status["s1"] = ServiceHealth(
            name="s1", status="up", passed_tests=10, total_tests=10,
            last_check=datetime.now(timezone.utc)
        )
        monitor.health_status["s2"] = ServiceHealth(
            name="s2", status="down", passed_tests=0, total_tests=10,
            last_check=datetime.now(timezone.utc)
        )

        assert monitor.get_unhealthy_count() == 1


class TestHealthAggregator:
    """Test HealthAggregator class."""

    @pytest.fixture
    def services(self):
        """Get default service definitions."""
        from components.health import get_default_services
        return get_default_services()

    def test_get_default_services(self, services):
        """Test getting default services."""
        assert len(services) == 8
        service_names = [s.name for s in services]
        assert "scenespeak-agent" in service_names
        assert "captioning-agent" in service_names
        assert "bsl-agent" in service_names
        assert "sentiment-agent" in service_names
        assert "safety-filter" in service_names
        assert "lighting-service" in service_names
        assert "openclaw-orchestrator" in service_names
        assert "operator-console" in service_names

    def test_service_ports(self, services):
        """Test service port assignments."""
        ports = {s.name: s.port for s in services}
        assert ports["scenespeak-agent"] == 8001
        assert ports["captioning-agent"] == 8002
        assert ports["bsl-agent"] == 8003
        assert ports["sentiment-agent"] == 8004
        assert ports["lighting-service"] == 8005
        assert ports["safety-filter"] == 8006
        assert ports["operator-console"] == 8007
        assert ports["openclaw-orchestrator"] == 8000

    def test_aggregator_init(self, services):
        """Test aggregator initialization."""
        from components.health import HealthAggregator
        aggregator = HealthAggregator(services)
        assert aggregator.monitor.get_service_count() == 8

    def test_aggregator_get_summary(self, services):
        """Test getting health summary."""
        from components.health import HealthAggregator, ServiceHealth
        aggregator = HealthAggregator(services)

        summary = aggregator.get_summary()
        assert "total_services" in summary
        assert "healthy_count" in summary
        assert "unhealthy_count" in summary
        assert summary["total_services"] == 8
        assert summary["healthy_count"] == 0  # No actual health data yet
        assert summary["unhealthy_count"] == 0

    def test_aggregator_get_services_by_status(self, services):
        """Test getting services by status."""
        from components.health import HealthAggregator, ServiceHealth
        aggregator = HealthAggregator(services)

        # Manually set some health status
        monitor = aggregator.monitor
        monitor.health_status["scenespeak-agent"] = ServiceHealth(
            name="scenespeak-agent", status="up", passed_tests=45, total_tests=50,
            last_check=datetime.now(timezone.utc)
        )
        monitor.health_status["captioning-agent"] = ServiceHealth(
            name="captioning-agent", status="up", passed_tests=120, total_tests=125,
            last_check=datetime.now(timezone.utc)
        )
        monitor.health_status["bsl-agent"] = ServiceHealth(
            name="bsl-agent", status="down", passed_tests=0, total_tests=40,
            last_check=datetime.now(timezone.utc)
        )

        up_services = aggregator.get_services_by_status("up")
        down_services = aggregator.get_services_by_status("down")

        assert len(up_services) == 2
        assert len(down_services) == 1
        assert up_services[0].name == "scenespeak-agent"
        assert down_services[0].name == "bsl-agent"


class TestHealthJSONSerialization:
    """Test JSON serialization of health data."""

    def test_service_health_to_dict(self):
        """Test converting service health to dict."""
        from components.health import ServiceHealth
        health = ServiceHealth(
            name="test-service",
            status="up",
            passed_tests=10,
            total_tests=10,
            last_check=datetime.now(timezone.utc),
            response_time_ms=50
        )
        data = health.to_dict()
        assert data["name"] == "test-service"
        assert data["status"] == "up"
        assert data["passed_tests"] == 10
        assert data["total_tests"] == 10
        assert data["response_time_ms"] == 50
        assert "last_check" in data
        assert "success_rate" in data

    def test_service_health_from_dict(self):
        """Test creating service health from dict."""
        from components.health import ServiceHealth
        data = {
            "name": "test-service",
            "status": "up",
            "passed_tests": 10,
            "total_tests": 10,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": 50
        }
        health = ServiceHealth.from_dict(data)
        assert health.name == "test-service"
        assert health.status == "up"
        assert health.passed_tests == 10
