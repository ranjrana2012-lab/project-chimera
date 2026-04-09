"""
Tests for BSL Agent Avatar Renderer

Comprehensive test suite for avatar rendering functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from avatar_renderer import AvatarRenderer, SignGesture


@pytest.fixture
def renderer():
    """Create AvatarRenderer instance."""
    return AvatarRenderer()


class TestAvatarRendererInitialization:
    """Tests for AvatarRenderer initialization."""

    def test_avatar_renderer_initialization(self):
        """Test AvatarRenderer initializes correctly."""
        renderer = AvatarRenderer()
        assert renderer is not None
        assert renderer.model_path == "/models/bsl_avatar"


class TestSignGesture:
    """Tests for SignGesture dataclass."""

    def test_sign_gesture_creation(self):
        """Test SignGesture can be created with valid data."""
        gesture = SignGesture(
            id="gesture_1",
            gloss="HELLO",
            duration=2.0,
            both_hands=True,
            dominant_hand="right",
            facial_expression="neutral",
            body_language="neutral"
        )
        assert gesture.id == "gesture_1"
        assert gesture.gloss == "HELLO"
        assert gesture.duration == 2.0
        assert gesture.both_hands is True

    def test_sign_gesture_to_dict(self):
        """Test SignGesture to_dict method."""
        gesture = SignGesture(
            id="test_123",
            gloss="TEST",
            duration=1.5,
            handshape="fist",
            orientation="palm",
            location="chest"
        )
        result = gesture.to_dict()
        assert result["id"] == "test_123"
        assert result["gloss"] == "TEST"
        assert result["duration"] == 1.5
        assert result["handshape"] == "fist"
        assert result["orientation"] == "palm"
        assert result["location"] == "chest"


class TestRenderGloss:
    """Tests for render_gloss method."""

    def test_render_gloss_returns_success(self, renderer):
        """Test render_gloss returns successful response."""
        result = renderer.render_gloss(
            gloss="HELLO[right]",
            non_manual_markers=[]
        )

        assert result["format"] == "bsl-animation-v1"
        assert "gestures" in result
        assert len(result["gestures"]) > 0

    def test_render_gloss_with_empty_gloss(self, renderer):
        """Test render_gloss handles empty gloss."""
        result = renderer.render_gloss(
            gloss="",
            non_manual_markers=[]
        )

        # Should handle gracefully
        assert result is not None
        assert "gestures" in result

    def test_render_gloss_with_long_gloss(self, renderer):
        """Test render_gloss handles long gloss strings."""
        long_gloss = " ".join(["WORD[right]"] * 100)

        result = renderer.render_gloss(
            gloss=long_gloss,
            non_manual_markers=[]
        )

        assert result is not None
        assert result["total_duration"] > 0

    def test_render_gloss_with_special_markers(self, renderer):
        """Test render_gloss with special non-manual markers."""
        result = renderer.render_gloss(
            gloss="GOOD[really]",
            non_manual_markers=["brows-down", "head-tilt"]
        )

        assert result is not None
        assert result["non_manual_markers"] == ["brows-down", "head-tilt"]

    def test_render_gloss_with_brows_up_marker(self, renderer):
        """Test render_gloss with brows-up marker."""
        result = renderer.render_gloss(
            gloss="REALLY",
            non_manual_markers=["brows-up"]
        )

        assert result is not None
        # First gesture should have brows-up facial expression
        assert result["gestures"][0]["facial_expression"] == "brows-up"

    def test_render_gloss_with_head_shake_marker(self, renderer):
        """Test render_gloss with head-shake marker."""
        result = renderer.render_gloss(
            gloss="NO",
            non_manual_markers=["head-shake"]
        )

        assert result is not None
        # First gesture should have head-shake body language
        assert result["gestures"][0]["body_language"] == "head-shake"

    def test_render_gloss_with_head_nod_marker(self, renderer):
        """Test render_gloss with head-nod marker."""
        result = renderer.render_gloss(
            gloss="YES",
            non_manual_markers=["head-nod"]
        )

        assert result is not None
        # First gesture should have head-nod body language
        assert result["gestures"][0]["body_language"] == "head-nod"

    def test_render_gloss_with_body_lean_forward_marker(self, renderer):
        """Test render_gloss with body-lean-forward marker."""
        result = renderer.render_gloss(
            gloss="LISTEN",
            non_manual_markers=["body-lean-forward"]
        )

        assert result is not None
        # First gesture should have lean-forward body language
        assert result["gestures"][0]["body_language"] == "lean-forward"


class TestGetAvatarInfo:
    """Tests for get_avatar_info method."""

    def test_get_avatar_info_returns_dict(self, renderer):
        """Test get_avatar_info returns dictionary."""
        info = renderer.get_avatar_info()

        assert isinstance(info, dict)
        assert "model_path" in info
        assert "resolution" in info
        assert "fps" in info

    def test_get_avatar_info_contains_correct_values(self, renderer):
        """Test get_avatar_info returns correct configuration values."""
        renderer.fps = 60
        renderer.resolution = (1280, 720)

        info = renderer.get_avatar_info()

        assert info["fps"] == 60
        assert info["resolution"]["width"] == 1280
        assert info["resolution"]["height"] == 720


class TestAnimationFormats:
    """Tests for different animation output formats."""

    def test_render_format_version(self, renderer):
        """Test rendering returns correct format version."""
        result = renderer.render_gloss(
            gloss="HELLO",
            non_manual_markers=[]
        )

        assert result["format"] == "bsl-animation-v1"
        assert result["version"] == "1.0.0"

    def test_render_includes_metadata(self, renderer):
        """Test rendering includes metadata."""
        result = renderer.render_gloss(
            gloss="HELLO HOW ARE YOU",
            non_manual_markers=[]
        )

        assert "metadata" in result
        assert result["metadata"]["word_count"] == 4
        assert "source_gloss" in result["metadata"]


class TestFrameGeneration:
    """Tests for animation frame generation."""

    def test_frame_count_calculation(self, renderer):
        """Test that frame count is calculated correctly."""
        result = renderer.render_gloss(
            gloss="HELLO",
            non_manual_markers=[]
        )

        # Default FPS is 30, duration is 0.5 per word
        assert result["frame_count"] > 0
        assert result["total_duration"] > 0

    def test_frame_count_with_floating_point_duration(self, renderer):
        """Test frame count calculation works correctly."""
        result = renderer.render_gloss(
            gloss="TEST",
            non_manual_markers=[]
        )

        assert result["frame_count"] > 0
        assert "fps" in result
        assert result["fps"] == 30


class TestErrorHandling:
    """Tests for error handling in avatar rendering."""

    def test_render_with_unicode_gloss(self, renderer):
        """Test rendering with unicode characters in gloss."""
        result = renderer.render_gloss(
            gloss="HELLO 世界 🌍",
            non_manual_markers=[]
        )

        assert result is not None

    def test_render_with_special_characters(self, renderer):
        """Test rendering with special characters."""
        result = renderer.render_gloss(
            gloss="HELLO! @#$%^&*()",
            non_manual_markers=[]
        )

        assert result is not None


class TestGesturesStructure:
    """Tests for gestures structure in rendering."""

    def test_gestures_structure(self, renderer):
        """Test that gestures have correct structure."""
        result = renderer.render_gloss(
            gloss="HELLO HOW ARE YOU",
            non_manual_markers=[]
        )

        gestures = result["gestures"]
        assert len(gestures) == 4

        # Check first gesture structure
        gesture = gestures[0]
        assert "id" in gesture
        assert "gloss" in gesture
        assert "duration" in gesture
        assert "both_hands" in gesture
        assert "dominant_hand" in gesture
        assert "handshape" in gesture
        assert "orientation" in gesture
        assert "location" in gesture

    def test_gestures_have_unique_ids(self, renderer):
        """Test that each gesture has a unique ID."""
        result = renderer.render_gloss(
            gloss="HELLO HOW ARE YOU",
            non_manual_markers=[]
        )

        gestures = result["gestures"]
        ids = [g["id"] for g in gestures]
        assert len(ids) == len(set(ids)), "Gesture IDs should be unique"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
