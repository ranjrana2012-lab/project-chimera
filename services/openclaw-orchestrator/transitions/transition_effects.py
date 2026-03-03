"""
Transition Effects - OpenClaw Orchestrator

Handles visual/audio transition effects between scenes (CUT, FADE, CROSSFADE).
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time

from core.scene_manager import SceneManager, SceneState

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """Types of scene transitions."""
    CUT = "cut"
    FADE = "fade"
    CROSSFADE = "crossfade"


class EffectState(Enum):
    """States of a transition effect."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TransitionEffectConfig:
    """
    Configuration for a transition effect.

    Attributes:
        source_scene_id: Scene transitioning from
        target_scene_id: Scene transitioning to
        transition_type: Type of transition (CUT, FADE, CROSSFADE)
        duration_seconds: Duration of transition in seconds
        metadata: Additional effect metadata
    """
    source_scene_id: str
    target_scene_id: str
    transition_type: TransitionType
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionEffect:
    """
    A transition effect between scenes.

    Manages the execution and state of a single transition.
    """

    def __init__(self, config: TransitionEffectConfig):
        """
        Initialize transition effect.

        Args:
            config: Effect configuration
        """
        self._config = config
        self._effect_id = f"te-{uuid.uuid4().hex[:8]}"
        self._state = EffectState.PENDING
        self._progress = 0.0
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._failed_at: Optional[datetime] = None
        self._cancelled_at: Optional[datetime] = None
        self._error_message: Optional[str] = None
        self._cancellation_reason: Optional[str] = None

        logger.info(
            f"Created {config.transition_type.value.upper()} transition effect "
            f"{self._effect_id} from {config.source_scene_id} to {config.target_scene_id} "
            f"({config.duration_seconds}s)"
        )

    @property
    def effect_id(self) -> str:
        """Get effect ID."""
        return self._effect_id

    @property
    def state(self) -> EffectState:
        """Get current state."""
        return self._state

    @property
    def transition_type(self) -> TransitionType:
        """Get transition type."""
        return self._config.transition_type

    @property
    def source_scene_id(self) -> str:
        """Get source scene ID."""
        return self._config.source_scene_id

    @property
    def target_scene_id(self) -> str:
        """Get target scene ID."""
        return self._config.target_scene_id

    @property
    def started_at(self) -> Optional[datetime]:
        """Get start timestamp."""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get completion timestamp."""
        return self._completed_at

    @property
    def failed_at(self) -> Optional[datetime]:
        """Get failure timestamp."""
        return self._failed_at

    @property
    def cancelled_at(self) -> Optional[datetime]:
        """Get cancellation timestamp."""
        return self._cancelled_at

    @property
    def error_message(self) -> Optional[str]:
        """Get error message."""
        return self._error_message

    @property
    def cancellation_reason(self) -> Optional[str]:
        """Get cancellation reason."""
        return self._cancellation_reason

    def get_duration(self) -> float:
        """Get effect duration in seconds."""
        return self._config.duration_seconds

    def get_progress(self) -> float:
        """Get effect progress (0-100)."""
        return self._progress

    def start(self) -> None:
        """Start effect execution."""
        if self._state != EffectState.PENDING:
            raise RuntimeError(f"Cannot start effect in state {self._state.value}")

        self._state = EffectState.RUNNING
        self._started_at = datetime.now(timezone.utc)
        self._progress = 0.0

        logger.info(f"Started transition effect {self._effect_id}")

    def update_progress(self, progress: float) -> None:
        """
        Update effect progress.

        Args:
            progress: Progress value (0-100)
        """
        if self._state != EffectState.RUNNING:
            return

        # Clamp progress between 0 and 100
        self._progress = max(0.0, min(100.0, progress))

        # Auto-complete when reaching 100%
        if self._progress >= 100.0:
            self.complete()

    def complete(self) -> None:
        """Mark effect as complete."""
        if self._state != EffectState.RUNNING:
            raise RuntimeError(f"Cannot complete effect in state {self._state.value}")

        self._state = EffectState.COMPLETE
        self._completed_at = datetime.now(timezone.utc)
        self._progress = 100.0

        logger.info(f"Completed transition effect {self._effect_id}")

    def fail(self, error_message: str) -> None:
        """
        Mark effect as failed.

        Args:
            error_message: Error description
        """
        self._state = EffectState.FAILED
        self._failed_at = datetime.now(timezone.utc)
        self._error_message = error_message

        logger.error(f"Failed transition effect {self._effect_id}: {error_message}")

    def cancel(self, reason: str) -> None:
        """
        Cancel effect execution.

        Args:
            reason: Cancellation reason
        """
        if self._state == EffectState.COMPLETE:
            raise RuntimeError("Cannot cancel completed effect")

        self._state = EffectState.CANCELLED
        self._cancelled_at = datetime.now(timezone.utc)
        self._cancellation_reason = reason

        logger.info(f"Cancelled transition effect {self._effect_id}: {reason}")

    def is_complete(self) -> bool:
        """Check if effect is complete."""
        return self._state == EffectState.COMPLETE

    def is_running(self) -> bool:
        """Check if effect is currently running."""
        return self._state == EffectState.RUNNING


class TransitionEffectExecutor:
    """
    Executor for transition effects.

    Manages concurrent effect execution with limits.
    """

    MAX_CONCURRENT_EFFECTS = 3

    def __init__(self):
        """Initialize executor."""
        self._active_effects: Dict[str, TransitionEffect] = {}
        self._completed_effects: Dict[str, TransitionEffect] = {}
        self._progress_callbacks: Dict[str, List[Callable]] = {}

        logger.info(
            f"TransitionEffectExecutor initialized "
            f"(max_concurrent={self.MAX_CONCURRENT_EFFECTS})"
        )

    def execute_transition(
        self,
        config: TransitionEffectConfig,
        source_manager: SceneManager,
        target_manager: SceneManager
    ) -> str:
        """
        Execute a transition effect.

        Args:
            config: Effect configuration
            source_manager: Source scene manager
            target_manager: Target scene manager

        Returns:
            Effect ID

        Raises:
            RuntimeError: If max concurrent effects reached
        """
        # Check concurrent limit
        if len(self._active_effects) >= self.MAX_CONCURRENT_EFFECTS:
            raise RuntimeError(
                f"Maximum concurrent effects ({self.MAX_CONCURRENT_EFFECTS}) reached"
            )

        # Create effect
        effect = TransitionEffect(config)

        # Validate scenes exist and are in appropriate state
        if source_manager.scene_id != config.source_scene_id:
            raise ValueError(f"Source scene ID mismatch")

        if target_manager.scene_id != config.target_scene_id:
            raise ValueError(f"Target scene ID mismatch")

        # Add to active effects
        self._active_effects[effect.effect_id] = effect

        # Start effect execution
        self._execute_effect(effect, source_manager, target_manager)

        return effect.effect_id

    def _execute_effect(
        self,
        effect: TransitionEffect,
        source_manager: SceneManager,
        target_manager: SceneManager
    ) -> None:
        """
        Execute effect asynchronously.

        Args:
            effect: Effect to execute
            source_manager: Source scene manager
            target_manager: Target scene manager
        """
        try:
            effect.start()

            # Execute based on transition type
            if effect.transition_type == TransitionType.CUT:
                self._execute_cut(effect, source_manager, target_manager)
            elif effect.transition_type == TransitionType.FADE:
                self._execute_fade(effect, source_manager, target_manager)
            elif effect.transition_type == TransitionType.CROSSFADE:
                self._execute_crossfade(effect, source_manager, target_manager)

        except Exception as e:
            logger.error(f"Error executing effect {effect.effect_id}: {e}")
            if effect.state == EffectState.RUNNING:
                effect.fail(str(e))

        finally:
            # Move to completed if not running
            if effect.state != EffectState.RUNNING:
                self._move_to_completed(effect)

    def _execute_cut(
        self,
        effect: TransitionEffect,
        source_manager: SceneManager,
        target_manager: SceneManager
    ) -> None:
        """
        Execute CUT transition (immediate).

        Args:
            effect: Effect to execute
            source_manager: Source scene manager
            target_manager: Target scene manager
        """
        logger.info(f"Executing CUT transition {effect.effect_id}")

        # CUT is immediate - complete right away
        effect.complete()

        # Notify scene managers
        self._notify_scene_changed(source_manager, target_manager)

    def _execute_fade(
        self,
        effect: TransitionEffect,
        source_manager: SceneManager,
        target_manager: SceneManager
    ) -> None:
        """
        Execute FADE transition (async).

        Args:
            effect: Effect to execute
            source_manager: Source scene manager
            target_manager: Target scene manager
        """
        logger.info(f"Executing FADE transition {effect.effect_id}")

        # Start async fade execution
        def fade_task():
            duration = effect.get_duration()
            steps = 10
            step_duration = duration / steps

            try:
                for i in range(steps + 1):
                    if effect.state != EffectState.RUNNING:
                        return

                    progress = (i / steps) * 100
                    effect.update_progress(progress)

                    if i < steps:
                        time.sleep(step_duration)

                # Fade complete
                if effect.state == EffectState.RUNNING:
                    effect.complete()
                    self._notify_scene_changed(source_manager, target_manager)

            except Exception as e:
                logger.error(f"Error in fade task: {e}")
                raise

        # Run in background thread
        import threading
        thread = threading.Thread(target=fade_task, daemon=True)
        thread.start()

    def _execute_crossfade(
        self,
        effect: TransitionEffect,
        source_manager: SceneManager,
        target_manager: SceneManager
    ) -> None:
        """
        Execute CROSSFADE transition (async).

        Args:
            effect: Effect to execute
            source_manager: Source scene manager
            target_manager: Target scene manager
        """
        logger.info(f"Executing CROSSFADE transition {effect.effect_id}")

        # Start async crossfade execution
        def crossfade_task():
            duration = effect.get_duration()
            steps = 20  # More steps for smoother crossfade
            step_duration = duration / steps

            try:
                # Phase 1: Fade out source (first half)
                for i in range(steps // 2):
                    if effect.state != EffectState.RUNNING:
                        return

                    progress = (i / (steps // 2)) * 50
                    effect.update_progress(progress)

                    time.sleep(step_duration)

                # Phase 2: Fade in target (second half)
                for i in range(steps // 2, steps + 1):
                    if effect.state != EffectState.RUNNING:
                        return

                    progress = 50 + ((i - (steps // 2)) / (steps // 2)) * 50
                    effect.update_progress(progress)

                    if i < steps:
                        time.sleep(step_duration)

                # Crossfade complete
                if effect.state == EffectState.RUNNING:
                    effect.complete()
                    self._notify_scene_changed(source_manager, target_manager)

            except Exception as e:
                logger.error(f"Error in crossfade task: {e}")
                raise

        # Run in background thread
        import threading
        thread = threading.Thread(target=crossfade_task, daemon=True)
        thread.start()

    def _notify_scene_changed(
        self,
        source_manager: SceneManager,
        target_manager: SceneManager
    ) -> None:
        """
        Notify scene managers of transition completion.

        Args:
            source_manager: Source scene manager
            target_manager: Target scene manager
        """
        # Source scene completes
        if source_manager.state == SceneState.ACTIVE:
            try:
                source_manager.complete("Scene transition completed")
            except Exception as e:
                logger.warning(f"Failed to complete source scene: {e}")

        # Target scene activates (if not already)
        if target_manager.state != SceneState.ACTIVE:
            try:
                target_manager.activate()
            except Exception as e:
                logger.warning(f"Failed to activate target scene: {e}")

    def _move_to_completed(self, effect: TransitionEffect) -> None:
        """
        Move effect from active to completed.

        Args:
            effect: Effect to move
        """
        if effect.effect_id in self._active_effects:
            del self._active_effects[effect.effect_id]

        self._completed_effects[effect.effect_id] = effect

    def get_effect(self, effect_id: str) -> Optional[TransitionEffect]:
        """
        Get effect by ID.

        Args:
            effect_id: Effect ID

        Returns:
            TransitionEffect or None if not found
        """
        # Check active first
        if effect_id in self._active_effects:
            return self._active_effects[effect_id]

        # Check completed
        return self._completed_effects.get(effect_id)

    def get_active_effects(self) -> List[TransitionEffect]:
        """
        Get all active effects.

        Returns:
            List of running effects
        """
        return [
            effect for effect in self._active_effects.values()
            if effect.state == EffectState.RUNNING
        ]

    def get_effect_status(self, effect_id: str) -> Optional[Dict[str, Any]]:
        """
        Get effect status.

        Args:
            effect_id: Effect ID

        Returns:
            Status dict or None if not found
        """
        effect = self.get_effect(effect_id)
        if not effect:
            return None

        return {
            "effect_id": effect.effect_id,
            "transition_type": effect.transition_type.value,
            "source_scene_id": effect.source_scene_id,
            "target_scene_id": effect.target_scene_id,
            "state": effect.state.value,
            "progress": effect.get_progress(),
            "duration": effect.get_duration(),
            "started_at": effect.started_at.isoformat() if effect.started_at else None,
            "completed_at": effect.completed_at.isoformat() if effect.completed_at else None
        }

    def cancel_effect(self, effect_id: str, reason: str) -> bool:
        """
        Cancel an active effect.

        Args:
            effect_id: Effect ID
            reason: Cancellation reason

        Returns:
            True if cancelled
        """
        effect = self._active_effects.get(effect_id)
        if not effect:
            return False

        try:
            effect.cancel(reason)
            self._move_to_completed(effect)
            return True
        except Exception as e:
            logger.error(f"Error cancelling effect {effect_id}: {e}")
            return False

    def update_progress(self, effect_id: str, progress: float) -> None:
        """
        Update effect progress.

        Args:
            effect_id: Effect ID
            progress: Progress value (0-100)
        """
        effect = self._active_effects.get(effect_id)
        if effect:
            effect.update_progress(progress)

            # Trigger progress callbacks
            for callback in self._progress_callbacks.get(effect_id, []):
                try:
                    callback(progress)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

    def cleanup_old_effects(self, max_age_seconds: float = 3600) -> int:
        """
        Remove old completed effects.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of effects cleaned up
        """
        now = datetime.now(timezone.utc)
        cleaned = 0

        effects_to_remove = []

        for effect_id, effect in self._completed_effects.items():
            # Only cleanup completed effects
            if effect.state != EffectState.COMPLETE:
                continue

            # Check age
            if effect.completed_at:
                age = (now - effect.completed_at).total_seconds()
                if age > max_age_seconds:
                    effects_to_remove.append(effect_id)

        for effect_id in effects_to_remove:
            del self._completed_effects[effect_id]
            cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old transition effects")

        return cleaned

    def register_progress_callback(
        self,
        effect_id: str,
        callback: Callable[[float], None]
    ) -> None:
        """
        Register progress callback for effect.

        Args:
            effect_id: Effect ID
            callback: Function to call with progress updates
        """
        if effect_id not in self._progress_callbacks:
            self._progress_callbacks[effect_id] = []

        self._progress_callbacks[effect_id].append(callback)


# Convenience functions

def create_transition_effect(
    source_scene_id: str,
    target_scene_id: str,
    transition_type: TransitionType,
    duration_seconds: float = 3.0
) -> TransitionEffect:
    """
    Create a transition effect.

    Args:
        source_scene_id: Scene transitioning from
        target_scene_id: Scene transitioning to
        transition_type: Type of transition
        duration_seconds: Duration in seconds

    Returns:
        Configured TransitionEffect
    """
    config = TransitionEffectConfig(
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_id,
        transition_type=transition_type,
        duration_seconds=duration_seconds
    )

    return TransitionEffect(config)


def get_executor() -> TransitionEffectExecutor:
    """Get global transition effect executor."""
    # Could be made into a singleton if needed
    return TransitionEffectExecutor()
