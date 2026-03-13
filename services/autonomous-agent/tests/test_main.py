"""Tests for main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "autonomous-agent"


def test_status_endpoint(client):
    """Test status endpoint."""
    response = client.get("/status")

    assert response.status_code == 200
    data = response.json()
    assert "retry_count" in data
    assert "last_updated" in data


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "autonomous_agent_service_info" in response.text
