"""
Tests for Lighting-Sound-Music Service main application.

Tests the FastAPI endpoints, health checks, and integration with controllers.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from main import app
from models import LightingSceneRequest, AudioCueRequest, SyncSceneRequest


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_dmx_response():
    """Create a mock DMX response"""
    return {
        "success": True,
        "channels_set": 5
    }


@pytest.fixture
def mock_audio_response():
    """Create a mock audio response"""
    return {
        "success": True,
        "file": "/audio/test.mp3"
    }


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
    assert "status" in data
    assert "service" in data
    assert "checks" in data
    assert data["service"] == "lighting-sound-music"


@patch('main.dmx_controller')
def test_set_lighting_scene(mock_dmx, client):
    """Test setting a lighting scene"""
    # Mock the DMX controller
    mock_dmx.set_scene = AsyncMock(return_value={
        "success": True,
        "channels_set": 3
    })
    mock_dmx.is_ready.return_value = True

    # Create request
    request = {
        "scene_id": "test-scene-1",
        "channels": {
            1: 255,
            2: 128,
            3: 0
        }
    }

    # Make request
    response = client.post("/v1/lighting/set", json=request)

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["scene_id"] == "test-scene-1"
    assert data["status"] == "success"
    assert data["channels_set"] == 3
    assert "duration_ms" in data


@patch('main.audio_controller')
def test_play_audio_cue(mock_audio, client):
    """Test playing an audio cue"""
    # Mock the audio controller
    mock_audio.play_audio = AsyncMock(return_value={
        "success": True,
        "file": "/audio/test.mp3"
    })
    mock_audio.is_ready.return_value = True

    # Create request
    request = {
        "cue_id": "test-cue-1",
        "file_path": "/audio/test.mp3",
        "volume": 0.8,
        "loop": False
    }

    # Make request
    response = client.post("/v1/audio/play", json=request)

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["cue_id"] == "test-cue-1"
    assert data["status"] == "playing"
    assert "duration_ms" in data


@patch('main.audio_controller')
def test_stop_audio(mock_audio, client):
    """Test stopping audio playback"""
    # Mock the audio controller
    mock_audio.stop_audio = AsyncMock(return_value={
        "success": True
    })

    # Make request
    response = client.post("/v1/audio/stop")

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"


@patch('main.audio_controller')
def test_set_audio_volume(mock_audio, client):
    """Test setting audio volume"""
    # Mock the audio controller
    mock_audio.set_volume = AsyncMock(return_value={
        "success": True,
        "volume": 0.5
    })

    # Make request with proper JSON body
    response = client.post("/v1/audio/volume", json={"volume": 0.5})

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["volume"] == 0.5


def test_set_audio_volume_invalid(client):
    """Test setting invalid audio volume"""
    # Make request with invalid volume
    response = client.post("/v1/audio/volume", json=1.5)

    # Assert response
    assert response.status_code == 422  # Validation error


@patch('main.sync_manager')
def test_trigger_sync_scene(mock_sync, client):
    """Test triggering a synchronized scene"""
    # Mock the sync manager
    mock_sync.trigger_scene = AsyncMock(return_value={
        "success": True,
        "lighting_time": 0.01,
        "audio_time": 0.02
    })

    # Create request
    request = {
        "scene_id": "test-sync-1",
        "lighting_channels": {
            1: 255,
            2: 200
        },
        "audio_file": "/audio/test.mp3",
        "audio_volume": 0.9,
        "delay_ms": 0
    }

    # Make request
    response = client.post("/v1/sync/scene", json=request)

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["scene_id"] == "test-sync-1"
    assert data["status"] == "success"
    assert "lighting_triggered_at" in data
    assert "audio_triggered_at" in data


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
