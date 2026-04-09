"""
Tests for BSL Agent Main Application.

Tests the FastAPI endpoints, health checks, and integration with translator and avatar renderer.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from translator import BSLTranslator


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def translator():
    """Create a BSL translator instance for testing"""
    return BSLTranslator()


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_liveness(self, client):
        """Test liveness probe"""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_readiness(self, client):
        """Test readiness probe"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "bsl-agent"
        assert "translator_ready" in data
        assert "avatar_ready" in data

    def test_readiness_translator_ready(self, client):
        """Test that readiness probe checks translator status"""
        response = client.get("/health/ready")
        data = response.json()
        # Translator should always be ready (rule-based)
        assert data["translator_ready"] is True


class TestTranslateEndpoint:
    """Test /v1/translate endpoint"""

    def test_translate_basic(self, client):
        """Test basic translation"""
        request_data = {
            "text": "Hello, how are you?",
            "include_nmm": True
        }

        response = client.post("/v1/translate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "gloss" in data
        assert "breakdown" in data
        assert "duration_estimate" in data
        assert "confidence" in data
        assert "non_manual_markers" in data
        assert "translation_time_ms" in data

        # Check gloss contains expected words
        assert "HELLO" in data["gloss"]
        assert "HOW" in data["gloss"]

    def test_translate_without_nmm(self, client):
        """Test translation without non-manual markers"""
        request_data = {
            "text": "What is your name?",
            "include_nmm": False
        }

        response = client.post("/v1/translate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # NMM should be None or empty
        assert data["non_manual_markers"] is None or len(data["non_manual_markers"]) == 0

    def test_translate_with_context(self, client):
        """Test translation with context"""
        request_data = {
            "text": "Thank you",
            "context": {
                "show_id": "test-show",
                "scene_number": "1"
            }
        }

        response = client.post("/v1/translate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "THANK YOU" in data["gloss"] or "THANK-YOU" in data["gloss"]

    def test_translate_empty_text(self, client):
        """Test translation with empty text"""
        request_data = {
            "text": ""
        }

        response = client.post("/v1/translate", json=request_data)

        # Should handle empty text gracefully
        assert response.status_code == 200 or response.status_code == 422

    def test_translate_missing_text_field(self, client):
        """Test translation with missing text field"""
        request_data = {}

        response = client.post("/v1/translate", json=request_data)

        # Should return validation error
        assert response.status_code == 422

    def test_translate_question(self, client):
        """Test translation of question with NMM"""
        request_data = {
            "text": "What is your name?",
            "include_nmm": True
        }

        response = client.post("/v1/translate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should have NMM markers for questions
        assert len(data["non_manual_markers"]) > 0
        assert any("brows" in marker for marker in data["non_manual_markers"])


class TestRenderEndpoint:
    """Test /v1/render endpoint"""

    def test_render_basic(self, client):
        """Test basic avatar rendering"""
        request_data = {
            "gloss": "HELLO HOW YOU",
            "include_nmm": True
        }

        response = client.post("/v1/render", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "animation_data" in data
        assert "gestures_queued" in data

        assert data["success"] is True
        assert data["gestures_queued"] == 3  # Three words

    def test_render_with_session_id(self, client):
        """Test rendering with session ID"""
        request_data = {
            "gloss": "THANK YOU",
            "session_id": "test-session-123"
        }

        response = client.post("/v1/render", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["session_id"] == "test-session-123"

    def test_render_animation_data_structure(self, client):
        """Test that animation data has correct structure"""
        request_data = {
            "gloss": "HELLO"
        }

        response = client.post("/v1/render", json=request_data)

        assert response.status_code == 200
        data = response.json()
        animation = data["animation_data"]

        # Check animation data structure
        assert "format" in animation
        assert "gestures" in animation
        assert "fps" in animation
        assert "total_duration" in animation
        assert "resolution" in animation
        assert "metadata" in animation

        # Check gestures array
        assert len(animation["gestures"]) == 1
        gesture = animation["gestures"][0]
        assert "gloss" in gesture
        assert "duration" in gesture
        assert gesture["gloss"] == "HELLO"

    def test_render_empty_gloss(self, client):
        """Test rendering with empty gloss"""
        request_data = {
            "gloss": ""
        }

        response = client.post("/v1/render", json=request_data)

        # Should handle empty gloss gracefully
        assert response.status_code == 200 or response.status_code == 422

    def test_render_missing_gloss_field(self, client):
        """Test rendering with missing gloss field"""
        request_data = {}

        response = client.post("/v1/render", json=request_data)

        # Should return validation error
        assert response.status_code == 422


class TestMetricsEndpoint:
    """Test /metrics endpoint"""

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Prometheus metrics endpoint should return text/plain
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_content(self, client):
        """Test that metrics endpoint returns actual metrics"""
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        # Should contain Prometheus metric comments or bsl metrics
        assert "#" in content or "bsl" in content.lower()


class TestIntegration:
    """Integration tests"""

    def test_translate_then_render(self, client):
        """Test translation followed by rendering"""
        # First translate
        translate_request = {
            "text": "Hello world",
            "include_nmm": True
        }

        translate_response = client.post("/v1/translate", json=translate_request)
        assert translate_response.status_code == 200

        translate_data = translate_response.json()
        gloss = translate_data["gloss"]
        nmm = translate_data["non_manual_markers"]

        # Then render the gloss
        render_request = {
            "gloss": gloss,
            "include_nmm": True
        }

        render_response = client.post("/v1/render", json=render_request)
        assert render_response.status_code == 200

        render_data = render_response.json()
        assert render_data["success"] is True
        assert len(render_data["animation_data"]["gestures"]) > 0

    def test_multiple_translations(self, client):
        """Test multiple translation requests"""
        texts = [
            "Hello",
            "Thank you",
            "What is your name?",
            "I don't understand"
        ]

        for text in texts:
            request_data = {"text": text}
            response = client.post("/v1/translate", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert "gloss" in data
            assert len(data["gloss"]) > 0

    def test_translation_performance(self, client):
        """Test that translation completes in reasonable time"""
        import time

        request_data = {
            "text": "This is a longer sentence with more words to translate",
            "include_nmm": True
        }

        start_time = time.time()
        response = client.post("/v1/translate", json=request_data)
        duration = time.time() - start_time

        assert response.status_code == 200
        # Should complete in less than 1 second
        assert duration < 1.0
