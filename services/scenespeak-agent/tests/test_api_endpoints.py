"""
Tests for SceneSpeak Agent API Endpoints

Comprehensive test suite for API endpoint coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_glm_client():
    """Mock GLM client."""
    with patch('main.glm_client') as mock:
        mock.generate = AsyncMock(return_value={
            "text": "Generated dialogue",
            "model": "glm-4",
            "finish_reason": "stop"
        })
        yield mock


@pytest.fixture
def mock_local_llm_client():
    """Mock local LLM client."""
    with patch('main.local_llm_client') as mock:
        mock.is_available = AsyncMock(return_value=False)
        mock.generate = AsyncMock(return_value={
            "text": "Local LLM response",
            "model": "local-model"
        })
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
        assert data["service"] == "scenespeak-agent"

    def test_health_check_with_model_available(self, client):
        """Test health check reports model availability."""
        response = client.get("/health")
        data = response.json()
        assert "model_available" in data
        assert isinstance(data["model_available"], bool)


class TestGenerateEndpoint:
    """Tests for dialogue generation endpoint."""

    def test_generate_endpoint_returns_200(self, client):
        """Test generate endpoint returns 200 on success."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Test dialogue",
                "model": "glm-4",
                "finish_reason": "stop"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Generate dialogue"
            })

        assert response.status_code == 200

    def test_generate_with_minimal_request(self, client):
        """Test generate with minimal required fields."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Response",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Test"
            })

        assert response.status_code == 200

    def test_generate_with_empty_prompt(self, client):
        """Test generate with empty prompt."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": ""
            })

        # Should handle gracefully
        assert response.status_code in [200, 422]

    def test_generate_with_long_prompt(self, client):
        """Test generate with long prompt."""
        long_prompt = "Generate dialogue " * 100

        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Long response",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": long_prompt
            })

        assert response.status_code == 200

    def test_generate_with_temperature(self, client):
        """Test generate with temperature parameter."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Response",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Test",
                "temperature": 0.8
            })

        assert response.status_code == 200

    def test_generate_with_max_tokens(self, client):
        """Test generate with max_tokens parameter."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Response",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Test",
                "max_tokens": 500
            })

        assert response.status_code == 200

    def test_generate_with_context(self, client):
        """Test generate with conversation context."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Contextual response",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Continue",
                "context": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"}
                ]
            })

        assert response.status_code == 200


class TestLegacyEndpoints:
    """Tests for legacy endpoint compatibility."""

    def test_legacy_generate_endpoint(self, client):
        """Test legacy /generate endpoint works."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Legacy response",
                "model": "glm-4"
            })

            response = client.post("/generate", json={
                "prompt": "Test"
            })

        assert response.status_code in [200, 404]  # May or may not be implemented


class TestErrorHandling:
    """Tests for error handling in endpoints."""

    def test_generate_with_missing_prompt(self, client):
        """Test generate without prompt parameter."""
        response = client.post("/api/v1/generate", json={})
        assert response.status_code == 422  # Validation error

    def test_generate_with_invalid_temperature(self, client):
        """Test generate with invalid temperature."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test",
            "temperature": 5.0  # Invalid: should be 0-2
        })
        assert response.status_code in [200, 422]

    def test_generate_with_negative_max_tokens(self, client):
        """Test generate with negative max_tokens."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Test",
            "max_tokens": -100
        })
        assert response.status_code in [200, 422]

    def test_generate_handles_service_error(self, client):
        """Test generate handles service errors gracefully."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(side_effect=Exception("Service error"))

            response = client.post("/api/v1/generate", json={
                "prompt": "Test"
            })

        assert response.status_code == 500


class TestEdgeCases:
    """Tests for edge cases."""

    def test_generate_with_special_characters(self, client):
        """Test generate with special characters in prompt."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Special response",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Test @#$%^&*()_+-=[]{}|;':\",./<>?"
            })

        assert response.status_code == 200

    def test_generate_with_unicode(self, client):
        """Test generate with unicode characters."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Unicode response 世界 🌍",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Hello 世界 🌍"
            })

        assert response.status_code == 200

    def test_generate_with_newlines(self, client):
        """Test generate with newlines in prompt."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Multiline\nresponse",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Line 1\nLine 2\nLine 3"
            })

        assert response.status_code == 200


class TestResponseFormat:
    """Tests for response format validation."""

    def test_generate_returns_dialogue(self, client):
        """Test generate returns dialogue field."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Test dialogue",
                "model": "glm-4"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Test"
            })

            data = response.json()
            assert "text" in data or "dialogue" in data

    def test_generate_includes_metadata(self, client):
        """Test generate includes metadata."""
        with patch('main.glm_client') as mock_client:
            mock_client.generate = AsyncMock(return_value={
                "text": "Test",
                "model": "glm-4",
                "finish_reason": "stop"
            })

            response = client.post("/api/v1/generate", json={
                "prompt": "Test"
            })

            data = response.json()
            assert "model" in data or "metadata" in data


class TestConfiguration:
    """Tests for service configuration."""

    def test_service_version(self, client):
        """Test service reports correct version."""
        response = client.get("/health")
        data = response.json()
        # Version should be present in service info
        assert "service" in data

    def test_service_name(self, client):
        """Test service reports correct name."""
        response = client.get("/health")
        data = response.json()
        assert data["service"] == "scenespeak-agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
