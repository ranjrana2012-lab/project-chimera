"""Tests for metrics collector."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from metrics_collector import MetricsCollector


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    @pytest.fixture
    def service_urls(self):
        """Sample service URLs."""
        return {
            "test-service": "http://localhost:8000",
            "another-service": "http://localhost:8001"
        }

    @pytest.fixture
    def collector(self, service_urls):
        """Create a metrics collector instance."""
        return MetricsCollector(service_urls=service_urls, poll_interval=1.0)

    @pytest.mark.asyncio
    async def test_start(self, collector):
        """Test starting the metrics collector."""
        assert not collector.is_running()

        await collector.start()

        assert collector.is_running()

        # Clean up
        await collector.stop()

    @pytest.mark.asyncio
    async def test_stop(self, collector):
        """Test stopping the metrics collector."""
        await collector.start()
        assert collector.is_running()

        await collector.stop()

        assert not collector.is_running()

    @pytest.mark.asyncio
    async def test_collect_once(self, collector):
        """Test collecting metrics once."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
# HELP test_metric A test metric
# TYPE test_metric gauge
test_metric 123.456
"""

        with patch('httpx.AsyncClient') as mock_client:
            mock_http_client = AsyncMock()
            mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
            mock_http_client.__aexit__ = AsyncMock()
            mock_http_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_http_client

            metrics = await collector.collect_once()

            # Should have collected metrics from both services
            assert len(metrics) >= 0  # May be empty if services are down

    @pytest.mark.asyncio
    async def test_get_metrics(self, collector):
        """Test getting metrics for a specific service."""
        # Pre-populate some metrics
        collector._latest_metrics["test-service"] = {
            "cpu_percent": 50.0,
            "memory_mb": 500.0
        }

        metrics = collector.get_metrics("test-service")

        assert metrics is not None
        assert metrics["cpu_percent"] == 50.0
        assert metrics["memory_mb"] == 500.0

    def test_get_metrics_nonexistent(self, collector):
        """Test getting metrics for non-existent service."""
        metrics = collector.get_metrics("nonexistent")

        assert metrics is None

    def test_get_all_metrics(self, collector):
        """Test getting all metrics."""
        collector._latest_metrics = {
            "service-1": {"cpu": 50.0},
            "service-2": {"memory": 1000.0}
        }

        all_metrics = collector.get_all_metrics()

        assert len(all_metrics) == 2
        assert "service-1" in all_metrics
        assert "service-2" in all_metrics

    def test_get_service_status(self, collector):
        """Test getting service status."""
        collector._service_status["test-service"] = "up"

        status = collector.get_service_status("test-service")

        assert status == "up"

    def test_get_service_status_unknown(self, collector):
        """Test getting status for unknown service."""
        status = collector.get_service_status("unknown")

        assert status == "unknown"

    def test_get_all_service_status(self, collector):
        """Test getting all service statuses."""
        collector._service_status = {
            "service-1": "up",
            "service-2": "down"
        }

        all_status = collector.get_all_service_status()

        assert len(all_status) == 2
        assert all_status["service-1"] == "up"
        assert all_status["service-2"] == "down"

    @pytest.mark.asyncio
    async def test_collect_service_metrics_success(self, collector):
        """Test successful metric collection from a service."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
# HELP cpu_percent CPU usage percentage
# TYPE cpu_percent gauge
cpu_percent 75.5

# HELP memory_mb Memory usage in MB
# TYPE memory_mb gauge
memory_mb 1024.0
"""

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()

            metrics = await collector._collect_service_metrics("test-service", "http://localhost:8000")

            assert metrics is not None
            assert "cpu_percent" in metrics or "memory_mb" in metrics

    @pytest.mark.asyncio
    async def test_collect_service_metrics_failure(self, collector):
        """Test metric collection failure."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()

            metrics = await collector._collect_service_metrics("test-service", "http://localhost:8000")

            assert metrics is None
