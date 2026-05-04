"""Unit tests for monitoring dashboard metrics endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.fixture(autouse=True)
def clear_metrics_cache():
    """Keep metrics cache state from leaking between endpoint tests."""
    from services.dashboard.main import MetricsCache

    MetricsCache.clear()
    yield
    MetricsCache.clear()


@pytest.mark.unit
def test_metrics_summary_returns_combined_data(monkeypatch):
    """Test that metrics_summary combines system and app metrics."""
    from services.dashboard.main import app

    # Mock Prometheus client
    mock_prom = MagicMock()
    mock_prom.custom_query_range.return_value = [
        MagicMock(value=[1714761200, '45.2'])
    ]

    # Mock health aggregator
    async def mock_get_service_health():
        return {"operator-console": {"status": "healthy"}}

    # Apply mocks
    monkeypatch.setattr("services.dashboard.main.prometheus", mock_prom)
    monkeypatch.setattr("services.dashboard.main.get_service_health", mock_get_service_health)

    # Test
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/metrics/summary")

    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert "applications" in data
    assert "timestamp" in data


@pytest.mark.unit
def test_prometheus_timeout_returns_cached(monkeypatch):
    """Test that cached metrics are returned on Prometheus timeout."""
    from services.dashboard.main import app, MetricsCache

    # Set up cache with stale data
    MetricsCache.set("prom:system.cpu.total_pct:5m", {"value": 42.0, "data": [], "stale": True})

    # Mock Prometheus to raise timeout
    mock_prom = MagicMock()
    mock_prom.custom_query_range.side_effect = TimeoutError("Prometheus timeout")

    monkeypatch.setattr("services.dashboard.main.prometheus", mock_prom)

    # Test
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/metrics/cpu")

    assert response.status_code == 200
    data = response.json()
    assert data["usage_pct"] == 42.0
    assert data["stale"] is True


@pytest.mark.unit
def test_gpu_metrics_uses_nvidia_query(monkeypatch):
    """Test that GPU metrics query NVIDIA-specific metrics."""
    from services.dashboard.main import app

    # Mock Prometheus to return GPU data
    mock_prom = MagicMock()
    mock_prom.custom_query_range.return_value = [
        MagicMock(value=[1714761200, '78.5'])
    ]

    monkeypatch.setattr("services.dashboard.main.prometheus", mock_prom)

    # Test
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/metrics/gpu")

    assert response.status_code == 200
    # Verify Prometheus was called with NVIDIA query
    mock_prom.custom_query_range.assert_called()
    call_args = mock_prom.custom_query_range.call_args
    assert "nvidia" in str(call_args).lower()


@pytest.mark.unit
def test_memory_metrics_returns_percentage(monkeypatch):
    """Test that memory metrics return percentage values."""
    from services.dashboard.main import app

    mock_prom = MagicMock()
    mock_prom.custom_query_range.return_value = [
        MagicMock(value=[1714761200, '67.8'])
    ]

    monkeypatch.setattr("services.dashboard.main.prometheus", mock_prom)

    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/api/metrics/memory")

    assert response.status_code == 200
    data = response.json()
    assert "usage_pct" in data
    assert data["usage_pct"] == 67.8
