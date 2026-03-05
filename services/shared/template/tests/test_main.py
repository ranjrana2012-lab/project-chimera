# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_live(client):
    """Test liveness endpoint returns 200"""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_health_ready(client):
    """Test readiness endpoint returns 200"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert "status" in response.json()


def test_metrics_endpoint(client):
    """Test metrics endpoint returns prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
