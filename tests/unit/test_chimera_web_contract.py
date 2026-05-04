import csv
import importlib.util
import os
import sys
from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_CONSOLE = REPO_ROOT / "services" / "operator-console"
CHIMERA_WEB = OPERATOR_CONSOLE / "chimera_web.py"


def load_chimera_web():
    os.environ["CHIMERA_ENABLE_VOICE"] = "0"
    sys.path.insert(0, str(OPERATOR_CONSOLE))
    previous_cwd = Path.cwd()
    os.chdir(OPERATOR_CONSOLE)
    try:
        spec = importlib.util.spec_from_file_location("chimera_web", CHIMERA_WEB)
        web_module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(web_module)
        return web_module
    finally:
        os.chdir(previous_cwd)


web_module = load_chimera_web()


def reset_web_state():
    web_module.chimera.sentiment_analyzer = web_module.chimera.heuristic_sentiment
    web_module.chimera.text_generator = None
    web_module.app.state.history = []
    web_module.app.state.latest_response = {
        "text": "",
        "sentiment": "NEUTRAL",
        "strategy": "standard_response",
        "response": "Awaiting initial dialogue...",
    }


def csv_rows(response_text):
    return list(csv.reader(StringIO(response_text)))


def test_state_starts_with_neutral_waiting_response():
    reset_web_state()
    client = TestClient(web_module.app)

    response = client.get("/api/state")

    assert response.status_code == 200
    assert response.json() == {
        "text": "",
        "sentiment": "NEUTRAL",
        "strategy": "standard_response",
        "response": "Awaiting initial dialogue...",
    }


def test_process_positive_input_updates_state_and_export():
    reset_web_state()
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


def test_process_rejects_empty_text_without_mutating_history():
    reset_web_state()
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
