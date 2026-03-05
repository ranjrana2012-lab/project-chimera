"""
Tests for SceneSpeak Agent main application.

Tests the FastAPI endpoints, health checks, and integration with GLM client.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from glm_client import DialogueResponse
from models import GenerateRequest


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_glm_response():
    """Create a mock GLM response"""
    return DialogueResponse(
        text="Generated dialogue text",
        tokens_used=50,
        model="glm-4",
        source="api",
        duration_ms=500
    )


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "scenespeak-agent"


def test_liveness(client):
    """Test liveness probe"""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness(client):
    """Test readiness probe"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "scenespeak-agent"


def test_metrics_endpoint(client):
    """Test metrics endpoint returns Prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus metrics endpoint should return text/plain
    assert "text/plain" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_generate_dialogue_v1(mock_glm_response):
    """Test /v1/generate endpoint with mocked GLM client"""
    from main import glm_client

    # Mock the GLM client
    with patch.object(glm_client, 'generate', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_glm_response

        # Create test client
        with TestClient(app) as client:
            request_data = {
                "prompt": "Generate dialogue for a play",
                "max_tokens": 500,
                "temperature": 0.7,
                "context": {
                    "show_id": "test-show",
                    "scene_number": "1",
                    "adapter": "dramatic"
                }
            }

            response = client.post("/v1/generate", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "Generated dialogue text"
            assert data["tokens_used"] == 50
            assert data["model"] == "glm-4"
            assert data["source"] == "api"
            assert data["duration_ms"] == 500


def test_generate_dialogue_legacy():
    """Test /v1/generate/legacy endpoint with mocked GLM client"""
    from main import glm_client

    mock_response = DialogueResponse(
        text="Legacy dialogue",
        tokens_used=75,
        model="glm-4",
        source="api",
        duration_ms=600
    )

    # Mock the GLM client
    with patch.object(glm_client, 'generate', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response

        # Create test client
        with TestClient(app) as client:
            request_data = {
                "prompt": "Generate dialogue",
                "max_tokens": 500,
                "temperature": 0.7,
                "context": {
                    "show_id": "test-show",
                    "adapter": "default"
                }
            }

            response = client.post("/v1/generate/legacy", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["dialogue"] == "Legacy dialogue"
            assert data["adapter"] == "api"
            assert data["metadata"]["model"] == "glm-4"
            assert data["metadata"]["tokens_used"] == 75


def test_metrics_endpoint_content():
    """Test that metrics endpoint returns actual metrics"""
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        # Should contain Prometheus metric comments
        assert "#" in content or "scenespeak" in content.lower()
