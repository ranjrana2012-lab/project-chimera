"""
Event-based Transition Triggers - OpenClaw Orchestrator

Provides Kafka-based event triggers for scene transitions.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of event triggers."""
    AUDIENCE_THRESHOLD = "audience_threshold"
    AGENT_HEALTH = "agent_health"
    CUSTOM = "custom"


@dataclass
class EventCondition:
    """
    Conditions for event trigger matching.

    Attributes:
        topic: Kafka topic to consume events from
        event_type: Type of event to match
        metadata_filter: Optional metadata key-value pairs to match
        threshold_type: For audience triggers, type of threshold
        min_duration: For audience triggers, minimum duration in seconds
        critical_agents: For agent health, list of critical agent IDs
    """
    topic: str
    event_type: str
    metadata_filter: Optional[Dict[str, Any]] = None
    threshold_type: Optional[str] = None
    min_duration: Optional[int] = None
    critical_agents: Optional[List[str]] = None


@dataclass
class EventTriggerConfig:
    """
    Configuration for an event-based trigger.

    Attributes:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        event_condition: Event matching conditions
        priority: Trigger priority (0-100, higher is more important)
        enabled: Whether trigger is active
        metadata: Additional trigger metadata
    """
    trigger_id: str
    source_scene_id: str
    target_scene_id: str
    event_condition: EventCondition
    priority: int = 50
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Transition settings
    transition_type: str = "fade"  # cut, fade, crossfade


class EventTrigger:
    """
    An event-based transition trigger.

    Triggers when a matching Kafka event is received.
    """

    def __init__(self, config: EventTriggerConfig):
        """
        Initialize event trigger.

        Args:
            config: Trigger configuration
        """
        self._config = config
        self._state = TriggerState.ENABLED if config.enabled else TriggerState.CANCELLED
        self._event_type = self._determine_type()
        self._armed_at: Optional[datetime] = None
        self._triggered_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None

        logger.info(
            f"Created {self._event_type.value} trigger {config.trigger_id} "
            f"for scene {config.source_scene_id} "
            f"listening on topic {config.event_condition.topic}"
        )

    def _determine_type(self) -> EventType:
        """Determine event type from condition."""
        topic = self._config.event_condition.topic

        if "audience" in topic:
            return EventType.AUDIENCE_THRESHOLD
        elif "agent" in topic and "health" in topic:
            return EventType.AGENT_HEALTH
        else:
            return EventType.CUSTOM

    @property
    def trigger_id(self) -> str:
        """Get trigger ID."""
        return self._config.trigger_id

    @property
    def event_type(self) -> EventType:
        """Get event type."""
        return self._event_type

    @property
    def state(self) -> 'TriggerState':
        """Get current state."""
        return self._state

    @property
    def source_scene_id(self) -> str:
        """Get source scene ID."""
        return self._config.source_scene_id

    @property
    def target_scene_id(self) -> str:
        """Get target scene ID."""
        return self._config.target_scene_id

    @property
    def priority(self) -> int:
        """Get trigger priority."""
        return self._config.priority

    @property
    def transition_type(self) -> str:
        """Get transition type."""
        return self._config.transition_type

    @property
    def topic(self) -> str:
        """Get Kafka topic."""
        return self._config.event_condition.topic

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

    def evaluate_event(self, event: Dict[str, Any]) -> bool:
        """
        Evaluate if event matches trigger conditions.

        Args:
            event: Event data from Kafka

        Returns:
            True if event matches and trigger should fire
        """
        if self._state not in (TriggerState.ENABLED, TriggerState.ARMED):
            return False

        condition = self._config.event_condition

        # Check event type
        if event.get("event_type") != condition.event_type:
            return False

        # Check source scene ID if present in event
        if "source_scene_id" in event:
            if event["source_scene_id"] != self._config.source_scene_id:
                return False
        elif "scene_id" in event:
            if event["scene_id"] != self._config.source_scene_id:
                return False

        # Check metadata filter
        if condition.metadata_filter:
            event_metadata = event.get("metadata", {})
            for key, value in condition.metadata_filter.items():
                if event_metadata.get(key) != value:
                    return False

        # Check threshold duration for audience events
        if self._event_type == EventType.AUDIENCE_THRESHOLD:
            if condition.min_duration is not None:
                duration = event.get("duration_seconds", 0)
                if duration < condition.min_duration:
                    return False

        # Check critical agents for agent health events
        if self._event_type == EventType.AGENT_HEALTH:
            if condition.critical_agents:
                agent_id = event.get("agent_id")
                if agent_id not in condition.critical_agents:
                    return False

        # Event matches - arm the trigger
        self.arm()
        return True

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


class TriggerState(Enum):
    """States of a trigger."""
    ENABLED = "enabled"
    ARMED = "armed"
    TRIGGERED = "triggered"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class EventTriggerScheduler:
    """
    Scheduler for event-based triggers.

    Listens for Kafka events and evaluates triggers.
    """

    def __init__(self):
        """Initialize scheduler."""
        self._triggers: Dict[str, EventTrigger] = {}
        self._transition_callback: Optional[Callable[[EventTrigger], None]] = None
        self._running = False

        # Index triggers by topic for efficient lookup
        self._triggers_by_topic: Dict[str, List[str]] = {}

        logger.info("EventTriggerScheduler initialized")

    def start(self) -> None:
        """Start the scheduler."""
        self._running = True
        logger.info("EventTriggerScheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        logger.info("EventTriggerScheduler stopped")

    def add_trigger(self, trigger: EventTrigger) -> None:
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

        # Add to topic index
        topic = trigger.topic
        if topic not in self._triggers_by_topic:
            self._triggers_by_topic[topic] = []
        self._triggers_by_topic[topic].append(trigger.trigger_id)

        logger.info(f"Added trigger {trigger.trigger_id} to scheduler")

    def remove_trigger(self, trigger_id: str) -> bool:
        """
        Remove trigger from scheduler.

        Args:
            trigger_id: ID of trigger to remove

        Returns:
            True if trigger was removed
        """
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False

        # Remove from topic index
        topic = trigger.topic
        if topic in self._triggers_by_topic:
            self._triggers_by_topic[topic].remove(trigger_id)
            if not self._triggers_by_topic[topic]:
                del self._triggers_by_topic[topic]

        del self._triggers[trigger_id]
        logger.info(f"Removed trigger {trigger_id} from scheduler")
        return True

    def get_trigger(self, trigger_id: str) -> Optional[EventTrigger]:
        """
        Get trigger by ID.

        Args:
            trigger_id: Trigger ID

        Returns:
            Trigger or None if not found
        """
        return self._triggers.get(trigger_id)

    def get_all_triggers(self) -> List[EventTrigger]:
        """
        Get all triggers sorted by priority.

        Returns:
            List of triggers sorted by priority (highest first)
        """
        triggers = list(self._triggers.values())
        triggers.sort(key=lambda t: t.priority, reverse=True)
        return triggers

    def get_triggers_for_topic(self, topic: str) -> List[EventTrigger]:
        """
        Get triggers for a specific topic.

        Args:
            topic: Kafka topic

        Returns:
            List of triggers listening to the topic
        """
        trigger_ids = self._triggers_by_topic.get(topic, [])
        return [
            self._triggers[trigger_id]
            for trigger_id in trigger_ids
            if trigger_id in self._triggers
        ]

    def register_transition_callback(
        self,
        callback: Callable[[EventTrigger], None]
    ) -> None:
        """
        Register callback for transition execution.

        Args:
            callback: Function to call when trigger fires
        """
        self._transition_callback = callback

    def process_event(self, topic: str, event: Dict[str, Any]) -> None:
        """
        Process a Kafka event.

        Evaluates all triggers for the topic and fires matching ones.

        Args:
            topic: Kafka topic the event was received on
            event: Event data
        """
        triggers = self.get_triggers_for_topic(topic)

        # Sort by priority (highest first) so higher priority triggers fire first
        triggers.sort(key=lambda t: t.priority, reverse=True)

        for trigger in triggers:
            # Skip if already cancelled or completed
            if trigger.state in (TriggerState.CANCELLED, TriggerState.COMPLETE):
                continue

            if trigger.is_enabled() and trigger.evaluate_event(event):
                self._fire_trigger(trigger)

    def _fire_trigger(self, trigger: EventTrigger) -> None:
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

    def _cancel_lower_priority_triggers(self, fired_trigger: EventTrigger) -> None:
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

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running


# Convenience functions

def create_audience_threshold_trigger(
    trigger_id: str,
    source_scene_id: str,
    target_scene_id: str,
    threshold_type: str,
    min_duration: int = 30,
    priority: int = 70
) -> EventTrigger:
    """
    Create an audience threshold trigger.

    Args:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        threshold_type: Type of threshold (e.g., "positive_sentiment")
        min_duration: Minimum duration threshold must be met
        priority: Trigger priority

    Returns:
        Configured EventTrigger
    """
    condition = EventCondition(
        topic="audience.response.detected",
        event_type="audience_threshold_reached",
        threshold_type=threshold_type,
        min_duration=min_duration
    )

    config = EventTriggerConfig(
        trigger_id=trigger_id,
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_id,
        event_condition=condition,
        priority=priority
    )

    return EventTrigger(config)


def create_agent_health_trigger(
    trigger_id: str,
    source_scene_id: str,
    target_scene_id: str,
    critical_agents: List[str],
    priority: int = 90
) -> EventTrigger:
    """
    Create an agent health trigger.

    Args:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to (usually fallback)
        critical_agents: List of critical agent IDs to monitor
        priority: Trigger priority (default high for health triggers)

    Returns:
        Configured EventTrigger
    """
    condition = EventCondition(
        topic="agent.health.changed",
        event_type="agent_unhealthy",
        critical_agents=critical_agents
    )

    config = EventTriggerConfig(
        trigger_id=trigger_id,
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_id,
        event_condition=condition,
        priority=priority,
        transition_type="cut"  # Use cut for emergency transitions
    )

    return EventTrigger(config)


def create_custom_event_trigger(
    trigger_id: str,
    source_scene_id: str,
    target_scene_id: str,
    event_type: str,
    metadata_filter: Optional[Dict[str, Any]] = None,
    priority: int = 60
) -> EventTrigger:
    """
    Create a custom event trigger.

    Args:
        trigger_id: Unique trigger identifier
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        event_type: Type of custom event to match
        metadata_filter: Optional metadata key-value pairs to match
        priority: Trigger priority

    Returns:
        Configured EventTrigger
    """
    condition = EventCondition(
        topic="custom.transition.request",
        event_type=event_type,
        metadata_filter=metadata_filter
    )

    config = EventTriggerConfig(
        trigger_id=trigger_id,
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_id,
        event_condition=condition,
        priority=priority
    )

    return EventTrigger(config)
