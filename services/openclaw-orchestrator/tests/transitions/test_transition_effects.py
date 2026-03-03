"""
Unit tests for Transition Effects.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio

import sys
sys.path.insert(0, '.')

from core.scene_manager import SceneManager, SceneConfig, SceneState
from transitions.transition_effects import (
    TransitionType,
    TransitionEffect,
    TransitionEffectConfig,
    TransitionEffectExecutor,
    EffectState
)


class TestTransitionType:
    """Test TransitionType enum."""

    def test_transition_types(self):
        """All transition types exist."""
        assert TransitionType.CUT
        assert TransitionType.FADE
        assert TransitionType.CROSSFADE


class TestEffectState:
    """Test EffectState enum."""

    def test_effect_states(self):
        """All effect states exist."""
        assert EffectState.PENDING
        assert EffectState.RUNNING
        assert EffectState.COMPLETE
        assert EffectState.FAILED
        assert EffectState.CANCELLED


class TestTransitionEffectConfig:
    """Test TransitionEffectConfig dataclass."""

    def test_create_config(self):
        """Create effect configuration."""
        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=3.0
        )

        assert config.source_scene_id == "scene-001"
        assert config.target_scene_id == "scene-002"
        assert config.transition_type == TransitionType.FADE
        assert config.duration_seconds == 3.0

    def test_create_config_with_optional_fields(self):
        """Create config with all optional fields."""
        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CROSSFADE,
            duration_seconds=5.0,
            metadata={"urgency": "high"}
        )

        assert config.duration_seconds == 5.0
        assert config.metadata == {"urgency": "high"}


class TestTransitionEffect:
    """Test TransitionEffect class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=3.0
        )

    def test_create_effect(self, config):
        """Create transition effect."""
        effect = TransitionEffect(config)

        assert effect.effect_id is not None
        assert effect.effect_id.startswith("te-")
        assert effect.state == EffectState.PENDING
        assert effect.transition_type == TransitionType.FADE

    def test_get_duration(self, config):
        """Get effect duration."""
        effect = TransitionEffect(config)

        assert effect.get_duration() == 3.0

    def test_get_progress_initial(self, config):
        """Get progress before start."""
        effect = TransitionEffect(config)

        assert effect.get_progress() == 0.0

    def test_start_effect(self, config):
        """Start effect execution."""
        effect = TransitionEffect(config)
        effect.start()

        assert effect.state == EffectState.RUNNING
        assert effect.started_at is not None

    def test_complete_effect(self, config):
        """Complete effect."""
        effect = TransitionEffect(config)
        effect.start()
        effect.complete()

        assert effect.state == EffectState.COMPLETE
        assert effect.completed_at is not None

    def test_fail_effect(self, config):
        """Fail effect."""
        effect = TransitionEffect(config)
        effect.start()
        effect.fail("Test failure")

        assert effect.state == EffectState.FAILED
        assert effect.error_message == "Test failure"

    def test_cancel_effect(self, config):
        """Cancel effect."""
        effect = TransitionEffect(config)
        effect.start()
        effect.cancel("Cancelled by operator")

        assert effect.state == EffectState.CANCELLED
        assert effect.cancellation_reason == "Cancelled by operator"

    def test_update_progress(self, config):
        """Update effect progress."""
        effect = TransitionEffect(config)
        effect.start()
        effect.update_progress(50.0)

        assert effect.get_progress() == 50.0

    def test_update_progress_clamped(self, config):
        """Progress is clamped between 0 and 100."""
        effect = TransitionEffect(config)
        effect.start()
        effect.update_progress(150.0)

        assert effect.get_progress() == 100.0

    def test_is_complete(self, config):
        """Check if effect is complete."""
        effect = TransitionEffect(config)

        assert effect.is_complete() is False

        effect.start()
        effect.update_progress(100.0)  # This auto-completes

        assert effect.is_complete() is True


class TestTransitionEffectExecutor:
    """Test TransitionEffectExecutor."""

    @pytest.fixture
    def executor(self):
        """Create effect executor."""
        return TransitionEffectExecutor()

    @pytest.fixture
    def scene_manager_factory(self):
        """Create scene managers."""
        def create_manager(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            manager.activate()
            return manager
        return create_manager

    def test_executor_init(self, executor):
        """Initialize executor."""
        assert len(executor._active_effects) == 0
        assert len(executor._completed_effects) == 0

    def test_execute_cut_transition(self, executor, scene_manager_factory):
        """Execute CUT transition (immediate)."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=0.1  # 100ms
        )

        effect_id = executor.execute_transition(
            config,
            source_manager,
            target_manager
        )

        assert effect_id is not None
        assert effect_id.startswith("te-")

        effect = executor.get_effect(effect_id)
        assert effect is not None
        assert effect.state == EffectState.COMPLETE

    def test_execute_fade_transition(self, executor, scene_manager_factory):
        """Execute FADE transition."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=2.5
        )

        effect_id = executor.execute_transition(
            config,
            source_manager,
            target_manager
        )

        effect = executor.get_effect(effect_id)

        # Should be running initially
        assert effect.state == EffectState.RUNNING

        # Complete the effect
        effect.complete()

        assert effect.state == EffectState.COMPLETE

    def test_execute_crossfade_transition(self, executor, scene_manager_factory):
        """Execute CROSSFADE transition."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CROSSFADE,
            duration_seconds=4.0
        )

        effect_id = executor.execute_transition(
            config,
            source_manager,
            target_manager
        )

        effect = executor.get_effect(effect_id)
        assert effect.state == EffectState.RUNNING

    def test_get_active_effects(self, executor, scene_manager_factory):
        """Get all active effects."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=3.0
        )

        executor.execute_transition(config, source_manager, target_manager)

        active = executor.get_active_effects()

        assert len(active) == 1
        assert active[0].state == EffectState.RUNNING

    def test_cancel_effect(self, executor, scene_manager_factory):
        """Cancel an active effect."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=3.0
        )

        effect_id = executor.execute_transition(config, source_manager, target_manager)

        cancelled = executor.cancel_effect(effect_id, "Test cancellation")

        assert cancelled is True

        effect = executor.get_effect(effect_id)
        assert effect.state == EffectState.CANCELLED

    def test_get_effect_status(self, executor, scene_manager_factory):
        """Get effect status."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=3.0
        )

        effect_id = executor.execute_transition(config, source_manager, target_manager)

        status = executor.get_effect_status(effect_id)

        assert status["effect_id"] == effect_id
        assert status["state"] == "running"
        assert status["progress"] >= 0

    def test_cleanup_old_effects(self, executor, scene_manager_factory):
        """Cleanup old completed effects."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=0.1
        )

        executor.execute_transition(config, source_manager, target_manager)

        # Wait for effect to complete
        import time
        time.sleep(0.2)

        # Cleanup
        cleaned = executor.cleanup_old_effects(max_age_seconds=0)

        assert cleaned >= 1

    def test_concurrent_effects_limit(self, executor, scene_manager_factory):
        """Test limit on concurrent effects."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=3.0
        )

        # Execute max concurrent effects
        for i in range(executor.MAX_CONCURRENT_EFFECTS):
            executor.execute_transition(config, source_manager, target_manager)

        # Try to exceed limit
        with pytest.raises(RuntimeError):
            executor.execute_transition(config, source_manager, target_manager)

    def test_update_progress_during_execution(self, executor, scene_manager_factory):
        """Test progress updates during execution."""
        source_manager = scene_manager_factory("scene-001")
        target_manager = scene_manager_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=2.0
        )

        effect_id = executor.execute_transition(config, source_manager, target_manager)
        effect = executor.get_effect(effect_id)

        # Simulate progress updates
        executor.update_progress(effect_id, 25.0)
        assert effect.get_progress() == 25.0

        executor.update_progress(effect_id, 50.0)
        assert effect.get_progress() == 50.0

        executor.update_progress(effect_id, 100.0)
        assert effect.get_progress() == 100.0

        # Auto-complete when progress reaches 100
        assert effect.state == EffectState.COMPLETE
