"""
Real-time BSL (British Sign Language) avatar rendering system.

Provides 3D avatar animation and rendering for sign language translation.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class AvatarState(Enum):
    """Avatar rendering state."""
    IDLE = "idle"
    SIGNING = "signing"
    TRANSITIONING = "transitioning"
    ERROR = "error"


@dataclass
class SignGesture:
    """BSL sign gesture data."""
    id: str
    gloss: str  # BSL gloss word
    duration: float  # seconds
    both_hands: bool = True
    dominant_hand: str = "right"  # left or right
    facial_expression: str = "neutral"
    body_language: str = "neutral"

    # Hand configuration (simplified)
    handshape: str = "fist"
    orientation: str = "palm"
    location: str = "chest"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "gloss": self.gloss,
            "duration": self.duration,
            "both_hands": self.both_hands,
            "dominant_hand": self.dominant_hand,
            "facial_expression": self.facial_expression,
            "body_language": self.body_language,
            "handshape": self.handshape,
            "orientation": self.orientation,
            "location": self.location
        }


@dataclass
class AvatarConfig:
    """Avatar rendering configuration."""
    model_path: str = "/models/bsl_avatar"
    resolution: tuple = (1920, 1080)
    fps: int = 30
    enable_facial_expressions: bool = True
    enable_body_language: bool = True
    cache_gestures: bool = True
    max_cached_gestures: int = 1000


@dataclass
class RenderingMetrics:
    """Avatar rendering performance metrics."""
    frames_rendered: int = 0
    total_render_time: float = 0.0
    avg_frame_time: float = 0.0
    dropped_frames: int = 0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class GestureLibrary:
    """Library of BSL gestures with caching."""

    def __init__(self, cache_size: int = 1000):
        self._gestures: Dict[str, SignGesture] = {}
        self._cache_size = cache_size

    def load_gesture(self, gloss: str) -> Optional[SignGesture]:
        """Load a gesture by gloss."""
        if gloss in self._gestures:
            return self._gestures[gloss]

        # In production, would load from gesture database
        # For now, create a default gesture
        gesture = SignGesture(
            id=f"gesture_{hashlib.md5(gloss.encode()).hexdigest()[:8]}",
            gloss=gloss,
            duration=1.5
        )

        self._gestures[gloss] = gesture
        return gesture

    def get_gestures(self, glosses: List[str]) -> List[SignGesture]:
        """Get multiple gestures."""
        return [self.load_gesture(g) for g in glosses]

    def preload_common_gestures(self, common_words: List[str]):
        """Preload frequently used gestures."""
        for word in common_words[:50]:  # Limit cache size
            self.load_gesture(word)


class BSLAvatarRenderer:
    """Real-time BSL avatar renderer."""

    def __init__(
        self,
        config: Optional[AvatarConfig] = None,
        translation_service_url: str = "http://localhost:8003"
    ):
        self.config = config or AvatarConfig()
        self.translation_url = translation_service_url
        self.gesture_library = GestureLibrary()
        self.state = AvatarState.IDLE
        self.metrics = RenderingMetrics()
        self._current_gesture: Optional[SignGesture] = None
        self._gesture_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers: List[Callable] = []
        self._rendering = False

    def subscribe(self, callback: Callable[[str, AvatarState], None]):
        """Subscribe to avatar state changes."""
        self._subscribers.append(callback)

    def _notify_subscribers(self, event: str, state: AvatarState):
        """Notify subscribers of state changes."""
        for callback in self._subscribers:
            try:
                callback(event, state)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")

    async def translate_to_gestures(
        self,
        text: str,
        session_id: Optional[str] = None
    ) -> List[SignGesture]:
        """Translate text to BSL gestures."""
        # In production, would call translation service
        # For now, split by words and create gestures
        words = text.split()
        gestures = []

        for word in words:
            gesture = self.gesture_library.load_gesture(word)
            gestures.append(gesture)

        return gestures

    async def queue_gesture(self, gesture: SignGesture) -> bool:
        """Queue a gesture for rendering."""
        try:
            self._gesture_queue.put_nowait(gesture)
            return True
        except asyncio.QueueFull:
            logger.warning("Gesture queue full, dropping gesture")
            self.metrics.dropped_frames += 1
            return False

    async def queue_text(self, text: str) -> int:
        """Queue text for gesture translation and rendering."""
        gestures = await self.translate_to_gestures(text)
        queued = 0

        for gesture in gestures:
            if await self.queue_gesture(gesture):
                queued += 1

        return queued

    async def start_rendering(self):
        """Start the rendering loop."""
        if self._rendering:
            return

        self._rendering = True
        self.state = AvatarState.SIGNING
        self._notify_subscribers("rendering_started", AvatarState.SIGNING)

        try:
            while self._rendering:
                gesture = await self._gesture_queue.get()

                start_time = datetime.now(timezone.utc)
                await self._render_gesture(gesture)
                end_time = datetime.now(timezone.utc)

                # Update metrics
                duration = (end_time - start_time).total_seconds()
                self.metrics.frames_rendered += 1
                self.metrics.total_render_time += duration
                self.metrics.avg_frame_time = (
                    self.metrics.total_render_time / self.metrics.frames_rendered
                )
                self.metrics.last_update = end_time

        except Exception as e:
            logger.error(f"Rendering error: {e}")
            self.state = AvatarState.ERROR

    async def _render_gesture(self, gesture: SignGesture):
        """Render a single gesture."""
        self._current_gesture = gesture

        # In production, would:
        # 1. Update avatar model with gesture data
        # 2. Animate transition between gestures
        # 3. Render frame to output stream
        # 4. Apply facial expressions and body language

        await asyncio.sleep(0.01)  # Simulate rendering time

    async def stop_rendering(self):
        """Stop the rendering loop."""
        self._rendering = False
        self.state = AvatarState.IDLE
        self._notify_subscribers("rendering_stopped", AvatarState.IDLE)

    def get_metrics(self) -> RenderingMetrics:
        """Get rendering metrics."""
        return self.metrics

    def get_state(self) -> AvatarState:
        """Get current avatar state."""
        return self.state

    def get_current_gesture(self) -> Optional[Dict[str, Any]]:
        """Get currently rendered gesture."""
        if self._current_gesture:
            return self._current_gesture.to_dict()
        return None


class BSLAvatarService:
    """Service for managing multiple BSL avatar instances."""

    def __init__(self, max_avatars: int = 10):
        self.max_avatars = max_avatars
        self._avatars: Dict[str, BSLAvatarRenderer] = {}
        self._active_sessions: Dict[str, str] = {}  # session_id -> avatar_id

    async def create_avatar(
        self,
        avatar_id: str,
        config: Optional[AvatarConfig] = None
    ) -> BSLAvatarRenderer:
        """Create a new avatar instance."""
        if len(self._avatars) >= self.max_avatars:
            raise Exception(f"Maximum avatars ({self.max_avatars}) reached")

        if avatar_id in self._avatars:
            raise Exception(f"Avatar {avatar_id} already exists")

        avatar = BSLAvatarRenderer(config=config)
        self._avatars[avatar_id] = avatar

        logger.info(f"Created avatar: {avatar_id}")
        return avatar

    async def remove_avatar(self, avatar_id: str) -> bool:
        """Remove an avatar instance."""
        if avatar_id not in self._avatars:
            return False

        avatar = self._avatars[avatar_id]
        await avatar.stop_rendering()

        # Remove from sessions
        sessions_to_remove = [
            session_id for session_id, av_id in self._active_sessions.items()
            if av_id == avatar_id
        ]
        for session_id in sessions_to_remove:
            del self._active_sessions[session_id]

        del self._avatars[avatar_id]
        logger.info(f"Removed avatar: {avatar_id}")
        return True

    def get_avatar(self, avatar_id: str) -> Optional[BSLAvatarRenderer]:
        """Get an avatar by ID."""
        return self._avatars.get(avatar_id)

    async def get_avatar_for_session(self, session_id: str) -> Optional[BSLAvatarRenderer]:
        """Get or create avatar for a session."""
        if session_id in self._active_sessions:
            avatar_id = self._active_sessions[session_id]
            return self._avatars.get(avatar_id)

        # Create new avatar for session
        avatar_id = f"avatar_{session_id}"
        try:
            avatar = await self.create_avatar(avatar_id)
            self._active_sessions[session_id] = avatar_id
            return avatar
        except Exception as e:
            logger.error(f"Failed to create avatar for session {session_id}: {e}")
            return None

    def list_avatars(self) -> List[Dict[str, Any]]:
        """List all avatars."""
        return [
            {
                "id": avatar_id,
                "state": avatar.get_state().value,
                "metrics": {
                    "frames_rendered": avatar.metrics.frames_rendered,
                    "avg_frame_time": avatar.metrics.avg_frame_time
                }
            }
            for avatar_id, avatar in self._avatars.items()
        ]

    async def sign_text(
        self,
        session_id: str,
        text: str
    ) -> Dict[str, Any]:
        """Sign text using session's avatar."""
        avatar = await self.get_avatar_for_session(session_id)
        if not avatar:
            return {
                "success": False,
                "error": "Could not get avatar for session"
            }

        # Queue gestures
        queued = await avatar.queue_text(text)

        # Ensure rendering is active
        if avatar.get_state() == AvatarState.IDLE:
            asyncio.create_task(avatar.start_rendering())

        return {
            "success": True,
            "avatar_id": self._active_sessions[session_id],
            "gestures_queued": queued
        }


# Global BSL avatar service instance
bsl_avatar_service = BSLAvatarService()


__all__ = [
    "AvatarState",
    "SignGesture",
    "AvatarConfig",
    "RenderingMetrics",
    "GestureLibrary",
    "BSLAvatarRenderer",
    "BSLAvatarService",
    "bsl_avatar_service"
]
