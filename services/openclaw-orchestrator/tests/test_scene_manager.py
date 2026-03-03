"""
Unit tests for Scene State Manager.

Tests all state transitions and validation.
"""

import pytest
import time
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, '.')

from core.scene_manager import (
    SceneManager,
    SceneState,
    SceneConfig,
    InvalidTransitionError,
    SceneValidationError,
    StateTransition,
    create_scene_from_dict,
    VALID_TRANSITIONS
)


class TestSceneState:
    """Test SceneState enum."""

    def test_state_values(self):
        """All states have correct string values."""
        assert SceneState.IDLE.value == "idle"
        assert SceneState.LOADING.value == "loading"
        assert SceneState.ACTIVE.value == "active"
        assert SceneState.PAUSED.value == "paused"
        assert SceneState.TRANSITION.value == "transition"
        assert SceneState.COMPLETED.value == "completed"
        assert SceneState.ERROR.value == "error"

    def test_terminal_states(self):
        """Terminal states identified correctly."""
        assert SceneState.COMPLETED.is_terminal
        assert not SceneState.ACTIVE.is_terminal
        assert not SceneState.ERROR.is_terminal

    def test_active_states(self):
        """Active states identified correctly."""
        assert SceneState.ACTIVE.is_active
        assert SceneState.PAUSED.is_active
        assert SceneState.TRANSITION.is_active
        assert not SceneState.LOADING.is_active
        assert not SceneState.IDLE.is_active

    def test_transitional_states(self):
        """Transitional states identified correctly."""
        assert SceneState.LOADING.is_transitional
        assert SceneState.TRANSITION.is_transitional
        assert SceneState.ERROR.is_transitional


class TestSceneConfig:
    """Test SceneConfig dataclass."""

    def test_create_from_dict(self):
        """Create SceneConfig from dictionary."""
        data = {
            "scene_id": "test-scene",
            "name": "Test Scene",
            "scene_type": "dialogue",
            "version": "1.0.0"
        }
        config = SceneConfig.from_dict(data)

        assert config.scene_id == "test-scene"
        assert config.name == "Test Scene"
        assert config.scene_type == "dialogue"
        assert config.version == "1.0.0"

    def test_create_with_full_config(self):
        """Create SceneConfig with full configuration."""
        data = {
            "scene_id": "full-scene",
            "name": "Full Scene",
            "scene_type": "monologue",
            "version": "2.0.0",
            "description": "A test scene",
            "agents": {
                "scenespeak": {"enabled": True}
            }
        }
        config = SceneConfig.from_dict(data)

        assert config.scene_id == "full-scene"
        assert config.config["description"] == "A test scene"
        assert config.config["agents"]["scenespeak"]["enabled"] is True


class TestSceneManagerInit:
    """Test SceneManager initialization."""

    def test_initial_state_is_idle(self):
        """Manager starts in IDLE state."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)

        assert manager.state == SceneState.IDLE
        assert not manager.is_active
        assert not manager.is_terminal

    def test_properties(self):
        """Manager properties are accessible."""
        config = SceneConfig(
            scene_id="scene-123",
            name="My Scene",
            scene_type="monologue",
            version="1.0.0"
        )
        manager = SceneManager(config)

        assert manager.scene_id == "scene-123"
        assert manager.config.name == "My Scene"
        assert manager.config.scene_type == "monologue"

    def test_repr(self):
        """Manager repr is informative."""
        config = SceneConfig(
            scene_id="abc",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)

        assert "abc" in repr(manager)
        assert "Test" in repr(manager)
        assert "idle" in repr(manager)


class TestStateTransitions:
    """Test state transitions."""

    @pytest.fixture
    def manager(self):
        """Create a manager for testing."""
        config = SceneConfig(
            scene_id="test-scene",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        return SceneManager(config)

    def test_idle_to_loading(self, manager):
        """IDLE -> LOADING transition."""
        assert manager.state == SceneState.IDLE

        manager.initialize()
        assert manager.state == SceneState.LOADING

    def test_loading_to_active(self, manager):
        """LOADING -> ACTIVE transition."""
        manager.initialize()
        assert manager.state == SceneState.LOADING

        manager.activate()
        assert manager.state == SceneState.ACTIVE

    def test_active_to_paused(self, manager):
        """ACTIVE -> PAUSED transition."""
        manager.initialize()
        manager.activate()

        manager.pause("user requested")
        assert manager.state == SceneState.PAUSED

    def test_paused_to_active(self, manager):
        """PAUSED -> ACTIVE transition."""
        manager.initialize()
        manager.activate()
        manager.pause()

        manager.resume()
        assert manager.state == SceneState.ACTIVE

    def test_active_to_transition(self, manager):
        """ACTIVE -> TRANSITION transition."""
        manager.initialize()
        manager.activate()

        manager.begin_transition("next-scene", "fade")
        assert manager.state == SceneState.TRANSITION

    def test_active_to_completed(self, manager):
        """ACTIVE -> COMPLETED transition."""
        manager.initialize()
        manager.activate()

        manager.complete("natural")
        assert manager.state == SceneState.COMPLETED

    def test_paused_to_completed(self, manager):
        """PAUSED -> COMPLETED transition."""
        manager.initialize()
        manager.activate()
        manager.pause()

        manager.complete("manual")
        assert manager.state == SceneState.COMPLETED

    def test_active_to_error(self, manager):
        """ACTIVE -> ERROR transition."""
        manager.initialize()
        manager.activate()

        manager.error("E001", "Something went wrong", recoverable=True)
        assert manager.state == SceneState.ERROR

    def test_loading_to_error(self, manager):
        """LOADING -> ERROR transition."""
        manager.initialize()

        manager.error("E002", "Load failed", recoverable=True)
        assert manager.state == SceneState.ERROR

    def test_error_to_loading(self, manager):
        """ERROR -> LOADING transition (recovery)."""
        manager.initialize()
        manager.error("E001", "Recoverable error", recoverable=True)

        manager.recover()
        assert manager.state == SceneState.LOADING

    def test_error_to_completed(self, manager):
        """ERROR -> COMPLETED transition (unrecoverable)."""
        manager.initialize()
        manager.error("E999", "Fatal error", recoverable=False)

        manager.complete("error_recovery")
        assert manager.state == SceneState.COMPLETED

    def test_invalid_transition_raises_error(self, manager):
        """Invalid transitions raise InvalidTransitionError."""
        manager.initialize()
        manager.activate()

        # Can't go from ACTIVE to LOADING
        with pytest.raises(InvalidTransitionError):
            manager._validate_transition(SceneState.LOADING)

    def test_cannot_transition_from_completed(self, manager):
        """COMPLETED is a terminal state."""
        manager.initialize()
        manager.activate()
        manager.complete()

        # Can't transition from COMPLETED
        with pytest.raises(InvalidTransitionError):
            manager.pause()


class TestStateValidation:
    """Test state transition validation."""

    @pytest.fixture
    def manager(self):
        """Create a manager for testing."""
        config = SceneConfig(
            scene_id="test-scene",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        return SceneManager(config)

    def test_can_transition_to_valid_states(self, manager):
        """can_transition_to returns True for valid transitions."""
        assert manager.can_transition_to(SceneState.LOADING)
        assert not manager.can_transition_to(SceneState.ACTIVE)

    def test_all_valid_transitions_defined(self):
        """All valid transitions are defined."""
        # Each state should have at most 5 valid transitions
        for state, valid_targets in VALID_TRANSITIONS.items():
            assert len(valid_targets) <= 5

    def test_transition_metadata(self, manager):
        """Transition metadata is preserved."""
        manager.initialize()
        manager.activate()

        manager.pause("testing metadata")

        history = manager.get_transition_history()
        pause_transition = [t for t in history if t.to_state == SceneState.PAUSED][0]
        assert pause_transition.metadata["reason"] == "testing metadata"


class TestTransitionHistory:
    """Test transition history tracking."""

    @pytest.fixture
    def manager(self):
        """Create a manager for testing."""
        config = SceneConfig(
            scene_id="test-scene",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        return SceneManager(config)

    def test_transitions_recorded(self, manager):
        """All transitions are recorded."""
        manager.initialize()
        manager.activate()
        manager.pause()
        manager.resume()

        history = manager.get_transition_history()
        assert len(history) == 4

    def test_transition_order(self, manager):
        """Transitions are in chronological order."""
        manager.initialize()
        manager.activate()

        history = manager.get_transition_history()
        assert history[0].from_state == SceneState.IDLE
        assert history[0].to_state == SceneState.LOADING
        assert history[1].from_state == SceneState.LOADING
        assert history[1].to_state == SceneState.ACTIVE

    def test_transition_timestamp(self, manager):
        """Transitions have timestamps."""
        manager.initialize()

        history = manager.get_transition_history()
        assert isinstance(history[0].timestamp, datetime)

    def test_transition_trigger(self, manager):
        """Transitions record trigger."""
        manager.initialize()

        history = manager.get_transition_history()
        assert history[0].trigger == "initialize"


class TestStateData:
    """Test state-specific data."""

    @pytest.fixture
    def manager(self):
        """Create a manager for testing."""
        config = SceneConfig(
            scene_id="test-scene",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        return SceneManager(config)

    def test_default_state_data(self, manager):
        """Default state data is set."""
        assert "created_at" in manager._state_data
        assert manager._state_data["activated_at"] is None

    def test_activated_at_set_on_activate(self, manager):
        """activated_at is set when scene becomes active."""
        manager.initialize()
        manager.activate()

        assert manager._state_data["activated_at"] is not None

    def test_paused_at_set_on_pause(self, manager):
        """paused_at is set when scene is paused."""
        manager.initialize()
        manager.activate()
        manager.pause()

        assert manager._state_data["paused_at"] is not None

    def test_error_data_set(self, manager):
        """Error data is stored."""
        manager.initialize()
        manager.error("E001", "Test error", recoverable=True)

        error = manager._state_data["error"]
        assert error["code"] == "E001"
        assert error["message"] == "Test error"
        assert error["recoverable"] is True

    def test_retry_count_increments_on_recover(self, manager):
        """Retry count increments on recovery."""
        manager.initialize()
        manager.error("E001", "Error", recoverable=True)

        assert manager._state_data["retry_count"] == 0

        manager.recover()
        assert manager._state_data["retry_count"] == 1

    def test_get_set_state_data(self, manager):
        """Can get and set custom state data."""
        manager.set_state_data("custom_key", "custom_value")

        assert manager.get_state_data("custom_key") == "custom_value"
        assert manager.get_state_data("missing", "default") == "default"


class TestCallbacks:
    """Test state and transition callbacks."""

    @pytest.fixture
    def manager(self):
        """Create a manager for testing."""
        config = SceneConfig(
            scene_id="test-scene",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        return SceneManager(config)

    def test_state_callback(self, manager):
        """State callback is invoked when state is entered."""
        called = []

        def callback(mgr):
            called.append(mgr.state)

        manager.register_callback(SceneState.ACTIVE, callback)
        manager.initialize()
        manager.activate()

        assert SceneState.ACTIVE in called

    def test_transition_callback(self, manager):
        """Transition callback is invoked for all transitions."""
        transitions = []

        def callback(transition):
            transitions.append(transition)

        manager.register_transition_callback(callback)
        manager.initialize()

        assert len(transitions) == 1
        assert transitions[0].from_state == SceneState.IDLE
        assert transitions[0].to_state == SceneState.LOADING

    def test_multiple_callbacks(self, manager):
        """Multiple callbacks can be registered."""
        count = [0]

        def callback1(_):
            count[0] += 1

        def callback2(_):
            count[0] += 1

        manager.register_callback(SceneState.ACTIVE, callback1)
        manager.register_callback(SceneState.ACTIVE, callback2)
        manager.initialize()
        manager.activate()

        assert count[0] == 2


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config_passes(self):
        """Valid configuration passes validation."""
        data = {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "dialogue",
            "version": "1.0.0"
        }
        manager = create_scene_from_dict(data)
        manager.initialize()  # Triggers validation

        assert manager.state == SceneState.LOADING

    def test_missing_scene_id_fails(self):
        """Missing scene_id fails validation."""
        data = {
            "name": "Test",
            "scene_type": "dialogue",
            "version": "1.0.0"
        }

        with pytest.raises(SceneValidationError):
            SceneConfig.from_dict(data)

    def test_invalid_scene_type_fails(self):
        """Invalid scene_type fails validation."""
        data = {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "invalid_type",
            "version": "1.0.0"
        }
        manager = create_scene_from_dict(data)

        with pytest.raises(SceneValidationError):
            manager.initialize()

    def test_valid_scene_types(self):
        """All valid scene types pass."""
        valid_types = ["monologue", "dialogue", "interactive",
                      "transition", "finale", "intermission"]

        for scene_type in valid_types:
            data = {
                "scene_id": f"test-{scene_type}",
                "name": "Test",
                "scene_type": scene_type,
                "version": "1.0.0"
            }
            manager = create_scene_from_dict(data)
            manager.initialize()  # Should not raise

            assert manager.state == SceneState.LOADING


class TestThreadSafety:
    """Test thread-safe operations."""

    def test_concurrent_state_reads(self):
        """Multiple threads can read state safely."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)

        states = []
        def read_state():
            for _ in range(100):
                states.append(manager.state)

        import threading
        threads = [threading.Thread(target=read_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(states) == 500
        assert all(s == SceneState.IDLE for s in states)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_scene_from_dict(self):
        """Create manager from dictionary."""
        data = {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "dialogue",
            "version": "1.0.0"
        }
        manager = create_scene_from_dict(data)

        assert manager.scene_id == "test"
        assert manager.state == SceneState.IDLE

    def test_create_scene_from_dict_with_full_config(self):
        """Create manager with full configuration."""
        data = {
            "scene_id": "full",
            "name": "Full Scene",
            "scene_type": "monologue",
            "version": "2.0.0",
            "description": "Test scene",
            "metadata": {"author": "Test Author"},
            "timing": {
                "min_duration": 60,
                "max_duration": 300
            }
        }
        manager = create_scene_from_dict(data)

        assert manager.config.config["description"] == "Test scene"
        assert manager.config.config["metadata"]["author"] == "Test Author"
        assert manager.config.config["timing"]["min_duration"] == 60
