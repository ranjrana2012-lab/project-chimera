"""
Unit tests for Time-based Transition Triggers.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
import threading
import time

from core.scene_manager import SceneManager, SceneConfig, SceneState
from transitions.time_triggers import (
    TimeTriggerType,
    TransitionType,
    TimeTrigger,
    TimeTriggerConfig,
    TimeTriggerScheduler,
    TriggerState
)


class TestTimeTriggerType:
    """Test TimeTriggerType enum."""

    def test_trigger_types(self):
        """All trigger types exist."""
        assert TimeTriggerType.SCHEDULED
        assert TimeTriggerType.DURATION
        assert TimeTriggerType.INTERVAL


class TestTransitionType:
    """Test TransitionType enum."""

    def test_transition_types(self):
        """All transition types exist."""
        assert TransitionType.CUT
        assert TransitionType.FADE
        assert TransitionType.CROSSFADE


class TestTriggerState:
    """Test TriggerState enum."""

    def test_trigger_states(self):
        """All trigger states exist."""
        assert TriggerState.ENABLED
        assert TriggerState.ARMED
        assert TriggerState.TRIGGERED
        assert TriggerState.COMPLETE
        assert TriggerState.CANCELLED


class TestTimeTriggerConfig:
    """Test TimeTriggerConfig dataclass."""

    def test_create_config(self):
        """Create trigger configuration."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            priority=50
        )

        assert config.trigger_id == "tt-001"
        assert config.source_scene_id == "scene-001"
        assert config.target_scene_id == "scene-002"
        assert config.transition_type == TransitionType.FADE
        assert config.priority == 50
        assert config.enabled is True  # Default

    def test_create_config_with_optional_fields(self):
        """Create config with all optional fields."""
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1)

        config = TimeTriggerConfig(
            trigger_id="tt-002",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CROSSFADE,
            priority=70,
            enabled=False,
            scheduled_time=scheduled_time,
            duration_seconds=300,
            interval_seconds=600,
            metadata={"reason": "test"}
        )

        assert config.enabled is False
        assert config.scheduled_time == scheduled_time
        assert config.duration_seconds == 300
        assert config.interval_seconds == 600
        assert config.metadata == {"reason": "test"}


class TestTimeTrigger:
    """Test TimeTrigger class."""

    @pytest.fixture
    def scene_manager(self):
        """Create test scene manager."""
        config = SceneConfig(
            scene_id="scene-001",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        return SceneManager(config)

    @pytest.fixture
    def future_time(self):
        """Get a time in the future."""
        return datetime.now(timezone.utc) + timedelta(hours=1)

    def test_create_scheduled_trigger(self, future_time):
        """Create scheduled time trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time
        )

        trigger = TimeTrigger(config)

        assert trigger.trigger_id == "tt-001"
        assert trigger.trigger_type == TimeTriggerType.SCHEDULED
        assert trigger.state == TriggerState.ENABLED
        assert trigger.scheduled_time == future_time

    def test_create_duration_trigger(self):
        """Create duration-based trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-002",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=300
        )

        trigger = TimeTrigger(config)

        assert trigger.trigger_type == TimeTriggerType.DURATION
        assert trigger.duration_seconds == 300

    def test_create_interval_trigger(self):
        """Create interval trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-003",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CROSSFADE,
            interval_seconds=600,
            target_scene_sequence=["scene-002", "scene-003"]
        )

        trigger = TimeTrigger(config)

        assert trigger.trigger_type == TimeTriggerType.INTERVAL
        assert trigger.interval_seconds == 600
        assert trigger.target_scene_sequence == ["scene-002", "scene-003"]

    def test_evaluate_scheduled_not_ready(self, future_time):
        """Scheduled trigger not ready when time not reached."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time
        )

        trigger = TimeTrigger(config)
        result = trigger.evaluate()

        assert result is False
        assert trigger.state == TriggerState.ENABLED

    def test_evaluate_scheduled_ready(self):
        """Scheduled trigger ready when time reached."""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=1)

        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=past_time
        )

        trigger = TimeTrigger(config)
        result = trigger.evaluate()

        assert result is True
        assert trigger.state == TriggerState.ARMED

    def test_evaluate_duration_not_started(self, scene_manager):
        """Duration trigger not ready when scene not active."""
        config = TimeTriggerConfig(
            trigger_id="tt-002",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=300
        )

        trigger = TimeTrigger(config)
        result = trigger.evaluate(scene_manager)

        assert result is False
        assert trigger.state == TriggerState.ENABLED

    def test_evaluate_duration_not_elapsed(self, scene_manager):
        """Duration trigger not ready when time not elapsed."""
        # Initialize and activate scene
        scene_manager.initialize()
        scene_manager.activate()

        config = TimeTriggerConfig(
            trigger_id="tt-002",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=300
        )

        trigger = TimeTrigger(config)
        result = trigger.evaluate(scene_manager)

        assert result is False
        assert trigger.state == TriggerState.ENABLED

    def test_evaluate_duration_elapsed(self, scene_manager):
        """Duration trigger ready when time elapsed."""
        scene_manager.initialize()
        scene_manager.activate()

        # Set activated_at to past
        scene_manager._state_data["activated_at"] = (
            datetime.now(timezone.utc) - timedelta(seconds=301)
        )

        config = TimeTriggerConfig(
            trigger_id="tt-002",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=300
        )

        trigger = TimeTrigger(config)
        result = trigger.evaluate(scene_manager)

        assert result is True
        assert trigger.state == TriggerState.ARMED

    def test_arm_trigger(self, future_time):
        """Arm a trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time
        )

        trigger = TimeTrigger(config)
        trigger.arm()

        assert trigger.state == TriggerState.ARMED
        assert trigger.armed_at is not None

    def test_trigger_fire(self, future_time):
        """Fire a trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time
        )

        trigger = TimeTrigger(config)
        trigger.arm()
        trigger.fire()

        assert trigger.state == TriggerState.TRIGGERED
        assert trigger.triggered_at is not None

    def test_trigger_complete(self, future_time):
        """Complete a trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time
        )

        trigger = TimeTrigger(config)
        trigger.arm()
        trigger.fire()
        trigger.complete()

        assert trigger.state == TriggerState.COMPLETE
        assert trigger.completed_at is not None

    def test_trigger_cancel(self, future_time):
        """Cancel a trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time
        )

        trigger = TimeTrigger(config)
        trigger.cancel()

        assert trigger.state == TriggerState.CANCELLED

    def test_enable_disable_trigger(self, future_time):
        """Enable and disable a trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time,
            enabled=False
        )

        trigger = TimeTrigger(config)

        assert trigger.is_enabled() is False

        trigger.enable()
        assert trigger.is_enabled() is True

        trigger.disable()
        assert trigger.is_enabled() is False

    def test_time_until_trigger_scheduled(self, future_time):
        """Get time until scheduled trigger."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            scheduled_time=future_time
        )

        trigger = TimeTrigger(config)
        time_until = trigger.time_until()

        assert time_until is not None
        assert time_until.total_seconds() > 0
        assert time_until.total_seconds() < 3600  # Less than 1 hour

    def test_time_until_trigger_duration(self, scene_manager):
        """Get time until duration trigger."""
        scene_manager.initialize()
        scene_manager.activate()

        config = TimeTriggerConfig(
            trigger_id="tt-002",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=300
        )

        trigger = TimeTrigger(config)
        time_until = trigger.time_until(scene_manager)

        assert time_until is not None
        assert time_until.total_seconds() > 0
        assert time_until.total_seconds() <= 300


class TestTimeTriggerScheduler:
    """Test TimeTriggerScheduler class."""

    @pytest.fixture
    def scheduler(self):
        """Create trigger scheduler."""
        return TimeTriggerScheduler()

    @pytest.fixture
    def scene_manager(self):
        """Create test scene manager."""
        config = SceneConfig(
            scene_id="scene-001",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        return SceneManager(config)

    def test_scheduler_init(self, scheduler):
        """Initialize scheduler."""
        assert len(scheduler._triggers) == 0
        assert scheduler.is_running() is False

    def test_add_trigger(self, scheduler):
        """Add trigger to scheduler."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        trigger = TimeTrigger(config)
        scheduler.add_trigger(trigger)

        assert len(scheduler._triggers) == 1
        assert scheduler.get_trigger("tt-001") is trigger

    def test_add_duplicate_trigger_id(self, scheduler):
        """Cannot add duplicate trigger ID."""
        config1 = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        config2 = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-003",
            target_scene_id="scene-004",
            transition_type=TransitionType.CUT
        )

        trigger1 = TimeTrigger(config1)
        trigger2 = TimeTrigger(config2)

        scheduler.add_trigger(trigger1)

        with pytest.raises(ValueError):
            scheduler.add_trigger(trigger2)

    def test_remove_trigger(self, scheduler):
        """Remove trigger from scheduler."""
        config = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        trigger = TimeTrigger(config)
        scheduler.add_trigger(trigger)
        scheduler.remove_trigger("tt-001")

        assert len(scheduler._triggers) == 0
        assert scheduler.get_trigger("tt-001") is None

    def test_get_ready_triggers(self, scheduler):
        """Get triggers that are ready to fire."""
        # Past trigger (ready)
        past_config = TimeTriggerConfig(
            trigger_id="tt-past",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            scheduled_time=datetime.now(timezone.utc) - timedelta(seconds=1)
        )

        # Future trigger (not ready)
        future_config = TimeTriggerConfig(
            trigger_id="tt-future",
            source_scene_id="scene-001",
            target_scene_id="scene-003",
            transition_type=TransitionType.FADE,
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        scheduler.add_trigger(TimeTrigger(past_config))
        scheduler.add_trigger(TimeTrigger(future_config))

        ready = scheduler.get_ready_triggers()

        assert len(ready) == 1
        assert ready[0].trigger_id == "tt-past"

    def test_start_stop_scheduler(self, scheduler):
        """Start and stop scheduler."""
        scheduler.start()

        assert scheduler.is_running() is True

        scheduler.stop()

        assert scheduler.is_running() is False

    def test_scheduler_tick(self, scheduler):
        """Scheduler tick evaluates triggers."""
        past_config = TimeTriggerConfig(
            trigger_id="tt-past",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            scheduled_time=datetime.now(timezone.utc) - timedelta(seconds=1)
        )

        callback_called = []

        def mock_callback(trigger):
            callback_called.append(trigger.trigger_id)

        trigger = TimeTrigger(past_config)
        scheduler.add_trigger(trigger)
        scheduler.register_transition_callback(mock_callback)

        scheduler.tick()

        assert len(callback_called) == 1
        assert callback_called[0] == "tt-past"
        assert trigger.state == TriggerState.TRIGGERED

    def test_sort_triggers_by_priority(self, scheduler):
        """Triggers sorted by priority when returned."""
        config1 = TimeTriggerConfig(
            trigger_id="tt-low",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            priority=30
        )

        config2 = TimeTriggerConfig(
            trigger_id="tt-high",
            source_scene_id="scene-001",
            target_scene_id="scene-003",
            transition_type=TransitionType.FADE,
            priority=80
        )

        scheduler.add_trigger(TimeTrigger(config1))
        scheduler.add_trigger(TimeTrigger(config2))

        all_triggers = scheduler.get_all_triggers()

        # Should be sorted by priority descending
        assert all_triggers[0].trigger_id == "tt-high"
        assert all_triggers[1].trigger_id == "tt-low"

    def test_get_triggers_by_scene(self, scheduler):
        """Get triggers for specific scene."""
        config1 = TimeTriggerConfig(
            trigger_id="tt-001",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT
        )

        config2 = TimeTriggerConfig(
            trigger_id="tt-002",
            source_scene_id="scene-002",
            target_scene_id="scene-003",
            transition_type=TransitionType.FADE
        )

        scheduler.add_trigger(TimeTrigger(config1))
        scheduler.add_trigger(TimeTrigger(config2))

        scene_001_triggers = scheduler.get_triggers_for_scene("scene-001")

        assert len(scene_001_triggers) == 1
        assert scene_001_triggers[0].trigger_id == "tt-001"

    def test_register_transition_callback(self, scheduler):
        """Register transition callback."""
        callback_called = []

        def mock_callback(trigger):
            callback_called.append(True)

        scheduler.register_transition_callback(mock_callback)

        past_config = TimeTriggerConfig(
            trigger_id="tt-past",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            scheduled_time=datetime.now(timezone.utc) - timedelta(seconds=1)
        )

        scheduler.add_trigger(TimeTrigger(past_config))
        scheduler.tick()

        assert len(callback_called) == 1

    def test_cancel_lower_priority_on_same_scene(self, scheduler):
        """Lower priority triggers cancelled when higher fires."""
        config_low = TimeTriggerConfig(
            trigger_id="tt-low",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            priority=30
        )

        config_high = TimeTriggerConfig(
            trigger_id="tt-high",
            source_scene_id="scene-001",
            target_scene_id="scene-003",
            transition_type=TransitionType.FADE,
            priority=80,
            scheduled_time=datetime.now(timezone.utc) - timedelta(seconds=1)
        )

        scheduler.add_trigger(TimeTrigger(config_low))
        high_trigger = TimeTrigger(config_high)
        scheduler.add_trigger(high_trigger)

        scheduler.tick()

        # High trigger should be triggered
        assert high_trigger.state == TriggerState.TRIGGERED

        # Low trigger should be cancelled
        low_trigger = scheduler.get_trigger("tt-low")
        assert low_trigger.state == TriggerState.CANCELLED
