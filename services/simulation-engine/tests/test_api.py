import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_liveness_probe(client):
    """Test liveness endpoint returns healthy status."""
    response = client.get("/health/live")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "simulation-engine"
    assert data["version"] == "0.1.0"


def test_readiness_probe(client):
    """Test readiness endpoint returns ready status."""
    response = client.get("/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint is accessible."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
