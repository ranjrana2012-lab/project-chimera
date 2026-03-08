"""
BSL Avatar WebGL Renderer

Three.js-based 3D avatar rendering system for British Sign Language.
Supports NMM (Neural Model Format) animations, facial expressions,
hand gestures, body poses, and lip-sync for speech.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class NMMKeyframe:
    """Single keyframe in NMM animation format."""
    time: float  # Time in seconds
    morph_targets: Dict[str, float] = field(default_factory=dict)
    bone_rotations: Dict[str, Tuple[float, float, float, float]] = field(default_factory=dict)  # quaternions
    bone_positions: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)
    bone_scales: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)
    facial_expression: Optional[str] = None
    handshape: Optional[str] = None
    lip_sync_value: float = 0.0  # 0-1 for mouth open/close

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "time": self.time,
            "morph_targets": self.morph_targets,
            "bone_rotations": self.bone_rotations,
            "bone_positions": self.bone_positions,
            "bone_scales": self.bone_scales,
            "facial_expression": self.facial_expression,
            "handshape": self.handshape,
            "lip_sync_value": self.lip_sync_value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NMMKeyframe':
        """Create from dictionary."""
        return cls(
            time=data["time"],
            morph_targets=data.get("morph_targets", {}),
            bone_rotations=data.get("bone_rotations", {}),
            bone_positions=data.get("bone_positions", {}),
            bone_scales=data.get("bone_scales", {}),
            facial_expression=data.get("facial_expression"),
            handshape=data.get("handshape"),
            lip_sync_value=data.get("lip_sync_value", 0.0)
        )


@dataclass
class NMMAnimation:
    """NMM (Neural Model Format) animation for BSL signs."""
    name: str
    duration: float
    fps: int = 30
    loop: bool = False
    easing: str = "linear"  # linear, easeIn, easeOut, easeInOut
    keyframes: List[NMMKeyframe] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "duration": self.duration,
            "fps": self.fps,
            "loop": self.loop,
            "easing": self.easing,
            "keyframes": [kf.to_dict() for kf in self.keyframes],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NMMAnimation':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            duration=data["duration"],
            fps=data.get("fps", 30),
            loop=data.get("loop", False),
            easing=data.get("easing", "linear"),
            keyframes=[NMMKeyframe.from_dict(kf) for kf in data.get("keyframes", [])],
            metadata=data.get("metadata", {})
        )

    def add_keyframe(self, keyframe: NMMKeyframe) -> None:
        """Add a keyframe to the animation."""
        self.keyframes.append(keyframe)
        # Update duration if needed
        if keyframe.time > self.duration:
            self.duration = keyframe.time

    def get_keyframe_at_time(self, time: float) -> Optional[NMMKeyframe]:
        """Get the keyframe at a specific time."""
        for kf in self.keyframes:
            if abs(kf.time - time) < 0.001:
                return kf
        return None

    def interpolate(self, time: float) -> Dict[str, Any]:
        """
        Interpolate animation state at given time.
        Returns interpolated morph targets, bone transforms, etc.
        """
        if not self.keyframes:
            return {}

        # Handle looping
        if self.loop and time > self.duration:
            time = time % self.duration

        # Clamp to duration
        time = max(0, min(time, self.duration))

        # Find surrounding keyframes
        prev_kf = None
        next_kf = None

        for kf in self.keyframes:
            if kf.time <= time:
                prev_kf = kf
            if kf.time >= time and next_kf is None:
                next_kf = kf
                break

        # If we only have one keyframe or exact match
        if prev_kf is None:
            return next_kf.to_dict() if next_kf else {}
        if next_kf is None:
            return prev_kf.to_dict()
        if prev_kf == next_kf:
            return prev_kf.to_dict()

        # Interpolate between keyframes
        t = (time - prev_kf.time) / (next_kf.time - prev_kf.time)

        # Apply easing
        if self.easing == "easeIn":
            t = t * t
        elif self.easing == "easeOut":
            t = 1 - (1 - t) * (1 - t)
        elif self.easing == "easeInOut":
            t = 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)

        # Interpolate values
        result = {
            "time": time,
            "morph_targets": {},
            "bone_rotations": {},
            "bone_positions": {},
            "bone_scales": {},
            "facial_expression": prev_kf.facial_expression,
            "handshape": prev_kf.handshape,
            "lip_sync_value": prev_kf.lip_sync_value + t * (next_kf.lip_sync_value - prev_kf.lip_sync_value)
        }

        # Interpolate morph targets
        all_morph_keys = set(prev_kf.morph_targets.keys()) | set(next_kf.morph_targets.keys())
        for key in all_morph_keys:
            prev_val = prev_kf.morph_targets.get(key, 0.0)
            next_val = next_kf.morph_targets.get(key, 0.0)
            result["morph_targets"][key] = prev_val + t * (next_val - prev_val)

        # Interpolate bone rotations (quaternion slerp approximation)
        all_bone_keys = set(prev_kf.bone_rotations.keys()) | set(next_kf.bone_rotations.keys())
        for key in all_bone_keys:
            prev_val = prev_kf.bone_rotations.get(key, (0, 0, 0, 1))
            next_val = next_kf.bone_rotations.get(key, (0, 0, 0, 1))
            # Linear interpolation for quaternions (simplified)
            result["bone_rotations"][key] = tuple(
                prev_val[i] + t * (next_val[i] - prev_val[i])
                for i in range(4)
            )

        # Interpolate bone positions
        all_pos_keys = set(prev_kf.bone_positions.keys()) | set(next_kf.bone_positions.keys())
        for key in all_pos_keys:
            prev_val = prev_kf.bone_positions.get(key, (0, 0, 0))
            next_val = next_kf.bone_positions.get(key, (0, 0, 0))
            result["bone_positions"][key] = tuple(
                prev_val[i] + t * (next_val[i] - prev_val[i])
                for i in range(3)
            )

        # Interpolate bone scales
        all_scale_keys = set(prev_kf.bone_scales.keys()) | set(next_kf.bone_scales.keys())
        for key in all_scale_keys:
            prev_val = prev_kf.bone_scales.get(key, (1, 1, 1))
            next_val = next_kf.bone_scales.get(key, (1, 1, 1))
            result["bone_scales"][key] = tuple(
                prev_val[i] + t * (next_val[i] - prev_val[i])
                for i in range(3)
            )

        return result


@dataclass
class AvatarModel:
    """3D Avatar model configuration."""
    name: str
    model_path: str  # Path to GLTF/GLB file
    texture_path: Optional[str] = None
    scale: float = 1.0
    position: Tuple[float, float, float] = (0, 0, 0)
    rotation: Tuple[float, float, float] = (0, 0, 0)  # Euler angles in degrees
    morph_target_names: List[str] = field(default_factory=list)
    bone_names: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "model_path": self.model_path,
            "texture_path": self.texture_path,
            "scale": self.scale,
            "position": self.position,
            "rotation": self.rotation,
            "morph_target_names": self.morph_target_names,
            "bone_names": self.bone_names
        }


class WebGLError(Exception):
    """Base exception for WebGL avatar errors."""
    pass


class AvatarLoadError(WebGLError):
    """Exception raised when avatar fails to load."""
    pass


class AnimationLoadError(WebGLError):
    """Exception raised when animation fails to load."""
    pass


class AvatarWebGLRenderer:
    """
    Three.js-based 3D avatar renderer for BSL sign language.

    This server-side component generates NMM animation data and
    configuration for the client-side Three.js renderer.

    Features:
    - Avatar model loading and configuration
    - NMM animation generation and management
    - Facial expression blending
    - Hand gesture animation
    - Body pose animation
    - Lip-sync support
    """

    # Default facial expressions
    FACIAL_EXPRESSIONS = {
        "neutral": {"brows": 0.0, "eyes_open": 1.0, "smile": 0.0, "mouth_open": 0.0},
        "happy": {"brows": 0.2, "eyes_open": 0.8, "smile": 1.0, "mouth_open": 0.1},
        "sad": {"brows": -0.3, "eyes_open": 0.7, "smile": -0.5, "mouth_open": 0.0},
        "surprised": {"brows": 0.5, "eyes_open": 1.0, "smile": 0.0, "mouth_open": 0.8},
        "angry": {"brows": -0.4, "eyes_open": 0.6, "smile": -0.3, "mouth_open": 0.0},
        "questioning": {"brows": 0.3, "eyes_open": 0.9, "smile": 0.1, "mouth_open": 0.2},
        "brows-up": {"brows": 0.5, "eyes_open": 1.0, "smile": 0.0, "mouth_open": 0.1},
        "brows-down": {"brows": -0.4, "eyes_open": 0.7, "smile": 0.0, "mouth_open": 0.0},
    }

    # Hand shapes for BSL
    HANDSHAPES = {
        "fist": {"fingers": [0, 0, 0, 0], "thumb": 0},
        "open": {"fingers": [1, 1, 1, 1], "thumb": 1},
        "point": {"fingers": [0, 1, 1, 1], "thumb": 0},
        "peace": {"fingers": [0, 0, 1, 1], "thumb": 0},
        "thumbs_up": {"fingers": [0, 0, 0, 0], "thumb": 1},
        "wave": {"fingers": [1, 1, 1, 1], "thumb": 0.5},
    }

    def __init__(
        self,
        model_path: str = "/models/bsl_avatar",
        resolution: Tuple[int, int] = (1920, 1080),
        fps: int = 30,
        enable_facial_expressions: bool = True,
        enable_body_language: bool = True
    ):
        """
        Initialize WebGL Avatar Renderer.

        Args:
            model_path: Path to avatar 3D model files (GLTF/GLB)
            resolution: Rendering resolution (width, height)
            fps: Animation frames per second
            enable_facial_expressions: Enable facial expression animations
            enable_body_language: Enable body language animations
        """
        self.model_path = model_path
        self.resolution = resolution
        self.fps = fps
        self.enable_facial_expressions = enable_facial_expressions
        self.enable_body_language = enable_body_language
        self.logger = logging.getLogger(__name__)

        # Avatar model registry
        self._avatar_models: Dict[str, AvatarModel] = {}
        self._animations: Dict[str, NMMAnimation] = {}
        self._current_avatar: Optional[AvatarModel] = None
        self._current_animation: Optional[NMMAnimation] = None

        # Three.js scene configuration (for client)
        self.scene_config = {
            "camera": {
                "type": "PerspectiveCamera",
                "fov": 45,
                "near": 0.1,
                "far": 1000,
                "position": [0, 1.6, 3],
                "look_at": [0, 1.2, 0]
            },
            "renderer": {
                "antialias": True,
                "alpha": True,
                "shadows": True
            },
            "lights": [
                {
                    "type": "AmbientLight",
                    "color": 0xffffff,
                    "intensity": 0.6
                },
                {
                    "type": "DirectionalLight",
                    "color": 0xffffff,
                    "intensity": 0.8,
                    "position": [5, 10, 7],
                    "cast_shadow": True
                },
                {
                    "type": "HemisphereLight",
                    "color": 0xffffff,
                    "ground_color": 0x444444,
                    "intensity": 0.4
                }
            ]
        }

        self.logger.info(
            f"WebGL Avatar Renderer initialized: "
            f"resolution={resolution}, fps={fps}, "
            f"facial_expressions={enable_facial_expressions}, "
            f"body_language={enable_body_language}"
        )

    def load_avatar(self, avatar_name: str, model_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load or configure an avatar model.

        Args:
            avatar_name: Unique identifier for the avatar
            model_path: Optional path to model file (overrides default)

        Returns:
            Avatar configuration dictionary

        Raises:
            AvatarLoadError: If avatar configuration fails
        """
        try:
            # Use provided path or default
            model_file = model_path or f"{self.model_path}/{avatar_name}.glb"

            # Create avatar model configuration
            avatar = AvatarModel(
                name=avatar_name,
                model_path=model_file,
                texture_path=None,
                scale=1.0,
                position=(0, 0, 0),
                rotation=(0, 0, 0),
                morph_target_names=[
                    "brows", "eyes_open", "smile", "mouth_open",
                    "head_nod", "head_tilt", "head_turn"
                ],
                bone_names=[
                    "head", "neck", "spine", "chest",
                    "left_shoulder", "left_arm", "left_forearm", "left_hand",
                    "right_shoulder", "right_arm", "right_forearm", "right_hand"
                ]
            )

            self._avatar_models[avatar_name] = avatar
            self._current_avatar = avatar

            self.logger.info(f"Avatar '{avatar_name}' loaded from {model_file}")

            return {
                "success": True,
                "avatar": avatar.to_dict(),
                "scene_config": self.scene_config
            }

        except Exception as e:
            error_msg = f"Failed to load avatar '{avatar_name}': {str(e)}"
            self.logger.error(error_msg)
            raise AvatarLoadError(error_msg) from e

    def load_animation(self, animation_data: Dict[str, Any]) -> NMMAnimation:
        """
        Load an NMM animation from dictionary data.

        Args:
            animation_data: Dictionary containing NMM animation data

        Returns:
            NMMAnimation object

        Raises:
            AnimationLoadError: If animation loading fails
        """
        try:
            animation = NMMAnimation.from_dict(animation_data)
            self._animations[animation.name] = animation
            self.logger.info(f"Animation '{animation.name}' loaded ({len(animation.keyframes)} keyframes)")
            return animation

        except Exception as e:
            error_msg = f"Failed to load animation: {str(e)}"
            self.logger.error(error_msg)
            raise AnimationLoadError(error_msg) from e

    def load_animation_from_file(self, file_path: str) -> NMMAnimation:
        """
        Load an NMM animation from a JSON file.

        Args:
            file_path: Path to JSON file containing animation data

        Returns:
            NMMAnimation object
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return self.load_animation(data)

        except FileNotFoundError as e:
            error_msg = f"Animation file not found: {file_path}"
            self.logger.error(error_msg)
            raise AnimationLoadError(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in animation file: {file_path}"
            self.logger.error(error_msg)
            raise AnimationLoadError(error_msg) from e

    def play_animation(self, animation_name: str) -> Dict[str, Any]:
        """
        Set the current animation for playback.

        Args:
            animation_name: Name of the animation to play

        Returns:
            Animation data for client-side playback
        """
        if animation_name not in self._animations:
            raise AnimationLoadError(f"Animation '{animation_name}' not found")

        self._current_animation = self._animations[animation_name]

        return {
            "success": True,
            "animation": self._current_animation.to_dict(),
            "fps": self.fps
        }

    def set_expression(self, expression: str, intensity: float = 1.0) -> Dict[str, Any]:
        """
        Set facial expression for the avatar.

        Args:
            expression: Expression name (e.g., 'happy', 'sad', 'surprised')
            intensity: Intensity value 0.0 to 1.0

        Returns:
            Expression morph target values

        Raises:
            ValueError: If expression name is invalid
        """
        if expression not in self.FACIAL_EXPRESSIONS:
            raise ValueError(
                f"Unknown expression '{expression}'. "
                f"Available: {list(self.FACIAL_EXPRESSIONS.keys())}"
            )

        # Get base expression values
        base_values = self.FACIAL_EXPRESSIONS[expression]

        # Apply intensity
        morph_targets = {
            key: value * intensity
            for key, value in base_values.items()
        }

        self.logger.debug(f"Expression set to '{expression}' (intensity={intensity})")

        return {
            "success": True,
            "expression": expression,
            "intensity": intensity,
            "morph_targets": morph_targets
        }

    def blend_expressions(
        self,
        expressions: List[Tuple[str, float]]
    ) -> Dict[str, Any]:
        """
        Blend multiple facial expressions together.

        Args:
            expressions: List of (expression_name, weight) tuples
                        Weights should sum to 1.0

        Returns:
            Blended morph target values
        """
        # Initialize blended values
        blended = {key: 0.0 for key in self.FACIAL_EXPRESSIONS["neutral"].keys()}

        # Track valid expressions
        valid_expressions = []

        # Blend each expression
        for expr_name, weight in expressions:
            if expr_name not in self.FACIAL_EXPRESSIONS:
                self.logger.warning(f"Unknown expression '{expr_name}', skipping")
                continue

            valid_expressions.append((expr_name, weight))
            expr_values = self.FACIAL_EXPRESSIONS[expr_name]
            for key, value in expr_values.items():
                blended[key] += value * weight

        return {
            "success": True,
            "morph_targets": blended,
            "expressions": valid_expressions
        }

    def set_handshape(
        self,
        hand: str,
        handshape: str,
        intensity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Set hand shape for BSL signing.

        Args:
            hand: 'left', 'right', or 'both'
            handshape: Hand shape name (e.g., 'fist', 'open', 'point')
            intensity: Intensity value 0.0 to 1.0

        Returns:
            Hand configuration for animation
        """
        if handshape not in self.HANDSHAPES:
            raise ValueError(
                f"Unknown handshape '{handshape}'. "
                f"Available: {list(self.HANDSHAPES.keys())}"
            )

        base_values = self.HANDSHAPES[handshape]
        hand_values = {}
        for key, value in base_values.items():
            if isinstance(value, list):
                # Multiply each element in the list
                hand_values[key] = [v * intensity for v in value]
            else:
                # Multiply single value
                hand_values[key] = value * intensity

        hands = ["left", "right"] if hand == "both" else [hand]

        return {
            "success": True,
            "hands": hands,
            "handshape": handshape,
            "intensity": intensity,
            "finger_values": hand_values
        }

    def generate_lip_sync(self, text: str, duration: float) -> NMMAnimation:
        """
        Generate basic lip-sync animation for speech.

        Args:
            text: Text to lip-sync to
            duration: Duration in seconds

        Returns:
            NMMAnimation with lip-sync keyframes
        """
        # Simple phoneme-to-viseme mapping
        viseme_map = {
            'a': 0.8, 'e': 0.6, 'i': 0.7, 'o': 0.5, 'u': 0.3,
            'b': 0.2, 'p': 0.2, 'm': 0.1,
            'f': 0.4, 'v': 0.4,
            't': 0.3, 'd': 0.3, 's': 0.3, 'z': 0.3,
            'l': 0.2, 'n': 0.1,
        }

        # Normalize text and calculate timing
        text = text.lower().replace(" ", "")
        if not text:
            return NMMAnimation(name="lip_sync", duration=duration, fps=self.fps)

        char_duration = duration / len(text)

        # Generate keyframes
        animation = NMMAnimation(
            name="lip_sync",
            duration=duration,
            fps=self.fps,
            loop=False
        )

        # Add keyframes for each character
        for i, char in enumerate(text):
            time = i * char_duration
            mouth_open = viseme_map.get(char, 0.2)

            keyframe = NMMKeyframe(
                time=time,
                lip_sync_value=mouth_open,
                morph_targets={"mouth_open": mouth_open}
            )
            animation.add_keyframe(keyframe)

        # Add closing keyframe
        animation.add_keyframe(NMMKeyframe(
            time=duration,
            lip_sync_value=0.0,
            morph_targets={"mouth_open": 0.0}
        ))

        return animation

    def render_gloss_to_nmm(
        self,
        gloss: str,
        non_manual_markers: Optional[List[str]] = None,
        duration_per_sign: float = 0.5
    ) -> Dict[str, Any]:
        """
        Convert BSL gloss to NMM animation format.

        Args:
            gloss: BSL gloss notation
            non_manual_markers: List of NMM markers (facial expressions, body language)
            duration_per_sign: Duration for each sign in seconds

        Returns:
            NMM animation data for client-side rendering
        """
        start_time = datetime.now(timezone.utc)

        # Split gloss into individual signs
        gloss_words = gloss.split()

        # Create animation
        total_duration = len(gloss_words) * duration_per_sign
        animation = NMMAnimation(
            name=f"sign_{hashlib.md5(gloss.encode()).hexdigest()[:8]}",
            duration=total_duration,
            fps=self.fps,
            loop=False,
            easing="easeInOut"
        )

        # Determine facial expression from NMM markers
        expression = "neutral"
        if non_manual_markers:
            if "brows-up" in non_manual_markers:
                expression = "brows-up"
            elif "brows-down" in non_manual_markers:
                expression = "brows-down"
            elif any(m in non_manual_markers for m in ["head-tilt", "head-nod"]):
                expression = "questioning"

        # Generate keyframes for each sign
        for i, word in enumerate(gloss_words):
            sign_time = i * duration_per_sign

            # Starting pose
            start_keyframe = NMMKeyframe(
                time=sign_time,
                morph_targets=self.FACIAL_EXPRESSIONS[expression],
                handshape="fist",
                facial_expression=expression
            )
            animation.add_keyframe(start_keyframe)

            # Mid-sign pose (hand movement)
            mid_time = sign_time + duration_per_sign * 0.5
            mid_keyframe = NMMKeyframe(
                time=mid_time,
                morph_targets=self.FACIAL_EXPRESSIONS[expression],
                handshape="open",
                facial_expression=expression,
                bone_positions={
                    "right_hand": (0.3, 1.2, 0.2),
                    "left_hand": (-0.3, 1.2, 0.2)
                }
            )
            animation.add_keyframe(mid_keyframe)

            # End pose
            end_time = sign_time + duration_per_sign
            end_keyframe = NMMKeyframe(
                time=end_time,
                morph_targets=self.FACIAL_EXPRESSIONS[expression],
                handshape="fist",
                facial_expression=expression,
                bone_positions={
                    "right_hand": (0.2, 1.0, 0.0),
                    "left_hand": (-0.2, 1.0, 0.0)
                }
            )
            animation.add_keyframe(end_keyframe)

        # Store animation
        animation_id = f"anim_{hashlib.md5(gloss.encode()).hexdigest()[:8]}"
        self._animations[animation_id] = animation

        # Generate response
        generation_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        response = {
            "format": "nmm-animation-v1",
            "version": "1.0.0",
            "animation_id": animation_id,
            "animation": animation.to_dict(),
            "scene_config": self.scene_config,
            "avatar_config": self._current_avatar.to_dict() if self._current_avatar else None,
            "metadata": {
                "source_gloss": gloss,
                "word_count": len(gloss_words),
                "duration": total_duration,
                "fps": self.fps,
                "generated_at": start_time.isoformat(),
                "generation_time_ms": generation_time,
                "non_manual_markers": non_manual_markers or []
            }
        }

        self.logger.info(
            f"NMM animation generated: {len(gloss_words)} signs, "
            f"{total_duration:.2f}s, {generation_time:.2f}ms"
        )

        return response

    def get_renderer_info(self) -> Dict[str, Any]:
        """
        Get renderer information and configuration.

        Returns:
            Dictionary with renderer status and configuration
        """
        return {
            "type": "WebGL",
            "library": "Three.js",
            "version": "1.0.0",
            "model_path": self.model_path,
            "resolution": {
                "width": self.resolution[0],
                "height": self.resolution[1]
            },
            "fps": self.fps,
            "facial_expressions_enabled": self.enable_facial_expressions,
            "body_language_enabled": self.enable_body_language,
            "loaded_avatars": list(self._avatar_models.keys()),
            "loaded_animations": list(self._animations.keys()),
            "current_avatar": self._current_avatar.name if self._current_avatar else None,
            "current_animation": self._current_animation.name if self._current_animation else None,
            "available_expressions": list(self.FACIAL_EXPRESSIONS.keys()),
            "available_handshapes": list(self.HANDSHAPES.keys()),
            "status": "ready"
        }


__all__ = [
    "AvatarWebGLRenderer",
    "AvatarModel",
    "NMMAnimation",
    "NMMKeyframe",
    "WebGLError",
    "AvatarLoadError",
    "AnimationLoadError"
]
