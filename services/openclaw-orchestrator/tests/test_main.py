import pytest
from fastapi.testclient import TestClient
import httpx
import sys
import types
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[2]


def _prefer_service_shared_package():
    sys.path.insert(0, str(SERVICES_DIR))
    shared_module = sys.modules.get("shared")
    if shared_module is not None and not str(
        getattr(shared_module, "__file__", "")
    ).startswith(str(SERVICES_DIR)):
        sys.modules.pop("shared", None)
    sys.modules.setdefault(
        "tracing",
        types.SimpleNamespace(
            setup_telemetry=lambda service_name, otlp_endpoint: None,
            instrument_fastapi=lambda app, service_name: None,
        ),
    )

@pytest.fixture
def client():
    _prefer_service_shared_package()
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

def test_orchestrate_dialogue(client, monkeypatch):
    import main

    async def fake_call_agent(agent_url, skill, input_data):
        return {"dialogue": f"Echo: {input_data['prompt']}"}

    monkeypatch.setattr(main, "get_agent_for_skill", lambda skill: "http://test-agent")
    monkeypatch.setattr(main, "call_agent", fake_call_agent)

    response = client.post(
        "/v1/orchestrate",
        json={
            "skill": "dialogue_generator",
            "input": {"prompt": "Hello world"}
        }
    )
    assert response.status_code == 200
    assert response.json()["result"] == {"dialogue": "Echo: Hello world"}


class _FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, agent_url):
        self.agent_url = agent_url

    async def post(self, path, json=None, timeout=None):
        if "8004" in self.agent_url:
            return _FakeResponse(
                {"sentiment": "positive", "score": 0.9, "confidence": 0.9}
            )
        if "8006" in self.agent_url:
            raise httpx.ConnectError("safety filter unavailable")
        raise AssertionError("dialogue generation must not run without safety")


class _FakePool:
    async def get_session(self, agent_url):
        return _FakeSession(agent_url)

    async def release_session(self, agent_url):
        return None


class _FakeCache:
    def cache_key(self, *parts):
        return ":".join(str(part) for part in parts)

    async def get(self, cache_key):
        return None

    async def set(self, cache_key, result, ttl):
        raise AssertionError("unsafe or degraded orchestration must not be cached")


def test_api_orchestrate_fails_closed_when_safety_filter_is_unavailable(monkeypatch):
    _prefer_service_shared_package()
    import main

    monkeypatch.setattr(main, "get_global_pool", lambda: _FakePool())
    monkeypatch.setattr(main, "get_global_cache", lambda: _FakeCache())
    client = TestClient(main.app)

    response = client.post(
        "/api/orchestrate",
        json={"prompt": "Keep this family friendly", "show_id": "phase1-demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response"] == ""
    assert payload["safety_check"] == {
        "passed": False,
        "reason": "Safety filter unavailable; content blocked until reviewed",
    }
    assert payload["metadata"]["degraded_mode"] == "safety_filter_unavailable"
