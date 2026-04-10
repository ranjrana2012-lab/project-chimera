"""
Scene Recovery - OpenClaw Orchestrator

Handles recovery of scenes after orchestrator restart or crash.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timezone

from .scene_manager import (
    SceneManager,
    SceneState,
    SceneConfig,
    SceneStateError
)
from persistence.scene_store import SceneStore


logger = logging.getLogger(__name__)


class SceneRecoveryError(Exception):
    """Base exception for scene recovery errors."""
    pass


class RecoveryResult:
    """
    Result of scene recovery attempt.

    Attributes:
        scene_id: Scene identifier
        success: Whether recovery succeeded
        state: Scene state after recovery
        error: Error message if failed
        recovered_at: Timestamp of recovery
    """

    def __init__(
        self,
        scene_id: str,
        success: bool,
        state: SceneState = None,
        error: str = None
    ):
        self.scene_id = scene_id
        self.success = success
        self.state = state
        self.error = error
        self.recovered_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        if self.success:
            return f"RecoveryResult({self.scene_id}: {self.state.value})"
        else:
            return f"RecoveryResult({self.scene_id}: FAILED - {self.error})"


class SceneRecoveryManager:
    """
    Manages scene recovery after orchestrator restart.

    Features:
        - Discover scenes from Redis
        - Restore scene state
        - Resume active scenes
        - Handle recovery failures
        - Recovery callbacks

    Usage:
        recovery_mgr = SceneRecoveryManager(scene_store)
        results = recovery_mgr.recover_all_scenes()
        for result in results:
            if result.success:
                logger.info(f"Recovered {result.scene_id}")
    """

    def __init__(
        self,
        scene_store: SceneStore,
        max_recovery_attempts: int = 3
    ):
        """
        Initialize recovery manager.

        Args:
            scene_store: SceneStore for loading saved scenes
            max_recovery_attempts: Max retry attempts per scene
        """
        self._scene_store = scene_store
        self._max_recovery_attempts = max_recovery_attempts
        self._recovery_callbacks: List[Callable[[RecoveryResult], None]] = []

        logger.info("SceneRecoveryManager initialized")

    def register_callback(self, callback: Callable[[RecoveryResult], None]) -> None:
        """
        Register callback for recovery results.

        Args:
            callback: Function called with RecoveryResult
        """
        self._recovery_callbacks.append(callback)

    def discover_scenes(self) -> List[str]:
        """
        Discover all scenes in Redis.

        Returns:
            List of scene IDs
        """
        scene_ids = self._scene_store.list_scenes()
        logger.info(f"Discovered {len(scene_ids)} scenes in Redis")
        return scene_ids

    def recover_scene(self, scene_id: str) -> RecoveryResult:
        """
        Recover a single scene from Redis.

        Args:
            scene_id: Scene identifier

        Returns:
            RecoveryResult with outcome
        """
        logger.info(f"Attempting to recover scene: {scene_id}")

        # Check if scene exists
        state_data = self._scene_store.load_state(scene_id)
        if state_data is None:
            result = RecoveryResult(
                scene_id,
                success=False,
                error="Scene not found in Redis"
            )
            self._notify_callbacks(result)
            return result

        # Determine if scene is recoverable
        state_str = state_data.get("state", "idle")
        try:
            state = SceneState(state_str)
        except ValueError:
            result = RecoveryResult(
                scene_id,
                success=False,
                error=f"Invalid state: {state_str}"
            )
            self._notify_callbacks(result)
            return result

        # Check if scene is in a recoverable state
        if state == SceneState.COMPLETED:
            logger.info(f"Scene {scene_id} is completed, skipping recovery")
            result = RecoveryResult(
                scene_id,
                success=True,
                state=state
            )
            self._notify_callbacks(result)
            return result

        # Restore the scene
        for attempt in range(self._max_recovery_attempts):
            try:
                manager = self._scene_store.restore_scene(scene_id)

                if manager is None:
                    raise SceneRecoveryError("Failed to restore scene from Redis")

                # Validate restored scene
                self._validate_restored_scene(manager)

                logger.info(
                    f"Scene {scene_id} recovered successfully "
                    f"(state: {state.value})"
                )

                result = RecoveryResult(
                    scene_id,
                    success=True,
                    state=manager.state
                )
                self._notify_callbacks(result)
                return result

            except Exception as e:
                if attempt < self._max_recovery_attempts - 1:
                    logger.warning(
                        f"Recovery attempt {attempt + 1} failed for {scene_id}: {e}. "
                        f"Retrying..."
                    )
                else:
                    logger.error(
                        f"Failed to recover scene {scene_id} after "
                        f"{self._max_recovery_attempts} attempts: {e}"
                    )
                    result = RecoveryResult(
                        scene_id,
                        success=False,
                        error=str(e)
                    )
                    self._notify_callbacks(result)
                    return result

    def recover_all_scenes(self) -> List[RecoveryResult]:
        """
        Recover all scenes from Redis.

        Returns:
            List of RecoveryResults for all scenes
        """
        logger.info("Starting scene recovery for all scenes")

        scene_ids = self.discover_scenes()
        if not scene_ids:
            logger.info("No scenes to recover")
            return []

        results = []
        for scene_id in scene_ids:
            result = self.recover_scene(scene_id)
            results.append(result)

        # Summary
        success_count = sum(1 for r in results if r.success)
        logger.info(
            f"Recovery complete: {success_count}/{len(results)} scenes recovered"
        )

        return results

    def recover_active_scenes(self) -> Dict[str, SceneManager]:
        """
        Recover only active scenes (ACTIVE, PAUSED, TRANSITION).

        Returns:
            Dict mapping scene_id -> SceneManager
        """
        logger.info("Recovering active scenes only")

        scene_ids = self.discover_scenes()
        active_managers = {}

        for scene_id in scene_ids:
            state_data = self._scene_store.load_state(scene_id)
            if state_data is None:
                continue

            state_str = state_data.get("state", "")
            try:
                state = SceneState(state_str)
            except ValueError:
                continue

            # Only recover active scenes
            if state.is_active:
                manager = self._scene_store.restore_scene(scene_id)
                if manager is not None:
                    active_managers[scene_id] = manager
                    logger.info(f"Recovered active scene: {scene_id}")

        logger.info(f"Recovered {len(active_managers)} active scenes")
        return active_managers

    def cleanup_stale_scenes(self, max_age_hours: int = 24) -> int:
        """
        Clean up stale scenes from Redis.

        Args:
            max_age_hours: Maximum age in hours for completed/error scenes

        Returns:
            Number of scenes cleaned up
        """
        logger.info(f"Cleaning up scenes older than {max_age_hours} hours")

        scene_ids = self.discover_scenes()
        cleaned_count = 0

        for scene_id in scene_ids:
            state_data = self._scene_store.load_state(scene_id)
            if state_data is None:
                continue

            # Check state - only clean completed/error scenes
            state_str = state_data.get("state", "")
            if state_str not in ("completed", "error"):
                continue

            # Check updated_at timestamp
            updated_at_str = state_data.get("updated_at", "")
            if not updated_at_str:
                continue

            try:
                updated_at = datetime.fromisoformat(updated_at_str)
                age_hours = (datetime.now(timezone.utc) - updated_at).total_seconds() / 3600

                if age_hours > max_age_hours:
                    if self._scene_store.delete_scene(scene_id):
                        cleaned_count += 1
                        logger.info(f"Cleaned up stale scene: {scene_id}")

            except Exception as e:
                logger.warning(f"Error checking scene {scene_id} age: {e}")

        logger.info(f"Cleaned up {cleaned_count} stale scenes")
        return cleaned_count

    def _validate_restored_scene(self, manager: SceneManager) -> None:
        """
        Validate a restored scene.

        Args:
            manager: Restored SceneManager

        Raises:
            SceneRecoveryError: If validation fails
        """
        # Check basic properties
        if not manager.scene_id:
            raise SceneRecoveryError("Scene has no ID")

        if not manager.config.name:
            raise SceneRecoveryError("Scene has no name")

        # Check state is valid
        if manager.state == SceneState.IDLE:
            # Idle scenes shouldn't be persisted
            logger.warning(f"Scene {manager.scene_id} is in IDLE state, may be corrupted")

        # Validate config
        try:
            manager._validate_config()
        except SceneStateError as e:
            raise SceneRecoveryError(f"Invalid configuration: {e}")

        logger.debug(f"Scene {manager.scene_id} validation passed")

    def _notify_callbacks(self, result: RecoveryResult) -> None:
        """Notify all registered callbacks of recovery result."""
        for callback in self._recovery_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Recovery callback error: {e}")


# Convenience functions

def recover_scenes_on_startup(
    scene_store: SceneStore,
    recover_active_only: bool = True
) -> List[RecoveryResult]:
    """
    Recover scenes on orchestrator startup.

    Args:
        scene_store: SceneStore instance
        recover_active_only: Only recover active scenes

    Returns:
        List of RecoveryResults
    """
    recovery_mgr = SceneRecoveryManager(scene_store)

    if recover_active_only:
        # Recover and return active scene managers
        active_managers = recovery_mgr.recover_active_scenes()
        # Convert managers to results
        results = [
            RecoveryResult(scene_id, True, manager.state)
            for scene_id, manager in active_managers.items()
        ]
        return results
    else:
        # Recover all scenes
        return recovery_mgr.recover_all_scenes()


def get_recovery_summary(results: List[RecoveryResult]) -> Dict[str, Any]:
    """
    Get summary of recovery results.

    Args:
        results: List of RecoveryResults

    Returns:
        Summary dict with counts and details
    """
    total = len(results)
    success_count = sum(1 for r in results if r.success)
    failed_count = total - success_count

    # Group by state
    state_counts = {}
    for result in results:
        if result.success and result.state:
            state = result.state.value
            state_counts[state] = state_counts.get(state, 0) + 1

    return {
        "total": total,
        "success": success_count,
        "failed": failed_count,
        "success_rate": success_count / total if total > 0 else 0,
        "state_counts": state_counts,
        "failed_scenes": [
            r.scene_id for r in results if not r.success
        ]
    }
