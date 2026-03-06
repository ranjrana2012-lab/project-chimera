"""Tests for Operator Console main application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from main import app
from config import get_settings


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.service_name = "operator-console"
    settings.port = 8007
    settings.log_level = "INFO"
    settings.environment = "test"
    settings.get_all_service_urls = Mock(return_value={
        "openclaw-orchestrator": "http://localhost:8000",
        "scenespeak-agent": "http://localhost:8001",
        "captioning-agent": "http://localhost:8002",
        "bsl-agent": "http://localhost:8003",
        "sentiment-agent": "http://localhost:8004",
        "lighting-sound-music": "http://localhost:8005",
        "safety-filter": "http://localhost:8006",
    })
    settings.metrics_poll_interval = 1.0
    settings.alert_cpu_threshold = 80.0
    settings.alert_memory_threshold = 2000.0
    settings.alert_error_rate_threshold = 0.05
    return settings


class TestHealthEndpoints:
    """Tests for health endpoints."""

    def test_liveness(self, client):
        """Test liveness endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    @patch('main.metrics_collector')
    @patch('main.get_settings')
    def test_readiness_all_up(self, mock_get_settings, mock_collector, client):
        """Test readiness endpoint when all services are up."""
        mock_settings = Mock()
        mock_settings.get_all_service_urls = Mock(return_value={
            "test-service": "http://localhost:8000"
        })
        mock_get_settings.return_value = mock_settings
        mock_collector.get_all_service_urls.return_value = {}

        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data


class TestDashboardEndpoint:
    """Tests for dashboard endpoint."""

    def test_dashboard_html(self, client):
        """Test dashboard returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Operator Console" in response.text


class TestAPIEndpoints:
    """Tests for API endpoints."""

    @patch('main.metrics_collector')
    def test_list_services(self, mock_collector, client):
        """Test list services endpoint."""
        mock_collector.get_service_status.return_value = "up"

        response = client.get("/api/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "total" in data
        assert isinstance(data["services"], list)

    @patch('main.metrics_collector')
    def test_get_metrics(self, mock_collector, client):
        """Test get metrics endpoint."""
        mock_collector.get_all_metrics.return_value = {
            "test-service": {
                "cpu_percent": 50.0,
                "memory_mb": 500.0,
                "request_rate": 10.0,
                "error_rate": 0.01
            }
        }

        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    @patch('main.alert_manager')
    def test_get_alerts(self, mock_alert_manager, client):
        """Test get alerts endpoint."""
        mock_alert_manager.get_active_alerts.return_value = []

        response = client.get("/api/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data

    @patch('main.alert_manager')
    def test_acknowledge_alert(self, mock_alert_manager, client):
        """Test acknowledge alert endpoint."""
        mock_alert_manager.acknowledge_alert.return_value = True
        mock_alert_manager.get_alert_history.return_value = []

        response = client.post("/api/alerts/test-alert-id/acknowledge")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @patch('main.alert_manager')
    def test_acknowledge_alert_not_found(self, mock_alert_manager, client):
        """Test acknowledge alert with invalid ID."""
        mock_alert_manager.acknowledge_alert.return_value = False

        response = client.post("/api/alerts/invalid-id/acknowledge")
        assert response.status_code == 404


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    def test_websocket_connect(self, client):
        """Test WebSocket connection."""
        # Note: WebSocket testing requires pytest-asyncio and a different approach
        # This is a placeholder for future WebSocket testing
        pass


class TestMetricsEndpoint:
    """Tests for Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
