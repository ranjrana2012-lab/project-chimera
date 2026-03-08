"""
Tests for BSL Agent Pydantic models.

Tests request/response models for BSL translation and avatar rendering.
"""

import pytest
from pydantic import ValidationError
from models import (
    TranslateRequest,
    TranslateResponse,
    RenderRequest,
    RenderResponse,
    HealthResponse
)


class TestTranslateRequest:
    """Test TranslateRequest model"""

    def test_translate_request_minimal(self):
        """Test minimal translate request"""
        request = TranslateRequest(text="Hello")
        assert request.text == "Hello"
        assert request.include_nmm is True  # Default value
        assert request.context is None  # Default value

    def test_translate_request_with_nmm_false(self):
        """Test translate request with NMM disabled"""
        request = TranslateRequest(text="Hello", include_nmm=False)
        assert request.include_nmm is False

    def test_translate_request_with_context(self):
        """Test translate request with context"""
        context = {"show_id": "test-show", "scene": "1"}
        request = TranslateRequest(text="Hello", context=context)
        assert request.context == context

    def test_translate_request_empty_text_raises_error(self):
        """Test that empty text raises validation error"""
        with pytest.raises(ValidationError):
            TranslateRequest(text="")

    def test_translate_request_whitespace_only_raises_error(self):
        """Test that whitespace-only text raises validation error"""
        with pytest.raises(ValidationError):
            TranslateRequest(text="   ")

    def test_translate_request_min_length_validation(self):
        """Test text min_length validation"""
        # Single character should work
        request = TranslateRequest(text="H")
        assert request.text == "H"

    def test_translate_request_long_text(self):
        """Test translate request with long text"""
        long_text = "word " * 1000
        request = TranslateRequest(text=long_text)
        assert len(request.text) == len(long_text)

    def test_translate_request_with_unicode(self):
        """Test translate request with unicode characters"""
        request = TranslateRequest(text="Hello 世界 🌍")
        assert request.text == "Hello 世界 🌍"

    def test_translate_request_with_special_chars(self):
        """Test translate request with special characters"""
        request = TranslateRequest(text="Hello, @world! #test")
        assert request.text == "Hello, @world! #test"

    def test_translate_request_with_newlines(self):
        """Test translate request with newlines"""
        request = TranslateRequest(text="Hello\nworld")
        assert request.text == "Hello\nworld"

    def test_translate_request_complex_context(self):
        """Test translate request with complex context"""
        context = {
            "show_id": "test-show",
            "scene_number": "1",
            "act": "2",
            "custom_field": "value",
            "nested": {"key": "value"}
        }
        request = TranslateRequest(text="Hello", context=context)
        assert request.context == context


class TestTranslateResponse:
    """Test TranslateResponse model"""

    def test_translate_response_complete(self):
        """Test complete translate response"""
        response = TranslateResponse(
            gloss="HELLO WORLD",
            breakdown=["HELLO", "WORLD"],
            duration_estimate=1.0,
            confidence=0.85,
            non_manual_markers=["brows-down"],
            translation_time_ms=50.0
        )
        assert response.gloss == "HELLO WORLD"
        assert response.breakdown == ["HELLO", "WORLD"]
        assert response.duration_estimate == 1.0
        assert response.confidence == 0.85
        assert response.non_manual_markers == ["brows-down"]
        assert response.translation_time_ms == 50.0

    def test_translate_response_without_nmm(self):
        """Test translate response without NMM"""
        response = TranslateResponse(
            gloss="HELLO",
            breakdown=["HELLO"],
            duration_estimate=0.5,
            confidence=0.9,
            non_manual_markers=None,
            translation_time_ms=25.0
        )
        assert response.non_manual_markers is None

    def test_translate_response_empty_nmm_list(self):
        """Test translate response with empty NMM list"""
        response = TranslateResponse(
            gloss="HELLO",
            breakdown=["HELLO"],
            duration_estimate=0.5,
            confidence=0.9,
            non_manual_markers=[],
            translation_time_ms=25.0
        )
        assert response.non_manual_markers == []

    def test_translate_response_confidence_range(self):
        """Test confidence score range"""
        # Minimum confidence
        response1 = TranslateResponse(
            gloss="TEST",
            breakdown=["TEST"],
            duration_estimate=0.5,
            confidence=0.0,
            non_manual_markers=None,
            translation_time_ms=10.0
        )
        assert response1.confidence == 0.0

        # Maximum confidence
        response2 = TranslateResponse(
            gloss="TEST",
            breakdown=["TEST"],
            duration_estimate=0.5,
            confidence=1.0,
            non_manual_markers=None,
            translation_time_ms=10.0
        )
        assert response2.confidence == 1.0

    def test_translate_response_negative_duration(self):
        """Test translate response with negative duration"""
        response = TranslateResponse(
            gloss="TEST",
            breakdown=["TEST"],
            duration_estimate=-0.5,  # Invalid but allowed by model
            confidence=0.5,
            non_manual_markers=None,
            translation_time_ms=10.0
        )
        assert response.duration_estimate == -0.5

    def test_translate_response_zero_translation_time(self):
        """Test translate response with zero translation time"""
        response = TranslateResponse(
            gloss="TEST",
            breakdown=["TEST"],
            duration_estimate=0.5,
            confidence=0.5,
            non_manual_markers=None,
            translation_time_ms=0.0
        )
        assert response.translation_time_ms == 0.0

    def test_translate_response_large_breakdown(self):
        """Test translate response with large breakdown"""
        large_breakdown = [f"WORD{i}" for i in range(1000)]
        response = TranslateResponse(
            gloss=" ".join(large_breakdown),
            breakdown=large_breakdown,
            duration_estimate=500.0,
            confidence=0.8,
            non_manual_markers=None,
            translation_time_ms=1000.0
        )
        assert len(response.breakdown) == 1000


class TestRenderRequest:
    """Test RenderRequest model"""

    def test_render_request_minimal(self):
        """Test minimal render request"""
        request = RenderRequest(gloss="HELLO")
        assert request.gloss == "HELLO"
        assert request.include_nmm is True  # Default value
        assert request.session_id is None  # Default value

    def test_render_request_with_session_id(self):
        """Test render request with session ID"""
        request = RenderRequest(
            gloss="HELLO",
            session_id="session-123"
        )
        assert request.session_id == "session-123"

    def test_render_request_with_nmm_false(self):
        """Test render request with NMM disabled"""
        request = RenderRequest(
            gloss="HELLO",
            include_nmm=False
        )
        assert request.include_nmm is False

    def test_render_request_empty_gloss_raises_error(self):
        """Test that empty gloss raises validation error"""
        with pytest.raises(ValidationError):
            RenderRequest(gloss="")

    def test_render_request_whitespace_only_raises_error(self):
        """Test that whitespace-only gloss raises validation error"""
        with pytest.raises(ValidationError):
            RenderRequest(gloss="   ")

    def test_render_request_complex_gloss(self):
        """Test render request with complex gloss"""
        gloss = "HELLO[right] HOW[left] YOU[both]"
        request = RenderRequest(gloss=gloss)
        assert request.gloss == gloss

    def test_render_request_with_unicode(self):
        """Test render request with unicode characters"""
        request = RenderRequest(gloss="HELLO 世界")
        assert request.gloss == "HELLO 世界"

    def test_render_request_with_special_chars(self):
        """Test render request with special characters"""
        request = RenderRequest(gloss="HELLO! @WORLD#")
        assert request.gloss == "HELLO! @WORLD#"

    def test_render_request_session_id_formats(self):
        """Test various session ID formats"""
        session_ids = [
            "session-123",
            "user_session_456",
            "abc123def456",
            "session-with-multiple-hyphens"
        ]
        for session_id in session_ids:
            request = RenderRequest(gloss="HELLO", session_id=session_id)
            assert request.session_id == session_id


class TestRenderResponse:
    """Test RenderResponse model"""

    def test_render_response_success(self):
        """Test successful render response"""
        response = RenderResponse(
            success=True,
            animation_data={"format": "bsl-animation-v1"},
            gestures_queued=5,
            session_id="session-123",
            message="Successfully queued 5 gestures"
        )
        assert response.success is True
        assert response.animation_data == {"format": "bsl-animation-v1"}
        assert response.gestures_queued == 5
        assert response.session_id == "session-123"
        assert response.message == "Successfully queued 5 gestures"

    def test_render_response_failure(self):
        """Test failed render response"""
        response = RenderResponse(
            success=False,
            animation_data={},
            gestures_queued=0,
            session_id="session-123",
            message="Rendering failed"
        )
        assert response.success is False
        assert response.gestures_queued == 0

    def test_render_response_without_session_id(self):
        """Test render response without session ID"""
        response = RenderResponse(
            success=True,
            animation_data={"format": "test"},
            gestures_queued=1,
            session_id=None,
            message="Success"
        )
        assert response.session_id is None

    def test_render_response_without_message(self):
        """Test render response without message"""
        response = RenderResponse(
            success=True,
            animation_data={"format": "test"},
            gestures_queued=1,
            session_id="session-123",
            message=None
        )
        assert response.message is None

    def test_render_response_zero_gestures(self):
        """Test render response with zero gestures"""
        response = RenderResponse(
            success=True,
            animation_data={},
            gestures_queued=0,
            session_id=None,
            message="No gestures to render"
        )
        assert response.gestures_queued == 0

    def test_render_response_large_gesture_count(self):
        """Test render response with large gesture count"""
        response = RenderResponse(
            success=True,
            animation_data={"format": "test"},
            gestures_queued=10000,
            session_id=None,
            message="Success"
        )
        assert response.gestures_queued == 10000

    def test_render_response_complex_animation_data(self):
        """Test render response with complex animation data"""
        animation_data = {
            "format": "bsl-animation-v1",
            "version": "1.0.0",
            "resolution": {"width": 1920, "height": 1080},
            "fps": 30,
            "gestures": [
                {
                    "id": "gesture_1",
                    "gloss": "HELLO",
                    "duration": 0.5
                }
            ],
            "metadata": {
                "word_count": 1,
                "generated_at": "2024-01-01T00:00:00Z"
            }
        }
        response = RenderResponse(
            success=True,
            animation_data=animation_data,
            gestures_queued=1,
            session_id=None,
            message="Success"
        )
        assert response.animation_data == animation_data


class TestHealthResponse:
    """Test HealthResponse model"""

    def test_health_response_ready(self):
        """Test ready health response"""
        response = HealthResponse(
            status="ready",
            service="bsl-agent",
            translator_ready=True,
            avatar_ready=True
        )
        assert response.status == "ready"
        assert response.service == "bsl-agent"
        assert response.translator_ready is True
        assert response.avatar_ready is True

    def test_health_response_not_ready(self):
        """Test not ready health response"""
        response = HealthResponse(
            status="not_ready",
            service="bsl-agent",
            translator_ready=False,
            avatar_ready=False
        )
        assert response.status == "not_ready"
        assert response.translator_ready is False
        assert response.avatar_ready is False

    def test_health_response_partial_ready(self):
        """Test partially ready health response"""
        response = HealthResponse(
            status="degraded",
            service="bsl-agent",
            translator_ready=True,
            avatar_ready=False
        )
        assert response.translator_ready is True
        assert response.avatar_ready is False


class TestModelSerialization:
    """Test model serialization/deserialization"""

    def test_translate_request_to_dict(self):
        """Test TranslateRequest serialization to dict"""
        request = TranslateRequest(
            text="Hello",
            include_nmm=True,
            context={"show_id": "test"}
        )
        data = request.model_dump()
        assert data["text"] == "Hello"
        assert data["include_nmm"] is True
        assert data["context"] == {"show_id": "test"}

    def test_translate_response_to_dict(self):
        """Test TranslateResponse serialization to dict"""
        response = TranslateResponse(
            gloss="HELLO",
            breakdown=["HELLO"],
            duration_estimate=0.5,
            confidence=0.9,
            non_manual_markers=None,
            translation_time_ms=25.0
        )
        data = response.model_dump()
        assert data["gloss"] == "HELLO"
        assert data["breakdown"] == ["HELLO"]

    def test_render_request_from_dict(self):
        """Test RenderRequest deserialization from dict"""
        data = {
            "gloss": "HELLO WORLD",
            "session_id": "session-123",
            "include_nmm": True
        }
        request = RenderRequest(**data)
        assert request.gloss == "HELLO WORLD"
        assert request.session_id == "session-123"

    def test_health_response_to_json(self):
        """Test HealthResponse serialization to JSON"""
        response = HealthResponse(
            status="ready",
            service="bsl-agent",
            translator_ready=True,
            avatar_ready=True
        )
        json_str = response.model_dump_json()
        assert "ready" in json_str
        assert "bsl-agent" in json_str


class TestModelValidation:
    """Test model validation scenarios"""

    def test_translate_request_field_types(self):
        """Test TranslateRequest field type validation"""
        # Valid types
        request = TranslateRequest(
            text="Hello",
            include_nmm=True,
            context={"key": "value"}
        )
        assert isinstance(request.text, str)
        assert isinstance(request.include_nmm, bool)
        assert isinstance(request.context, dict) or request.context is None

    def test_render_request_field_types(self):
        """Test RenderRequest field type validation"""
        request = RenderRequest(
            gloss="HELLO",
            session_id="session-123",
            include_nmm=False
        )
        assert isinstance(request.gloss, str)
        assert isinstance(request.session_id, str) or request.session_id is None
        assert isinstance(request.include_nmm, bool)

    def test_response_field_types(self):
        """Test response field type validation"""
        # TranslateResponse
        tr = TranslateResponse(
            gloss="TEST",
            breakdown=["TEST"],
            duration_estimate=0.5,
            confidence=0.9,
            non_manual_markers=None,
            translation_time_ms=25.0
        )
        assert isinstance(tr.gloss, str)
        assert isinstance(tr.breakdown, list)
        assert isinstance(tr.duration_estimate, float)
        assert isinstance(tr.confidence, float)
        assert isinstance(tr.translation_time_ms, float)

        # RenderResponse
        rr = RenderResponse(
            success=True,
            animation_data={},
            gestures_queued=1,
            session_id=None,
            message="Success"
        )
        assert isinstance(rr.success, bool)
        assert isinstance(rr.animation_data, dict)
        assert isinstance(rr.gestures_queued, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
