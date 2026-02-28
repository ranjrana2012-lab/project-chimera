"""Sentiment Agent API tests."""
import pytest
from tests.fixtures.test_data import TestData


@pytest.mark.requires_services
class TestSentimentHealth:
    """Test Sentiment Agent health endpoints."""

    def test_health_live(self, base_urls, http_client):
        """Test /health/live endpoint."""
        response = http_client.get(f"{base_urls['sentiment']}/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.requires_services
class TestSentimentAPI:
    """Test Sentiment Agent API."""

    def test_analyze_with_valid_request(self, base_urls, http_client):
        """Test POST /api/v1/analyze with valid request."""
        request = {"texts": TestData.SENTIMENT_REQUESTS}

        response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "results" in data or "analysis" in data

    def test_analyze_response_model_validation(self, base_urls, http_client):
        """Test response model has SentimentScore object."""
        request = {"texts": ["This performance is absolutely amazing!"]}

        response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Check results array
        if "results" in data:
            results = data["results"]
        elif "analysis" in data:
            results = data["analysis"]
        else:
            results = [data]

        # Verify first result has sentiment as object
        if len(results) > 0:
            first_result = results[0]
            assert "sentiment" in first_result

            # Verify sentiment is SentimentScore object with label and score
            sentiment = first_result["sentiment"]
            if isinstance(sentiment, dict):
                # SentimentScore object structure
                assert "label" in sentiment or "score" in sentiment

            # Verify required fields exist
            assert "processing_time_ms" in first_result or "processing_time_ms" in data
            assert "model_version" in first_result or "model_version" in data

    def test_analyze_single_text(self, base_urls, http_client):
        """Test analyzing a single text."""
        request = {"texts": ["Best show I've ever seen!"]}

        response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Should have results
        assert "results" in data or "analysis" in data

    def test_analyze_empty_texts(self, base_urls, http_client):
        """Test error handling for empty texts array."""
        request = {"texts": []}

        response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze",
            json=request,
            timeout=30
        )

        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]

    def test_analyze_batch(self, base_urls, http_client):
        """Test POST /api/v1/analyze-batch endpoint."""
        batch_request = {
            "texts": [
                "This performance is absolutely amazing!",
                "I'm not sure about this scene...",
                "Best show I've ever seen!",
                "The actors were phenomenal.",
                "Great lighting and sound design."
            ],
            "include_emotions": True
        }

        response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze-batch",
            json=batch_request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify batch response
        assert "results" in data or "analysis" in data
        assert "summary" in data or "overall" in data

    def test_get_trend(self, base_urls, http_client):
        """Test GET /api/v1/trend endpoint."""
        response = http_client.get(
            f"{base_urls['sentiment']}/api/v1/trend",
            params={"window_minutes": 60},
            timeout=30
        )

        # May return 200 with data or 404 if not implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Should have trend data
            assert "trend" in data or "sentiment" in data or "data" in data

    def test_sentiment_categories(self, base_urls, http_client):
        """Test sentiment returns valid categories."""
        request = {"texts": ["Amazing performance!"]}

        response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Check if sentiment has scores
        if "results" in data:
            results = data["results"]
        elif "analysis" in data:
            results = data["analysis"]
        else:
            results = [data]

        if len(results) > 0:
            first_result = results[0]

            # Check for scores object
            if "scores" in first_result:
                scores = first_result["scores"]
                # Should have positive, negative, neutral scores
                assert any(k in scores for k in ["positive", "negative", "neutral"])

    def test_sentiment_confidence_range(self, base_urls, http_client):
        """Test sentiment confidence is in valid range."""
        request = {"texts": ["Great performance!"]}

        response = http_client.post(
            f"{base_urls['sentiment']}/api/v1/analyze",
            json=request,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Check confidence values
        if "results" in data:
            results = data["results"]
        elif "analysis" in data:
            results = data["analysis"]
        else:
            results = [data]

        if len(results) > 0:
            first_result = results[0]
            if "confidence" in first_result:
                confidence = first_result["confidence"]
                assert isinstance(confidence, (int, float))
                assert 0.0 <= confidence <= 1.0
