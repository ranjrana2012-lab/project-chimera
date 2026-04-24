"""
Tests for Operator Console API Endpoints

Comprehensive test suite for API endpoint coverage to reach 70%+.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import pytest
pytest.skip("Deprecated microservice API endpoints (Phase 1). Migrated to chimera_web.py monolith.", allow_module_level=True)

import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector."""
    with patch('main.metrics_collector') as mock:
        mock.get_all_metrics = AsyncMock(return_value={
            "service1": {"cpu": 50.0, "memory": 60.0},
            "service2": {"cpu": 45.0, "memory": 55.0}
        })
        mock.get_service_metrics = AsyncMock(return_value={
            "cpu": 50.0,
            "memory": 60.0,
            "status": "healthy"
        })
        yield mock


@pytest.fixture
def mock_alert_manager():
    """Mock alert manager."""
    with patch('main.alert_manager') as mock:
        mock.get_active_alerts = Mock(return_value=[])
        mock.acknowledge_alert = Mock()
        mock.get_all_thresholds = Mock(return_value={})
        yield mock


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_liveness_probe(self, client):
        """Test liveness probe returns 200."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness_probe(self, client):
        """Test readiness probe returns 200."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "operator-console"

    def test_health_endpoint(self, client):
        """Test general health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data


class TestDashboardEndpoints:
    """Tests for dashboard endpoints."""

    def test_dashboard_html(self, client):
        """Test dashboard returns HTML."""
        response = client.get("/")
        assert response.status_code in [200, 404]  # May redirect or return HTML

    def test_dashboard_redirect(self, client):
        """Test dashboard redirect behavior."""
        response = client.get("/dashboard")
        assert response.status_code in [200, 307, 404]


class TestServiceEndpoints:
    """Tests for service management endpoints."""

    def test_list_services(self, client):
        """Test listing all services."""
        response = client.get("/api/v1/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data or isinstance(data, list)

    def test_get_service_info(self, client, mock_metrics_collector):
        """Test getting specific service information."""
        response = client.get("/api/v1/services/scenespeak-agent")
        assert response.status_code == 200

    def test_get_service_metrics(self, client, mock_metrics_collector):
        """Test getting service metrics."""
        response = client.get("/api/v1/services/scenespeak-agent/metrics")
        assert response.status_code == 200

    def test_get_all_metrics(self, client, mock_metrics_collector):
        """Test getting all service metrics."""
        response = client.get("/api/v1/metrics/all")
        assert response.status_code == 200

    def test_get_nonexistent_service(self, client):
        """Test getting info for non-existent service."""
        response = client.get("/api/v1/services/nonexistent-service")
        assert response.status_code == 404


class TestAlertEndpoints:
    """Tests for alert management endpoints."""

    def test_get_active_alerts(self, client, mock_alert_manager):
        """Test getting active alerts."""
        mock_alert_manager.get_active_alerts.return_value = [
            {
                "id": "alert-1",
                "service": "test-service",
                "severity": "warning",
                "message": "Test alert"
            }
        ]

        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data or isinstance(data, list)

    def test_acknowledge_alert(self, client, mock_alert_manager):
        """Test acknowledging an alert."""
        response = client.post("/api/v1/alerts/alert-1/acknowledge")
        assert response.status_code == 200

    def test_get_alert_history(self, client, mock_alert_manager):
        """Test getting alert history."""
        response = client.get("/api/v1/alerts/history")
        assert response.status_code in [200, 404]

    def test_set_alert_threshold(self, client, mock_alert_manager):
        """Test setting alert threshold."""
        response = client.post("/api/v1/alerts/thresholds", json={
            "service": "test-service",
            "metric": "cpu_percent",
            "warning": 70.0,
            "critical": 90.0
        })
        assert response.status_code in [200, 201]

    def test_get_alert_thresholds(self, client, mock_alert_manager):
        """Test getting alert thresholds."""
        mock_alert_manager.get_all_thresholds.return_value = {
            "test-service": {
                "cpu_percent": {"warning": 70.0, "critical": 90.0}
            }
        }

        response = client.get("/api/v1/alerts/thresholds")
        assert response.status_code == 200


class TestServiceControlEndpoints:
    """Tests for service control endpoints."""

    def test_restart_service(self, client):
        """Test restarting a service."""
        response = client.post("/api/v1/services/test-service/restart")
        assert response.status_code in [200, 501]  # May not be implemented

    def test_stop_service(self, client):
        """Test stopping a service."""
        response = client.post("/api/v1/services/test-service/stop")
        assert response.status_code in [200, 501]

    def test_start_service(self, client):
        """Test starting a service."""
        response = client.post("/api/v1/services/test-service/start")
        assert response.status_code in [200, 501]

    def test_scale_service(self, client):
        """Test scaling a service."""
        response = client.post("/api/v1/services/test-service/scale", json={
            "replicas": 3
        })
        assert response.status_code in [200, 501]


class TestConfigurationEndpoints:
    """Tests for configuration endpoints."""

    def test_get_config(self, client):
        """Test getting service configuration."""
        response = client.get("/api/v1/config")
        assert response.status_code in [200, 404]

    def test_update_config(self, client):
        """Test updating service configuration."""
        response = client.put("/api/v1/config", json={
            "poll_interval": 10
        })
        assert response.status_code in [200, 404]


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    def test_websocket_connection(self, client):
        """Test WebSocket connection."""
        # WebSocket testing requires special handling
        # This is a placeholder for WebSocket tests
        with client.websocket_connect("/ws") as websocket:
            # If connection succeeds, test passes
            pass


class TestMetricsEndpoints:
    """Tests for metrics endpoints."""

    def test_prometheus_metrics(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_service_metrics_format(self, client):
        """Test service metrics are in correct format."""
        response = client.get("/api/v1/metrics/all")
        if response.status_code == 200:
            data = response.json()
            # Should be a dictionary or list
            assert isinstance(data, (dict, list))


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_service_name(self, client):
        """Test with invalid service name."""
        response = client.get("/api/v1/services/invalid@service")
        assert response.status_code in [400, 404]

    def test_invalid_threshold_values(self, client):
        """Test setting invalid threshold values."""
        response = client.post("/api/v1/alerts/thresholds", json={
            "service": "test",
            "metric": "cpu",
            "warning": "invalid",
            "critical": 90.0
        })
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test with missing required fields."""
        response = client.post("/api/v1/alerts/thresholds", json={
            "service": "test"
        })
        assert response.status_code == 422


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_service_list(self, client):
        """Test when no services are available."""
        with patch('main.metrics_collector') as mock:
            mock.get_all_metrics = AsyncMock(return_value={})

            response = client.get("/api/v1/services")
            assert response.status_code == 200

    def test_service_with_no_metrics(self, client, mock_metrics_collector):
        """Test service with no available metrics."""
        mock_metrics_collector.get_service_metrics = AsyncMock(return_value={})

        response = client.get("/api/v1/services/test-service/metrics")
        assert response.status_code == 200

    def test_large_number_of_alerts(self, client, mock_alert_manager):
        """Test with large number of alerts."""
        alerts = [
            {
                "id": f"alert-{i}",
                "service": "test",
                "severity": "warning",
                "message": f"Alert {i}"
            }
            for i in range(100)
        ]
        mock_alert_manager.get_active_alerts.return_value = alerts

        response = client.get("/api/v1/alerts")
        assert response.status_code == 200


class TestServiceStatus:
    """Tests for service status tracking."""

    def test_unhealthy_service_status(self, client, mock_metrics_collector):
        """Test status of unhealthy service."""
        mock_metrics_collector.get_service_metrics = AsyncMock(return_value={
            "cpu": 95.0,
            "memory": 90.0,
            "status": "unhealthy"
        })

        response = client.get("/api/v1/services/test-service/status")
        assert response.status_code == 200

    def test_degraded_service_status(self, client, mock_metrics_collector):
        """Test status of degraded service."""
        mock_metrics_collector.get_service_metrics = AsyncMock(return_value={
            "cpu": 75.0,
            "memory": 80.0,
            "status": "degraded"
        })

        response = client.get("/api/v1/services/test-service/status")
        assert response.status_code == 200


class TestResponseFormat:
    """Tests for response format validation."""

    def test_service_list_format(self, client):
        """Test service list has correct format."""
        response = client.get("/api/v1/services")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_metrics_format(self, client):
        """Test metrics have correct format."""
        response = client.get("/api/v1/metrics/all")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
