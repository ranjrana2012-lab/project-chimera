"""Tests for cues module."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


def test_list_cues():
    """Test listing all cues."""
    response = client.get("/cues/library")
    assert response.status_code == 200
    data = response.json()
    assert "cues" in data
    assert "count" in data


def test_save_cue():
    """Test saving a cue to library."""
    cue_data = {
        "name": "test_cue",
        "description": "Test coordinated cue",
        "duration": 10.0,
        "lighting": [
            {
                "fixture_id": "fixture1",
                "intensity": 0.8,
                "color": "#FF0000",
                "fade_time": 2.0
            }
        ],
        "sound": [
            {
                "sound_name": "thunder",
                "volume": 0.7,
                "start_time": 0.0
            }
        ],
        "music": {
            "action": "play",
            "track_id": "track1",
            "volume": 0.5,
            "fade_time": 1.0
        },
        "tags": ["test"]
    }

    response = client.post("/cues/library", json=cue_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "saved"


def test_save_duplicate_cue():
    """Test saving duplicate cue (should fail)."""
    cue_data = {
        "name": "test_cue",
        "description": "Duplicate cue",
        "duration": 5.0
    }

    response = client.post("/cues/library", json=cue_data)
    assert response.status_code == 409  # Conflict


def test_get_cue():
    """Test getting a specific cue."""
    response = client.get("/cues/library/test_cue")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_cue"


def test_get_nonexistent_cue():
    """Test getting non-existent cue."""
    response = client.get("/cues/library/nonexistent")
    assert response.status_code == 404


def test_execute_nonexistent_cue():
    """Test executing non-existent cue."""
    response = client.post("/cues/execute", json={
        "cue_name": "nonexistent",
        "background": True
    })
    assert response.status_code == 404


def test_execute_cue():
    """Test executing a cue."""
    response = client.post("/cues/execute", json={
        "cue_name": "test_cue",
        "background": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    assert "execution_id" in data


def test_get_cue_status():
    """Test getting cue execution status."""
    response = client.get("/cues/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_executions" in data
    assert "count" in data


def test_stop_execution():
    """Test stopping a cue execution."""
    # First execute a cue
    exec_response = client.post("/cues/execute", json={
        "cue_name": "test_cue",
        "background": True
    })
    execution_id = exec_response.json()["execution_id"]

    # Stop it
    response = client.post(f"/cues/stop/{execution_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"


def test_stop_nonexistent_execution():
    """Test stopping non-existent execution."""
    response = client.post("/cues/stop/nonexistent_exec")
    assert response.status_code == 404


def test_update_cue():
    """Test updating a cue."""
    updated_cue = {
        "name": "test_cue",
        "description": "Updated description",
        "duration": 15.0,
        "lighting": [],
        "sound": [],
        "tags": ["updated"]
    }

    response = client.put("/cues/library/test_cue", json=updated_cue)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"


def test_update_nonexistent_cue():
    """Test updating non-existent cue."""
    cue_data = {"name": "nonexistent", "duration": 5.0}
    response = client.put("/cues/library/nonexistent", json=cue_data)
    assert response.status_code == 404


def test_delete_cue():
    """Test deleting a cue."""
    # Create a temporary cue
    client.post("/cues/library", json={
        "name": "temp_cue",
        "description": "Temporary cue",
        "duration": 5.0
    })

    # Delete it
    response = client.delete("/cues/library/temp_cue")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"


def test_delete_nonexistent_cue():
    """Test deleting non-existent cue."""
    response = client.delete("/cues/library/nonexistent")
    assert response.status_code == 404


def test_get_execution_history():
    """Test getting execution history."""
    response = client.get("/cues/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "count" in data


def test_load_preset():
    """Test loading a preset scene."""
    response = client.post("/cues/preset/blackout")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "saved"
    assert data["name"] == "blackout"


def test_load_nonexistent_preset():
    """Test loading non-existent preset."""
    response = client.post("/cues/preset/nonexistent")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
