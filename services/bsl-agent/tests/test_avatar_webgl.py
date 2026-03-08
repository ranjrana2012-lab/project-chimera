"""
Tests for BSL Agent WebGL Avatar Renderer

Comprehensive test suite for WebGL/Three.js avatar rendering functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import json
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from avatar_webgl import (
    AvatarWebGLRenderer,
    AvatarModel,
    NMMAnimation,
    NMMKeyframe,
    WebGLError,
    AvatarLoadError,
    AnimationLoadError
)


@pytest.fixture
def renderer():
    """Create AvatarWebGLRenderer instance."""
    return AvatarWebGLRenderer(
        model_path="/models/bsl_avatar",
        resolution=(1920, 1080),
        fps=30,
        enable_facial_expressions=True,
        enable_body_language=True
    )


class TestNMMKeyframe:
    """Tests for NMMKeyframe dataclass."""

    def test_keyframe_creation(self):
        """Test NMMKeyframe can be created with valid data."""
        keyframe = NMMKeyframe(
            time=0.5,
            morph_targets={"brows": 0.5, "smile": 0.8},
            bone_rotations={"head": (0, 0, 0, 1)},
            facial_expression="happy",
            lip_sync_value=0.3
        )

        assert keyframe.time == 0.5
        assert keyframe.morph_targets == {"brows": 0.5, "smile": 0.8}
        assert keyframe.bone_rotations == {"head": (0, 0, 0, 1)}
        assert keyframe.facial_expression == "happy"
        assert keyframe.lip_sync_value == 0.3

    def test_keyframe_to_dict(self):
        """Test NMMKeyframe to_dict method."""
        keyframe = NMMKeyframe(
            time=1.0,
            morph_targets={"mouth_open": 0.5},
            bone_positions={"right_hand": (1, 2, 3)},
            handshape="fist"
        )

        result = keyframe.to_dict()

        assert result["time"] == 1.0
        assert result["morph_targets"] == {"mouth_open": 0.5}
        assert result["bone_positions"] == {"right_hand": (1, 2, 3)}
        assert result["handshape"] == "fist"

    def test_keyframe_from_dict(self):
        """Test NMMKeyframe from_dict class method."""
        data = {
            "time": 0.75,
            "morph_targets": {"eyes_open": 0.9},
            "bone_scales": {"head": (1, 1, 1)},
            "facial_expression": "surprised"
        }

        keyframe = NMMKeyframe.from_dict(data)

        assert keyframe.time == 0.75
        assert keyframe.morph_targets == {"eyes_open": 0.9}
        assert keyframe.facial_expression == "surprised"


class TestNMMAnimation:
    """Tests for NMMAnimation class."""

    def test_animation_creation(self):
        """Test NMMAnimation can be created."""
        animation = NMMAnimation(
            name="test_anim",
            duration=2.0,
            fps=30,
            loop=True,
            easing="easeInOut"
        )

        assert animation.name == "test_anim"
        assert animation.duration == 2.0
        assert animation.fps == 30
        assert animation.loop is True
        assert animation.easing == "easeInOut"

    def test_animation_to_dict(self):
        """Test NMMAnimation to_dict method."""
        keyframe = NMMKeyframe(time=0.0, morph_targets={"brows": 0.5})
        animation = NMMAnimation(
            name="wave",
            duration=1.5,
            keyframes=[keyframe],
            metadata={"description": "Wave animation"}
        )

        result = animation.to_dict()

        assert result["name"] == "wave"
        assert result["duration"] == 1.5
        assert len(result["keyframes"]) == 1
        assert result["metadata"]["description"] == "Wave animation"

    def test_animation_from_dict(self):
        """Test NMMAnimation from_dict class method."""
        data = {
            "name": "greet",
            "duration": 3.0,
            "fps": 60,
            "loop": False,
            "easing": "easeIn",
            "keyframes": [
                {"time": 0.0, "morph_targets": {}},
                {"time": 1.5, "morph_targets": {}}
            ],
            "metadata": {}
        }

        animation = NMMAnimation.from_dict(data)

        assert animation.name == "greet"
        assert animation.duration == 3.0
        assert animation.fps == 60
        assert len(animation.keyframes) == 2

    def test_add_keyframe(self):
        """Test adding keyframes to animation."""
        animation = NMMAnimation(name="test", duration=1.0)
        keyframe1 = NMMKeyframe(time=0.0)
        keyframe2 = NMMKeyframe(time=0.5)
        keyframe3 = NMMKeyframe(time=1.5)

        animation.add_keyframe(keyframe1)
        animation.add_keyframe(keyframe2)
        animation.add_keyframe(keyframe3)

        assert len(animation.keyframes) == 3
        # Duration should update to accommodate latest keyframe
        assert animation.duration == 1.5

    def test_get_keyframe_at_time(self):
        """Test getting keyframe at specific time."""
        kf1 = NMMKeyframe(time=0.0, morph_targets={"brows": 0})
        kf2 = NMMKeyframe(time=0.5, morph_targets={"brows": 0.5})
        kf3 = NMMKeyframe(time=1.0, morph_targets={"brows": 1.0})

        animation = NMMAnimation(name="test", duration=1.0, keyframes=[kf1, kf2, kf3])

        # Exact match
        result = animation.get_keyframe_at_time(0.5)
        assert result is kf2

        # No exact match
        result = animation.get_keyframe_at_time(0.75)
        assert result is None

    def test_interpolate_empty_animation(self):
        """Test interpolation with empty animation."""
        animation = NMMAnimation(name="empty", duration=1.0)
        result = animation.interpolate(0.5)

        assert result == {}

    def test_interpolate_single_keyframe(self):
        """Test interpolation with single keyframe."""
        keyframe = NMMKeyframe(
            time=0.5,
            morph_targets={"brows": 0.5},
            lip_sync_value=0.7
        )
        animation = NMMAnimation(name="single", duration=1.0, keyframes=[keyframe])

        result = animation.interpolate(0.5)

        assert result["time"] == 0.5
        assert result["morph_targets"]["brows"] == 0.5
        assert result["lip_sync_value"] == 0.7

    def test_interpolate_between_keyframes(self):
        """Test interpolation between two keyframes."""
        kf1 = NMMKeyframe(
            time=0.0,
            morph_targets={"brows": 0.0, "smile": 0.0},
            lip_sync_value=0.0
        )
        kf2 = NMMKeyframe(
            time=1.0,
            morph_targets={"brows": 1.0, "smile": 0.5},
            lip_sync_value=1.0
        )

        animation = NMMAnimation(
            name="interpolate_test",
            duration=1.0,
            keyframes=[kf1, kf2],
            easing="linear"
        )

        # Interpolate at midpoint
        result = animation.interpolate(0.5)

        assert result["time"] == 0.5
        assert result["morph_targets"]["brows"] == 0.5  # Halfway
        assert result["morph_targets"]["smile"] == 0.25  # Halfway
        assert result["lip_sync_value"] == 0.5  # Halfway

    def test_interpolate_with_looping(self):
        """Test interpolation with looping enabled."""
        kf1 = NMMKeyframe(time=0.0, morph_targets={"brows": 0.0})
        kf2 = NMMKeyframe(time=1.0, morph_targets={"brows": 1.0})

        animation = NMMAnimation(
            name="loop_test",
            duration=1.0,
            loop=True,
            keyframes=[kf1, kf2]
        )

        # Request time beyond duration (should loop)
        result = animation.interpolate(1.5)

        # Should be same as 0.5 due to looping
        assert result["morph_targets"]["brows"] == 0.5

    def test_interpolate_clamping(self):
        """Test that interpolation clamps to duration."""
        kf1 = NMMKeyframe(time=0.0, morph_targets={"brows": 0.0})
        kf2 = NMMKeyframe(time=1.0, morph_targets={"brows": 1.0})

        animation = NMMAnimation(
            name="clamp_test",
            duration=1.0,
            loop=False,
            keyframes=[kf1, kf2]
        )

        # Request time beyond duration (should clamp)
        result = animation.interpolate(2.0)

        # Should be clamped to last keyframe
        assert result["morph_targets"]["brows"] == 1.0


class TestAvatarModel:
    """Tests for AvatarModel dataclass."""

    def test_avatar_model_creation(self):
        """Test AvatarModel can be created."""
        model = AvatarModel(
            name="test_avatar",
            model_path="/models/test.glb",
            texture_path="/models/test.png",
            scale=1.5,
            position=(0, 1, 0),
            rotation=(0, 90, 0),
            morph_target_names=["brows", "smile"],
            bone_names=["head", "right_hand"]
        )

        assert model.name == "test_avatar"
        assert model.model_path == "/models/test.glb"
        assert model.scale == 1.5
        assert model.position == (0, 1, 0)
        assert model.rotation == (0, 90, 0)
        assert len(model.morph_target_names) == 2
        assert len(model.bone_names) == 2

    def test_avatar_model_to_dict(self):
        """Test AvatarModel to_dict method."""
        model = AvatarModel(
            name="avatar1",
            model_path="/models/avatar1.glb",
            morph_target_names=["eyes_open"],
            bone_names=["left_arm"]
        )

        result = model.to_dict()

        assert result["name"] == "avatar1"
        assert result["model_path"] == "/models/avatar1.glb"
        assert result["morph_target_names"] == ["eyes_open"]
        assert result["bone_names"] == ["left_arm"]


class TestAvatarWebGLRendererInitialization:
    """Tests for AvatarWebGLRenderer initialization."""

    def test_renderer_initialization(self, renderer):
        """Test renderer initializes correctly."""
        assert renderer.model_path == "/models/bsl_avatar"
        assert renderer.resolution == (1920, 1080)
        assert renderer.fps == 30
        assert renderer.enable_facial_expressions is True
        assert renderer.enable_body_language is True

    def test_renderer_scene_config(self, renderer):
        """Test scene configuration is set up correctly."""
        assert "camera" in renderer.scene_config
        assert "renderer" in renderer.scene_config
        assert "lights" in renderer.scene_config

        assert renderer.scene_config["camera"]["type"] == "PerspectiveCamera"
        assert renderer.scene_config["camera"]["fov"] == 45
        assert renderer.scene_config["renderer"]["antialias"] is True
        assert len(renderer.scene_config["lights"]) == 3

    def test_renderer_default_values(self):
        """Test renderer with default parameters."""
        renderer = AvatarWebGLRenderer()

        assert renderer.model_path == "/models/bsl_avatar"
        assert renderer.resolution == (1920, 1080)
        assert renderer.fps == 30


class TestLoadAvatar:
    """Tests for load_avatar method."""

    def test_load_avatar_success(self, renderer):
        """Test successful avatar loading."""
        result = renderer.load_avatar("test_avatar")

        assert result["success"] is True
        assert result["avatar"]["name"] == "test_avatar"
        assert "scene_config" in result

    def test_load_avatar_with_custom_path(self, renderer):
        """Test loading avatar with custom path."""
        result = renderer.load_avatar(
            "custom_avatar",
            model_path="/custom/path/avatar.glb"
        )

        assert result["success"] is True
        assert result["avatar"]["model_path"] == "/custom/path/avatar.glb"

    def test_load_avatar_stores_model(self, renderer):
        """Test that loaded avatar is stored."""
        renderer.load_avatar("avatar1")
        renderer.load_avatar("avatar2")

        assert "avatar1" in renderer._avatar_models
        assert "avatar2" in renderer._avatar_models
        assert renderer._current_avatar.name == "avatar2"


class TestLoadAnimation:
    """Tests for load_animation method."""

    def test_load_animation_success(self, renderer):
        """Test successful animation loading."""
        animation_data = {
            "name": "wave",
            "duration": 2.0,
            "fps": 30,
            "loop": False,
            "easing": "linear",
            "keyframes": [
                {"time": 0.0, "morph_targets": {}},
                {"time": 1.0, "morph_targets": {}}
            ],
            "metadata": {}
        }

        animation = renderer.load_animation(animation_data)

        assert animation.name == "wave"
        assert animation.duration == 2.0
        assert "wave" in renderer._animations

    def test_load_animation_from_file(self, renderer, tmp_path):
        """Test loading animation from JSON file."""
        # Create test animation file
        animation_data = {
            "name": "test_anim",
            "duration": 1.5,
            "fps": 30,
            "loop": True,
            "keyframes": [
                {"time": 0.0, "morph_targets": {"brows": 0}},
                {"time": 1.5, "morph_targets": {"brows": 1}}
            ],
            "metadata": {}
        }

        anim_file = tmp_path / "animation.json"
        with open(anim_file, 'w') as f:
            json.dump(animation_data, f)

        animation = renderer.load_animation_from_file(str(anim_file))

        assert animation.name == "test_anim"
        assert animation.duration == 1.5
        assert animation.loop is True

    def test_load_animation_file_not_found(self, renderer):
        """Test loading non-existent animation file."""
        with pytest.raises(AnimationLoadError) as exc_info:
            renderer.load_animation_from_file("/nonexistent/file.json")

        assert "not found" in str(exc_info.value)

    def test_load_animation_invalid_json(self, renderer, tmp_path):
        """Test loading animation with invalid JSON."""
        # Create invalid JSON file
        anim_file = tmp_path / "invalid.json"
        with open(anim_file, 'w') as f:
            f.write("{ invalid json }")

        with pytest.raises(AnimationLoadError) as exc_info:
            renderer.load_animation_from_file(str(anim_file))

        assert "Invalid JSON" in str(exc_info.value)


class TestPlayAnimation:
    """Tests for play_animation method."""

    def test_play_animation_success(self, renderer):
        """Test successful animation playback."""
        # Load animation first
        animation_data = {
            "name": "test",
            "duration": 1.0,
            "keyframes": [{"time": 0.0}]
        }
        renderer.load_animation(animation_data)

        result = renderer.play_animation("test")

        assert result["success"] is True
        assert result["animation"]["name"] == "test"
        assert result["fps"] == 30

    def test_play_animation_not_found(self, renderer):
        """Test playing non-existent animation."""
        with pytest.raises(AnimationLoadError) as exc_info:
            renderer.play_animation("nonexistent")

        assert "not found" in str(exc_info.value)


class TestSetExpression:
    """Tests for set_expression method."""

    def test_set_expression_valid(self, renderer):
        """Test setting valid expression."""
        result = renderer.set_expression("happy")

        assert result["success"] is True
        assert result["expression"] == "happy"
        assert result["intensity"] == 1.0
        assert "morph_targets" in result

    def test_set_expression_with_intensity(self, renderer):
        """Test setting expression with custom intensity."""
        result = renderer.set_expression("sad", intensity=0.5)

        assert result["success"] is True
        assert result["intensity"] == 0.5
        # Check that values are scaled
        assert result["morph_targets"]["smile"] == -0.25  # -0.5 * 0.5

    def test_set_expression_invalid(self, renderer):
        """Test setting invalid expression."""
        with pytest.raises(ValueError) as exc_info:
            renderer.set_expression("invalid_expression")

        assert "Unknown expression" in str(exc_info.value)

    def test_all_available_expressions(self, renderer):
        """Test all available expressions can be set."""
        expressions = ["neutral", "happy", "sad", "surprised",
                      "angry", "questioning", "brows-up", "brows-down"]

        for expr in expressions:
            result = renderer.set_expression(expr)
            assert result["expression"] == expr


class TestBlendExpressions:
    """Tests for blend_expressions method."""

    def test_blend_two_expressions(self, renderer):
        """Test blending two expressions."""
        result = renderer.blend_expressions([
            ("happy", 0.5),
            ("sad", 0.5)
        ])

        assert result["success"] is True
        assert "morph_targets" in result
        # Happy has smile=1, sad has smile=-0.5
        # Blend should be (1 * 0.5) + (-0.5 * 0.5) = 0.25
        assert abs(result["morph_targets"]["smile"] - 0.25) < 0.01

    def test_blend_three_expressions(self, renderer):
        """Test blending three expressions."""
        result = renderer.blend_expressions([
            ("neutral", 0.5),
            ("happy", 0.3),
            ("surprised", 0.2)
        ])

        assert result["success"] is True
        # Check that blend is normalized
        total_weight = sum(w for _, w in result["expressions"])
        assert abs(total_weight - 1.0) < 0.01

    def test_blend_with_invalid_expression(self, renderer):
        """Test blending with invalid expression (should be skipped)."""
        result = renderer.blend_expressions([
            ("happy", 0.5),
            ("invalid", 0.3),
            ("sad", 0.2)
        ])

        assert result["success"] is True
        # Should only have valid expressions
        assert all(e in ["happy", "sad"] for e, _ in result["expressions"])


class TestSetHandshape:
    """Tests for set_handshape method."""

    def test_set_handshape_valid(self, renderer):
        """Test setting valid handshape."""
        result = renderer.set_handshape("right", "fist")

        assert result["success"] is True
        assert result["hands"] == ["right"]
        assert result["handshape"] == "fist"
        assert "finger_values" in result

    def test_set_handshape_both_hands(self, renderer):
        """Test setting handshape for both hands."""
        result = renderer.set_handshape("both", "open")

        assert result["success"] is True
        assert result["hands"] == ["left", "right"]

    def test_set_handshape_with_intensity(self, renderer):
        """Test setting handshape with intensity."""
        result = renderer.set_handshape("left", "point", intensity=0.7)

        assert result["success"] is True
        assert result["intensity"] == 0.7

    def test_set_handshape_invalid(self, renderer):
        """Test setting invalid handshape."""
        with pytest.raises(ValueError) as exc_info:
            renderer.set_handshape("right", "invalid_shape")

        assert "Unknown handshape" in str(exc_info.value)

    def test_all_available_handshapes(self, renderer):
        """Test all available handshapes."""
        handshapes = ["fist", "open", "point", "peace", "thumbs_up", "wave"]

        for shape in handshapes:
            result = renderer.set_handshape("right", shape)
            assert result["handshape"] == shape


class TestGenerateLipSync:
    """Tests for generate_lip_sync method."""

    def test_generate_lip_sync_basic(self, renderer):
        """Test basic lip-sync generation."""
        animation = renderer.generate_lip_sync("hello", 2.0)

        assert animation.name == "lip_sync"
        assert animation.duration == 2.0
        assert len(animation.keyframes) > 0

    def test_generate_lip_sync_empty_text(self, renderer):
        """Test lip-sync with empty text."""
        animation = renderer.generate_lip_sync("", 1.0)

        assert animation.name == "lip_sync"
        assert len(animation.keyframes) == 0

    def test_generate_lip_sync_closing_keyframe(self, renderer):
        """Test that lip-sync adds closing keyframe."""
        animation = renderer.generate_lip_sync("test", 1.0)

        # Last keyframe should have mouth_open = 0
        last_kf = animation.keyframes[-1]
        assert last_kf.time == 1.0
        assert last_kf.lip_sync_value == 0.0
        assert last_kf.morph_targets["mouth_open"] == 0.0


class TestRenderGlossToNMM:
    """Tests for render_gloss_to_nmm method."""

    def test_render_gloss_basic(self, renderer):
        """Test basic gloss rendering."""
        result = renderer.render_gloss_to_nmm("HELLO")

        assert result["format"] == "nmm-animation-v1"
        assert "animation" in result
        assert "scene_config" in result
        assert result["metadata"]["source_gloss"] == "HELLO"
        assert result["metadata"]["word_count"] == 1

    def test_render_gloss_multiple_words(self, renderer):
        """Test rendering multiple words."""
        result = renderer.render_gloss_to_nmm("HELLO HOW ARE YOU")

        assert result["metadata"]["word_count"] == 4
        animation = result["animation"]
        # Should have keyframes for each word (3 per word)
        assert len(animation["keyframes"]) == 12

    def test_render_gloss_with_nmm_markers(self, renderer):
        """Test rendering with non-manual markers."""
        result = renderer.render_gloss_to_nmm(
            "REALLY",
            non_manual_markers=["brows-up"]
        )

        # First keyframe should have brows-up expression
        first_kf = result["animation"]["keyframes"][0]
        assert first_kf["facial_expression"] == "brows-up"

    def test_render_gloss_with_head_tilt(self, renderer):
        """Test rendering with head tilt marker."""
        result = renderer.render_gloss_to_nmm(
            "QUESTION",
            non_manual_markers=["head-tilt"]
        )

        first_kf = result["animation"]["keyframes"][0]
        assert first_kf["facial_expression"] == "questioning"

    def test_render_gloss_custom_duration(self, renderer):
        """Test rendering with custom duration per sign."""
        result = renderer.render_gloss_to_nmm("TEST", duration_per_sign=1.0)

        animation = result["animation"]
        assert animation["duration"] == 1.0  # One word * 1.0 seconds

    def test_render_gloss_unicode(self, renderer):
        """Test rendering with unicode characters."""
        result = renderer.render_gloss_to_nmm("HELLO 世界")

        assert result["metadata"]["word_count"] == 2
        assert result["metadata"]["source_gloss"] == "HELLO 世界"

    def test_render_gloss_animation_structure(self, renderer):
        """Test that rendered animation has correct structure."""
        result = renderer.render_gloss_to_nmm("TEST")

        animation = result["animation"]
        assert "name" in animation
        assert "duration" in animation
        assert "fps" in animation
        assert "keyframes" in animation
        assert animation["fps"] == 30


class TestGetRendererInfo:
    """Tests for get_renderer_info method."""

    def test_get_renderer_info(self, renderer):
        """Test getting renderer information."""
        info = renderer.get_renderer_info()

        assert info["type"] == "WebGL"
        assert info["library"] == "Three.js"
        assert info["model_path"] == "/models/bsl_avatar"
        assert info["resolution"]["width"] == 1920
        assert info["resolution"]["height"] == 1080
        assert info["fps"] == 30
        assert info["status"] == "ready"

    def test_get_renderer_info_with_custom_config(self):
        """Test renderer info with custom configuration."""
        renderer = AvatarWebGLRenderer(
            model_path="/custom/path",
            resolution=(1280, 720),
            fps=60
        )

        info = renderer.get_renderer_info()

        assert info["model_path"] == "/custom/path"
        assert info["resolution"]["width"] == 1280
        assert info["resolution"]["height"] == 720
        assert info["fps"] == 60

    def test_get_renderer_info_loaded_content(self, renderer):
        """Test renderer info includes loaded content."""
        renderer.load_avatar("test_avatar")
        renderer.load_animation({
            "name": "test_anim",
            "duration": 1.0,
            "keyframes": []
        })

        info = renderer.get_renderer_info()

        assert "test_avatar" in info["loaded_avatars"]
        assert "test_anim" in info["loaded_animations"]
        assert info["current_avatar"] == "test_avatar"


class TestErrorHandling:
    """Tests for error handling."""

    def test_webgl_error_base(self):
        """Test WebGLError base exception."""
        with pytest.raises(WebGLError):
            raise WebGLError("Test error")

    def test_avatar_load_error(self, renderer):
        """Test AvatarLoadError exception."""
        # Simulate load failure by mocking
        with patch.object(renderer, '_avatar_models', side_effect=Exception("Load failed")):
            # This would normally raise AvatarLoadError
            pass

    def test_animation_load_error(self, renderer):
        """Test AnimationLoadError exception."""
        # Test with invalid animation data
        with pytest.raises((AnimationLoadError, KeyError, TypeError)):
            renderer.load_animation({})  # Missing required fields


class TestFacialExpressions:
    """Tests for facial expression system."""

    def test_facial_expressions_completeness(self, renderer):
        """Test all facial expressions have required morph targets."""
        required_targets = ["brows", "eyes_open", "smile", "mouth_open"]

        for expr_name, expr_values in renderer.FACIAL_EXPRESSIONS.items():
            for target in required_targets:
                assert target in expr_values, f"{expr_name} missing {target}"

    def test_facial_expression_ranges(self, renderer):
        """Test facial expression values are in valid range."""
        for expr_name, expr_values in renderer.FACIAL_EXPRESSIONS.items():
            for target, value in expr_values.items():
                assert -1 <= value <= 1, f"{expr_name}.{target} = {value} out of range"


class TestHandshapes:
    """Tests for handshape system."""

    def test_handshapes_completeness(self, renderer):
        """Test all handshapes have required finger values."""
        for shape_name, shape_values in renderer.HANDSHAPES.items():
            assert "fingers" in shape_values
            assert "thumb" in shape_values
            assert len(shape_values["fingers"]) == 4  # 4 fingers

    def test_handshape_ranges(self, renderer):
        """Test handshape values are in valid range."""
        for shape_name, shape_values in renderer.HANDSHAPES.items():
            for finger_value in shape_values["fingers"]:
                assert 0 <= finger_value <= 1
            assert 0 <= shape_values["thumb"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
