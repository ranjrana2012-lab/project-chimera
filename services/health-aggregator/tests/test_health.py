"""Tests for health aggregator service."""
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app, check_service_health

client = TestClient(app=app)


@pytest.mark.asyncio
async def test_health_aggregate_all_healthy():
    """Test health aggregation when all services are healthy."""
    mock_health_response = {
        "name": "test-service",
        "status": "healthy",
        "response_time_ms": 10,
        "last_check": "2026-04-09T00:00:00Z",
        "error": None
    }

    with patch('main.check_service_health', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = mock_health_response

        from main import ACTIVE_SERVICES, FROZEN_SERVICES
        total_services = len(ACTIVE_SERVICES) + len(FROZEN_SERVICES)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "active_services" in data
        assert "frozen_services" in data
        assert "summary" in data

        # Check all active services are present
        assert len(data["active_services"]) == len(ACTIVE_SERVICES)
        for service_name in ACTIVE_SERVICES:
            assert service_name in data["active_services"]
            assert data["active_services"][service_name]["status"] == "healthy"

        # Check all frozen services are present
        assert len(data["frozen_services"]) == len(FROZEN_SERVICES)
        for service_name in FROZEN_SERVICES:
            assert service_name in data["frozen_services"]
            assert data["frozen_services"][service_name]["status"] == "healthy"

        # Check summary counts
        assert data["summary"]["total_active"] == len(ACTIVE_SERVICES)
        assert data["summary"]["total_frozen"] == len(FROZEN_SERVICES)
        assert data["summary"]["healthy_active"] == len(ACTIVE_SERVICES)
        assert data["summary"]["healthy_frozen"] == len(FROZEN_SERVICES)
        assert data["summary"]["unhealthy_active"] == 0
        assert data["summary"]["unhealthy_frozen"] == 0


@pytest.mark.asyncio
async def test_health_aggregate_mixed_status():
    """Test health aggregation with mixed healthy/unhealthy services."""
    async def mock_check_unhealthy(service_name, url):
        # Make every other service unhealthy
        if hash(service_name) % 2 == 0:
            return {
                "name": service_name,
                "status": "healthy",
                "response_time_ms": 10,
                "last_check": "2026-04-09T00:00:00Z",
                "error": None
            }
        else:
            return {
                "name": service_name,
                "status": "unhealthy",
                "response_time_ms": None,
                "last_check": "2026-04-09T00:00:00Z",
                "error": "Connection refused"
            }

    with patch('main.check_service_health', new_callable=AsyncMock) as mock_check:
        mock_check.side_effect = mock_check_unhealthy

        from main import ACTIVE_SERVICES, FROZEN_SERVICES

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data

        # Check that we have some unhealthy services
        assert data["summary"]["unhealthy_active"] > 0 or data["summary"]["unhealthy_frozen"] > 0

        # Verify total counts match
        total_checked = (
            data["summary"]["healthy_active"] +
            data["summary"]["unhealthy_active"] +
            data["summary"]["healthy_frozen"] +
            data["summary"]["unhealthy_frozen"]
        )
        assert total_checked == len(ACTIVE_SERVICES) + len(FROZEN_SERVICES)


def test_root_endpoint():
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "Health Aggregator"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data
    assert "/health" in data["endpoints"]


@pytest.mark.asyncio
async def test_check_service_health_timeout():
    """Test health check handles timeouts gracefully."""
    import httpx

    async def mock_get_timeout(*args, **kwargs):
        raise httpx.TimeoutException("Request timed out")

    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = mock_get_timeout

        result = await check_service_health("test-service", "http://localhost:9999")

        assert result["name"] == "test-service"
        assert result["status"] == "unhealthy"
        assert result["error"] is not None
        assert "timed out" in result["error"].lower()


@pytest.mark.asyncio
async def test_check_service_health_connection_error():
    """Test health check handles connection errors gracefully."""
    import httpx

    async def mock_get_error(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")

    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = mock_get_error

        result = await check_service_health("test-service", "http://localhost:9999")

        assert result["name"] == "test-service"
        assert result["status"] == "unhealthy"
        assert result["error"] is not None
        assert "connection" in result["error"].lower()
