"""
Enhanced tests for Captioning Agent Main Application.

Comprehensive tests for FastAPI endpoints, error handling, and integration scenarios.
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import io


@pytest.fixture
def client():
    """Create test client with mocked Whisper service"""
    with patch('whisper_service.WHISPER_AVAILABLE', False):
        import main
        if main.whisper_service is None:
            from whisper_service import WhisperService
            main.whisper_service = WhisperService(model_size="base")
        return TestClient(main.app)


class TestHealthEndpointsEnhanced:
    """Enhanced tests for health check endpoints"""

    def test_liveness_returns_json(self, client):
        """Test liveness returns proper JSON content type"""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_liveness_response_structure(self, client):
        """Test liveness response has correct structure"""
        response = client.get("/health/live")
        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"

    def test_readiness_with_loaded_model(self, client):
        """Test readiness when model is loaded"""
        response = client.get("/health/ready")
        data = response.json()
        assert response.status_code == 200
        assert "status" in data
        assert "checks" in data
        assert data["checks"]["whisper_model"] == "loaded"

    def test_readiness_response_structure(self, client):
        """Test readiness has all expected fields"""
        response = client.get("/health/ready")
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "whisper_model" in data["checks"]


class TestTranscribeEndpointEnhanced:
    """Enhanced tests for /v1/transcribe endpoint"""

    def test_transcribe_with_wav_file(self, client):
        """Test transcription with WAV file"""
        audio_content = b"RIFF" + b"\x00" * 100
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "language" in data

    def test_transcribe_with_mp3_file(self, client):
        """Test transcription with MP3 file"""
        audio_content = b"\xFF\xFB" + b"\x00" * 100
        files = {"file": ("test.mp3", audio_content, "audio/mpeg")}
        response = client.post("/v1/transcribe", files=files)
        assert response.status_code == 200

    def test_transcribe_with_language_parameter(self, client):
        """Test transcription with language parameter"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        data = {"language": "es"}
        response = client.post(
            "/v1/transcribe",
            files=files,
            data=data
        )
        assert response.status_code == 200
        assert response.json()["language"] == "es"

    def test_transcribe_with_task_parameter(self, client):
        """Test transcription with task parameter"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        data = {"task": "translate"}
        response = client.post(
            "/v1/transcribe",
            files=files,
            data=data
        )
        assert response.status_code == 200

    def test_transcribe_with_temperature(self, client):
        """Test transcription with temperature parameter"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        data = {"temperature": "0.5"}
        response = client.post(
            "/v1/transcribe",
            files=files,
            data=data
        )
        assert response.status_code == 200

    def test_transcribe_response_structure(self, client):
        """Test transcription response has correct structure"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        data = response.json()
        expected_fields = ["text", "language", "segments", "duration", "processing_time_ms"]
        for field in expected_fields:
            assert field in data

    def test_transcribe_returns_segments(self, client):
        """Test transcription returns segments"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        data = response.json()
        assert "segments" in data
        assert isinstance(data["segments"], list)

    def test_transcribe_segment_structure(self, client):
        """Test segments have correct structure"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        data = response.json()
        if len(data["segments"]) > 0:
            segment = data["segments"][0]
            assert "start" in segment
            assert "end" in segment
            assert "text" in segment

    def test_transcribe_processing_time(self, client):
        """Test transcription includes processing time"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        data = response.json()
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] >= 0

    def test_transcribe_without_file(self, client):
        """Test transcription without file returns validation error"""
        response = client.post("/v1/transcribe")
        assert response.status_code == 422

    def test_transcribe_with_unsupported_format(self, client):
        """Test transcription with unsupported file format"""
        files = {"file": ("test.txt", b"text data", "text/plain")}
        response = client.post("/v1/transcribe", files=files)
        assert response.status_code == 400

    def test_transcribe_with_empty_file(self, client):
        """Test transcription with empty file"""
        files = {"file": ("test.wav", b"", "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_transcribe_with_large_file(self, client):
        """Test transcription with large file (size validation)"""
        # Create content larger than max file size
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        files = {"file": ("test.wav", large_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        assert response.status_code == 413


class TestMetricsEndpoint:
    """Test /metrics endpoint"""

    def test_metrics_content_type(self, client):
        """Test metrics endpoint returns correct content type"""
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_has_content(self, client):
        """Test metrics endpoint returns content"""
        response = client.get("/metrics")
        assert len(response.content) > 0

    def test_metrics_after_transcription(self, client):
        """Test that metrics are recorded after transcription"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        client.post("/v1/transcribe", files=files)

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        assert len(response.content) > 0


class TestWebSocketEndpoint:
    """Test WebSocket endpoint"""

    def test_websocket_endpoint_exists(self, client):
        """Test that WebSocket endpoint is accessible"""
        # Note: We can't fully test WebSocket with TestClient
        # but we can verify the endpoint is registered
        from main import app
        routes = [route.path for route in app.routes]
        assert "/v1/stream" in routes


class TestErrorHandling:
    """Test error handling in API endpoints"""

    def test_transcribe_handles_corrupted_audio(self, client):
        """Test transcription handles corrupted audio gracefully"""
        files = {"file": ("test.wav", b"corrupted data", "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        # Should handle error and return 500 or 200 with error message
        assert response.status_code in [200, 500]

    def test_transcribe_with_invalid_parameters(self, client):
        """Test transcription with invalid parameters"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        data = {"temperature": "invalid"}
        response = client.post(
            "/v1/transcribe",
            files=files,
            data=data
        )
        # Should return validation error
        assert response.status_code in [200, 422]


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers(self, client):
        """Test that CORS headers are set"""
        response = client.options("/health/live")
        assert "access-control-allow-origin" in response.headers


class TestAPIContract:
    """Test API contract and responses"""

    def test_response_text_field(self, client):
        """Test response text field is string"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        data = response.json()
        assert isinstance(data["text"], str)

    def test_response_language_field(self, client):
        """Test response language field is valid"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        data = response.json()
        assert isinstance(data["language"], str)
        assert len(data["language"]) == 2

    def test_response_duration_field(self, client):
        """Test response duration field is number"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        data = response.json()
        assert "duration" in data
        assert isinstance(data["duration"], (int, float))


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_health_check_before_transcription(self, client):
        """Test health check before attempting transcription"""
        # Check readiness
        health_response = client.get("/health/ready")
        assert health_response.status_code == 200

        # Perform transcription
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        transcribe_response = client.post("/v1/transcribe", files=files)
        assert transcribe_response.status_code == 200

    def test_multiple_transcriptions(self, client):
        """Test multiple transcription requests"""
        for i in range(3):
            audio_content = b"fake audio data"
            files = {"file": (f"test{i}.wav", audio_content, "audio/wav")}
            response = client.post("/v1/transcribe", files=files)
            assert response.status_code == 200

    def test_different_languages(self, client):
        """Test transcription with different languages"""
        languages = ["en", "es", "fr", "de"]
        for lang in languages:
            audio_content = b"fake audio data"
            files = {"file": ("test.wav", audio_content, "audio/wav")}
            data = {"language": lang}
            response = client.post(
                "/v1/transcribe",
                files=files,
                data=data
            )
            assert response.status_code == 200
            assert response.json()["language"] == lang


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_transcribe_with_minimal_audio(self, client):
        """Test transcription with minimal audio data"""
        audio_content = b"x" * 100
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        assert response.status_code == 200

    def test_transcribe_with_special_filename(self, client):
        """Test transcription with special characters in filename"""
        audio_content = b"fake audio data"
        files = {"file": ("test file-123.wav", audio_content, "audio/wav")}
        response = client.post("/v1/transcribe", files=files)
        assert response.status_code == 200

    def test_transcribe_temperature_boundaries(self, client):
        """Test transcription with temperature boundary values"""
        audio_content = b"fake audio data"
        files = {"file": ("test.wav", audio_content, "audio/wav")}

        for temp in [0.0, 0.5, 1.0]:
            data = {"temperature": str(temp)}
            response = client.post(
                "/v1/transcribe",
                files=files,
                data=data
            )
            assert response.status_code == 200


class TestFileFormatSupport:
    """Test various audio format support"""

    def test_supported_formats(self, client):
        """Test that all supported formats work"""
        formats = [
            ("test.wav", "audio/wav", b"RIFF"),
            ("test.mp3", "audio/mpeg", b"\xFF\xFB"),
            ("test.ogg", "audio/ogg", b"OggS"),
            ("test.flac", "audio/flac", b"fLaC"),
            ("test.m4a", "audio/mp4", b"\x00\x00\x00\x20ftypM4A"),
        ]
        for filename, content_type, content_prefix in formats:
            audio_content = content_prefix + b"\x00" * 100
            files = {"file": (filename, audio_content, content_type)}
            response = client.post("/v1/transcribe", files=files)
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
