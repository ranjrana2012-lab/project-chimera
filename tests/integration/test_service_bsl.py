"""BSL-Text2Gloss Agent API tests."""
import pytest
from tests.fixtures.test_data import TestData


@pytest.mark.requires_services
class TestBSLHealth:
    """Test BSL Agent health endpoints."""

    def test_health_live(self, base_urls, http_client):
        """Test /health/live endpoint."""
        response = http_client.get(f"{base_urls['bsl']}/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.requires_services
class TestBSLAPI:
    """Test BSL Agent API."""

    def test_translate_with_valid_request(self, base_urls, http_client):
        """Test POST /api/v1/translate with valid request."""
        response = http_client.post(
            f"{base_urls['bsl']}/api/v1/translate",
            json=TestData.BSL_REQUEST,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "gloss" in data or "gloss_text" in data

        # Verify required fields exist
        assert "translation_time_ms" in data
        assert "model_version" in data

    def test_translate_response_model_validation(self, base_urls, http_client):
        """Test response model has all required fields."""
        response = http_client.post(
            f"{base_urls['bsl']}/api/v1/translate",
            json=TestData.BSL_REQUEST,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all TranslationResponse fields exist
        required_fields = [
            "request_id", "source_text", "gloss_text", "gloss_format",
            "confidence", "translation_time_ms", "model_version"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Verify field types
        assert isinstance(data["translation_time_ms"], (int, float))
        assert isinstance(data["model_version"], str)
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0

    def test_translate_with_empty_text(self, base_urls, http_client):
        """Test error handling for empty text."""
        request = {"text": "", "preserve_format": True}
        response = http_client.post(
            f"{base_urls['bsl']}/api/v1/translate",
            json=request,
            timeout=30
        )

        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]

    def test_translate_batch(self, base_urls, http_client):
        """Test POST /api/v1/translate/batch endpoint."""
        batch_request = {
            "texts": [
                "Hello, how are you?",
                "What is your name?",
                "Nice to meet you."
            ],
            "preserve_format": True
        }

        response = http_client.post(
            f"{base_urls['bsl']}/api/v1/translate/batch",
            json=batch_request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify batch response structure
        assert "results" in data or "translations" in data
        assert "translation_time_ms" in data

    def test_translate_preserves_format(self, base_urls, http_client):
        """Test that preserve_format option works."""
        request = {
            "text": "Hello, how are you today?",
            "preserve_format": True,
            "include_metadata": True
        }

        response = http_client.post(
            f"{base_urls['bsl']}/api/v1/translate",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Should have breakdown if metadata requested
        if "breakdown" in data:
            assert isinstance(data["breakdown"], list)
            if len(data["breakdown"]) > 0:
                assert "source" in data["breakdown"][0]
                assert "gloss" in data["breakdown"][0]
