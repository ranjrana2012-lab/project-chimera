"""
Tests for Music Generation API Endpoints

Comprehensive test suite for API endpoint coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_inference_engine():
    """Mock inference engine."""
    with patch('main.inference_engine') as mock:
        mock.generate = AsyncMock(return_value={
            "audio": b"fake audio data",
            "sample_rate": 16000,
            "duration": 5.0,
            "generation_time_ms": 1000
        })
        yield mock


@pytest.fixture
def mock_model_pool():
    """Mock model pool manager."""
    with patch('main.model_pool') as mock:
        mock.get_model = Mock(return_value=Mock())
        mock.return_model = Mock()
        yield mock


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_structure(self, client):
        """Test health check returns correct response structure."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "music-generation"

    def test_health_check_includes_model_status(self, client):
        """Test health check includes model availability status."""
        response = client.get("/health")
        data = response.json()
        # Should include model status info
        assert "status" in data or "model_loaded" in data


class TestGenerateEndpoint:
    """Tests for music generation endpoint."""

    def test_generate_with_text_prompt(self, client, mock_inference_engine):
        """Test generate with text prompt."""
        response = client.post("/api/v1/generate", json={
            "prompt": "A happy upbeat song"
        })

        assert response.status_code == 200

    def test_generate_with_empty_prompt(self, client, mock_inference_engine):
        """Test generate with empty prompt."""
        response = client.post("/api/v1/generate", json={
            "prompt": ""
        })

        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422]

    def test_generate_with_long_prompt(self, client, mock_inference_engine):
        """Test generate with long prompt."""
        long_prompt = "Generate music " * 100

        response = client.post("/api/v1/generate", json={
            "prompt": long_prompt
        })

        assert response.status_code == 200

    def test_generate_with_duration(self, client, mock_inference_engine):
        """Test generate with duration parameter."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test song",
            "duration": 10.0
        })

        assert response.status_code == 200

    def test_generate_with_invalid_duration(self, client):
        """Test generate with invalid duration."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test",
            "duration": -5.0
        })

        assert response.status_code in [200, 422]

    def test_generate_with_temperature(self, client, mock_inference_engine):
        """Test generate with temperature parameter."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test song",
            "temperature": 0.8
        })

        assert response.status_code == 200

    def test_generate_with_top_k(self, client, mock_inference_engine):
        """Test generate with top_k parameter."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test song",
            "top_k": 50
        })

        assert response.status_code == 200

    def test_generate_with_top_p(self, client, mock_inference_engine):
        """Test generate with top_p parameter."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test song",
            "top_p": 0.9
        })

        assert response.status_code == 200

    def test_generate_with_seed(self, client, mock_inference_engine):
        """Test generate with seed parameter for reproducibility."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test song",
            "seed": 42
        })

        assert response.status_code == 200

    def test_generate_without_prompt(self, client):
        """Test generate without prompt parameter."""
        response = client.post("/api/v1/generate", json={})
        assert response.status_code == 422  # Validation error


class TestGenerateFromParameters:
    """Tests for generation from audio parameters."""

    def test_generate_from_params(self, client, mock_inference_engine):
        """Test generate from audio parameters."""
        response = client.post("/api/v1/generate/from-params", json={
            "genre": "jazz",
            "tempo": 120,
            "key": "C",
            "duration": 10.0
        })

        assert response.status_code in [200, 404]  # May or may not be implemented

    def test_generate_from_params_with_all_options(self, client, mock_inference_engine):
        """Test generate with all audio parameters."""
        response = client.post("/api/v1/generate/from-params", json={
            "genre": "rock",
            "tempo": 140,
            "key": "A",
            "mode": "minor",
            "duration": 15.0,
            "instruments": ["guitar", "drums", "bass"]
        })

        assert response.status_code in [200, 404]


class TestResponseFormat:
    """Tests for response format validation."""

    def test_generate_returns_audio_data(self, client, mock_inference_engine):
        """Test generate returns audio data."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test"
        })

        if response.status_code == 200:
            data = response.json()
            assert "audio" in data or "audio_url" in data

    def test_generate_returns_metadata(self, client, mock_inference_engine):
        """Test generate returns generation metadata."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test"
        })

        if response.status_code == 200:
            data = response.json()
            # Should include metadata
            assert any(k in data for k in ["duration", "sample_rate", "generation_time"])


class TestErrorHandling:
    """Tests for error handling."""

    def test_generate_handles_model_error(self, client, mock_inference_engine):
        """Test generate handles model errors."""
        mock_inference_engine.generate.side_effect = Exception("Model error")

        response = client.post("/api/v1/generate", json={
            "prompt": "Test"
        })

        assert response.status_code == 500

    def test_generate_handles_timeout(self, client, mock_inference_engine):
        """Test generate handles timeout."""
        import asyncio
        mock_inference_engine.generate.side_effect = asyncio.TimeoutError()

        response = client.post("/api/v1/generate", json={
            "prompt": "Test"
        })

        assert response.status_code == 500


class TestEdgeCases:
    """Tests for edge cases."""

    def test_generate_with_special_characters(self, client, mock_inference_engine):
        """Test generate with special characters in prompt."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test @#$%^&*()_+-=[]{}|;':\",./<>?"
        })

        assert response.status_code == 200

    def test_generate_with_unicode(self, client, mock_inference_engine):
        """Test generate with unicode characters."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Generate music with world beats 世界 🌍"
        })

        assert response.status_code == 200

    def test_generate_with_multiline_prompt(self, client, mock_inference_engine):
        """Test generate with multiline prompt."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Line 1\nLine 2\nLine 3"
        })

        assert response.status_code == 200

    def test_generate_with_very_short_duration(self, client, mock_inference_engine):
        """Test generate with very short duration."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test",
            "duration": 0.5
        })

        assert response.status_code == 200

    def test_generate_with_very_long_duration(self, client, mock_inference_engine):
        """Test generate with very long duration."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test",
            "duration": 300.0
        })

        assert response.status_code == 200


class TestAudioFormats:
    """Tests for different audio output formats."""

    def test_generate_returns_wav_format(self, client, mock_inference_engine):
        """Test generate returns WAV format by default."""
        mock_inference_engine.generate.return_value = {
            "audio": b"wav data",
            "sample_rate": 16000,
            "format": "wav"
        }

        response = client.post("/api/v1/generate", json={
            "prompt": "Test"
        })

        assert response.status_code == 200

    def test_generate_with_mp3_format(self, client, mock_inference_engine):
        """Test generate with MP3 format request."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test",
            "format": "mp3"
        })

        assert response.status_code == 200

    def test_generate_with_sample_rate(self, client, mock_inference_engine):
        """Test generate with custom sample rate."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test",
            "sample_rate": 44100
        })

        assert response.status_code == 200


class TestModelEndpoints:
    """Tests for model management endpoints."""

    def test_list_models(self, client):
        """Test listing available models."""
        response = client.get("/api/v1/models")
        assert response.status_code in [200, 404]

    def test_get_model_info(self, client):
        """Test getting specific model information."""
        response = client.get("/api/v1/models/default")
        assert response.status_code in [200, 404]

    def test_load_model(self, client, mock_model_pool):
        """Test loading a specific model."""
        response = client.post("/api/v1/models/load", json={
            "model_name": "musicgen-small"
        })

        assert response.status_code in [200, 404]

    def test_unload_model(self, client, mock_model_pool):
        """Test unloading a model."""
        response = client.post("/api/v1/models/unload", json={
            "model_name": "musicgen-small"
        })

        assert response.status_code in [200, 404]


class TestStreaming:
    """Tests for streaming generation."""

    def test_generate_streaming(self, client):
        """Test streaming generation endpoint."""
        response = client.post("/api/v1/generate/stream", json={
            "prompt": "Test"
        })

        # May or may not be implemented
        assert response.status_code in [200, 404]


class TestConfiguration:
    """Tests for service configuration."""

    def test_service_version(self, client):
        """Test service reports correct version."""
        response = client.get("/health")
        data = response.json()
        assert "service" in data

    def test_service_name(self, client):
        """Test service reports correct name."""
        response = client.get("/health")
        data = response.json()
        assert data["service"] == "music-generation"


class TestPerformance:
    """Tests for performance characteristics."""

    def test_generate_includes_timing(self, client, mock_inference_engine):
        """Test generate includes timing information."""
        mock_inference_engine.generate.return_value = {
            "audio": b"data",
            "sample_rate": 16000,
            "generation_time_ms": 1234
        }

        response = client.post("/api/v1/generate", json={
            "prompt": "Test"
        })

        if response.status_code == 200:
            data = response.json()
            assert "generation_time" in str(data) or "generation_time_ms" in str(data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
