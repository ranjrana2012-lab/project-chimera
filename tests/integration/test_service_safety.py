"""Safety Filter API tests."""
import pytest
from tests.fixtures.test_data import TestData


@pytest.mark.requires_services
class TestSafetyHealth:
    """Test Safety Filter health endpoints."""

    def test_health_live(self, base_urls, http_client):
        """Test /health/live endpoint."""
        response = http_client.get(f"{base_urls['safety']}/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.requires_services
class TestSafetyAPI:
    """Test Safety Filter API."""

    def test_check_safe_content(self, base_urls, http_client):
        """Test POST /api/v1/check with safe content."""
        response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json=TestData.SAFETY_REQUEST_SAFE,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "safe" in data or "decision" in data
        assert "confidence" in data

    def test_check_response_model_validation(self, base_urls, http_client):
        """Test response model has complete CategoryScore."""
        response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json=TestData.SAFETY_REQUEST_SAFE,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify CategoryScore has both score and flagged fields
        if "categories" in data:
            categories = data["categories"]
            for category_name, category_score in categories.items():
                # CategoryScore should have score and flagged
                assert "score" in category_score, f"Missing score in {category_name}"
                assert "flagged" in category_score, f"Missing flagged in {category_name}"

                # Verify types
                assert isinstance(category_score["score"], (int, float))
                assert 0.0 <= category_score["score"] <= 1.0
                assert isinstance(category_score["flagged"], bool)

    def test_check_with_flagged_content(self, base_urls, http_client):
        """Test checking potentially flagged content."""
        request = {
            "content": "The character showed intense anger and violence.",
            "context": "family_show"
        }

        response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify safety decision
        assert "safe" in data or "decision" in data
        assert "confidence" in data

    def test_check_empty_content(self, base_urls, http_client):
        """Test error handling for empty content."""
        request = {"content": "", "context": "test"}

        response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json=request,
            timeout=30
        )

        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]

    def test_filter_content(self, base_urls, http_client):
        """Test POST /api/v1/filter endpoint."""
        request = {
            "content": "The character should say something appropriate here.",
            "context": "family_show",
            "filter_level": "strict"
        }

        response = http_client.post(
            f"{base_urls['safety']}/api/v1/filter",
            json=request,
            timeout=30
        )

        # May return 200 if implemented or 404 if not
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Verify filter response
            assert "filtered_content" in data or "content" in data
            assert "safe" in data or "changes" in data

    def test_multiple_categories(self, base_urls, http_client):
        """Test checking multiple safety categories."""
        request = {
            "content": "Test content for checking.",
            "context": "test",
            "categories": ["profanity", "hate_speech", "sexual", "violence"]
        }

        response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify categories are checked
        if "categories" in data:
            for cat in ["profanity", "hate_speech", "sexual", "violence"]:
                if cat in data["categories"]:
                    assert "score" in data["categories"][cat]
                    assert "flagged" in data["categories"][cat]

    def test_review_queue(self, base_urls, http_client):
        """Test GET /api/v1/safety/review-queue endpoint."""
        response = http_client.get(
            f"{base_urls['safety']}/api/v1/safety/review-queue",
            timeout=30
        )

        # May return 200 with queue or 404 if not implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Should have items array
            assert "items" in data or "queue" in data

    def test_confidence_range(self, base_urls, http_client):
        """Test confidence is in valid range."""
        response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json=TestData.SAFETY_REQUEST_SAFE,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        if "confidence" in data:
            confidence = data["confidence"]
            assert isinstance(confidence, (int, float))
            assert 0.0 <= confidence <= 1.0

    def test_flagged_categories_list(self, base_urls, http_client):
        """Test flagged_categories is a list."""
        response = http_client.post(
            f"{base_urls['safety']}/api/v1/check",
            json=TestData.SAFETY_REQUEST_SAFE,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        if "flagged_categories" in data:
            flagged = data["flagged_categories"]
            assert isinstance(flagged, list)
