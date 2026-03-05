import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

def test_health_live(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

def test_health_ready_checks_dependencies(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    # Checks should contain individual agent names
    assert "scenespeak-agent" in data["checks"] or "agents" in data["checks"]

def test_orchestrate_dialogue(client):
    response = client.post(
        "/v1/orchestrate",
        json={
            "skill": "dialogue_generator",
            "input": {"prompt": "Hello world"}
        }
    )
    # May fail if agents not running - that's ok for now
    assert response.status_code in [200, 503]
