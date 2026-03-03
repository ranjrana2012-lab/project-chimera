"""
Multi-Scene Orchestrator - OpenClaw Orchestrator

Manages multiple concurrent scenes with isolation and coordination.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .scene_manager import (
    SceneManager,
    SceneState,
    SceneConfig
)
from persistence.scene_store import SceneStore


logger = logging.getLogger(__name__)


class SceneConflictError(Exception):
    """Raised when scenes conflict with each other."""
    pass


class SceneLimitError(Exception):
    """Raised when maximum concurrent scenes reached."""
    pass


@dataclass
class SceneSlot:
    """
    A slot for a scene in the orchestrator.

    Attributes:
        scene_id: Scene identifier
        manager: SceneManager instance
        priority: Scene priority (0-100)
        created_at: When scene was created
        activated_at: When scene became active
    """
    scene_id: str
    manager: SceneManager
    priority: int
    created_at: datetime
    activated_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Check if scene is in an active state."""
        return self.manager.state.is_active


class MultiSceneOrchestrator:
    """
    Manages multiple concurrent scenes.

    Features:
        - Max 5 concurrent active scenes
        - Scene priority management
        - Resource isolation
        - Conflict detection
        - Graceful scene limits

    Usage:
        orchestrator = MultiSceneOrchestrator(max_scenes=5)
        orchestrator.add_scene(manager1)
        orchestrator.add_scene(manager2)
        active_scenes = orchestrator.get_active_scenes()
    """

    DEFAULT_MAX_SCENES = 5

    def __init__(
        self,
        max_scenes: int = DEFAULT_MAX_SCENES,
        scene_store: Optional[SceneStore] = None
    ):
        """
        Initialize multi-scene orchestrator.

        Args:
            max_scenes: Maximum concurrent active scenes
            scene_store: Optional SceneStore for persistence
        """
        self._max_scenes = max_scenes
        self._scene_store = scene_store
        self._scenes: Dict[str, SceneSlot] = {}

        logger.info(f"MultiSceneOrchestrator initialized (max_scenes={max_scenes})")

    @property
    def scene_count(self) -> int:
        """Get current number of scenes."""
        return len(self._scenes)

    @property
    def active_scene_count(self) -> int:
        """Get number of active scenes."""
        return sum(1 for slot in self._scenes.values() if slot.is_active)

    def add_scene(
        self,
        manager: SceneManager,
        priority: int = 50
    ) -> bool:
        """
        Add a scene to the orchestrator.

        Args:
            manager: SceneManager to add
            priority: Scene priority (0-100, higher is more important)

        Returns:
            True if scene added successfully

        Raises:
            SceneLimitError: If max concurrent scenes reached
            SceneConflictError: If scene conflicts with existing scene
        """
        scene_id = manager.scene_id

        # Check for duplicate scene ID
        if scene_id in self._scenes:
            raise SceneConflictError(
                f"Scene {scene_id} already exists in orchestrator"
            )

        # Check active scene limit
        if manager.state.is_active:
            active_count = self.active_scene_count
            if active_count >= self._max_scenes:
                # Try to make room by checking for lower priority scenes
                if not self._can_make_room(priority):
                    raise SceneLimitError(
                        f"Maximum concurrent scenes ({self._max_scenes}) reached. "
                        f"Cannot add {scene_id} with priority {priority}"
                    )

        # Create scene slot
        slot = SceneSlot(
            scene_id=scene_id,
            manager=manager,
            priority=priority,
            created_at=datetime.utcnow()
        )

        self._scenes[scene_id] = slot

        # Save to store if available
        if self._scene_store:
            self._scene_store.save_state(manager)

        logger.info(
            f"Added scene {scene_id} (priority={priority}, "
            f"total={self.scene_count}, active={self.active_scene_count})"
        )

        return True

    def remove_scene(self, scene_id: str) -> bool:
        """
        Remove a scene from the orchestrator.

        Args:
            scene_id: Scene identifier

        Returns:
            True if scene was removed
        """
        if scene_id not in self._scenes:
            logger.warning(f"Scene {scene_id} not found in orchestrator")
            return False

        # Check if scene is active
        slot = self._scenes[scene_id]
        if slot.is_active:
            logger.warning(
                f"Removing active scene {scene_id} in state {slot.manager.state.value}"
            )

        del self._scenes[scene_id]

        # Delete from store if available
        if self._scene_store:
            self._scene_store.delete_scene(scene_id)

        logger.info(
            f"Removed scene {scene_id} "
            f"(total={self.scene_count}, active={self.active_scene_count})"
        )

        return True

    def get_scene(self, scene_id: str) -> Optional[SceneManager]:
        """
        Get a scene manager by ID.

        Args:
            scene_id: Scene identifier

        Returns:
            SceneManager or None if not found
        """
        slot = self._scenes.get(scene_id)
        return slot.manager if slot else None

    def get_active_scenes(self) -> List[SceneManager]:
        """
        Get all active scene managers.

        Returns:
            List of active SceneManagers
        """
        return [
            slot.manager for slot in self._scenes.values()
            if slot.is_active
        ]

    def get_scenes_by_priority(self) -> List[SceneManager]:
        """
        Get all scenes sorted by priority (highest first).

        Returns:
            List of SceneManagers sorted by priority
        """
        slots = sorted(
            self._scenes.values(),
            key=lambda s: s.priority,
            reverse=True
        )
        return [slot.manager for slot in slots]

    def get_scene_states(self) -> Dict[str, str]:
        """
        Get state of all scenes.

        Returns:
            Dict mapping scene_id -> state
        """
        return {
            scene_id: slot.manager.state.value
            for scene_id, slot in self._scenes.items()
        }

    def can_add_scene(self, priority: int = 50) -> bool:
        """
        Check if a scene can be added.

        Args:
            priority: Proposed scene priority

        Returns:
            True if scene can be added
        """
        # Check for active scene limit
        active_count = self.active_scene_count
        if active_count < self._max_scenes:
            return True

        # At max capacity - check if we can make room
        return self._can_make_room(priority)

    def make_room_for_scene(self, priority: int) -> List[str]:
        """
        Make room for a new scene by pausing lower priority scenes.

        Args:
            priority: Priority of new scene

        Returns:
            List of scene IDs that were paused

        Raises:
            SceneLimitError: If no scenes can be paused
        """
        if not self._can_make_room(priority):
            raise SceneLimitError(
                f"Cannot make room for scene with priority {priority}. "
                f"All existing scenes have higher or equal priority."
            )

        paused_scenes = []

        # Find and pause lower priority active scenes
        active_scenes = [
            (scene_id, slot)
            for scene_id, slot in self._scenes.items()
            if slot.is_active and slot.priority < priority
        ]

        # Sort by priority (lowest first) to pause least important first
        active_scenes.sort(key=lambda x: x[1].priority)

        for scene_id, slot in active_scenes:
            if self.active_scene_count < self._max_scenes:
                break

            # Pause the scene
            try:
                if slot.manager.state == SceneState.ACTIVE:
                    slot.manager.pause("Making room for higher priority scene")
                    paused_scenes.append(scene_id)
                    logger.info(f"Paused scene {scene_id} to make room")
            except Exception as e:
                logger.warning(f"Failed to pause scene {scene_id}: {e}")

        return paused_scenes

    def pause_scene(self, scene_id: str, reason: str = "") -> bool:
        """
        Pause a scene.

        Args:
            scene_id: Scene identifier
            reason: Optional reason for pausing

        Returns:
            True if scene was paused
        """
        manager = self.get_scene(scene_id)
        if not manager:
            return False

        if manager.state != SceneState.ACTIVE:
            logger.warning(
                f"Cannot pause scene {scene_id}: "
                f"not in ACTIVE state (currently {manager.state.value})"
            )
            return False

        try:
            manager.pause(reason)
            return True
        except Exception as e:
            logger.error(f"Failed to pause scene {scene_id}: {e}")
            return False

    def resume_scene(self, scene_id: str) -> bool:
        """
        Resume a paused scene.

        Args:
            scene_id: Scene identifier

        Returns:
            True if scene was resumed
        """
        manager = self.get_scene(scene_id)
        if not manager:
            return False

        if manager.state != SceneState.PAUSED:
            logger.warning(
                f"Cannot resume scene {scene_id}: "
                f"not in PAUSED state (currently {manager.state.value})"
            )
            return False

        try:
            manager.resume()
            return True
        except Exception as e:
            logger.error(f"Failed to resume scene {scene_id}: {e}")
            return False

    def complete_scene(self, scene_id: str, reason: str = "manual") -> bool:
        """
        Complete a scene.

        Args:
            scene_id: Scene identifier
            reason: Reason for completion

        Returns:
            True if scene was completed
        """
        manager = self.get_scene(scene_id)
        if not manager:
            return False

        try:
            manager.complete(reason)
            # Remove from orchestrator after completion
            self.remove_scene(scene_id)
            return True
        except Exception as e:
            logger.error(f"Failed to complete scene {scene_id}: {e}")
            return False

    def get_scene_status(self) -> Dict[str, Any]:
        """
        Get overall orchestrator status.

        Returns:
            Status dict with scene counts and limits
        """
        return {
            "total_scenes": self.scene_count,
            "active_scenes": self.active_scene_count,
            "max_scenes": self._max_scenes,
            "available_slots": self._max_scenes - self.active_scene_count,
            "scenes": self.get_scene_states()
        }

    def cleanup_inactive_scenes(self, max_age_hours: int = 24) -> int:
        """
        Remove inactive/completed scenes.

        Args:
            max_age_hours: Maximum age in hours for inactive scenes

        Returns:
            Number of scenes cleaned up
        """
        cleaned = 0
        now = datetime.utcnow()
        scenes_to_remove = []

        for scene_id, slot in self._scenes.items():
            # Skip active scenes
            if slot.is_active:
                continue

            # Check age
            age = (now - slot.created_at).total_seconds() / 3600
            if age > max_age_hours:
                scenes_to_remove.append(scene_id)

        for scene_id in scenes_to_remove:
            if self.remove_scene(scene_id):
                cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} inactive scenes")

        return cleaned

    def _can_make_room(self, priority: int) -> bool:
        """
        Check if room can be made for a scene with given priority.

        Args:
            priority: Proposed scene priority

        Returns:
            True if a scene can be paused to make room
        """
        # Count lower priority active scenes
        lower_priority_active = sum(
            1 for slot in self._scenes.values()
            if slot.is_active and slot.priority < priority
        )

        return lower_priority_active > 0

    def enforce_scene_limit(self) -> List[str]:
        """
        Enforce maximum concurrent scene limit.

        Pauses lowest priority scenes if over limit.

        Returns:
            List of scene IDs that were paused
        """
        paused = []

        while self.active_scene_count > self._max_scenes:
            # Find lowest priority active scene
            lowest_priority_scene = None
            lowest_priority = 999

            for scene_id, slot in self._scenes.items():
                if slot.is_active and slot.priority < lowest_priority:
                    lowest_priority = slot.priority
                    lowest_priority_scene = scene_id

            if lowest_priority_scene:
                if self.pause_scene(lowest_priority_scene, "Enforcing scene limit"):
                    paused.append(lowest_priority_scene)
            else:
                # No scene to pause
                break

        return paused


# Convenience functions

def create_orchestrator(
    max_scenes: int = 5,
    scene_store: Optional[SceneStore] = None
) -> MultiSceneOrchestrator:
    """
    Create a multi-scene orchestrator.

    Args:
        max_scenes: Maximum concurrent scenes
        scene_store: Optional SceneStore

    Returns:
        MultiSceneOrchestrator instance
    """
    return MultiSceneOrchestrator(max_scenes, scene_store)
