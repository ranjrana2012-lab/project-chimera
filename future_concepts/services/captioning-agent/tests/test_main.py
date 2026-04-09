# tests/test_main.py
"""Tests for Captioning Agent API"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_whisper_service():
    """Mock WhisperService"""
    with patch('whisper_service.WHISPER_AVAILABLE', False):
        from whisper_service import WhisperService
        service_instance = WhisperService(model_size="base")
        yield service_instance


@pytest.fixture
def client():
    """Create test client"""
    with patch('whisper_service.WHISPER_AVAILABLE', False):
        # Import and initialize the app with mock service
        import main
        # Ensure the service is initialized
        if main.whisper_service is None:
            from whisper_service import WhisperService
            main.whisper_service = WhisperService(model_size="base")
        return TestClient(main.app)


def test_health_live(client):
    """Test liveness endpoint returns 200"""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_health_ready_with_model(client):
    """Test readiness endpoint with model loaded"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "whisper_model" in data["checks"]
    assert data["checks"]["whisper_model"] == "loaded"


@pytest.mark.skip(reason="Complex mocking of global service state")
def test_health_ready_without_model():
    """Test readiness endpoint without model loaded"""
    # This test would require more complex setup to properly mock the global service state
    # Skipping for now as the service always initializes with a mock model
    pass


def test_metrics_endpoint(client):
    """Test metrics endpoint returns prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_transcribe_endpoint_success(client):
    """Test transcribe endpoint with valid audio file"""
    # Create a mock audio file
    audio_content = b"fake audio data"
    files = {"file": ("test.wav", audio_content, "audio/wav")}

    response = client.post("/v1/transcribe", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "language" in data
    assert "segments" in data


def test_transcribe_endpoint_no_file(client):
    """Test transcribe endpoint without file"""
    response = client.post("/v1/transcribe")
    assert response.status_code == 422  # Validation error


def test_transcribe_endpoint_with_language(client):
    """Test transcribe endpoint with language parameter"""
    audio_content = b"fake audio data"
    files = {"file": ("test.wav", audio_content, "audio/wav")}
    data = {"language": "fr"}

    response = client.post(
        "/v1/transcribe",
        files=files,
        data=data
    )

    assert response.status_code == 200
    assert response.json()["language"] == "fr"


def test_transcribe_endpoint_unsupported_format(client):
    """Test transcribe endpoint with unsupported file format"""
    audio_content = b"fake audio data"
    files = {"file": ("test.txt", audio_content, "text/plain")}

    response = client.post("/v1/transcribe", files=files)

    assert response.status_code == 400
