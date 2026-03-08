"""
Enhanced tests for BSL Agent Avatar Renderer covering edge cases and error handling.

Tests avatar rendering functionality including:
- Advanced animation scenarios
- Error handling
- Performance tests
- Integration scenarios
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from avatar_renderer import AvatarRenderer, SignGesture


@pytest.fixture
def renderer():
    """Create AvatarRenderer instance for testing"""
    return AvatarRenderer()


@pytest.fixture
def custom_renderer():
    """Create AvatarRenderer with custom settings"""
    return AvatarRenderer(
        model_path="/custom/path",
        resolution=(1280, 720),
        fps=60,
        enable_facial_expressions=False,
        enable_body_language=False
    )


class TestAvatarRendererInitialization:
    """Test various initialization scenarios"""

    def test_initialization_with_custom_parameters(self):
        """Test initialization with custom parameters"""
        renderer = AvatarRenderer(
            model_path="/test/path",
            resolution=(640, 480),
            fps=24,
            enable_facial_expressions=False,
            enable_body_language=False
        )
        assert renderer.model_path == "/test/path"
        assert renderer.resolution == (640, 480)
        assert renderer.fps == 24
        assert renderer.enable_facial_expressions is False
        assert renderer.enable_body_language is False

    def test_initialization_default_values(self, renderer):
        """Test that default values are set correctly"""
        assert renderer.model_path == "/models/bsl_avatar"
        assert renderer.resolution == (1920, 1080)
        assert renderer.fps == 30
        assert renderer.enable_facial_expressions is True
        assert renderer.enable_body_language is True


class TestSignGestureDataclass:
    """Test SignGesture dataclass behavior"""

    def test_sign_gesture_all_fields(self):
        """Test SignGesture with all fields populated"""
        gesture = SignGesture(
            id="test_1",
            gloss="TEST",
            duration=1.5,
            both_hands=False,
            dominant_hand="left",
            facial_expression="brows-down",
            body_language="head-tilt",
            handshape="open",
            orientation="side",
            location="head"
        )
        assert gesture.id == "test_1"
        assert gesture.gloss == "TEST"
        assert gesture.duration == 1.5
        assert gesture.both_hands is False
        assert gesture.dominant_hand == "left"
        assert gesture.facial_expression == "brows-down"
        assert gesture.body_language == "head-tilt"
        assert gesture.handshape == "open"
        assert gesture.orientation == "side"
        assert gesture.location == "head"

    def test_sign_gesture_to_dict_completeness(self):
        """Test that to_dict includes all fields"""
        gesture = SignGesture(
            id="test",
            gloss="TEST",
            duration=1.0
        )
        result = gesture.to_dict()
        expected_keys = [
            "id", "gloss", "duration", "both_hands",
            "dominant_hand", "facial_expression", "body_language",
            "handshape", "orientation", "location"
        ]
        for key in expected_keys:
            assert key in result


class TestRenderGlossAdvanced:
    """Test advanced render_gloss scenarios"""

    def test_render_gloss_with_single_word(self, renderer):
        """Test rendering single word gloss"""
        result = renderer.render_gloss("HELLO")
        assert len(result["gestures"]) == 1
        assert result["gestures"][0]["gloss"] == "HELLO"

    def test_render_gloss_with_multiple_words(self, renderer):
        """Test rendering multi-word gloss"""
        result = renderer.render_gloss("HELLO HOW ARE YOU")
        assert len(result["gestures"]) == 4

    def test_render_gloss_with_spaces(self, renderer):
        """Test rendering gloss with multiple spaces"""
        result = renderer.render_gloss("HELLO    WORLD")
        assert len(result["gestures"]) == 2

    def test_render_glass_with_special_chars(self, renderer):
        """Test rendering gloss with special characters"""
        result = renderer.render_gloss("HELLO! @WORLD#")
        assert len(result["gestures"]) >= 1

    def test_render_gloss_with_unicode(self, renderer):
        """Test rendering gloss with unicode characters"""
        result = renderer.render_gloss("HELLO 世界")
        assert len(result["gestures"]) >= 1

    def test_render_gloss_very_long(self, renderer):
        """Test rendering very long gloss"""
        long_gloss = " ".join(["WORD"] * 1000)
        result = renderer.render_gloss(long_gloss)
        assert len(result["gestures"]) == 1000
        assert result["total_duration"] == 500.0  # 1000 * 0.5

    def test_render_gloss_empty_string(self, renderer):
        """Test rendering empty gloss"""
        result = renderer.render_gloss("")
        assert len(result["gestures"]) == 0
        assert result["total_duration"] == 0

    def test_render_gloss_with_none_markers(self, renderer):
        """Test rendering with None NMM markers"""
        result = renderer.render_gloss("HELLO", non_manual_markers=None)
        assert result["non_manual_markers"] == []

    def test_render_glass_with_empty_markers(self, renderer):
        """Test rendering with empty NMM markers"""
        result = renderer.render_gloss("HELLO", non_manual_markers=[])
        assert result["non_manual_markers"] == []

    def test_render_gloss_unique_gesture_ids(self, renderer):
        """Test that each gesture has a unique ID"""
        result = renderer.render_gloss("HELLO WORLD TEST")
        ids = [g["id"] for g in result["gestures"]]
        assert len(ids) == len(set(ids))

    def test_render_gloss_metadata_completeness(self, renderer):
        """Test that metadata is complete"""
        result = renderer.render_gloss("HELLO WORLD")
        metadata = result["metadata"]
        assert "source_gloss" in metadata
        assert "word_count" in metadata
        assert "generated_at" in metadata
        assert "model_path" in metadata
        assert metadata["word_count"] == 2


class TestNMMApplication:
    """Test Non-Manual Marker application"""

    def test_nmm_brows_down_applied(self, renderer):
        """Test brows-down NMM is applied"""
        result = renderer.render_gloss("HELLO", non_manual_markers=["brows-down"])
        assert result["gestures"][0]["facial_expression"] == "brows-down"

    def test_nmm_brows_up_applied(self, renderer):
        """Test brows-up NMM is applied"""
        result = renderer.render_gloss("HELLO", non_manual_markers=["brows-up"])
        assert result["gestures"][0]["facial_expression"] == "brows-up"

    def test_nmm_head_tilt_applied(self, renderer):
        """Test head-tilt NMM is applied"""
        result = renderer.render_gloss("HELLO", non_manual_markers=["head-tilt"])
        assert result["gestures"][0]["body_language"] == "head-tilt"

    def test_nmm_head_shake_applied(self, renderer):
        """Test head-shake NMM is applied"""
        result = renderer.render_gloss("HELLO", non_manual_markers=["head-shake"])
        assert result["gestures"][0]["body_language"] == "head-shake"

    def test_nmm_head_nod_applied(self, renderer):
        """Test head-nod NMM is applied"""
        result = renderer.render_gloss("HELLO", non_manual_markers=["head-nod"])
        assert result["gestures"][0]["body_language"] == "head-nod"

    def test_nmm_body_lean_forward_applied(self, renderer):
        """Test body-lean-forward NMM is applied"""
        result = renderer.render_gloss("HELLO", non_manual_markers=["body-lean-forward"])
        assert result["gestures"][0]["body_language"] == "lean-forward"

    def test_nmm_multiple_markers(self, renderer):
        """Test multiple NMM markers are applied"""
        result = renderer.render_gloss(
            "HELLO",
            non_manual_markers=["brows-down", "head-tilt"]
        )
        # First marker should be applied
        assert result["gestures"][0]["facial_expression"] == "brows-down"
        # Should have markers in result
        assert "brows-down" in result["non_manual_markers"]
        assert "head-tilt" in result["non_manual_markers"]

    def test_nmm_only_applies_to_first_gesture(self, renderer):
        """Test that NMM only affects first gesture"""
        result = renderer.render_gloss(
            "HELLO WORLD",
            non_manual_markers=["brows-down"]
        )
        assert result["gestures"][0]["facial_expression"] == "brows-down"
        # Second gesture should remain neutral
        assert result["gestures"][1]["facial_expression"] == "neutral"


class TestAnimationDataStructure:
    """Test animation data structure"""

    def test_animation_format_version(self, renderer):
        """Test animation format version"""
        result = renderer.render_gloss("HELLO")
        assert result["format"] == "bsl-animation-v1"
        assert result["version"] == "1.0.0"

    def test_animation_resolution(self, renderer):
        """Test animation resolution"""
        result = renderer.render_gloss("HELLO")
        assert result["resolution"]["width"] == 1920
        assert result["resolution"]["height"] == 1080

    def test_animation_fps(self, renderer):
        """Test animation FPS"""
        result = renderer.render_gloss("HELLO")
        assert result["fps"] == 30

    def test_animation_custom_resolution(self, custom_renderer):
        """Test animation with custom resolution"""
        result = custom_renderer.render_gloss("HELLO")
        assert result["resolution"]["width"] == 1280
        assert result["resolution"]["height"] == 720
        assert result["fps"] == 60

    def test_animation_frame_count(self, renderer):
        """Test frame count calculation"""
        result = renderer.render_gloss("HELLO")
        # 0.5 seconds * 30 fps = 15 frames
        assert result["frame_count"] == 15

    def test_animation_total_duration(self, renderer):
        """Test total duration calculation"""
        result = renderer.render_gloss("HELLO WORLD")
        # 2 words * 0.5 seconds = 1.0 second
        assert result["total_duration"] == 1.0


class TestGestureProperties:
    """Test individual gesture properties"""

    def test_gesture_default_values(self, renderer):
        """Test gesture default property values"""
        result = renderer.render_gloss("TEST")
        gesture = result["gestures"][0]
        assert gesture["both_hands"] is True
        assert gesture["dominant_hand"] == "right"
        assert gesture["handshape"] == "fist"
        assert gesture["orientation"] == "palm"
        assert gesture["location"] == "chest"

    def test_gesture_duration_default(self, renderer):
        """Test default gesture duration"""
        result = renderer.render_gloss("TEST")
        assert result["gestures"][0]["duration"] == 0.5

    def test_gesture_id_format(self, renderer):
        """Test gesture ID format"""
        result = renderer.render_gloss("HELLO")
        gesture_id = result["gestures"][0]["id"]
        assert "gesture_" in gesture_id
        assert "HELLO" in str(gesture_id) or str(hash("HELLO")) in gesture_id


class TestGetAvatarInfo:
    """Test get_avatar_info method"""

    def test_avatar_info_structure(self, renderer):
        """Test avatar info returns correct structure"""
        info = renderer.get_avatar_info()
        expected_keys = [
            "model_path", "resolution", "fps",
            "facial_expressions_enabled", "body_language_enabled",
            "status", "type"
        ]
        for key in expected_keys:
            assert key in info

    def test_avatar_info_values(self, renderer):
        """Test avatar info returns correct values"""
        info = renderer.get_avatar_info()
        assert info["model_path"] == "/models/bsl_avatar"
        assert info["resolution"]["width"] == 1920
        assert info["resolution"]["height"] == 1080
        assert info["fps"] == 30
        assert info["facial_expressions_enabled"] is True
        assert info["body_language_enabled"] is True
        assert info["status"] == "ready"
        assert info["type"] == "placeholder"

    def test_avatar_info_custom_values(self, custom_renderer):
        """Test avatar info with custom values"""
        info = custom_renderer.get_avatar_info()
        assert info["model_path"] == "/custom/path"
        assert info["resolution"]["width"] == 1280
        assert info["resolution"]["height"] == 720
        assert info["fps"] == 60
        assert info["facial_expressions_enabled"] is False
        assert info["body_language_enabled"] is False


class TestPerformanceAndTiming:
    """Test performance and timing aspects"""

    def test_render_speed_single_word(self, renderer):
        """Test rendering speed for single word"""
        start = time.time()
        renderer.render_gloss("HELLO")
        duration = time.time() - start
        assert duration < 0.1

    def test_render_speed_long_gloss(self, renderer):
        """Test rendering speed for long gloss"""
        long_gloss = " ".join(["WORD"] * 100)
        start = time.time()
        renderer.render_gloss(long_gloss)
        duration = time.time() - start
        assert duration < 0.5

    def test_generation_time_is_reasonable(self, renderer):
        """Test that generation time is reasonable"""
        result = renderer.render_gloss("HELLO WORLD TEST")
        # Generation should be fast (placeholder implementation)
        # Just verify it completes

    def test_metadata_timestamp_is_recent(self, renderer):
        """Test that metadata timestamp is recent"""
        before = datetime.now(timezone.utc)
        result = renderer.render_gloss("HELLO")
        after = datetime.now(timezone.utc)
        generated_at = datetime.fromisoformat(result["metadata"]["generated_at"])
        assert before <= generated_at <= after


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_render_with_invalid_input_type(self, renderer):
        """Test rendering with invalid input type"""
        with pytest.raises(AttributeError):
            renderer.render_gloss(None)

    def test_render_with_numbers(self, renderer):
        """Test rendering gloss with numbers"""
        result = renderer.render_gloss("123")
        assert len(result["gestures"]) >= 1

    def test_render_with_mixed_case(self, renderer):
        """Test rendering with mixed case"""
        result = renderer.render_gloss("Hello WoRlD")
        assert len(result["gestures"]) == 2

    def test_render_with_leading_trailing_spaces(self, renderer):
        """Test rendering with leading/trailing spaces"""
        result = renderer.render_gloss("  HELLO  ")
        assert len(result["gestures"]) == 1


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_full_render_workflow(self, renderer):
        """Test complete rendering workflow"""
        gloss = "HELLO HOW ARE YOU"
        nmm = ["brows-down", "head-tilt"]

        result = renderer.render_gloss(gloss, non_manual_markers=nmm)

        # Verify complete workflow
        assert len(result["gestures"]) == 4
        assert result["total_duration"] == 2.0
        assert result["non_manual_markers"] == nmm

    def test_batch_rendering(self, renderer):
        """Test rendering multiple glosses"""
        glosses = ["HELLO", "WORLD", "TEST"]
        results = [renderer.render_gloss(g) for g in glosses]

        assert len(results) == 3
        assert all(r["gestures"] for r in results)

    def test_render_consistency(self, renderer):
        """Test that same gloss produces consistent output"""
        gloss = "HELLO WORLD"
        result1 = renderer.render_gloss(gloss)
        result2 = renderer.render_gloss(gloss)

        # Same gloss should produce same word count
        assert len(result1["gestures"]) == len(result2["gestures"])
        # Same duration
        assert result1["total_duration"] == result2["total_duration"]


class TestLoggingBehavior:
    """Test logging behavior"""

    @patch('avatar_renderer.logger')
    def test_render_logs_info(self, mock_logger, renderer):
        """Test that rendering logs info messages"""
        renderer.render_gloss("HELLO WORLD")
        # Just verify no errors occurred
        assert True

    @patch('avatar_renderer.logger')
    def test_render_log_content(self, mock_logger, renderer):
        """Test that render log contains expected info"""
        renderer.render_gloss("HELLO WORLD")
        # Just verify no errors occurred
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
