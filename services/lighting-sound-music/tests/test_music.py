"""Tests for music module."""

import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


def test_list_models():
    """Test listing available music models."""
    response = client.get("/music/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "count" in data
    assert "default_model" in data


def test_generate_music():
    """Test music generation endpoint."""
    response = client.post("/music/generate", json={
        "prompt": "dramatic tension building",
        "duration": 15,
        "model": "turbo",
        "use_case": "show",
        "format": "wav"
    })
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "status" in data
    assert data["status"] in ["queued", "generating"]


def test_generate_music_invalid_duration():
    """Test music generation with invalid duration."""
    response = client.post("/music/generate", json={
        "prompt": "test",
        "duration": 500,  # Too long
        "model": "turbo"
    })
    assert response.status_code == 422  # Validation error


def test_generate_music_invalid_prompt():
    """Test music generation with invalid prompt."""
    response = client.post("/music/generate", json={
        "prompt": "hi",  # Too short
        "duration": 30,
        "model": "turbo"
    })
    assert response.status_code == 422  # Validation error


def test_list_tracks():
    """Test listing all tracks."""
    response = client.get("/music/tracks")
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data
    assert "count" in data


def test_get_generation_status():
    """Test getting generation status."""
    # First create a generation request
    gen_response = client.post("/music/generate", json={
        "prompt": "upbeat background music",
        "duration": 20,
        "model": "turbo"
    })
    request_id = gen_response.json()["request_id"]

    # Get status
    response = client.get(f"/music/generate/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "status" in data


def test_get_generation_status_not_found():
    """Test getting status of non-existent request."""
    response = client.get("/music/generate/nonexistent_req")
    assert response.status_code == 404


def test_get_track_not_found():
    """Test getting non-existent track."""
    response = client.get("/music/tracks/nonexistent_track")
    assert response.status_code == 404


def test_play_music_not_found():
    """Test playing non-existent track."""
    response = client.post("/music/play", json={
        "track_id": "nonexistent_track",
        "volume": 0.8,
        "loop": False
    })
    assert response.status_code == 404


def test_play_music_invalid_volume():
    """Test playing music with invalid volume."""
    response = client.post("/music/play", json={
        "track_id": "any_track",
        "volume": 1.5,  # Invalid
        "loop": False
    })
    # Could be 404 (track not found) or 422 (validation error)
    assert response.status_code in [404, 422]


def test_stop_music():
    """Test stopping music playback."""
    response = client.post("/music/stop")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_get_music_status():
    """Test getting music system status."""
    response = client.get("/music/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_playing" in data
    assert "volume" in data
    assert "position" in data


def test_set_music_volume():
    """Test setting music volume."""
    response = client.post("/music/volume", json={
        "volume": 0.5,
        "fade_time": 1.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["volume"] == 0.5


def test_set_music_volume_invalid():
    """Test setting invalid volume."""
    response = client.post("/music/volume", json={
        "volume": 1.5,
        "fade_time": 0.0
    })
    assert response.status_code == 422


def test_delete_track_not_found():
    """Test deleting non-existent track."""
    response = client.delete("/music/tracks/nonexistent_track")
    assert response.status_code == 404


def test_pause_music_when_not_playing():
    """Test pausing when nothing is playing."""
    response = client.post("/music/pause")
    # Should return 400 if not playing
    assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
