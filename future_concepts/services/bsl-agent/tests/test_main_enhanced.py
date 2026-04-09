"""
Enhanced tests for BSL Agent Main Application.

Comprehensive tests for FastAPI endpoints, error handling, and integration scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import time

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestHealthEndpointsEnhanced:
    """Enhanced tests for health check endpoints"""

    def test_liveness_returns_json(self, client):
        """Test liveness returns proper JSON content type"""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_readiness_all_fields(self, client):
        """Test readiness includes all expected fields"""
        response = client.get("/health/ready")
        data = response.json()
        expected_fields = ["status", "service", "translator_ready", "avatar_ready"]
        for field in expected_fields:
            assert field in data

    def test_readiness_values(self, client):
        """Test readiness returns correct values"""
        response = client.get("/health/ready")
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "bsl-agent"
        assert data["translator_ready"] is True
        assert data["avatar_ready"] is True


class TestTranslateEndpointEnhanced:
    """Enhanced tests for /v1/translate endpoint"""

    def test_translate_minimal_request(self, client):
        """Test translation with minimal request"""
        request_data = {"text": "Hello"}
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "gloss" in data
        assert len(data["gloss"]) > 0

    def test_translate_with_all_options(self, client):
        """Test translation with all options enabled"""
        request_data = {
            "text": "Hello world",
            "include_nmm": True,
            "context": {
                "show_id": "test-show",
                "scene_number": "1",
                "custom_field": "value"
            }
        }
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["non_manual_markers"] is not None

    def test_translate_response_structure(self, client):
        """Test translation response has correct structure"""
        request_data = {"text": "Hello"}
        response = client.post("/v1/translate", json=request_data)
        data = response.json()
        expected_fields = [
            "gloss", "breakdown", "duration_estimate",
            "confidence", "non_manual_markers", "translation_time_ms"
        ]
        for field in expected_fields:
            assert field in data

    def test_translate_question_includes_nmm(self, client):
        """Test that questions get NMM markers"""
        request_data = {
            "text": "What is your name?",
            "include_nmm": True
        }
        response = client.post("/v1/translate", json=request_data)
        data = response.json()
        assert len(data["non_manual_markers"]) > 0
        assert any("brows" in m for m in data["non_manual_markers"])

    def test_translate_exclamation_includes_nmm(self, client):
        """Test that exclamations get NMM markers"""
        request_data = {
            "text": "Great!",
            "include_nmm": True
        }
        response = client.post("/v1/translate", json=request_data)
        data = response.json()
        assert len(data["non_manual_markers"]) > 0

    def test_translate_negation_includes_nmm(self, client):
        """Test that negations get NMM markers"""
        request_data = {
            "text": "I do not understand",
            "include_nmm": True
        }
        response = client.post("/v1/translate", json=request_data)
        data = response.json()
        assert len(data["non_manual_markers"]) > 0
        assert any("shake" in m for m in data["non_manual_markers"])

    def test_translate_with_context_show_id(self, client):
        """Test translation with show_id in context"""
        request_data = {
            "text": "Hello",
            "context": {"show_id": "my-show-123"}
        }
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 200

    def test_translate_long_text(self, client):
        """Test translation of long text"""
        long_text = " ".join(["word"] * 100)
        request_data = {"text": long_text}
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["breakdown"]) == 100

    def test_translate_with_special_characters(self, client):
        """Test translation with special characters"""
        request_data = {"text": "Hello, @world! #test"}
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 200

    def test_translate_with_unicode(self, client):
        """Test translation with unicode characters"""
        request_data = {"text": "Hello 世界 🌍"}
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 200

    def test_translate_with_newlines(self, client):
        """Test translation with newlines"""
        request_data = {"text": "Hello\nworld"}
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 200

    def test_translate_confidence_range(self, client):
        """Test that confidence is in valid range"""
        request_data = {"text": "hello thank you"}
        response = client.post("/v1/translate", json=request_data)
        data = response.json()
        assert 0 <= data["confidence"] <= 1

    def test_translate_duration_estimate(self, client):
        """Test that duration estimate is reasonable"""
        request_data = {"text": "hello world"}
        response = client.post("/v1/translate", json=request_data)
        data = response.json()
        # 2 words * 0.5 seconds = 1.0 second
        assert data["duration_estimate"] == 1.0

    def test_translate_translation_time_recorded(self, client):
        """Test that translation time is recorded"""
        request_data = {"text": "hello world"}
        response = client.post("/v1/translate", json=request_data)
        data = response.json()
        assert data["translation_time_ms"] >= 0

    def test_translate_invalid_json(self, client):
        """Test translation with invalid JSON"""
        response = client.post(
            "/v1/translate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_translate_missing_content_type(self, client):
        """Test translation without content-type header"""
        response = client.post("/v1/translate", data="text")
        assert response.status_code in [422, 415]

    def test_translate_with_whitespace_only(self, client):
        """Test translation with whitespace only"""
        request_data = {"text": "   "}
        response = client.post("/v1/translate", json=request_data)
        # Should handle gracefully - either 200 or 422
        assert response.status_code in [200, 422]

    def test_translate_case_preservation(self, client):
        """Test that translation is case-insensitive"""
        request1 = {"text": "HELLO"}
        request2 = {"text": "hello"}
        response1 = client.post("/v1/translate", json=request1)
        response2 = client.post("/v1/translate", json=request2)
        assert response1.json()["gloss"] == response2.json()["gloss"]


class TestRenderEndpointEnhanced:
    """Enhanced tests for /v1/render endpoint"""

    def test_render_minimal_request(self, client):
        """Test rendering with minimal request"""
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_render_with_all_options(self, client):
        """Test rendering with all options"""
        request_data = {
            "gloss": "HELLO WORLD",
            "session_id": "test-session-123",
            "include_nmm": True
        }
        response = client.post("/v1/render", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"

    def test_render_response_structure(self, client):
        """Test render response has correct structure"""
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        expected_fields = ["success", "animation_data", "gestures_queued", "session_id", "message"]
        for field in expected_fields:
            assert field in data

    def test_render_animation_data_structure(self, client):
        """Test animation data has correct structure"""
        request_data = {"gloss": "HELLO WORLD"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        animation = data["animation_data"]

        expected_fields = ["format", "version", "resolution", "fps", "total_duration",
                          "frame_count", "gestures", "non_manual_markers", "metadata"]
        for field in expected_fields:
            assert field in animation

    def test_render_gesture_count_matches_words(self, client):
        """Test that gesture count matches word count"""
        request_data = {"gloss": "HELLO HOW ARE YOU"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        assert data["gestures_queued"] == 4

    def test_render_animation_format(self, client):
        """Test animation format version"""
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        assert data["animation_data"]["format"] == "bsl-animation-v1"

    def test_render_animation_resolution(self, client):
        """Test animation resolution"""
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        assert data["animation_data"]["resolution"]["width"] == 1920
        assert data["animation_data"]["resolution"]["height"] == 1080

    def test_render_animation_fps(self, client):
        """Test animation FPS"""
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        assert data["animation_data"]["fps"] == 30

    def test_render_with_session_id(self, client):
        """Test rendering with session ID"""
        request_data = {
            "gloss": "HELLO",
            "session_id": "session-abc-123"
        }
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        assert data["session_id"] == "session-abc-123"

    def test_render_without_session_id(self, client):
        """Test rendering without session ID"""
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        assert data["session_id"] is None

    def test_render_with_special_characters(self, client):
        """Test rendering with special characters"""
        request_data = {"gloss": "HELLO! @WORLD#"}
        response = client.post("/v1/render", json=request_data)
        assert response.status_code == 200

    def test_render_with_unicode(self, client):
        """Test rendering with unicode characters"""
        request_data = {"gloss": "HELLO 世界"}
        response = client.post("/v1/render", json=request_data)
        assert response.status_code == 200

    def test_render_empty_gloss(self, client):
        """Test rendering with empty gloss"""
        request_data = {"gloss": ""}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        # Should handle gracefully
        assert response.status_code == 200
        assert data["gestures_queued"] == 0

    def test_render_very_long_gloss(self, client):
        """Test rendering with very long gloss"""
        long_gloss = " ".join(["WORD"] * 1000)
        request_data = {"gloss": long_gloss}
        response = client.post("/v1/render", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["gestures_queued"] == 1000

    def test_render_gesture_structure(self, client):
        """Test that gestures have correct structure"""
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        gesture = data["animation_data"]["gestures"][0]

        expected_fields = ["id", "gloss", "duration", "both_hands", "dominant_hand",
                          "facial_expression", "body_language", "handshape",
                          "orientation", "location"]
        for field in expected_fields:
            assert field in gesture

    def test_render_metadata_completeness(self, client):
        """Test that animation metadata is complete"""
        request_data = {"gloss": "HELLO WORLD"}
        response = client.post("/v1/render", json=request_data)
        data = response.json()
        metadata = data["animation_data"]["metadata"]

        expected_fields = ["source_gloss", "word_count", "generated_at", "model_path"]
        for field in expected_fields:
            assert field in metadata


class TestMetricsEndpointEnhanced:
    """Enhanced tests for /metrics endpoint"""

    def test_metrics_content_type(self, client):
        """Test metrics endpoint returns correct content type"""
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_has_content(self, client):
        """Test metrics endpoint returns content"""
        response = client.get("/metrics")
        assert len(response.content) > 0

    def test_metrics_after_translation(self, client):
        """Test that metrics are recorded after translation"""
        # Perform translation
        client.post("/v1/translate", json={"text": "hello"})

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        # Metrics should contain some data
        assert len(response.content) > 0


class TestErrorHandling:
    """Test error handling in API endpoints"""

    def test_translate_with_invalid_schema(self, client):
        """Test translation with invalid request schema"""
        request_data = {"invalid_field": "value"}
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 422

    def test_render_with_invalid_schema(self, client):
        """Test render with invalid request schema"""
        request_data = {"invalid_field": "value"}
        response = client.post("/v1/render", json=request_data)
        assert response.status_code == 422

    def test_translate_with_empty_body(self, client):
        """Test translation with empty body"""
        response = client.post("/v1/translate", json={})
        assert response.status_code == 422

    def test_render_with_empty_body(self, client):
        """Test render with empty body"""
        response = client.post("/v1/render", json={})
        assert response.status_code == 422

    @patch('main.translator.translate_with_nmm')
    def test_translate_internal_error(self, mock_translate, client):
        """Test translation handles internal errors"""
        mock_translate.side_effect = Exception("Internal error")
        request_data = {"text": "hello"}
        response = client.post("/v1/translate", json=request_data)
        assert response.status_code == 500

    @patch('main.avatar_renderer.render_gloss')
    def test_render_internal_error(self, mock_render, client):
        """Test render handles internal errors"""
        mock_render.side_effect = Exception("Internal error")
        request_data = {"gloss": "HELLO"}
        response = client.post("/v1/render", json=request_data)
        # Render endpoint returns success=False on error
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestPerformanceAndTiming:
    """Test performance characteristics"""

    def test_translate_response_time(self, client):
        """Test translation completes in reasonable time"""
        request_data = {"text": "hello world"}
        start = time.time()
        response = client.post("/v1/translate", json=request_data)
        duration = time.time() - start
        assert response.status_code == 200
        assert duration < 1.0

    def test_render_response_time(self, client):
        """Test render completes in reasonable time"""
        request_data = {"gloss": "HELLO WORLD"}
        start = time.time()
        response = client.post("/v1/render", json=request_data)
        duration = time.time() - start
        assert response.status_code == 200
        assert duration < 1.0

    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        import threading

        def make_request():
            client.post("/v1/translate", json={"text": "hello"})

        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # If we get here without hanging, concurrent requests work


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_translate_then_render_workflow(self, client):
        """Test complete translate-then-render workflow"""
        # Translate
        translate_request = {
            "text": "Hello world",
            "include_nmm": True
        }
        translate_response = client.post("/v1/translate", json=translate_request)
        assert translate_response.status_code == 200

        translate_data = translate_response.json()
        gloss = translate_data["gloss"]
        nmm = translate_data["non_manual_markers"]

        # Render
        render_request = {
            "gloss": gloss,
            "include_nmm": True
        }
        render_response = client.post("/v1/render", json=render_request)
        assert render_response.status_code == 200

        render_data = render_response.json()
        assert render_data["success"] is True
        assert len(render_data["animation_data"]["gestures"]) > 0

    def test_batch_translations(self, client):
        """Test multiple translation requests"""
        texts = ["hello", "thank you", "what is your name?", "goodbye"]
        for text in texts:
            request_data = {"text": text}
            response = client.post("/v1/translate", json=request_data)
            assert response.status_code == 200

    def test_batch_renders(self, client):
        """Test multiple render requests"""
        glosses = ["HELLO", "WORLD", "THANK YOU", "GOODBYE"]
        for gloss in glosses:
            request_data = {"gloss": gloss}
            response = client.post("/v1/render", json=request_data)
            assert response.status_code == 200

    def test_round_trip_translation(self, client):
        """Test that translation is idempotent"""
        original_text = "hello world"

        # First translation
        response1 = client.post("/v1/translate", json={"text": original_text})
        gloss1 = response1.json()["gloss"]

        # Second translation of same text
        response2 = client.post("/v1/translate", json={"text": original_text})
        gloss2 = response2.json()["gloss"]

        # Should be consistent
        assert gloss1 == gloss2


class TestAPIDocumentation:
    """Test API documentation endpoints"""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_docs_endpoint(self, client):
        """Test docs endpoint is available"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self, client):
        """Test ReDoc endpoint is available"""
        response = client.get("/redoc")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
