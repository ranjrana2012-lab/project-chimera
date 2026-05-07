import csv
import importlib.util
import sys
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_CONSOLE = REPO_ROOT / "services" / "operator-console"
CHIMERA_WEB = OPERATOR_CONSOLE / "chimera_web.py"


@pytest.fixture
def web_module(monkeypatch):
    sys.modules.pop("chimera_web", None)
    sys.modules.pop("chimera_core", None)
    monkeypatch.setitem(sys.modules, "transformers", None)
    monkeypatch.setenv("CHIMERA_ENABLE_VOICE", "0")
    monkeypatch.syspath_prepend(str(OPERATOR_CONSOLE))
    monkeypatch.chdir(OPERATOR_CONSOLE)

    spec = importlib.util.spec_from_file_location("chimera_web", CHIMERA_WEB)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    module.chimera.sentiment_analyzer = module.chimera.heuristic_sentiment
    module.chimera.text_generator = None
    module.app.state.history = []
    module.app.state.latest_response = {
        "text": "",
        "sentiment": "NEUTRAL",
        "strategy": "standard_response",
        "response": "Awaiting initial dialogue...",
    }
    return module


def csv_rows(response_text):
    return list(csv.reader(StringIO(response_text)))


def test_state_starts_with_neutral_waiting_response(web_module):
    client = TestClient(web_module.app)

    response = client.get("/api/state")

    assert response.status_code == 200
    assert response.json() == {
        "text": "",
        "sentiment": "NEUTRAL",
        "strategy": "standard_response",
        "response": "Awaiting initial dialogue...",
    }


def test_process_positive_input_updates_state_and_export(web_module):
    client = TestClient(web_module.app)

    response = client.post("/api/process", json={"text": "I am very happy today!"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["text"] == "I am very happy today!"
    assert payload["sentiment"] == "POSITIVE"
    assert payload["strategy"] == "momentum_build"

    state = client.get("/api/state").json()
    assert state["text"] == "I am very happy today!"
    assert state["sentiment"] == "POSITIVE"
    assert state["strategy"] == "momentum_build"

    export = client.get("/api/export")
    assert export.status_code == 200
    rows = csv_rows(export.text)
    assert rows[0] == [
        "timestamp",
        "input",
        "sentiment",
        "confidence_score",
        "strategy_routed",
        "latency_ms",
    ]
    assert rows[1][1] == "I am very happy today!"
    assert rows[1][4] == "momentum_build"


def test_process_rejects_empty_text_without_mutating_history(web_module):
    client = TestClient(web_module.app)

    response = client.post("/api/process", json={"text": "   \t\n  "})

    assert response.status_code == 400
    assert response.json() == {"detail": "text is required"}

    export = client.get("/api/export")
    assert export.status_code == 200
    assert csv_rows(export.text) == [
        [
            "timestamp",
            "input",
            "sentiment",
            "confidence_score",
            "strategy_routed",
            "latency_ms",
        ]
    ]


def test_process_rejects_non_string_text_without_mutating_history(web_module):
    client = TestClient(web_module.app)

    response = client.post("/api/process", json={"text": None})

    assert response.status_code == 400
    assert response.json() == {"detail": "text is required"}

    export = client.get("/api/export")
    assert export.status_code == 200
    assert csv_rows(export.text) == [
        [
            "timestamp",
            "input",
            "sentiment",
            "confidence_score",
            "strategy_routed",
            "latency_ms",
        ]
    ]


def test_process_rejects_overlong_text_without_mutating_history(web_module):
    client = TestClient(web_module.app)
    limit = web_module.MAX_INPUT_CHARS

    response = client.post("/api/process", json={"text": "x" * (limit + 1)})

    assert response.status_code == 413
    assert response.json() == {
        "detail": f"text must be {limit} characters or fewer"
    }

    export = client.get("/api/export")
    assert export.status_code == 200
    assert csv_rows(export.text) == [
        [
            "timestamp",
            "input",
            "sentiment",
            "confidence_score",
            "strategy_routed",
            "latency_ms",
        ]
    ]


def test_web_server_defaults_to_loopback_for_local_demo(web_module, monkeypatch):
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    config = web_module.get_server_config()

    assert config.host == "127.0.0.1"
    assert config.port == 8080
