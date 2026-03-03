"""
Time-based Transition Triggers - OpenClaw Orchestrator

Provides scheduled, duration-based, and interval transition triggers.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

from core.scene_manager import SceneManager


logger = logging.getLogger(__name__)


class TimeTriggerType(Enum):
    """Types of time-based triggers."""
    SCHEDULED = "scheduled"
    DURATION = "duration"
    INTERVAL = "interval"


class TransitionType(Enum):
    """Types of scene transitions."""
    CUT = "cut"
    FADE = "fade"
    CROSSFADE = "crossfade"


class TriggerState(Enum):
    """States of a trigger."""
    ENABLED = "enabled"
    ARMED = "armed"
    TRIGGERED = "triggered"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


@dataclass
class TimeTriggerConfig:
    """
    Configuration for a time-based trigger.

    Attributes:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        transition_type: Type of transition
        priority: Trigger priority (0-100, higher is more important)
        enabled: Whether trigger is active
        scheduled_time: For SCHEDULED triggers, when to fire
        duration_seconds: For DURATION triggers, seconds after activation
        interval_seconds: For INTERVAL triggers, seconds between fires
        target_scene_sequence: For INTERVAL triggers, list of scenes to cycle
        metadata: Additional trigger metadata
    """
    trigger_id: str
    source_scene_id: str
    target_scene_id: str
    transition_type: TransitionType
    priority: int = 50
    enabled: bool = True
    scheduled_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    interval_seconds: Optional[int] = None
    target_scene_sequence: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TimeTrigger:
    """
    A time-based transition trigger.

    Can trigger based on:
    - Scheduled time (specific timestamp)
    - Duration (time since scene activation)
    - Interval (recurring at fixed periods)
    """

    def __init__(self, config: TimeTriggerConfig):
        """
        Initialize time trigger.

        Args:
            config: Trigger configuration
        """
        self._config = config
        self._state = TriggerState.ENABLED if config.enabled else TriggerState.CANCELLED
        self._trigger_type = self._determine_type()
        self._armed_at: Optional[datetime] = None
        self._triggered_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._sequence_index = 0

        logger.info(
            f"Created {self._trigger_type.value} trigger {config.trigger_id} "
            f"for scene {config.source_scene_id}"
        )

    def _determine_type(self) -> TimeTriggerType:
        """Determine trigger type from configuration."""
        if self._config.scheduled_time is not None:
            return TimeTriggerType.SCHEDULED
        elif self._config.duration_seconds is not None:
            return TimeTriggerType.DURATION
        elif self._config.interval_seconds is not None:
            return TimeTriggerType.INTERVAL
        else:
            # Default to scheduled if no time field specified
            return TimeTriggerType.SCHEDULED

    @property
    def trigger_id(self) -> str:
        """Get trigger ID."""
        return self._config.trigger_id

    @property
    def trigger_type(self) -> TimeTriggerType:
        """Get trigger type."""
        return self._trigger_type

    @property
    def state(self) -> TriggerState:
        """Get current state."""
        return self._state

    @property
    def source_scene_id(self) -> str:
        """Get source scene ID."""
        return self._config.source_scene_id

    @property
    def target_scene_id(self) -> str:
        """Get target scene ID (considering sequence)."""
        if self._trigger_type == TimeTriggerType.INTERVAL and self._config.target_scene_sequence:
            sequence = self._config.target_scene_sequence
            return sequence[self._sequence_index % len(sequence)]
        return self._config.target_scene_id

    @property
    def transition_type(self) -> TransitionType:
        """Get transition type."""
        return self._config.transition_type

    @property
    def priority(self) -> int:
        """Get trigger priority."""
        return self._config.priority

    @property
    def scheduled_time(self) -> Optional[datetime]:
        """Get scheduled time (for SCHEDULED triggers)."""
        return self._config.scheduled_time

    @property
    def duration_seconds(self) -> Optional[int]:
        """Get duration seconds (for DURATION triggers)."""
        return self._config.duration_seconds

    @property
    def interval_seconds(self) -> Optional[int]:
        """Get interval seconds (for INTERVAL triggers)."""
        return self._config.interval_seconds

    @property
    def target_scene_sequence(self) -> Optional[List[str]]:
        """Get target scene sequence (for INTERVAL triggers)."""
        return self._config.target_scene_sequence

    @property
    def armed_at(self) -> Optional[datetime]:
        """Get armed timestamp."""
        return self._armed_at

    @property
    def triggered_at(self) -> Optional[datetime]:
        """Get triggered timestamp."""
        return self._triggered_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get completed timestamp."""
        return self._completed_at

    def evaluate(self, scene_manager: Optional[SceneManager] = None) -> bool:
        """
        Evaluate if trigger is ready to fire.

        Args:
            scene_manager: Optional scene manager for duration triggers

        Returns:
            True if trigger should fire
        """
        if self._state not in (TriggerState.ENABLED, TriggerState.ARMED):
            return False

        if self._trigger_type == TimeTriggerType.SCHEDULED:
            return self._evaluate_scheduled()
        elif self._trigger_type == TimeTriggerType.DURATION:
            return self._evaluate_duration(scene_manager)
        elif self._trigger_type == TimeTriggerType.INTERVAL:
            return self._evaluate_interval(scene_manager)

        return False

    def _evaluate_scheduled(self) -> bool:
        """Evaluate scheduled time trigger."""
        if self._config.scheduled_time is None:
            return False

        now = datetime.now(timezone.utc)
        if now >= self._config.scheduled_time:
            self.arm()
            return True

        return False

    def _evaluate_duration(self, scene_manager: Optional[SceneManager]) -> bool:
        """Evaluate duration-based trigger."""
        if scene_manager is None:
            return False

        if self._config.duration_seconds is None:
            return False

        # Get scene active time
        activated_at = scene_manager._state_data.get("activated_at")
        if activated_at is None:
            return False

        # Convert to datetime if needed
        if isinstance(activated_at, str):
            activated_at = datetime.fromisoformat(activated_at)

        # Handle naive datetimes (assume UTC)
        if activated_at.tzinfo is None:
            activated_at = activated_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        elapsed = (now - activated_at).total_seconds()

        if elapsed >= self._config.duration_seconds:
            self.arm()
            return True

        return False

    def _evaluate_interval(self, scene_manager: Optional[SceneManager]) -> bool:
        """Evaluate interval trigger."""
        if scene_manager is None:
            return False

        if self._config.interval_seconds is None:
            return False

        # Get last trigger time or scene active time
        last_trigger = self._triggered_at or scene_manager._state_data.get("activated_at")

        if last_trigger is None:
            return False

        # Convert to datetime if needed
        if isinstance(last_trigger, str):
            last_trigger = datetime.fromisoformat(last_trigger)

        # Handle naive datetimes (assume UTC)
        if last_trigger.tzinfo is None:
            last_trigger = last_trigger.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        elapsed = (now - last_trigger).total_seconds()

        if elapsed >= self._config.interval_seconds:
            self.arm()
            return True

        return False

    def time_until(self, scene_manager: Optional[SceneManager] = None) -> Optional[timedelta]:
        """
        Get time until trigger is ready.

        Args:
            scene_manager: Optional scene manager for duration triggers

        Returns:
            Timedelta until ready, or None if not applicable
        """
        if self._trigger_type == TimeTriggerType.SCHEDULED:
            if self._config.scheduled_time is None:
                return None
            now = datetime.now(timezone.utc)
            if self._config.scheduled_time <= now:
                return timedelta(0)
            return self._config.scheduled_time - now

        elif self._trigger_type == TimeTriggerType.DURATION:
            if scene_manager is None or self._config.duration_seconds is None:
                return None

            activated_at = scene_manager._state_data.get("activated_at")
            if activated_at is None:
                return None

            if isinstance(activated_at, str):
                activated_at = datetime.fromisoformat(activated_at)

            # Handle naive datetimes (assume UTC)
            if activated_at.tzinfo is None:
                activated_at = activated_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            elapsed = (now - activated_at).total_seconds()
            remaining = self._config.duration_seconds - elapsed

            if remaining <= 0:
                return timedelta(0)
            return timedelta(seconds=remaining)

        elif self._trigger_type == TimeTriggerType.INTERVAL:
            if scene_manager is None or self._config.interval_seconds is None:
                return None

            last_trigger = self._triggered_at or scene_manager._state_data.get("activated_at")
            if last_trigger is None:
                return None

            if isinstance(last_trigger, str):
                last_trigger = datetime.fromisoformat(last_trigger)

            # Handle naive datetimes (assume UTC)
            if last_trigger.tzinfo is None:
                last_trigger = last_trigger.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            elapsed = (now - last_trigger).total_seconds()
            remaining = self._config.interval_seconds - elapsed

            if remaining <= 0:
                return timedelta(0)
            return timedelta(seconds=remaining)

        return None

    def arm(self) -> None:
        """Arm the trigger."""
        if self._state in (TriggerState.ENABLED, TriggerState.ARMED):
            self._state = TriggerState.ARMED
            self._armed_at = datetime.now(timezone.utc)
            logger.debug(f"Armed trigger {self._config.trigger_id}")

    def fire(self) -> None:
        """Fire the trigger."""
        if self._state == TriggerState.ARMED:
            self._state = TriggerState.TRIGGERED
            self._triggered_at = datetime.now(timezone.utc)
            logger.info(f"Fired trigger {self._config.trigger_id}")

    def complete(self) -> None:
        """Mark trigger as complete."""
        if self._state == TriggerState.TRIGGERED:
            self._state = TriggerState.COMPLETE
            self._completed_at = datetime.now(timezone.utc)

            # Advance sequence index for interval triggers
            if self._trigger_type == TimeTriggerType.INTERVAL:
                self._sequence_index += 1
                # Reset to ENABLED for interval triggers to fire again
                self._state = TriggerState.ENABLED
                self._triggered_at = None

            logger.info(f"Completed trigger {self._config.trigger_id}")

    def cancel(self) -> None:
        """Cancel the trigger."""
        self._state = TriggerState.CANCELLED
        logger.info(f"Cancelled trigger {self._config.trigger_id}")

    def enable(self) -> None:
        """Enable the trigger."""
        if self._state == TriggerState.CANCELLED:
            self._state = TriggerState.ENABLED
            logger.debug(f"Enabled trigger {self._config.trigger_id}")

    def disable(self) -> None:
        """Disable the trigger."""
        if self._state != TriggerState.COMPLETE:
            self._state = TriggerState.CANCELLED
            logger.debug(f"Disabled trigger {self._config.trigger_id}")

    def is_enabled(self) -> bool:
        """Check if trigger is enabled."""
        return self._state == TriggerState.ENABLED


class TimeTriggerScheduler:
    """
    Scheduler for time-based triggers.

    Evaluates triggers periodically and fires them when ready.
    """

    def __init__(self, tick_interval_seconds: float = 1.0):
        """
        Initialize scheduler.

        Args:
            tick_interval_seconds: Seconds between evaluation ticks
        """
        self._triggers: Dict[str, TimeTrigger] = {}
        self._tick_interval = tick_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._transition_callback: Optional[Callable[[TimeTrigger], None]] = None

        logger.info(f"TimeTriggerScheduler initialized (tick_interval={tick_interval_seconds}s)")

    def add_trigger(self, trigger: TimeTrigger) -> None:
        """
        Add trigger to scheduler.

        Args:
            trigger: Trigger to add

        Raises:
            ValueError: If trigger ID already exists
        """
        if trigger.trigger_id in self._triggers:
            raise ValueError(f"Trigger {trigger.trigger_id} already exists")

        self._triggers[trigger.trigger_id] = trigger
        logger.info(f"Added trigger {trigger.trigger_id} to scheduler")

        # Auto-evaluate trigger on addition (for scheduled triggers already past due)
        trigger.evaluate()

    def remove_trigger(self, trigger_id: str) -> bool:
        """
        Remove trigger from scheduler.

        Args:
            trigger_id: ID of trigger to remove

        Returns:
            True if trigger was removed
        """
        if trigger_id in self._triggers:
            del self._triggers[trigger_id]
            logger.info(f"Removed trigger {trigger_id} from scheduler")
            return True
        return False

    def get_trigger(self, trigger_id: str) -> Optional[TimeTrigger]:
        """
        Get trigger by ID.

        Args:
            trigger_id: Trigger ID

        Returns:
            Trigger or None if not found
        """
        return self._triggers.get(trigger_id)

    def get_all_triggers(self) -> List[TimeTrigger]:
        """
        Get all triggers sorted by priority.

        Returns:
            List of triggers sorted by priority (highest first)
        """
        triggers = list(self._triggers.values())
        triggers.sort(key=lambda t: t.priority, reverse=True)
        return triggers

    def get_triggers_for_scene(self, scene_id: str) -> List[TimeTrigger]:
        """
        Get triggers for a specific scene.

        Args:
            scene_id: Scene ID

        Returns:
            List of triggers for the scene
        """
        return [
            trigger for trigger in self._triggers.values()
            if trigger.source_scene_id == scene_id
        ]

    def get_ready_triggers(self) -> List[TimeTrigger]:
        """
        Get triggers that are ready to fire.

        Returns:
            List of armed triggers
        """
        return [
            trigger for trigger in self._triggers.values()
            if trigger.state == TriggerState.ARMED
        ]

    def register_transition_callback(
        self,
        callback: Callable[[TimeTrigger], None]
    ) -> None:
        """
        Register callback for transition execution.

        Args:
            callback: Function to call when trigger fires
        """
        self._transition_callback = callback

    def tick(self) -> None:
        """
        Perform one scheduler tick.

        Evaluates all enabled triggers and fires ready ones.
        Also fires any triggers that are already armed.
        """
        for trigger in self.get_all_triggers():
            # Evaluate enabled triggers
            if trigger.is_enabled() and trigger.evaluate():
                self._fire_trigger(trigger)
            # Fire already armed triggers
            elif trigger.state == TriggerState.ARMED:
                self._fire_trigger(trigger)

    def _fire_trigger(self, trigger: TimeTrigger) -> None:
        """
        Fire a trigger and execute callback.

        Args:
            trigger: Trigger to fire
        """
        trigger.fire()

        # Cancel lower priority triggers on same scene
        self._cancel_lower_priority_triggers(trigger)

        if self._transition_callback:
            try:
                self._transition_callback(trigger)
            except Exception as e:
                logger.error(f"Transition callback error: {e}")

    def _cancel_lower_priority_triggers(self, fired_trigger: TimeTrigger) -> None:
        """
        Cancel lower priority triggers for the same source scene.

        Args:
            fired_trigger: The trigger that fired
        """
        for trigger in self._triggers.values():
            if (trigger.source_scene_id == fired_trigger.source_scene_id and
                trigger.trigger_id != fired_trigger.trigger_id and
                trigger.priority < fired_trigger.priority and
                trigger.state in (TriggerState.ENABLED, TriggerState.ARMED)):
                trigger.cancel()
                logger.info(
                    f"Cancelled lower priority trigger {trigger.trigger_id} "
                    f"(priority {trigger.priority}) "
                    f"for scene {trigger.source_scene_id}"
                )

    def start(self) -> None:
        """Start the scheduler thread."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler thread."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                self.tick()
            except Exception as e:
                logger.error(f"Scheduler tick error: {e}")

            time.sleep(self._tick_interval)


# Convenience functions

def create_scheduled_trigger(
    trigger_id: str,
    source_scene_id: str,
    target_scene_id: str,
    scheduled_time: datetime,
    transition_type: TransitionType = TransitionType.FADE,
    priority: int = 50
) -> TimeTrigger:
    """
    Create a scheduled time trigger.

    Args:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        scheduled_time: When to trigger
        transition_type: Type of transition
        priority: Trigger priority

    Returns:
        Configured TimeTrigger
    """
    config = TimeTriggerConfig(
        trigger_id=trigger_id,
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_id,
        transition_type=transition_type,
        priority=priority,
        scheduled_time=scheduled_time
    )
    return TimeTrigger(config)


def create_duration_trigger(
    trigger_id: str,
    source_scene_id: str,
    target_scene_id: str,
    duration_seconds: int,
    transition_type: TransitionType = TransitionType.FADE,
    priority: int = 50
) -> TimeTrigger:
    """
    Create a duration-based trigger.

    Args:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        duration_seconds: Seconds after activation to trigger
        transition_type: Type of transition
        priority: Trigger priority

    Returns:
        Configured TimeTrigger
    """
    config = TimeTriggerConfig(
        trigger_id=trigger_id,
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_id,
        transition_type=transition_type,
        priority=priority,
        duration_seconds=duration_seconds
    )
    return TimeTrigger(config)


def create_interval_trigger(
    trigger_id: str,
    source_scene_id: str,
    target_scene_sequence: List[str],
    interval_seconds: int,
    transition_type: TransitionType = TransitionType.CROSSFADE,
    priority: int = 40
) -> TimeTrigger:
    """
    Create an interval trigger.

    Args:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_sequence: Scenes to cycle through
        interval_seconds: Seconds between triggers
        transition_type: Type of transition
        priority: Trigger priority

    Returns:
        Configured TimeTrigger
    """
    config = TimeTriggerConfig(
        trigger_id=trigger_id,
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_sequence[0],
        transition_type=transition_type,
        priority=priority,
        interval_seconds=interval_seconds,
        target_scene_sequence=target_scene_sequence
    )
    return TimeTrigger(config)
