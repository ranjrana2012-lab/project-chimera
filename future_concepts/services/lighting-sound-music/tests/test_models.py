"""
Tests for Pydantic models.

Tests request and response models for validation and serialization.
"""

import pytest
from models import (
    LightingSceneRequest,
    LightingResponse,
    AudioCueRequest,
    AudioResponse,
    SyncSceneRequest,
    SyncResponse,
    HealthResponse
)


def test_lighting_scene_request_valid():
    """Test valid lighting scene request"""
    request = LightingSceneRequest(
        scene_id="test-scene-1",
        channels={1: 255, 2: 128, 3: 0}
    )

    assert request.scene_id == "test-scene-1"
    assert request.channels == {1: 255, 2: 128, 3: 0}
    assert request.fade_time_ms == 0  # Default value


def test_lighting_scene_request_with_fade():
    """Test lighting scene request with fade time"""
    request = LightingSceneRequest(
        scene_id="test-scene-2",
        channels={1: 255},
        fade_time_ms=2000
    )

    assert request.fade_time_ms == 2000


def test_lighting_scene_request_invalid_fade_negative():
    """Test lighting scene request with negative fade time"""
    with pytest.raises(ValueError):
        LightingSceneRequest(
            scene_id="test-scene",
            channels={1: 255},
            fade_time_ms=-100
        )


def test_lighting_response():
    """Test lighting response model"""
    response = LightingResponse(
        scene_id="test-scene-1",
        status="success",
        channels_set=5,
        duration_ms=150,
        message="Scene applied successfully"
    )

    assert response.scene_id == "test-scene-1"
    assert response.status == "success"
    assert response.channels_set == 5
    assert response.duration_ms == 150
    assert response.message == "Scene applied successfully"


def test_audio_cue_request_valid():
    """Test valid audio cue request"""
    request = AudioCueRequest(
        cue_id="test-cue-1",
        file_path="/audio/test.mp3",
        volume=0.8,
        loop=False
    )

    assert request.cue_id == "test-cue-1"
    assert request.file_path == "/audio/test.mp3"
    assert request.volume == 0.8
    assert request.loop is False


def test_audio_cue_request_defaults():
    """Test audio cue request with default values"""
    request = AudioCueRequest(
        cue_id="test-cue-2",
        file_path="/audio/test.mp3"
    )

    assert request.volume == 1.0  # Default
    assert request.loop is False  # Default


def test_audio_cue_request_invalid_volume_high():
    """Test audio cue request with volume > 1.0"""
    with pytest.raises(ValueError):
        AudioCueRequest(
            cue_id="test-cue",
            file_path="/audio/test.mp3",
            volume=1.5
        )


def test_audio_cue_request_invalid_volume_low():
    """Test audio cue request with volume < 0.0"""
    with pytest.raises(ValueError):
        AudioCueRequest(
            cue_id="test-cue",
            file_path="/audio/test.mp3",
            volume=-0.1
        )


def test_audio_response():
    """Test audio response model"""
    response = AudioResponse(
        cue_id="test-cue-1",
        status="playing",
        duration_ms=50,
        message="Audio started successfully"
    )

    assert response.cue_id == "test-cue-1"
    assert response.status == "playing"
    assert response.duration_ms == 50
    assert response.message == "Audio started successfully"


def test_sync_scene_request_valid():
    """Test valid sync scene request"""
    request = SyncSceneRequest(
        scene_id="test-sync-1",
        lighting_channels={1: 255, 2: 200},
        audio_file="/audio/test.mp3",
        audio_volume=0.9
    )

    assert request.scene_id == "test-sync-1"
    assert request.lighting_channels == {1: 255, 2: 200}
    assert request.audio_file == "/audio/test.mp3"
    assert request.audio_volume == 0.9
    assert request.delay_ms == 0  # Default


def test_sync_scene_request_with_delay():
    """Test sync scene request with delay"""
    request = SyncSceneRequest(
        scene_id="test-sync-2",
        lighting_channels={1: 255},
        audio_file="/audio/test.mp3",
        delay_ms=500
    )

    assert request.delay_ms == 500


def test_sync_response():
    """Test sync response model"""
    response = SyncResponse(
        scene_id="test-sync-1",
        status="success",
        lighting_triggered_at=1234567890.123,
        audio_triggered_at=1234567890.138,
        duration_ms=200,
        message="Sync scene triggered successfully"
    )

    assert response.scene_id == "test-sync-1"
    assert response.status == "success"
    assert response.lighting_triggered_at == 1234567890.123
    assert response.audio_triggered_at == 1234567890.138
    assert response.duration_ms == 200
    assert response.message == "Sync scene triggered successfully"


def test_health_response():
    """Test health response model"""
    response = HealthResponse(
        status="ready",
        service="lighting-sound-music",
        checks={
            "dmx_controller": True,
            "audio_controller": True
        }
    )

    assert response.status == "ready"
    assert response.service == "lighting-sound-music"
    assert response.checks == {
        "dmx_controller": True,
        "audio_controller": True
    }


def test_health_response_not_ready():
    """Test health response when not ready"""
    response = HealthResponse(
        status="not_ready",
        service="lighting-sound-music",
        checks={
            "dmx_controller": False,
            "audio_controller": True
        }
    )

    assert response.status == "not_ready"
    assert response.checks["dmx_controller"] is False
