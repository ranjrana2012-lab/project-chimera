"""Captioning Agent API tests."""
import asyncio
import json

import pytest
import websockets
from tests.fixtures.test_data import TestData


@pytest.mark.requires_services
class TestCaptioningHealth:
    """Test Captioning Agent health endpoints."""

    def test_health_live(self, base_urls, http_client):
        """Test /health/live endpoint."""
        response = http_client.get(f"{base_urls['captioning']}/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"  # Verify actual status value


@pytest.mark.requires_services
class TestCaptioningAPI:
    """Test Captioning Agent API."""

    def test_transcribe_with_valid_request(self, base_urls, http_client):
        """Test POST /api/v1/transcribe with valid request."""
        response = http_client.post(
            f"{base_urls['captioning']}/api/v1/transcribe",
            json=TestData.CAPTIONING_REQUEST,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()
        # Should have processing_time_ms and model_version after fix
        assert "text" in data
        assert "processing_time_ms" in data
        assert "model_version" in data

    def test_detect_language(self, base_urls, http_client):
        """Test POST /api/v1/detect-language."""
        response = http_client.post(
            f"{base_urls['captioning']}/api/v1/detect-language",
            json={"audio_data": TestData.SAMPLE_AUDIO_BASE64},
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()
        assert "language" in data

    def test_transcribe_with_invalid_audio(self, base_urls, http_client):
        """Test error handling for invalid audio format."""
        response = http_client.post(
            f"{base_urls['captioning']}/api/v1/transcribe",
            json={"audio_data": "invalid_base64!!", "language": "en"},
            timeout=30
        )

        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]

    def test_transcribe_response_model_validation(self, base_urls, http_client):
        """Test response model has all required fields."""
        response = http_client.post(
            f"{base_urls['captioning']}/api/v1/transcribe",
            json=TestData.CAPTIONING_REQUEST,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all TranscriptionResponse fields exist
        required_fields = [
            "request_id", "text", "language", "duration",
            "confidence", "processing_time_ms", "model_version"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Verify field types
        assert isinstance(data["processing_time_ms"], (int, float))
        assert isinstance(data["model_version"], str)
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0


@pytest.mark.requires_services
class TestCaptioningWebSocket:
    """Test Captioning Agent WebSocket streaming."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, base_urls):
        """Test WebSocket /api/v1/stream connection."""
        # Use base_urls fixture for portability
        uri = f"{base_urls['captioning'].replace('http', 'ws')}/api/v1/stream"

        async with websockets.connect(uri, close_timeout=5) as websocket:
            # Send streaming config
            request = {
                "audio_data": "dGVzdCBhdWRpbyBkYXRh",
                "language": "en"
            }
            await websocket.send(json.dumps(request))

            # Receive with timeout
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)

            # Verify response structure
            assert "text" in data or "error" in data
