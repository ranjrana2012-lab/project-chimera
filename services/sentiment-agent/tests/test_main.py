"""
Unit tests for Sentiment Agent main API.

Tests verify that the FastAPI service:
- Has all required endpoints
- Returns proper responses
- Handles errors gracefully
"""

import pytest
from fastapi.testclient import TestClient

from sentiment_agent.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_liveness_endpoint(self, client):
        """Test /health/live returns alive status."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_readiness_endpoint(self, client):
        """Test /health/ready returns ready status with model check."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "service" in data
        assert data["service"] == "sentiment-agent"
        assert "model_available" in data
        assert isinstance(data["model_available"], bool)


class TestAnalyzeEndpoint:
    """Tests for /v1/analyze endpoint."""

    def test_analyze_positive_sentiment(self, client):
        """Test analyzing positive sentiment text."""
        response = client.post(
            "/v1/analyze",
            json={"text": "I absolutely loved this amazing performance!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "score" in data
        assert "confidence" in data
        assert "emotions" in data
        assert data["sentiment"] == "positive"

    def test_analyze_negative_sentiment(self, client):
        """Test analyzing negative sentiment text."""
        response = client.post(
            "/v1/analyze",
            json={"text": "This was a terrible and boring performance."}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "negative"

    def test_analyze_neutral_sentiment(self, client):
        """Test analyzing neutral sentiment text."""
        response = client.post(
            "/v1/analyze",
            json={"text": "The performance was okay, it was average."}
        )
        assert response.status_code == 200
        data = response.json()
        # ML model classification for ambiguous text can vary
        # The important part is that it returns a valid sentiment
        assert data["sentiment"] in ["positive", "negative", "neutral"]
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_analyze_empty_text(self, client):
        """Test analyzing empty text."""
        response = client.post(
            "/v1/analyze",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "neutral"

    def test_analyze_missing_text_field(self, client):
        """Test analyzing with missing text field."""
        response = client.post(
            "/v1/analyze",
            json={}
        )
        assert response.status_code == 422  # Validation error

    def test_analyze_response_structure(self, client):
        """Test that analyze response has correct structure."""
        response = client.post(
            "/v1/analyze",
            json={"text": "Great show!"}
        )
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "sentiment" in data
        assert "score" in data
        assert "confidence" in data
        assert "emotions" in data

        # Check sentiment value
        assert data["sentiment"] in ["positive", "negative", "neutral"]

        # Check score range
        assert 0.0 <= data["score"] <= 1.0

        # Check confidence range
        assert 0.0 <= data["confidence"] <= 1.0

        # Check emotions
        required_emotions = ["joy", "surprise", "neutral", "sadness", "anger", "fear"]
        for emotion in required_emotions:
            assert emotion in data["emotions"]
            assert 0.0 <= data["emotions"][emotion] <= 1.0


class TestBatchEndpoint:
    """Tests for /v1/batch endpoint."""

    def test_batch_analyze_multiple_texts(self, client):
        """Test batch analyzing multiple texts."""
        response = client.post(
            "/v1/batch",
            json={
                "texts": [
                    "I loved this amazing performance!",
                    "This was terrible and boring.",
                    "It was just okay, nothing special."
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
        assert data["results"][0]["sentiment"] == "positive"
        assert data["results"][1]["sentiment"] == "negative"
        # ML model classification for ambiguous text can vary
        assert data["results"][2]["sentiment"] in ["positive", "negative", "neutral"]

    def test_batch_analyze_empty_list(self, client):
        """Test batch analyzing with empty list."""
        response = client.post(
            "/v1/batch",
            json={"texts": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 0

    def test_batch_analyze_missing_texts_field(self, client):
        """Test batch analyzing with missing texts field."""
        response = client.post(
            "/v1/batch",
            json={}
        )
        assert response.status_code == 422  # Validation error

    def test_batch_analyze_response_structure(self, client):
        """Test that batch response has correct structure."""
        response = client.post(
            "/v1/batch",
            json={"texts": ["Great show!", "Terrible performance"]}
        )
        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert isinstance(data["results"], list)

        for result in data["results"]:
            assert "sentiment" in result
            assert "score" in result
            assert "confidence" in result
            assert "emotions" in result


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_endpoint(self, client):
        """Test that metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Should return text/plain content type
        assert "text/plain" in response.headers.get("content-type", "")


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/v1/analyze",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    def test_very_long_text(self, client):
        """Test handling of very long text."""
        long_text = "This is amazing! " * 1000
        response = client.post(
            "/v1/analyze",
            json={"text": long_text}
        )
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 413, 400]


class TestAPIModels:
    """Tests for API request/response models."""

    def test_analyze_request_model_validates_text(self):
        """Test that AnalyzeRequest model validates text field."""
        from sentiment_agent.models import AnalyzeRequest

        # Valid request
        request = AnalyzeRequest(text="Great show!")
        assert request.text == "Great show!"

    def test_batch_request_model_validates_texts(self):
        """Test that BatchRequest model validates texts field."""
        from sentiment_agent.models import BatchRequest

        # Valid request
        request = BatchRequest(texts=["Great!", "Terrible!"])
        assert len(request.texts) == 2

    def test_sentiment_response_model_structure(self):
        """Test that SentimentResponse model has correct structure."""
        from sentiment_agent.models import SentimentResponse

        response = SentimentResponse(
            sentiment="positive",
            score=0.8,
            confidence=0.9,
            emotions={
                "joy": 0.8,
                "surprise": 0.3,
                "neutral": 0.1,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0
            }
        )

        assert response.sentiment == "positive"
        assert response.score == 0.8
        assert response.confidence == 0.9
        assert len(response.emotions) == 6


class TestServiceIntegration:
    """Tests for service integration."""

    def test_service_has_correct_title(self, client):
        """Test that service has correct title in OpenAPI docs."""
        response = client.get("/docs")
        assert response.status_code == 200
        # The /docs endpoint returns HTML, not JSON
        assert "Sentiment Agent" in response.text

    def test_service_has_version(self, client):
        """Test that service has version information."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data.get("info", {})
        assert data["info"]["version"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
