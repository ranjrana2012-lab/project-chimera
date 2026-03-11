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

    def set_expression(self, expression: str) -> bool:
        """
        Set facial expression for the avatar.

        Args:
            expression: Expression name (e.g., 'happy', 'sad', 'neutral')

        Returns:
            True if expression was applied successfully, False otherwise
        """
        try:
            if expression not in self.FACIAL_EXPRESSIONS:
                self.logger.warning(f"Invalid expression: {expression}")
                return False

            # Store current expression for use in animations
            if not hasattr(self, '_current_expression'):
                self._current_expression = "neutral"

            self._current_expression = expression
            self.logger.info(f"Expression set to: {expression}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set expression: {e}")
            return False

    def set_handshape(self, handshape: str, hand: str) -> bool:
        """
        Set handshape for the avatar.

        Args:
            handshape: Handshape name (e.g., 'wave', 'point', 'fist')
            hand: Which hand ('left' or 'right')

        Returns:
            True if handshape was applied successfully, False otherwise
        """
        try:
            if handshape not in self.HANDSHAPES:
                self.logger.warning(f"Invalid handshape: {handshape}")
                return False

            if hand not in ("left", "right"):
                self.logger.warning(f"Invalid hand: {hand}")
                return False

            # Store current handshapes for use in animations
            if not hasattr(self, '_current_handshapes'):
                self._current_handshapes = {"left": "open", "right": "open"}

            self._current_handshapes[hand] = handshape
            self.logger.info(f"Handshape set to: {handshape} for {hand} hand")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set handshape: {e}")
            return False

    def generate_animation(self, gloss: list[str], expression: str = "neutral") -> Dict[str, Any]:
        """
        Generate animation data for BSL signs.

        Args:
            gloss: List of BSL gloss words to animate
            expression: Facial expression to apply

        Returns:
            Dictionary with animation frames and metadata
        """
        try:
            frames = []
            frame_duration = 1.0 / self.fps  # Duration per frame in seconds

            # Generate frames for each sign in the gloss
            for i, sign in enumerate(gloss):
                # Start frame for this sign
                start_time = i * 1.0  # 1 second per sign

                # Generate keyframes for this sign
                num_keyframes = max(3, int(self.fps * 0.5))  # 0.5 seconds per sign

                for kf in range(num_keyframes):
                    frame_time = start_time + (kf * frame_duration * 0.5)
                    progress = kf / (num_keyframes - 1)  # 0 to 1

                    frame = {
                        "time": frame_time,
                        "duration": frame_duration,
                        "sign": sign,
                        "progress": progress,
                        "left_hand": self._get_hand_frame_data(self._current_handshapes.get("left", "open") if hasattr(self, '_current_handshapes') else "open", progress),
                        "right_hand": self._get_hand_frame_data(self._current_handshapes.get("right", "open") if hasattr(self, '_current_handshapes') else "open", progress),
                        "face": self._get_face_frame_data(expression if hasattr(self, '_current_expression') else "neutral", progress),
                        "body": self._get_body_frame_data(progress)
                    }
                    frames.append(frame)

            response = {
                "frames": frames,
                "fps": self.fps,
                "duration": len(gloss) * 1.0,  # Total duration in seconds
                "sign_count": len(gloss),
                "expression": expression,
                "metadata": {
                    "gloss": gloss,
                    "generated_at": __import__('datetime').datetime.now().isoformat(),
                    "renderer": "WebGL"
                }
            }

            self.logger.info(f"Generated {len(frames)} frames for {len(gloss)} signs")
            return response

        except Exception as e:
            self.logger.error(f"Failed to generate animation: {e}")
            raise

    def _get_hand_frame_data(self, handshape: str, progress: float) -> Dict[str, Any]:
        """Get hand frame data for a given handshape and progress."""
        handshape_data = self.HANDSHAPES.get(handshape, self.HANDSHAPES["open"])

        # Interpolate finger positions based on progress
        fingers = handshape_data["fingers"]
        thumb = handshape_data["thumb"]

        return {
            "handshape": handshape,
            "fingers": [f * (0.5 + 0.5 * progress) for f in fingers],
            "thumb": thumb * (0.5 + 0.5 * progress),
            "position": {
                "x": 0.3 if progress < 0.5 else -0.3,
                "y": 1.0 + 0.1 * __import__('math').sin(progress * __import__('math').pi),
                "z": 0.5
            },
            "rotation": {
                "x": progress * 0.5,
                "y": progress * 0.3,
                "z": progress * 0.2
            }
        }

    def _get_face_frame_data(self, expression: str, progress: float) -> Dict[str, Any]:
        """Get face frame data for a given expression and progress."""
        expression_data = self.FACIAL_EXPRESSIONS.get(expression, self.FACIAL_EXPRESSIONS["neutral"])

        return {
            "expression": expression,
            "brows": expression_data["brows"] * (0.7 + 0.3 * progress),
            "eyes_open": expression_data["eyes_open"],
            "smile": expression_data["smile"] * progress,
            "mouth_open": expression_data["mouth_open"] * progress,
            "head_rotation": {
                "x": 0.1 * __import__('math').sin(progress * __import__('math').pi * 2),
                "y": 0.05 * __import__('math').cos(progress * __import__('math').pi * 2),
                "z": 0
            }
        }

    def _get_body_frame_data(self, progress: float) -> Dict[str, Any]:
        """Get body frame data for a given progress."""
        return {
            "position": {
                "x": 0,
                "y": 0,
                "z": 0
            },
            "rotation": {
                "x": 0,
                "y": 0,
                "z": 0
            },
            "posture": {
                "shoulders_down": 0.5 + 0.1 * progress,
                "spine_straight": 0.8 + 0.1 * __import__('math').sin(progress * __import__('math').pi)
            }
        }

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


# ============================================================================
# ADVANCED FEATURE CLASSES
# ============================================================================

class LipSyncEngine:
    """
    Advanced lip-sync engine for BSL avatar speech animation.

    Analyzes audio/text to generate mouth animation visemes with
    coarticulation support for smooth transitions between sounds.
    """

    # Enhanced viseme mapping with coarticulation data
    VISEMES = {
        # Silences
        '_': {'mouth_open': 0.0, 'lip_width': 0.5, 'lip_corner_pull': 0.0},
        ' ': {'mouth_open': 0.1, 'lip_width': 0.5, 'lip_corner_pull': 0.0},

        # Vowels
        'A': {'mouth_open': 0.9, 'lip_width': 0.8, 'lip_corner_pull': 0.3},
        'E': {'mouth_open': 0.5, 'lip_width': 0.6, 'lip_corner_pull': 0.5},
        'I': {'mouth_open': 0.4, 'lip_width': 0.3, 'lip_corner_pull': 0.6},
        'O': {'mouth_open': 0.5, 'lip_width': 0.7, 'lip_corner_pull': 0.0},
        'U': {'mouth_open': 0.3, 'lip_width': 0.5, 'lip_corner_pull': 0.0},

        # Consonants - Bilabial
        'B': {'mouth_open': 0.1, 'lip_width': 0.1, 'lip_corner_pull': 0.0},
        'P': {'mouth_open': 0.1, 'lip_width': 0.1, 'lip_corner_pull': 0.0},
        'M': {'mouth_open': 0.0, 'lip_width': 0.1, 'lip_corner_pull': 0.0},

        # Consonants - Labiodental
        'F': {'mouth_open': 0.4, 'lip_width': 0.7, 'lip_corner_pull': 0.3},
        'V': {'mouth_open': 0.3, 'lip_width': 0.6, 'lip_corner_pull': 0.2},

        # Consonants - Dental
        'T': {'mouth_open': 0.3, 'lip_width': 0.4, 'lip_corner_pull': 0.1},
        'D': {'mouth_open': 0.3, 'lip_width': 0.4, 'lip_corner_pull': 0.1},
        'S': {'mouth_open': 0.2, 'lip_width': 0.5, 'lip_corner_pull': 0.1},
        'Z': {'mouth_open': 0.2, 'lip_width': 0.5, 'lip_corner_pull': 0.1},
        'N': {'mouth_open': 0.2, 'lip_width': 0.4, 'lip_corner_pull': 0.1},
        'L': {'mouth_open': 0.3, 'lip_width': 0.4, 'lip_corner_pull': 0.2},

        # Consonants - Velar
        'K': {'mouth_open': 0.3, 'lip_width': 0.5, 'lip_corner_pull': 0.0},
        'G': {'mouth_open': 0.3, 'lip_width': 0.5, 'lip_corner_pull': 0.0},

        # Consonant - Glottal
        'H': {'mouth_open': 0.4, 'lip_width': 0.6, 'lip_corner_pull': 0.1},

        # Semi-vowels
        'R': {'mouth_open': 0.3, 'lip_width': 0.4, 'lip_corner_pull': 0.2},
        'W': {'mouth_open': 0.2, 'lip_width': 0.6, 'lip_corner_pull': 0.0},
        'Y': {'mouth_open': 0.4, 'lip_width': 0.3, 'lip_corner_pull': 0.3},
    }

    # Coarticulation matrix for smooth transitions
    COARTICULATION = {
        # Previous -> Current transition modifiers
        ('A', 'E'): {'duration_factor': 0.7},
        ('E', 'I'): {'duration_factor': 0.6},
        ('O', 'U'): {'duration_factor': 0.5},
        ('B', 'P'): {'duration_factor': 0.3},
        ('T', 'D'): {'duration_factor': 0.3},
    }

    def __init__(self, fps: int = 30):
        """Initialize the lip-sync engine."""
        self.fps = fps
        self.logger = logging.getLogger(__name__)

    def text_to_visemes(self, text: str, duration: float) -> List[Dict[str, Any]]:
        """
        Convert text to viseme sequence with timing.

        Args:
            text: Text to convert
            duration: Total duration in seconds

        Returns:
            List of viseme dictionaries with time and values
        """
        import re
        words = text.split()
        visemes = []
        current_time = 0.0

        # Calculate duration per word (proportional to length)
        word_durations = self._calculate_word_durations(words, duration)

        for word, word_duration in zip(words, word_durations):
            # Convert word to phonemes (simplified)
            phonemes = self._word_to_phonemes(word)
            phoneme_duration = word_duration / max(len(phonemes), 1)

            for i, phoneme in enumerate(phonemes):
                viseme_time = current_time + (i * phoneme_duration)

                # Apply coarticulation with previous viseme
                viseme_data = self._get_coarticulated_viseme(
                    phoneme,
                    visemes[-1] if visemes else None
                )

                visemes.append({
                    'time': viseme_time,
                    'duration': phoneme_duration,
                    'viseme': phoneme,
                    'morph_targets': viseme_data
                })

            current_time += word_duration

        return visemes

    def _calculate_word_durations(self, words: List[str], total_duration: float) -> List[float]:
        """Calculate duration for each word based on character count."""
        if not words:
            return []

        total_chars = sum(len(w) for w in words)
        return [
            (len(w) / total_chars) * total_duration
            for w in words
        ]

    def _word_to_phonemes(self, word: str) -> List[str]:
        """
        Convert word to phoneme sequence (simplified).

        This is a basic implementation. For production, use a proper
        phoneme library like epitran or g2p.
        """
        word = word.upper()
        phonemes = []

        # Simple letter-to-phoneme mapping
        for letter in word:
            if letter in self.VISEMES:
                phonemes.append(letter)
            elif letter in 'AEIOU':
                phonemes.append(letter)  # Vowel
            else:
                phonemes.append('_')  # Default silence

        return phonemes if phonemes else ['_']

    def _get_coarticulated_viseme(
        self,
        phoneme: str,
        prev_viseme: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Get viseme with coarticulation from previous viseme.

        Args:
            phoneme: Current phoneme
            prev_viseme: Previous viseme dictionary

        Returns:
            Coarticulated morph target values
        """
        base_viseme = self.VISEMES.get(phoneme, self.VISEMES['_'])

        if not prev_viseme:
            return base_viseme.copy()

        # Apply coarticulation blending
        prev_phoneme = prev_viseme.get('viseme', '_')
        coart_key = (prev_phoneme, phoneme)

        if coart_key in self.COARTICULATION:
            # Blend with previous viseme
            prev_morphs = prev_viseme.get('morph_targets', {})
            blend_factor = 0.3  # 30% influence from previous

            return {
                key: base_viseme[key] * (1 - blend_factor) +
                      prev_morphs.get(key, base_viseme[key]) * blend_factor
                for key in base_viseme
            }

        return base_viseme.copy()

    def generate_lip_sync_keyframes(
        self,
        text: str,
        duration: float,
        fps: int = None
    ) -> List[NMMKeyframe]:
        """
        Generate lip-sync keyframes for text.

        Args:
            text: Text to lip-sync
            duration: Duration in seconds
            fps: Frames per second (overrides instance fps)

        Returns:
            List of NMMKeyframe with lip_sync values
        """
        target_fps = fps or self.fps
        visemes = self.text_to_visemes(text, duration)
        keyframes = []

        # Generate keyframes at fps intervals
        frame_interval = 1.0 / target_fps
        current_time = 0.0

        while current_time <= duration:
            # Find active viseme at this time
            active_viseme = None
            for viseme in visemes:
                if viseme['time'] <= current_time < viseme['time'] + viseme['duration']:
                    active_viseme = viseme
                    break

            if active_viseme:
                morph_targets = active_viseme['morph_targets'].copy()
                morph_targets['mouth_open'] = active_viseme['morph_targets'].get('mouth_open', 0.0)

                keyframe = NMMKeyframe(
                    time=current_time,
                    morph_targets=morph_targets,
                    lip_sync_value=active_viseme['morph_targets'].get('mouth_open', 0.0)
                )
                keyframes.append(keyframe)

            current_time += frame_interval

        # Ensure closing keyframe
        keyframes.append(NMMKeyframe(
            time=duration,
            lip_sync_value=0.0,
            morph_targets={'mouth_open': 0.0}
        ))

        return keyframes


class FacialExpressionController:
    """
    Advanced facial expression controller with smooth transitions
    and layered expressions for BSL avatar.
    """

    # Expression blend masks for selective animation
    BLEND_MASKS = {
        'upper_face': ['brows', 'eyes_open', 'eyes_look_left', 'eyes_look_right'],
        'lower_face': ['smile', 'mouth_open', 'mouth_corner_pull', 'lip_purse'],
        'full_face': None  # All morph targets
    }

    def __init__(self, fps: int = 30):
        """Initialize the expression controller."""
        self.fps = fps
        self.logger = logging.getLogger(__name__)

        # Current expression state
        self._current_expressions = {}  # layer -> (expression, weight)
        self._transition_queue = []  # queue of pending transitions

        # Base expression reference
        self.BASE_EXPRESSIONS = AvatarWebGLRenderer.FACIAL_EXPRESSIONS

    def set_expression(
        self,
        expression: str,
        intensity: float = 1.0,
        duration: float = 0.3,
        layer: str = 'full_face'
    ) -> Dict[str, Any]:
        """
        Set facial expression with smooth transition.

        Args:
            expression: Expression name
            intensity: Intensity 0.0-1.0
            duration: Transition duration in seconds
            layer: Blend layer ('upper_face', 'lower_face', 'full_face')

        Returns:
            Expression transition data
        """
        if expression not in self.BASE_EXPRESSIONS:
            raise ValueError(f"Unknown expression: {expression}")

        transition = {
            'expression': expression,
            'intensity': intensity,
            'duration': duration,
            'layer': layer,
            'start_time': None,  # Will be set when played
            'target_values': self._apply_blend_mask(
                self.BASE_EXPRESSIONS[expression],
                layer
            )
        }

        self._transition_queue.append(transition)

        return {
            'success': True,
            'queued': True,
            'expression': expression,
            'layer': layer,
            'intensity': intensity
        }

    def blend_expressions(
        self,
        expression_layers: List[Tuple[str, str, float]]
    ) -> Dict[str, Any]:
        """
        Blend multiple expression layers together.

        Args:
            expression_layers: List of (expression, layer, weight) tuples

        Returns:
            Blended morph target values
        """
        blended = {key: 0.0 for key in self.BASE_EXPRESSIONS['neutral'].keys()}

        for expr_name, layer, weight in expression_layers:
            if expr_name not in self.BASE_EXPRESSIONS:
                continue

            expr_values = self._apply_blend_mask(
                self.BASE_EXPRESSIONS[expr_name],
                layer
            )

            for key, value in expr_values.items():
                blended[key] += value * weight

        # Clamp values
        for key in blended:
            blended[key] = max(-1.0, min(1.0, blended[key]))

        return {
            'success': True,
            'morph_targets': blended,
            'layers': expression_layers
        }

    def _apply_blend_mask(
        self,
        values: Dict[str, float],
        layer: str
    ) -> Dict[str, float]:
        """Apply blend mask to expression values."""
        if layer not in self.BLEND_MASKS:
            return values.copy()

        mask = self.BLEND_MASKS[layer]
        if mask is None:
            return values.copy()

        # Zero out masked values
        result = {key: 0.0 for key in values}
        for key in mask:
            if key in values:
                result[key] = values[key]

        return result

    def generate_transition_keyframes(
        self,
        from_expression: str,
        to_expression: str,
        duration: float,
        fps: int = None
    ) -> List[NMMKeyframe]:
        """
        Generate keyframes for smooth expression transition.

        Args:
            from_expression: Starting expression name
            to_expression: Target expression name
            duration: Transition duration
            fps: Frames per second

        Returns:
            List of NMMKeyframe for the transition
        """
        target_fps = fps or self.fps
        num_frames = int(duration * target_fps)
        keyframes = []

        from_values = self.BASE_EXPRESSIONS.get(from_expression, self.BASE_EXPRESSIONS['neutral'])
        to_values = self.BASE_EXPRESSIONS.get(to_expression, self.BASE_EXPRESSIONS['neutral'])

        # Generate transition keyframes with ease-in-out
        for i in range(num_frames + 1):
            t = i / num_frames if num_frames > 0 else 1.0

            # Ease-in-out easing
            eased_t = 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)

            morph_targets = {}
            for key in from_values:
                from_val = from_values.get(key, 0.0)
                to_val = to_values.get(key, 0.0)
                morph_targets[key] = from_val + eased_t * (to_val - from_val)

            keyframe = NMMKeyframe(
                time=i / target_fps,
                morph_targets=morph_targets,
                facial_expression=to_expression if t >= 1.0 else from_expression
            )
            keyframes.append(keyframe)

        return keyframes

    def get_available_expressions(self) -> List[str]:
        """Get list of available expressions."""
        return list(self.BASE_EXPRESSIONS.keys())

    def get_expression_layers(self) -> List[str]:
        """Get list of available blend layers."""
        return list(self.BLEND_MASKS.keys())


class BodyPoseController:
    """
    Body pose controller for BSL avatar with IK support
    for natural signing postures.
    """

    # Body joint hierarchy
    JOINT_HIERARCHY = {
        'root': ['spine', 'hips'],
        'spine': ['chest'],
        'chest': ['neck', 'shoulders'],
        'neck': ['head'],
        'shoulders': ['left_shoulder', 'right_shoulder'],
        'left_shoulder': ['left_arm', 'left_upper_arm'],
        'left_arm': ['left_forearm', 'left_elbow'],
        'left_forearm': ['left_wrist', 'left_hand'],
        'right_shoulder': ['right_arm', 'right_upper_arm'],
        'right_arm': ['right_forearm', 'right_elbow'],
        'right_forearm': ['right_wrist', 'right_hand'],
        'hips': ['left_hip', 'right_hip'],
        'left_hip': ['left_upper_leg'],
        'right_hip': ['right_upper_leg'],
    }

    # Predefined poses for BSL signing
    PREDEFINED_POSES = {
        'neutral': {
            'head': {'rotation': [0, 0, 0], 'position': [0, 1.7, 0]},
            'spine': {'rotation': [0, 0, 0], 'position': [0, 1.2, 0]},
            'chest': {'rotation': [0, 0, 0], 'position': [0, 1.0, 0]},
            'left_shoulder': {'rotation': [0, 0, -10], 'position': [-0.2, 1.45, 0]},
            'right_shoulder': {'rotation': [0, 0, 10], 'position': [0.2, 1.45, 0]},
            'left_arm': {'rotation': [0, 0, -20], 'position': [-0.3, 1.3, 0]},
            'right_arm': {'rotation': [0, 0, 20], 'position': [0.3, 1.3, 0]},
            'left_forearm': {'rotation': [0, 0, -30], 'position': [-0.4, 1.1, 0]},
            'right_forearm': {'rotation': [0, 0, 30], 'position': [0.4, 1.1, 0]},
            'left_hand': {'position': [-0.5, 1.0, 0.2]},
            'right_hand': {'position': [0.5, 1.0, 0.2]},
        },
        'signing_space': {
            'head': {'rotation': [0, 0, 0], 'position': [0, 1.7, 0]},
            'spine': {'rotation': [5, 0, 0], 'position': [0, 1.2, 0]},
            'chest': {'rotation': [-5, 0, 0], 'position': [0, 1.0, 0]},
            'left_shoulder': {'rotation': [0, 0, -30], 'position': [-0.25, 1.45, 0]},
            'right_shoulder': {'rotation': [0, 0, 30], 'position': [0.25, 1.45, 0]},
            'left_arm': {'rotation': [-45, 0, -30], 'position': [-0.35, 1.2, 0.2]},
            'right_arm': {'rotation': [-45, 0, 30], 'position': [0.35, 1.2, 0.2]},
            'left_forearm': {'rotation': [-30, 0, 0], 'position': [-0.45, 0.95, 0.3]},
            'right_forearm': {'rotation': [-30, 0, 0], 'position': [0.45, 0.95, 0.3]},
            'left_hand': {'position': [-0.5, 0.8, 0.4]},
            'right_hand': {'position': [0.5, 0.8, 0.4]},
        },
        'one_handed_sign': {
            'head': {'rotation': [0, 0, 0], 'position': [0, 1.7, 0]},
            'spine': {'rotation': [0, 0, 0], 'position': [0, 1.2, 0]},
            'chest': {'rotation': [0, 0, 0], 'position': [0, 1.0, 0]},
            'right_shoulder': {'rotation': [0, 0, 45], 'position': [0.25, 1.45, 0]},
            'right_arm': {'rotation': [-60, 0, 45], 'position': [0.4, 1.15, 0.3]},
            'right_forearm': {'rotation': [-45, 0, 0], 'position': [0.55, 0.85, 0.5]},
            'right_hand': {'position': [0.65, 0.7, 0.6]},
        },
        'two_handed_sign': {
            'head': {'rotation': [0, 0, 0], 'position': [0, 1.7, 0]},
            'spine': {'rotation': [0, 0, 0], 'position': [0, 1.2, 0]},
            'chest': {'rotation': [0, 0, 0], 'position': [0, 1.0, 0]},
            'left_shoulder': {'rotation': [0, 0, -45], 'position': [-0.25, 1.45, 0]},
            'right_shoulder': {'rotation': [0, 0, 45], 'position': [0.25, 1.45, 0]},
            'left_arm': {'rotation': [-60, 0, -45], 'position': [-0.4, 1.15, 0.3]},
            'right_arm': {'rotation': [-60, 0, 45], 'position': [0.4, 1.15, 0.3]},
            'left_forearm': {'rotation': [-45, 0, 0], 'position': [-0.55, 0.85, 0.5]},
            'right_forearm': {'rotation': [-45, 0, 0], 'position': [0.55, 0.85, 0.5]},
            'left_hand': {'position': [-0.65, 0.7, 0.6]},
            'right_hand': {'position': [0.65, 0.7, 0.6]},
        },
    }

    def __init__(self, fps: int = 30):
        """Initialize the body pose controller."""
        self.fps = fps
        self.logger = logging.getLogger(__name__)

        # Current pose state
        self._current_pose = 'neutral'
        self._joint_transforms = {}
        self._ik_constraints = {}

    def set_pose(self, pose_name: str) -> Dict[str, Any]:
        """
        Set predefined body pose.

        Args:
            pose_name: Name of predefined pose

        Returns:
            Pose configuration
        """
        if pose_name not in self.PREDEFINED_POSES:
            raise ValueError(
                f"Unknown pose: {pose_name}. "
                f"Available: {list(self.PREDEFINED_POSES.keys())}"
            )

        self._current_pose = pose_name
        self._joint_transforms = self.PREDEFINED_POSES[pose_name].copy()

        self.logger.info(f"Body pose set to: {pose_name}")

        return {
            'success': True,
            'pose': pose_name,
            'joints': self._joint_transforms
        }

    def set_joint_transform(
        self,
        joint: str,
        rotation: Optional[List[float]] = None,
        position: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Set transform for a specific joint.

        Args:
            joint: Joint name
            rotation: Euler rotation [x, y, z] in degrees
            position: Position [x, y, z]

        Returns:
            Updated joint configuration
        """
        if joint not in self._joint_transforms:
            self._joint_transforms[joint] = {}

        joint_data = self._joint_transforms[joint]

        if rotation is not None:
            joint_data['rotation'] = rotation

        if position is not None:
            joint_data['position'] = position

        return {
            'success': True,
            'joint': joint,
            'transform': joint_data
        }

    def solve_ik(
        self,
        target_joint: str,
        target_position: List[float],
        chain: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Simple IK solver for reaching a target position.

        Args:
            target_joint: End effector joint name
            target_position: Target [x, y, z] position
            chain: Optional list of joints in the IK chain

        Returns:
            Solved joint transforms
        """
        # Simplified CCD IK solver
        if chain is None:
            # Determine chain from hierarchy
            chain = self._get_chain_to_joint(target_joint)

        # For now, return a placeholder - full IK implementation
        # would require more complex math

        return {
            'success': True,
            'target_joint': target_joint,
            'target_position': target_position,
            'chain': chain,
            'solved': False,  # Requires full IK implementation
            'message': 'IK solver placeholder - use predefined poses'
        }

    def _get_chain_to_joint(self, joint: str) -> List[str]:
        """Get joint chain from root to target joint."""
        chain = []
        visited = set()

        def find_path(current, target, path):
            if current == target:
                return path + [current]
            if current in visited:
                return None
            visited.add(current)

            if current in self.JOINT_HIERARCHY:
                for child in self.JOINT_HIERARCHY[current]:
                    result = find_path(child, target, path + [current])
                    if result:
                        return result
            return None

        result = find_path('root', joint, [])
        return result if result else []

    def generate_pose_keyframes(
        self,
        from_pose: str,
        to_pose: str,
        duration: float,
        fps: int = None
    ) -> List[NMMKeyframe]:
        """
        Generate keyframes for pose transition.

        Args:
            from_pose: Starting pose name
            to_pose: Target pose name
            duration: Transition duration
            fps: Frames per second

        Returns:
            List of NMMKeyframe for the transition
        """
        target_fps = fps or self.fps
        num_frames = int(duration * target_fps)
        keyframes = []

        from_joints = self.PREDEFINED_POSES.get(from_pose, {})
        to_joints = self.PREDEFINED_POSES.get(to_pose, {})

        # Generate transition keyframes
        for i in range(num_frames + 1):
            t = i / num_frames if num_frames > 0 else 1.0
            eased_t = 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)

            bone_positions = {}
            bone_rotations = {}

            # Interpolate all joints
            for joint in to_joints:
                from_data = from_joints.get(joint, {})
                to_data = to_joints.get(joint, {})

                from_pos = from_data.get('position', [0, 0, 0])
                to_pos = to_data.get('position', [0, 0, 0])
                from_rot = from_data.get('rotation', [0, 0, 0])
                to_rot = to_data.get('rotation', [0, 0, 0])

                bone_positions[joint] = tuple(
                    from_pos[k] + eased_t * (to_pos[k] - from_pos[k])
                    for k in range(3)
                )
                bone_rotations[joint] = tuple(
                    from_rot[k] + eased_t * (to_rot[k] - from_rot[k])
                    for k in range(3)
                )

            keyframe = NMMKeyframe(
                time=i / target_fps,
                bone_positions=bone_positions,
                bone_rotations=bone_rotations
            )
            keyframes.append(keyframe)

        return keyframes

    def get_available_poses(self) -> List[str]:
        """Get list of available poses."""
        return list(self.PREDEFINED_POSES.keys())


class GestureQueueManager:
    """
    Queue manager for BSL avatar gestures with priority,
    blending, and smooth transitions.
    """

    # Gesture priority levels
    PRIORITY = {
        'critical': 0,  # Emergency stops, important alerts
        'high': 1,      # User interactions, explicit requests
        'normal': 2,    # Normal signing flow
        'low': 3,       # Background/idle animations
        'idle': 4,      # Idle animations
    }

    def __init__(self, fps: int = 30):
        """Initialize the gesture queue manager."""
        self.fps = fps
        self.logger = logging.getLogger(__name__)

        # Queue state
        self._queue = []  # List of queued gestures
        self._current_gesture = None
        self._blending_gestures = {}  # gesture_id -> blend_data

        # Configuration
        self._blend_duration = 0.2  # Default blend duration
        self._max_queue_size = 100

    def enqueue(
        self,
        gesture_id: str,
        animation: NMMAnimation,
        priority: str = 'normal',
        blend_mode: str = 'smooth',
        interruptible: bool = True
    ) -> Dict[str, Any]:
        """
        Add a gesture to the queue.

        Args:
            gesture_id: Unique gesture identifier
            animation: NMMAnimation to play
            priority: Priority level ('critical', 'high', 'normal', 'low', 'idle')
            blend_mode: How to blend with previous ('smooth', 'cut', 'crossfade')
            interruptible: Whether this gesture can be interrupted

        Returns:
            Queue status
        """
        if priority not in self.PRIORITY:
            raise ValueError(f"Invalid priority: {priority}")

        gesture = {
            'id': gesture_id,
            'animation': animation,
            'priority': self.PRIORITY[priority],
            'blend_mode': blend_mode,
            'interruptible': interruptible,
            'queued_at': datetime.now(timezone.utc).isoformat(),
            'status': 'queued'
        }

        # Insert in priority order
        self._queue.append(gesture)
        self._queue.sort(key=lambda g: g['priority'])

        # Limit queue size
        if len(self._queue) > self._max_queue_size:
            removed = self._queue.pop()
            self.logger.warning(f"Gesture {removed['id']} dropped (queue full)")

        self.logger.info(f"Gesture {gesture_id} queued (priority={priority})")

        return {
            'success': True,
            'gesture_id': gesture_id,
            'queue_position': self._get_queue_position(gesture_id),
            'queue_size': len(self._queue)
        }

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get next gesture from queue.

        Returns:
            Next gesture or None if queue is empty
        """
        if not self._queue:
            return None

        return self._queue.pop(0)

    def interrupt_current(self, gesture_id: str) -> bool:
        """
        Interrupt current gesture if it's interruptible.

        Args:
            gesture_id: New gesture to interrupt with

        Returns:
            True if interrupt was successful
        """
        if not self._current_gesture:
            return True  # No current gesture to interrupt

        if not self._current_gesture.get('interruptible', True):
            self.logger.warning("Current gesture is not interruptible")
            return False

        self.logger.info(f"Interrupting current gesture with {gesture_id}")

        # Move current gesture back to queue
        if self._current_gesture:
            self._queue.insert(0, self._current_gesture)

        # Find and promote the new gesture
        for i, gesture in enumerate(self._queue):
            if gesture['id'] == gesture_id:
                self._current_gesture = gesture
                self._queue.pop(i)
                return True

        return False

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            'current_gesture': self._current_gesture['id'] if self._current_gesture else None,
            'queue_size': len(self._queue),
            'queue': [
                {
                    'id': g['id'],
                    'priority': g['priority'],
                    'blend_mode': g['blend_mode']
                }
                for g in self._queue[:10]  # First 10
            ],
            'max_queue_size': self._max_queue_size
        }

    def clear_queue(self, priority_threshold: Optional[str] = None) -> int:
        """
        Clear queue, optionally up to a priority threshold.

        Args:
            priority_threshold: Clear gestures with this priority or lower

        Returns:
            Number of gestures cleared
        """
        if priority_threshold is None:
            cleared = len(self._queue)
            self._queue.clear()
        else:
            threshold = self.PRIORITY.get(priority_threshold, 2)
            original_size = len(self._queue)
            self._queue = [g for g in self._queue if g['priority'] < threshold]
            cleared = original_size - len(self._queue)

        self.logger.info(f"Cleared {cleared} gestures from queue")
        return cleared

    def _get_queue_position(self, gesture_id: str) -> int:
        """Get position of gesture in queue."""
        for i, gesture in enumerate(self._queue):
            if gesture['id'] == gesture_id:
                return i
        return -1

    def blend_gestures(
        self,
        gesture1: NMMAnimation,
        gesture2: NMMAnimation,
        blend_duration: float,
        blend_function: str = 'linear'
    ) -> NMMAnimation:
        """
        Blend two gestures together.

        Args:
            gesture1: First gesture
            gesture2: Second gesture
            blend_duration: Duration of blend in seconds
            blend_function: Blend function ('linear', 'ease-in-out')

        Returns:
            New blended animation
        """
        # Create blended animation
        blended = NMMAnimation(
            name=f"blend_{gesture1.name}_{gesture2.name}",
            duration=gesture1.duration + blend_duration + gesture2.duration,
            fps=self.fps,
            loop=False
        )

        # Add gesture1 keyframes
        for kf in gesture1.keyframes:
            blended.add_keyframe(kf)

        # Generate blend keyframes
        blend_frames = int(blend_duration * self.fps)
        if blend_frames > 0:
            last_kf1 = gesture1.keyframes[-1] if gesture1.keyframes else NMMKeyframe(time=0)
            first_kf2 = gesture2.keyframes[0] if gesture2.keyframes else NMMKeyframe(time=0)

            for i in range(1, blend_frames + 1):
                t = i / blend_frames
                if blend_function == 'ease-in-out':
                    t = 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)

                blended_kf = self._interpolate_keyframes(last_kf1, first_kf2, t)
                blended.add_keyframe(blended_kf)

        # Add gesture2 keyframes (offset time)
        offset = gesture1.duration + blend_duration
        for kf in gesture2.keyframes:
            new_kf = NMMKeyframe(
                time=kf.time + offset,
                morph_targets=kf.morph_targets.copy(),
                bone_rotations=kf.bone_rotations.copy(),
                bone_positions=kf.bone_positions.copy(),
                bone_scales=kf.bone_scales.copy(),
                facial_expression=kf.facial_expression,
                handshape=kf.handshape,
                lip_sync_value=kf.lip_sync_value
            )
            blended.add_keyframe(new_kf)

        return blended

    def _interpolate_keyframes(
        self,
        kf1: NMMKeyframe,
        kf2: NMMKeyframe,
        t: float
    ) -> NMMKeyframe:
        """Interpolate between two keyframes."""
        return NMMKeyframe(
            time=kf1.time + t * (kf2.time - kf1.time),
            morph_targets={
                k: kf1.morph_targets.get(k, 0) + t * (kf2.morph_targets.get(k, 0) - kf1.morph_targets.get(k, 0))
                for k in set(kf1.morph_targets) | set(kf2.morph_targets)
            },
            bone_rotations={
                k: tuple(
                    kf1.bone_rotations.get(k, (0, 0, 0, 1))[j] + t * (
                        kf2.bone_rotations.get(k, (0, 0, 0, 1))[j] -
                        kf1.bone_rotations.get(k, (0, 0, 0, 1))[j]
                    )
                    for j in range(4)
                )
                for k in set(kf1.bone_rotations) | set(kf2.bone_rotations)
            },
            bone_positions={
                k: tuple(
                    kf1.bone_positions.get(k, (0, 0, 0))[j] + t * (
                        kf2.bone_positions.get(k, (0, 0, 0))[j] -
                        kf1.bone_positions.get(k, (0, 0, 0))[j]
                    )
                    for j in range(3)
                )
                for k in set(kf1.bone_positions) | set(kf2.bone_positions)
            }
        )


class BSLAnimationLibrary:
    """
    Comprehensive BSL animation library with 107 predefined animations.

    Includes:
    - 50 common BSL phrases
    - 26 alphabet letters (A-Z)
    - 21 numbers (0-20)
    - 10 emotional expressions
    """

    def __init__(self, fps: int = 30):
        """
        Initialize the BSL animation library.

        Args:
            fps: Frames per second for generated animations
        """
        self.fps = fps
        self.logger = logging.getLogger(__name__)
        self._animations = self._build_animation_library()

    def _build_animation_library(self) -> Dict[str, NMMAnimation]:
        """Build the complete animation library."""
        library = {}

        # Add phrase animations
        for phrase, config in self.BSL_PHRASES.items():
            library[f"phrase_{phrase}"] = self._create_phrase_animation(phrase, config)

        # Add alphabet animations
        for letter, config in self.BSL_ALPHABET.items():
            library[f"letter_{letter}"] = self._create_alphabet_animation(letter, config)

        # Add number animations
        for number, config in self.BSL_NUMBERS.items():
            library[f"number_{number}"] = self._create_number_animation(number, config)

        # Add emotion animations
        for emotion, config in self.BSL_EMOTIONS.items():
            library[f"emotion_{emotion}"] = self._create_emotion_animation(emotion, config)

        self.logger.info(f"Built animation library with {len(library)} animations")
        return library

    def get_animation(self, animation_id: str) -> Optional[NMMAnimation]:
        """
        Get an animation by ID.

        Args:
            animation_id: Animation identifier (e.g., 'phrase_hello', 'letter_A')

        Returns:
            NMMAnimation or None if not found
        """
        return self._animations.get(animation_id)

    def list_animations(self, category: Optional[str] = None) -> List[str]:
        """
        List available animations.

        Args:
            category: Filter by category ('phrase', 'letter', 'number', 'emotion')

        Returns:
            List of animation IDs
        """
        if category:
            return [aid for aid in self._animations.keys() if aid.startswith(f"{category}_")]
        return list(self._animations.keys())

    def get_categories(self) -> Dict[str, int]:
        """Get count of animations by category."""
        categories = {'phrase': 0, 'letter': 0, 'number': 0, 'emotion': 0}
        for aid in self._animations:
            for cat in categories:
                if aid.startswith(f"{cat}_"):
                    categories[cat] += 1
        return categories

    # ==========================================================================
    # BSL PHRASES (50 common phrases)
    # ==========================================================================

    BSL_PHRASES = {
        # Greetings
        'hello': {
            'duration': 1.5,
            'hands': ['right_wave', 'left_open'],
            'expression': 'happy',
            'description': 'Wave hello'
        },
        'goodbye': {
            'duration': 1.8,
            'hands': ['right_wave', 'left_open'],
            'expression': 'neutral',
            'description': 'Wave goodbye'
        },
        'good_morning': {
            'duration': 2.0,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'happy',
            'description': 'Flat hands rise (sun)'
        },
        'good_night': {
            'duration': 2.0,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Flat hands lower'
        },
        'please': {
            'duration': 1.2,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Rub chest in circle'
        },
        'thank_you': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_open'],
            'expression': 'happy',
            'description': 'Hand from chin forward'
        },
        'sorry': {
            'duration': 1.8,
            'hands': ['right_fist', 'left_open'],
            'expression': 'sad',
            'description': 'Fist circles on chest'
        },
        'welcome': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'happy',
            'description': 'Open arms gesture'
        },

        # Common questions
        'how_are_you': {
            'duration': 2.5,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Both flat hands forward, then point'
        },
        'whats_your_name': {
            'duration': 2.2,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index finger points, then chest tap'
        },
        'whats_wrong': {
            'duration': 2.0,
            'hands': ['right_open', 'left_open'],
            'expression': 'concerned',
            'description': 'Hands up, palms forward, questioning'
        },
        'where_is': {
            'duration': 1.8,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index scans, then points'
        },
        'when': {
            'duration': 1.5,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index finger points to wrist'
        },
        'why': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Both hands open, palms up, tilt'
        },
        'who': {
            'duration': 1.5,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index finger points around'
        },
        'what': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Both hands shake, palms down'
        },

        # Responses
        'i_am_fine': {
            'duration': 2.0,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'happy',
            'description': 'Flat hand chest, then thumbs up'
        },
        'i_am_happy': {
            'duration': 1.8,
            'hands': ['right_flat', 'left_open'],
            'expression': 'happy',
            'description': 'Flat hand chest, smile'
        },
        'i_am_sad': {
            'duration': 1.8,
            'hands': ['right_flat', 'left_open'],
            'expression': 'sad',
            'description': 'Flat hand chest, frown'
        },
        'i_dont_understand': {
            'duration': 2.2,
            'hands': ['right_index', 'left_index'],
            'expression': 'confused',
            'description': 'Index fingers cross, shake head'
        },
        'i_agree': {
            'duration': 1.5,
            'hands': ['right_fist', 'left_fist'],
            'expression': 'neutral',
            'description': 'Both fists shake (yes gesture)'
        },
        'i_disagree': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Hands wave side to side'
        },
        'yes': {
            'duration': 1.2,
            'hands': ['right_fist', 'left_fist'],
            'expression': 'neutral',
            'description': 'Fist nods up and down'
        },
        'no': {
            'duration': 1.2,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Hand waves side to side'
        },
        'maybe': {
            'duration': 1.8,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Hands rock side to side'
        },

        # Common phrases
        'help': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'concerned',
            'description': 'Flat hand lifts up'
        },
        'wait': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Both hands flat, fingers spread'
        },
        'slow': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Hands move slowly downward'
        },
        'fast': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Hands move quickly outward'
        },
        'stop': {
            'duration': 1.2,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand faces forward'
        },
        'go': {
            'duration': 1.2,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index finger points forward'
        },
        'come_here': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Hand waves inward'
        },
        'look': {
            'duration': 1.2,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index points to eyes, then out'
        },
        'listen': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Cup hand to ear'
        },

        # Time phrases
        'now': {
            'duration': 1.2,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand snaps forward'
        },
        'later': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Hand moves from center to side'
        },
        'today': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Both arms form arch overhead'
        },
        'tomorrow': {
            'duration': 1.8,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Arms arch overhead, then forward'
        },
        'yesterday': {
            'duration': 1.8,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Thumb points over shoulder'
        },

        # People
        'me': {
            'duration': 1.0,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand points to chest'
        },
        'you': {
            'duration': 1.0,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index finger points forward'
        },
        'he': {
            'duration': 1.2,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand points to side'
        },
        'she': {
            'duration': 1.2,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand points to side (pinkie out)'
        },
        'we': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Both flat hands circle together'
        },
        'they': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_flat'],
            'expression': 'neutral',
            'description': 'Both flat hands point outward'
        },

        # Other common phrases
        'love': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_open'],
            'expression': 'happy',
            'description': 'Both arms crossed over chest'
        },
        'like': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_open'],
            'expression': 'happy',
            'description': 'Flat hand chest, then lift'
        },
        'dont_like': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand chest, then hand drops'
        },
        'want': {
            'duration': 1.5,
            'hands': ['right_open', 'left_open'],
            'expression': 'neutral',
            'description': 'Hands pull toward chest'
        },
        'need': {
            'duration': 1.8,
            'hands': ['right_fist', 'left_open'],
            'expression': 'neutral',
            'description': 'Fist rubs chest'
        },
        'think': {
            'duration': 1.8,
            'hands': ['right_index', 'left_open'],
            'expression': 'neutral',
            'description': 'Index finger circles temple'
        },
        'know': {
            'duration': 1.5,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand taps forehead'
        },
        'remember': {
            'duration': 2.0,
            'hands': ['right_flat', 'left_open'],
            'expression': 'neutral',
            'description': 'Flat hand forehead, then pull forward'
        },
    }

    # ==========================================================================
    # BSL ALPHABET (A-Z, 26 letters)
    # ==========================================================================

    BSL_ALPHABET = {
        'A': {
            'duration': 1.0,
            'handshape': 'fist',
            'thumb': 'up',
            'description': 'Fist with thumb up'
        },
        'B': {
            'duration': 1.0,
            'handshape': 'flat',
            'thumb': 'crossed',
            'description': 'Flat hand, thumb across palm'
        },
        'C': {
            'duration': 1.0,
            'handshape': 'curved',
            'thumb': 'out',
            'description': 'Curved hand, C shape'
        },
        'D': {
            'duration': 1.0,
            'handshape': 'index',
            'thumb': 'out',
            'description': 'Index up, others curved, thumb out'
        },
        'E': {
            'duration': 1.0,
            'handshape': 'curved',
            'thumb': 'crossed',
            'description': 'Fingers curved down across thumb'
        },
        'F': {
            'duration': 1.0,
            'handshape': 'ok',
            'description': 'OK sign, thumb and index circle'
        },
        'G': {
            'duration': 1.0,
            'handshape': 'point',
            'thumb': 'out',
            'description': 'Index and thumb point sideways'
        },
        'H': {
            'duration': 1.0,
            'handshape': 'two_finger',
            'thumb': 'out',
            'description': 'Index and middle sideways, thumb out'
        },
        'I': {
            'duration': 1.0,
            'handshape': 'pinkie',
            'description': 'Pinkie finger up only'
        },
        'J': {
            'duration': 1.2,
            'handshape': 'pinkie',
            'motion': 'i_to_j',
            'description': 'Pinkie up, draws J in air'
        },
        'K': {
            'duration': 1.0,
            'handshape': 'peace',
            'thumb': 'between',
            'description': 'Index and middle up, thumb between'
        },
        'L': {
            'duration': 1.0,
            'handshape': 'l_shape',
            'description': 'Thumb and index form L'
        },
        'M': {
            'duration': 1.0,
            'handshape': 'three_finger_over',
            'description': 'Three fingers over thumb'
        },
        'N': {
            'duration': 1.0,
            'handshape': 'two_finger_over',
            'description': 'Two fingers over thumb'
        },
        'O': {
            'duration': 1.0,
            'handshape': 'circle',
            'description': 'Fingers and thumb form circle'
        },
        'P': {
            'duration': 1.0,
            'handshape': 'down_k',
            'description': 'K handshape pointing down'
        },
        'Q': {
            'duration': 1.0,
            'handshape': 'down_g',
            'description': 'G handshape pointing down'
        },
        'R': {
            'duration': 1.0,
            'handshape': 'crossed',
            'description': 'Index and middle crossed'
        },
        'S': {
            'duration': 1.0,
            'handshape': 'fist',
            'thumb': 'crossed',
            'description': 'Fist, thumb over fingers'
        },
        'T': {
            'duration': 1.0,
            'handshape': 'fist',
            'thumb': 'between',
            'description': 'Fist, thumb between index and middle'
        },
        'U': {
            'duration': 1.0,
            'handshape': 'two_finger',
            'description': 'Index and middle together up'
        },
        'V': {
            'duration': 1.0,
            'handshape': 'peace',
            'description': 'Peace sign (index and middle up)'
        },
        'W': {
            'duration': 1.0,
            'handshape': 'three_finger',
            'description': 'Three fingers up (index, middle, ring)'
        },
        'X': {
            'duration': 1.0,
            'handshape': 'hook',
            'description': 'Index finger hooked like claw'
        },
        'Y': {
            'duration': 1.0,
            'handshape': 'y_shaped',
            'description': 'Thumb and pinkie up (hang loose)'
        },
        'Z': {
            'duration': 1.2,
            'handshape': 'index',
            'motion': 'z_shape',
            'description': 'Index finger draws Z in air'
        },
    }

    # ==========================================================================
    # BSL NUMBERS (0-20, 21 numbers)
    # ==========================================================================

    BSL_NUMBERS = {
        '0': {
            'duration': 1.0,
            'handshape': 'fist',
            'description': 'Closed fist'
        },
        '1': {
            'duration': 1.0,
            'handshape': 'index',
            'description': 'Index finger up'
        },
        '2': {
            'duration': 1.0,
            'handshape': 'peace',
            'description': 'V sign (index and middle)'
        },
        '3': {
            'duration': 1.0,
            'handshape': 'three_finger',
            'description': 'Three fingers up'
        },
        '4': {
            'duration': 1.0,
            'handshape': 'four_finger',
            'description': 'Four fingers up, thumb in'
        },
        '5': {
            'duration': 1.0,
            'handshape': 'open',
            'description': 'All five fingers spread'
        },
        '6': {
            'duration': 1.0,
            'handshape': 'six',
            'description': 'All five up, thumb touches pinkie'
        },
        '7': {
            'duration': 1.0,
            'handshape': 'seven',
            'description': 'All five up, thumb touches ring'
        },
        '8': {
            'duration': 1.0,
            'handshape': 'eight',
            'description': 'All five up, thumb touches middle'
        },
        '9': {
            'duration': 1.0,
            'handshape': 'nine',
            'description': 'All five up, thumb touches index'
        },
        '10': {
            'duration': 1.2,
            'handshape': 'fist',
            'thumb': 'out',
            'motion': 'shake',
            'description': 'Thumb shakes side to side'
        },
        '11': {
            'duration': 1.2,
            'handshape': 'index',
            'motion': 'flick',
            'description': 'Index flicks up twice'
        },
        '12': {
            'duration': 1.2,
            'handshape': 'peace',
            'motion': 'flick',
            'description': 'V sign flicks up twice'
        },
        '13': {
            'duration': 1.2,
            'handshape': 'three_finger',
            'motion': 'flick',
            'description': 'Three fingers flick up twice'
        },
        '14': {
            'duration': 1.2,
            'handshape': 'four_finger',
            'motion': 'flick',
            'description': 'Four fingers flick up twice'
        },
        '15': {
            'duration': 1.2,
            'handshape': 'open',
            'motion': 'flick',
            'description': 'Open hand flicks up twice'
        },
        '16': {
            'duration': 1.5,
            'handshape': 'six',
            'motion': 'rotate',
            'description': 'Six handshape twists'
        },
        '17': {
            'duration': 1.5,
            'handshape': 'seven',
            'motion': 'rotate',
            'description': 'Seven handshape twists'
        },
        '18': {
            'duration': 1.5,
            'handshape': 'eight',
            'motion': 'rotate',
            'description': 'Eight handshape twists'
        },
        '19': {
            'duration': 1.5,
            'handshape': 'nine',
            'motion': 'rotate',
            'description': 'Nine handshape twists'
        },
        '20': {
            'duration': 1.5,
            'handshape': 'two_finger',
            'motion': 'bounce',
            'description': 'Two fingers bounce up twice'
        },
    }

    # ==========================================================================
    # BSL EMOTIONS (10 emotions)
    # ==========================================================================

    BSL_EMOTIONS = {
        'happy': {
            'duration': 1.5,
            'expression': 'happy',
            'body_language': 'upright',
            'description': 'Smile, open posture, slight bounce'
        },
        'sad': {
            'duration': 1.8,
            'expression': 'sad',
            'body_language': 'slumped',
            'description': 'Frown, shoulders down, look down'
        },
        'angry': {
            'duration': 1.5,
            'expression': 'angry',
            'body_language': 'tense',
            'description': 'Furrowed brows, tense shoulders, fists'
        },
        'surprised': {
            'duration': 1.2,
            'expression': 'surprised',
            'body_language': 'alert',
            'description': 'Wide eyes, mouth open, lean back'
        },
        'confused': {
            'duration': 2.0,
            'expression': 'confused',
            'body_language': 'tense',
            'description': 'Head tilt, brow furrow, hand to chin'
        },
        'excited': {
            'duration': 1.5,
            'expression': 'happy',
            'body_language': 'energetic',
            'description': 'Big smile, bouncy, hands up'
        },
        'bored': {
            'duration': 2.0,
            'expression': 'neutral',
            'body_language': 'slumped',
            'description': 'Neutral face, shoulders down, sighing'
        },
        'worried': {
            'duration': 2.0,
            'expression': 'concerned',
            'body_language': 'tense',
            'description': 'Brows up, corners down, hands fidget'
        },
        'proud': {
            'duration': 1.5,
            'expression': 'happy',
            'body_language': 'upright',
            'description': 'Chin up, chest out, smile'
        },
        'embarrassed': {
            'duration': 2.0,
            'expression': 'neutral',
            'body_language': 'closed',
            'description': 'Look down, cover face, shoulders forward'
        },
    }

    # ==========================================================================
    # ANIMATION CREATION METHODS
    # ==========================================================================

    def _create_phrase_animation(self, phrase: str, config: Dict[str, Any]) -> NMMAnimation:
        """Create a phrase animation from config."""
        animation = NMMAnimation(
            name=f"phrase_{phrase}",
            duration=config['duration'],
            fps=self.fps,
            loop=False
        )

        num_frames = int(config['duration'] * self.fps)

        # Generate keyframes based on configuration
        for i in range(num_frames):
            t = i / num_frames
            progress = 0.5 - 0.5 * __import__('math').cos(t * __import__('math').pi)

            kf = NMMKeyframe(time=t * config['duration'])

            # Apply facial expression
            if 'expression' in config:
                kf.facial_expression = config['expression']

            # Apply handshapes
            hands = config.get('hands', ['right_open', 'left_open'])
            if len(hands) > 0 and 'right' in hands[0]:
                kf.handshape = hands[0].replace('right_', '')

            # Add motion based on description
            if 'wave' in config['description']:
                kf.bone_rotations['right_forearm'] = (
                    0.5 * __import__('math').sin(progress * __import__('math').pi * 2),
                    0, 0, 1
                )
            elif 'point' in config['description']:
                kf.bone_positions['right_hand'] = (0.3, 1.0, 0.5)

            animation.add_keyframe(kf)

        return animation

    def _create_alphabet_animation(self, letter: str, config: Dict[str, Any]) -> NMMAnimation:
        """Create an alphabet letter animation."""
        animation = NMMAnimation(
            name=f"letter_{letter}",
            duration=config['duration'],
            fps=self.fps,
            loop=False
        )

        num_frames = int(config['duration'] * self.fps)

        # Starting pose
        for i in range(num_frames):
            t = i / num_frames
            progress = min(1.0, t * 2)  # Quick transition

            kf = NMMKeyframe(time=t * config['duration'])
            kf.handshape = config['handshape']

            # Position hand in signing space
            kf.bone_positions['right_hand'] = (0.3, 1.1, 0.5)

            # Add motion if specified
            if 'motion' in config:
                if config['motion'] == 'i_to_j':
                    # Draw J shape
                    angle = progress * __import__('math').pi
                    kf.bone_positions['right_hand'] = (
                        0.3 + 0.1 * __import__('math').sin(angle),
                        1.1 - 0.2 * progress,
                        0.5
                    )
                elif config['motion'] == 'z_shape':
                    # Draw Z shape
                    kf.bone_positions['right_hand'] = (
                        0.3 + 0.15 * (t if t < 0.33 else (0.66 - t) if t < 0.66 else t - 0.66),
                        1.1 - 0.2 * (t if t < 0.5 else 1 - t),
                        0.5
                    )

            animation.add_keyframe(kf)

        return animation

    def _create_number_animation(self, number: str, config: Dict[str, Any]) -> NMMAnimation:
        """Create a number animation."""
        animation = NMMAnimation(
            name=f"number_{number}",
            duration=config['duration'],
            fps=self.fps,
            loop=False
        )

        num_frames = int(config['duration'] * self.fps)

        for i in range(num_frames):
            t = i / num_frames
            progress = min(1.0, t * 3)  # Quick pose

            kf = NMMKeyframe(time=t * config['duration'])
            kf.handshape = config['handshape']

            # Position hand
            kf.bone_positions['right_hand'] = (0.25, 1.15, 0.4)

            # Add motion
            motion = config.get('motion', '')
            if motion == 'shake':
                kf.bone_rotations['right_forearm'] = (
                    0, 0.5 * __import__('math').sin(t * __import__('math').pi * 4), 0, 1
                )
            elif motion == 'flick':
                # Flick motion
                if i < num_frames // 2:
                    kf.bone_positions['right_hand'] = (0.25, 1.05, 0.4)
                else:
                    kf.bone_positions['right_hand'] = (0.25, 1.15, 0.4)
            elif motion == 'rotate':
                kf.bone_rotations['right_hand'] = (t * __import__('math').pi * 2, 0, 0, 1)
            elif motion == 'bounce':
                kf.bone_positions['right_hand'] = (
                    0.25,
                    1.15 + 0.05 * __import__('math').sin(t * __import__('math').pi * 2),
                    0.4
                )

            animation.add_keyframe(kf)

        return animation

    def _create_emotion_animation(self, emotion: str, config: Dict[str, Any]) -> NMMAnimation:
        """Create an emotion animation."""
        animation = NMMAnimation(
            name=f"emotion_{emotion}",
            duration=config['duration'],
            fps=self.fps,
            loop=False
        )

        num_frames = int(config['duration'] * self.fps)

        for i in range(num_frames):
            t = i / num_frames
            progress = 0.5 - 0.5 * __import__('math').cos(t * __import__('math').pi)

            kf = NMMKeyframe(time=t * config['duration'])
            kf.facial_expression = emotion

            # Body language modifications
            body = config.get('body_language', 'neutral')
            if body == 'slumped':
                kf.bone_rotations['spine'] = (0.2 * progress, 0, 0, 1)
            elif body == 'upright':
                kf.bone_rotations['spine'] = (-0.1 * progress, 0, 0, 1)
            elif body == 'tense':
                kf.bone_positions['shoulders'] = (0, 0.05 * progress, 0)
            elif body == 'energetic':
                # Bouncy motion
                kf.bone_positions['hips'] = (
                    0,
                    0.02 * __import__('math').sin(t * __import__('math').pi * 4),
                    0
                )
            elif body == 'closed':
                kf.bone_rotations['shoulders'] = (0, 0, 0.3 * progress, 1)

            animation.add_keyframe(kf)

        return animation


__all__ = [
    "AvatarWebGLRenderer",
    "AvatarModel",
    "NMMAnimation",
    "NMMKeyframe",
    "WebGLError",
    "AvatarLoadError",
    "AnimationLoadError",
    "LipSyncEngine",
    "FacialExpressionController",
    "BodyPoseController",
    "GestureQueueManager",
    "BSLAnimationLibrary",
]
