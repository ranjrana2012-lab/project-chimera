"""
Unit tests for Event-based Transition Triggers.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
import threading
import time
import json

import sys
sys.path.insert(0, '.')

from core.scene_manager import SceneManager, SceneConfig, SceneState
from transitions.event_triggers import (
    EventType,
    EventTriggerConfig,
    EventCondition,
    EventTrigger,
    EventTriggerScheduler,
    TriggerState
)


class TestEventType:
    """Test EventType enum."""

    def test_event_types(self):
        """All event types exist."""
        assert EventType.AUDIENCE_THRESHOLD
        assert EventType.AGENT_HEALTH
        assert EventType.CUSTOM


class TestEventCondition:
    """Test EventCondition dataclass."""

    def test_create_condition(self):
        """Create event condition."""
        condition = EventCondition(
            topic="audience.response.detected",
            event_type="audience_threshold_reached"
        )

        assert condition.topic == "audience.response.detected"
        assert condition.event_type == "audience_threshold_reached"
        assert condition.metadata_filter is None

    def test_create_condition_with_filters(self):
        """Create condition with metadata filter."""
        condition = EventCondition(
            topic="custom.transition.request",
            event_type="custom_transition",
            metadata_filter={"choice_id": "choice-a"}
        )

        assert condition.metadata_filter == {"choice_id": "choice-a"}

    def test_create_audience_condition(self):
        """Create audience threshold condition."""
        condition = EventCondition(
            topic="audience.response.detected",
            event_type="audience_threshold_reached",
            threshold_type="positive_sentiment",
            min_duration=30
        )

        assert condition.threshold_type == "positive_sentiment"
        assert condition.min_duration == 30

    def test_create_agent_health_condition(self):
        """Create agent health condition."""
        condition = EventCondition(
            topic="agent.health.changed",
            event_type="agent_unhealthy",
            critical_agents=["scenespeak", "sentiment"]
        )

        assert condition.critical_agents == ["scenespeak", "sentiment"]


class TestEventTriggerConfig:
    """Test EventTriggerConfig dataclass."""

    def test_create_config(self):
        """Create trigger configuration."""
        condition = EventCondition(
            topic="audience.response.detected",
            event_type="audience_threshold_reached"
        )

        config = EventTriggerConfig(
            trigger_id="et-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=70
        )

        assert config.trigger_id == "et-001"
        assert config.source_scene_id == "scene-001"
        assert config.target_scene_id == "scene-002"
        assert config.priority == 70
        assert config.enabled is True


class TestEventTrigger:
    """Test EventTrigger class."""

    @pytest.fixture
    def condition(self):
        """Create test condition."""
        return EventCondition(
            topic="audience.response.detected",
            event_type="audience_threshold_reached"
        )

    @pytest.fixture
    def config(self, condition):
        """Create test config."""
        return EventTriggerConfig(
            trigger_id="et-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=70
        )

    def test_create_trigger(self, config):
        """Create event trigger."""
        trigger = EventTrigger(config)

        assert trigger.trigger_id == "et-001"
        assert trigger.state == TriggerState.ENABLED
        assert trigger.event_type == EventType.AUDIENCE_THRESHOLD

    def test_create_agent_health_trigger(self):
        """Create agent health trigger."""
        condition = EventCondition(
            topic="agent.health.changed",
            event_type="agent_unhealthy",
            critical_agents=["scenespeak"]
        )

        config = EventTriggerConfig(
            trigger_id="et-002",
            source_scene_id="scene-001",
            target_scene_id="scene-fallback",
            event_condition=condition,
            priority=90
        )

        trigger = EventTrigger(config)

        assert trigger.event_type == EventType.AGENT_HEALTH

    def test_create_custom_event_trigger(self):
        """Create custom event trigger."""
        condition = EventCondition(
            topic="custom.transition.request",
            event_type="custom_transition",
            metadata_filter={"choice_id": "choice-a"}
        )

        config = EventTriggerConfig(
            trigger_id="et-003",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=60
        )

        trigger = EventTrigger(config)

        assert trigger.event_type == EventType.CUSTOM

    def test_evaluate_matching_event(self, config):
        """Evaluate trigger with matching event."""
        trigger = EventTrigger(config)

        event = {
            "event_type": "audience_threshold_reached",
            "scene_id": "scene-001",
            "threshold_type": "positive_sentiment",
            "current_value": 0.85,
            "threshold": 0.80,
            "duration_seconds": 30,
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is True
        assert trigger.state == TriggerState.ARMED

    def test_evaluate_non_matching_event_type(self, config):
        """Evaluate trigger with non-matching event type."""
        trigger = EventTrigger(config)

        event = {
            "event_type": "different_event",
            "scene_id": "scene-001",
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is False
        assert trigger.state == TriggerState.ENABLED

    def test_evaluate_with_metadata_filter(self):
        """Evaluate trigger with metadata filter."""
        condition = EventCondition(
            topic="custom.transition.request",
            event_type="custom_transition",
            metadata_filter={"choice_id": "choice-a"}
        )

        config = EventTriggerConfig(
            trigger_id="et-003",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=60
        )

        trigger = EventTrigger(config)

        # Matching metadata
        event = {
            "event_type": "custom_transition",
            "source_scene_id": "scene-001",
            "target_scene_id": "scene-002",
            "metadata": {"choice_id": "choice-a"},
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is True

    def test_evaluate_with_non_matching_metadata(self):
        """Evaluate trigger with non-matching metadata."""
        condition = EventCondition(
            topic="custom.transition.request",
            event_type="custom_transition",
            metadata_filter={"choice_id": "choice-a"}
        )

        config = EventTriggerConfig(
            trigger_id="et-003",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=60
        )

        trigger = EventTrigger(config)

        # Non-matching metadata
        event = {
            "event_type": "custom_transition",
            "source_scene_id": "scene-001",
            "target_scene_id": "scene-002",
            "metadata": {"choice_id": "choice-b"},
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is False

    def test_evaluate_agent_health_critical_agent(self):
        """Evaluate agent health trigger for critical agent."""
        condition = EventCondition(
            topic="agent.health.changed",
            event_type="agent_unhealthy",
            critical_agents=["scenespeak", "sentiment"]
        )

        config = EventTriggerConfig(
            trigger_id="et-002",
            source_scene_id="scene-001",
            target_scene_id="scene-fallback",
            event_condition=condition,
            priority=90
        )

        trigger = EventTrigger(config)

        # Critical agent unhealthy
        event = {
            "event_type": "agent_unhealthy",
            "scene_id": "scene-001",
            "agent_id": "scenespeak",
            "health_status": "unhealthy",
            "error_code": "AGENT_TIMEOUT",
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is True

    def test_evaluate_agent_health_non_critical_agent(self):
        """Evaluate agent health trigger for non-critical agent."""
        condition = EventCondition(
            topic="agent.health.changed",
            event_type="agent_unhealthy",
            critical_agents=["scenespeak", "sentiment"]
        )

        config = EventTriggerConfig(
            trigger_id="et-002",
            source_scene_id="scene-001",
            target_scene_id="scene-fallback",
            event_condition=condition,
            priority=90
        )

        trigger = EventTrigger(config)

        # Non-critical agent unhealthy
        event = {
            "event_type": "agent_unhealthy",
            "scene_id": "scene-001",
            "agent_id": "captioning",
            "health_status": "unhealthy",
            "error_code": "AGENT_TIMEOUT",
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is False

    def test_evaluate_audience_threshold_with_duration(self):
        """Evaluate audience threshold with minimum duration."""
        condition = EventCondition(
            topic="audience.response.detected",
            event_type="audience_threshold_reached",
            threshold_type="positive_sentiment",
            min_duration=30
        )

        config = EventTriggerConfig(
            trigger_id="et-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=70
        )

        trigger = EventTrigger(config)

        # Event with sufficient duration
        event = {
            "event_type": "audience_threshold_reached",
            "scene_id": "scene-001",
            "threshold_type": "positive_sentiment",
            "current_value": 0.85,
            "threshold": 0.80,
            "duration_seconds": 30,
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is True

    def test_evaluate_audience_threshold_insufficient_duration(self):
        """Evaluate audience threshold with insufficient duration."""
        condition = EventCondition(
            topic="audience.response.detected",
            event_type="audience_threshold_reached",
            threshold_type="positive_sentiment",
            min_duration=30
        )

        config = EventTriggerConfig(
            trigger_id="et-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=70
        )

        trigger = EventTrigger(config)

        # Event with insufficient duration
        event = {
            "event_type": "audience_threshold_reached",
            "scene_id": "scene-001",
            "threshold_type": "positive_sentiment",
            "current_value": 0.85,
            "threshold": 0.80,
            "duration_seconds": 10,
            "timestamp": "2026-03-04T03:30:00Z"
        }

        result = trigger.evaluate_event(event)

        assert result is False

    def test_fire_trigger(self, config):
        """Fire a trigger."""
        trigger = EventTrigger(config)
        trigger.arm()
        trigger.fire()

        assert trigger.state == TriggerState.TRIGGERED
        assert trigger.triggered_at is not None

    def test_complete_trigger(self, config):
        """Complete a trigger."""
        trigger = EventTrigger(config)
        trigger.arm()
        trigger.fire()
        trigger.complete()

        assert trigger.state == TriggerState.COMPLETE
        assert trigger.completed_at is not None

    def test_cancel_trigger(self, config):
        """Cancel a trigger."""
        trigger = EventTrigger(config)
        trigger.cancel()

        assert trigger.state == TriggerState.CANCELLED

    def test_enable_disable_trigger(self, config):
        """Enable and disable a trigger."""
        config.enabled = False
        trigger = EventTrigger(config)

        assert trigger.is_enabled() is False

        trigger.enable()
        assert trigger.is_enabled() is True

        trigger.disable()
        assert trigger.is_enabled() is False


class TestEventTriggerScheduler:
    """Test EventTriggerScheduler class."""

    @pytest.fixture
    def scheduler(self):
        """Create trigger scheduler."""
        return EventTriggerScheduler()

    @pytest.fixture
    def condition(self):
        """Create test condition."""
        return EventCondition(
            topic="audience.response.detected",
            event_type="audience_threshold_reached"
        )

    @pytest.fixture
    def config(self, condition):
        """Create test config."""
        return EventTriggerConfig(
            trigger_id="et-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition,
            priority=70
        )

    def test_scheduler_init(self, scheduler):
        """Initialize scheduler."""
        assert len(scheduler._triggers) == 0
        assert scheduler.is_running() is False

    def test_add_trigger(self, scheduler, config):
        """Add trigger to scheduler."""
        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        assert len(scheduler._triggers) == 1
        assert scheduler.get_trigger("et-001") is trigger

    def test_add_duplicate_trigger_id(self, scheduler, config):
        """Cannot add duplicate trigger ID."""
        trigger1 = EventTrigger(config)
        trigger2 = EventTrigger(config)

        scheduler.add_trigger(trigger1)

        with pytest.raises(ValueError):
            scheduler.add_trigger(trigger2)

    def test_remove_trigger(self, scheduler, config):
        """Remove trigger from scheduler."""
        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)
        scheduler.remove_trigger("et-001")

        assert len(scheduler._triggers) == 0
        assert scheduler.get_trigger("et-001") is None

    def test_get_trigger(self, scheduler, config):
        """Get trigger by ID."""
        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        retrieved = scheduler.get_trigger("et-001")

        assert retrieved is trigger

    def test_get_all_triggers(self, scheduler):
        """Get all triggers sorted by priority."""
        config1 = EventTriggerConfig(
            trigger_id="et-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=EventCondition(
                topic="test", event_type="test"
            ),
            priority=30
        )

        config2 = EventTriggerConfig(
            trigger_id="et-002",
            source_scene_id="scene-001",
            target_scene_id="scene-003",
            event_condition=EventCondition(
                topic="test", event_type="test"
            ),
            priority=80
        )

        scheduler.add_trigger(EventTrigger(config1))
        scheduler.add_trigger(EventTrigger(config2))

        all_triggers = scheduler.get_all_triggers()

        # Should be sorted by priority descending
        assert all_triggers[0].trigger_id == "et-002"
        assert all_triggers[1].trigger_id == "et-001"

    def test_get_triggers_for_topic(self, scheduler, config):
        """Get triggers for specific topic."""
        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        topic_triggers = scheduler.get_triggers_for_topic("audience.response.detected")

        assert len(topic_triggers) == 1
        assert topic_triggers[0].trigger_id == "et-001"

    def test_process_event_matching(self, scheduler, config):
        """Process event that matches trigger."""
        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        callback_called = []

        def mock_callback(trigger):
            callback_called.append(trigger.trigger_id)

        scheduler.register_transition_callback(mock_callback)

        event = {
            "event_type": "audience_threshold_reached",
            "scene_id": "scene-001",
            "threshold_type": "positive_sentiment",
            "current_value": 0.85,
            "threshold": 0.80,
            "duration_seconds": 30,
            "timestamp": "2026-03-04T03:30:00Z"
        }

        scheduler.process_event("audience.response.detected", event)

        assert len(callback_called) == 1
        assert callback_called[0] == "et-001"
        assert trigger.state == TriggerState.TRIGGERED

    def test_process_event_non_matching(self, scheduler, config):
        """Process event that doesn't match trigger."""
        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        callback_called = []

        def mock_callback(trigger):
            callback_called.append(trigger.trigger_id)

        scheduler.register_transition_callback(mock_callback)

        event = {
            "event_type": "different_event",
            "scene_id": "scene-001",
            "timestamp": "2026-03-04T03:30:00Z"
        }

        scheduler.process_event("audience.response.detected", event)

        assert len(callback_called) == 0
        assert trigger.state == TriggerState.ENABLED

    def test_process_event_wrong_topic(self, scheduler, config):
        """Process event for wrong topic."""
        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        event = {
            "event_type": "audience_threshold_reached",
            "scene_id": "scene-001",
            "timestamp": "2026-03-04T03:30:00Z"
        }

        scheduler.process_event("wrong.topic", event)

        assert trigger.state == TriggerState.ENABLED

    def test_sort_triggers_by_priority(self, scheduler):
        """Triggers sorted by priority."""
        config1 = EventTriggerConfig(
            trigger_id="et-low",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=EventCondition(
                topic="test", event_type="test"
            ),
            priority=30
        )

        config2 = EventTriggerConfig(
            trigger_id="et-high",
            source_scene_id="scene-001",
            target_scene_id="scene-003",
            event_condition=EventCondition(
                topic="test", event_type="test"
            ),
            priority=80
        )

        scheduler.add_trigger(EventTrigger(config1))
        scheduler.add_trigger(EventTrigger(config2))

        all_triggers = scheduler.get_all_triggers()

        # Should be sorted by priority descending
        assert all_triggers[0].trigger_id == "et-high"
        assert all_triggers[1].trigger_id == "et-low"

    def test_cancel_lower_priority_on_same_scene(self, scheduler):
        """Lower priority triggers cancelled when higher fires."""
        config_low = EventTriggerConfig(
            trigger_id="et-low",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=EventCondition(
                topic="test", event_type="test"
            ),
            priority=30
        )

        config_high = EventTriggerConfig(
            trigger_id="et-high",
            source_scene_id="scene-001",
            target_scene_id="scene-003",
            event_condition=EventCondition(
                topic="test", event_type="test"
            ),
            priority=80
        )

        low_trigger = EventTrigger(config_low)
        high_trigger = EventTrigger(config_high)

        scheduler.add_trigger(low_trigger)
        scheduler.add_trigger(high_trigger)

        # Fire high priority trigger
        event = {
            "event_type": "test",
            "scene_id": "scene-001",
            "timestamp": "2026-03-04T03:30:00Z"
        }

        scheduler.process_event("test", event)

        # High trigger should be triggered
        assert high_trigger.state == TriggerState.TRIGGERED

        # Low trigger should be cancelled
        assert low_trigger.state == TriggerState.CANCELLED

    def test_register_transition_callback(self, scheduler, config):
        """Register transition callback."""
        callback_called = []

        def mock_callback(trigger):
            callback_called.append(True)

        scheduler.register_transition_callback(mock_callback)

        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        event = {
            "event_type": "audience_threshold_reached",
            "scene_id": "scene-001",
            "timestamp": "2026-03-04T03:30:00Z"
        }

        scheduler.process_event("audience.response.detected", event)

        assert len(callback_called) == 1
