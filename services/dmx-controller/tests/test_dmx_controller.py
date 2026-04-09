#!/usr/bin/env python3
"""
DMX Controller Service Tests

Test suite for DMX512 lighting controller functionality.
"""

import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dmx_controller import (
    DMXController,
    DMXState,
    DMXChannel,
    Fixture,
    Scene
)


class TestDMXChannel:
    """Test DMX channel validation and functionality."""

    def test_valid_channel_value(self):
        """Test creating channel with valid value."""
        channel = DMXChannel(channel=1, value=128, label="intensity")
        assert channel.channel == 1
        assert channel.value == 128
        assert channel.label == "intensity"

    def test_minimum_value(self):
        """Test channel with minimum value (0)."""
        channel = DMXChannel(channel=1, value=0)
        assert channel.value == 0

    def test_maximum_value(self):
        """Test channel with maximum value (255)."""
        channel = DMXChannel(channel=1, value=255)
        assert channel.value == 255

    def test_invalid_value_too_high(self):
        """Test that value > 255 raises ValueError."""
        with pytest.raises(ValueError, match="Channel value must be 0-255"):
            DMXChannel(channel=1, value=256)

    def test_invalid_value_negative(self):
        """Test that negative value raises ValueError."""
        with pytest.raises(ValueError, match="Channel value must be 0-255"):
            DMXChannel(channel=1, value=-1)

    def test_invalid_value_too_low(self):
        """Test that value < 0 raises ValueError."""
        with pytest.raises(ValueError, match="Channel value must be 0-255"):
            DMXChannel(channel=1, value=-10)


class TestFixture:
    """Test fixture creation and management."""

    def test_create_valid_fixture(self):
        """Test creating a valid fixture."""
        channels = {
            1: DMXChannel(1, 0, "intensity"),
            2: DMXChannel(2, 0, "pan"),
            3: DMXChannel(3, 0, "tilt")
        }
        fixture = Fixture(
            id="mh_1",
            name="Moving Head 1",
            start_address=1,
            channel_count=3,
            channels=channels
        )
        assert fixture.id == "mh_1"
        assert fixture.name == "Moving Head 1"
        assert fixture.start_address == 1
        assert fixture.channel_count == 3
        assert len(fixture.channels) == 3

    def test_invalid_channel_count_mismatch(self):
        """Test that mismatched channel count raises ValueError."""
        channels = {
            1: DMXChannel(1, 0, "intensity"),
            2: DMXChannel(2, 0, "pan")
        }
        with pytest.raises(ValueError, match="Channel count mismatch"):
            Fixture(
                id="test",
                name="Test Fixture",
                start_address=1,
                channel_count=3,  # Claims 3 channels
                channels=channels  # Only provides 2
            )

    def test_set_channel_value(self):
        """Test setting a channel value on a fixture."""
        channels = {
            1: DMXChannel(1, 0, "intensity")
        }
        fixture = Fixture(
            id="test",
            name="Test",
            start_address=1,
            channel_count=1,
            channels=channels
        )
        fixture.set_channel(1, 255)
        assert fixture.channels[1].value == 255

    def test_set_invalid_channel(self):
        """Test setting non-existent channel raises ValueError."""
        channels = {1: DMXChannel(1, 0, "intensity")}
        fixture = Fixture(
            id="test",
            name="Test",
            start_address=1,
            channel_count=1,
            channels=channels
        )
        with pytest.raises(ValueError, match="Channel 2 not found"):
            fixture.set_channel(2, 128)


class TestScene:
    """Test scene creation and validation."""

    def test_create_valid_scene(self):
        """Test creating a valid lighting scene."""
        scene = Scene(
            name="happy_scene",
            fixtures={
                "mh_1": {1: 255, 2: 128}
            },
            transition_time_ms=1000
        )
        assert scene.name == "happy_scene"
        assert len(scene.fixtures) == 1
        assert scene.transition_time_ms == 1000

    def test_default_transition_time(self):
        """Test scene with default transition time."""
        scene = Scene(
            name="test",
            fixtures={}
        )
        assert scene.transition_time_ms == 1000  # Default value

    def test_negative_transition_time(self):
        """Test that negative transition time raises ValueError."""
        with pytest.raises(ValueError, match="Transition time must be non-negative"):
            Scene(
                name="test",
                fixtures={},
                transition_time_ms=-100
            )

    def test_zero_transition_time(self):
        """Test that zero transition time is valid."""
        scene = Scene(
            name="instant",
            fixtures={},
            transition_time_ms=0
        )
        assert scene.transition_time_ms == 0


class TestDMXController:
    """Test DMX controller functionality."""

    @pytest.fixture
    def controller(self):
        """Create a DMX controller for testing."""
        return DMXController(universe=1, refresh_rate=44)

    @pytest.fixture
    def sample_fixture(self):
        """Create a sample fixture for testing."""
        channels = {
            1: DMXChannel(1, 0, "intensity"),
            2: DMXChannel(2, 0, "pan"),
            3: DMXChannel(3, 0, "tilt"),
            4: DMXChannel(4, 0, "color_red"),
            5: DMXChannel(5, 0, "color_green"),
            6: DMXChannel(6, 0, "color_blue")
        }
        return Fixture(
            id="mh_1",
            name="Moving Head 1",
            start_address=1,
            channel_count=6,
            channels=channels
        )

    def test_controller_initialization(self, controller):
        """Test controller initializes with correct values."""
        assert controller.universe == 1
        assert controller.refresh_rate == 44
        assert controller.state == DMXState.IDLE
        assert len(controller.fixtures) == 0
        assert len(controller.scenes) == 0

    def test_invalid_universe_too_low(self):
        """Test that universe < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Universe must be 1-512"):
            DMXController(universe=0)

    def test_invalid_universe_too_high(self):
        """Test that universe > 512 raises ValueError."""
        with pytest.raises(ValueError, match="Universe must be 1-512"):
            DMXController(universe=513)

    def test_add_fixture(self, controller, sample_fixture):
        """Test adding a fixture to controller."""
        controller.add_fixture(sample_fixture)
        assert "mh_1" in controller.fixtures
        assert controller.fixtures["mh_1"].name == "Moving Head 1"

    def test_remove_fixture(self, controller, sample_fixture):
        """Test removing a fixture from controller."""
        controller.add_fixture(sample_fixture)
        controller.remove_fixture("mh_1")
        assert "mh_1" not in controller.fixtures

    def test_remove_nonexistent_fixture(self, controller):
        """Test removing non-existent fixture doesn't raise error."""
        # Should not raise exception
        controller.remove_fixture("nonexistent")

    def test_set_fixture_channel(self, controller, sample_fixture):
        """Test setting a single fixture channel."""
        controller.add_fixture(sample_fixture)
        controller.set_fixture_channel("mh_1", 1, 255)
        assert controller.fixtures["mh_1"].channels[1].value == 255

    def test_set_fixture_channel_invalid_fixture(self, controller):
        """Test setting channel on non-existent fixture raises ValueError."""
        with pytest.raises(ValueError, match="Fixture nonexistent not found"):
            controller.set_fixture_channel("nonexistent", 1, 128)

    def test_set_fixture_channels_multiple(self, controller, sample_fixture):
        """Test setting multiple fixture channels at once."""
        controller.add_fixture(sample_fixture)
        controller.set_fixture_channels("mh_1", {
            1: 255,
            2: 128,
            3: 64
        })
        assert controller.fixtures["mh_1"].channels[1].value == 255
        assert controller.fixtures["mh_1"].channels[2].value == 128
        assert controller.fixtures["mh_1"].channels[3].value == 64

    def test_create_scene(self, controller, sample_fixture):
        """Test creating a lighting scene."""
        controller.add_fixture(sample_fixture)
        scene = controller.create_scene(
            name="test_scene",
            fixture_values={
                "mh_1": {1: 255, 2: 128}
            },
            transition_time_ms=2000
        )
        assert "test_scene" in controller.scenes
        assert controller.scenes["test_scene"].transition_time_ms == 2000

    def test_activate_scene(self, controller, sample_fixture):
        """Test activating a lighting scene."""
        controller.add_fixture(sample_fixture)
        controller.create_scene(
            name="test_scene",
            fixture_values={
                "mh_1": {1: 255, 4: 200}
            }
        )
        controller.activate_scene("test_scene")
        assert controller.current_scene == "test_scene"
        assert controller.fixtures["mh_1"].channels[1].value == 255
        assert controller.fixtures["mh_1"].channels[4].value == 200

    def test_activate_nonexistent_scene(self, controller):
        """Test activating non-existent scene raises ValueError."""
        with pytest.raises(ValueError, match="Scene nonexistent not found"):
            controller.activate_scene("nonexistent")

    def test_get_fixture_state(self, controller, sample_fixture):
        """Test getting current fixture state."""
        controller.add_fixture(sample_fixture)
        controller.set_fixture_channel("mh_1", 1, 128)
        state = controller.get_fixture_state("mh_1")
        assert state[1] == 128

    def test_get_nonexistent_fixture_state(self, controller):
        """Test getting state of non-existent fixture raises ValueError."""
        with pytest.raises(ValueError, match="Fixture nonexistent not found"):
            controller.get_fixture_state("nonexistent")

    def test_get_all_fixtures_state(self, controller, sample_fixture):
        """Test getting state of all fixtures."""
        controller.add_fixture(sample_fixture)
        controller.set_fixture_channel("mh_1", 1, 200)
        all_states = controller.get_all_fixtures_state()
        assert "mh_1" in all_states
        assert all_states["mh_1"][1] == 200

    def test_emergency_stop(self, controller, sample_fixture):
        """Test emergency stop functionality."""
        controller.add_fixture(sample_fixture)
        controller.set_fixture_channel("mh_1", 1, 255)
        controller.set_fixture_channel("mh_1", 2, 128)

        controller.emergency_stop()

        # All channels should be set to 0
        assert controller.state == DMXState.EMERGENCY_STOP
        for channel in controller.fixtures["mh_1"].channels.values():
            assert channel.value == 0
        assert controller.current_scene is None

    def test_reset_from_emergency(self, controller, sample_fixture):
        """Test resetting from emergency stop state."""
        controller.add_fixture(sample_fixture)
        controller.emergency_stop()
        assert controller.state == DMXState.EMERGENCY_STOP

        controller.reset_from_emergency()
        assert controller.state == DMXState.IDLE

    def test_reset_when_not_in_emergency(self, controller):
        """Test that reset when not in emergency doesn't change state."""
        controller.state = DMXState.IDLE
        controller.reset_from_emergency()
        # State should remain IDLE (with warning logged)
        assert controller.state == DMXState.IDLE

    def test_command_blocked_in_emergency_stop(self, controller, sample_fixture):
        """Test that commands are blocked during emergency stop."""
        controller.add_fixture(sample_fixture)
        controller.emergency_stop()

        with pytest.raises(RuntimeError, match="System in emergency stop state"):
            controller.set_fixture_channel("mh_1", 1, 128)

    def test_get_status(self, controller, sample_fixture):
        """Test getting controller status."""
        controller.add_fixture(sample_fixture)
        controller.create_scene("test", {"mh_1": {1: 255}})
        controller.activate_scene("test")

        status = controller.get_status()
        assert status["universe"] == 1
        assert status["state"] == "active"
        assert status["refresh_rate"] == 44
        assert status["fixture_count"] == 1
        assert status["scene_count"] == 1
        assert status["current_scene"] == "test"

    def test_emergency_stop_callback(self, controller):
        """Test emergency stop callback is called."""
        callback_called = []

        def test_callback():
            callback_called.append(True)

        controller.set_emergency_stop_callback(test_callback)
        controller.emergency_stop()

        assert len(callback_called) == 1


@pytest.mark.integration
class TestDMXControllerIntegration:
    """Integration tests for DMX controller."""

    def test_full_lighting_sequence(self):
        """Test a complete lighting sequence."""
        controller = DMXController(universe=1)

        # Create fixture
        channels = {
            1: DMXChannel(1, 0, "intensity"),
            2: DMXChannel(2, 0, "color_red"),
            3: DMXChannel(3, 0, "color_green"),
            4: DMXChannel(4, 0, "color_blue")
        }
        fixture = Fixture(
            id="par_1",
            name="PAR Can 1",
            start_address=1,
            channel_count=4,
            channels=channels
        )
        controller.add_fixture(fixture)

        # Create scenes
        controller.create_scene("red", {"par_1": {1: 255, 2: 255}}, 1000)
        controller.create_scene("blue", {"par_1": {1: 255, 4: 255}}, 1000)
        controller.create_scene("off", {"par_1": {1: 0}}, 500)

        # Test scene transitions
        controller.activate_scene("red")
        assert controller.fixtures["par_1"].channels[2].value == 255

        controller.activate_scene("blue")
        assert controller.fixtures["par_1"].channels[4].value == 255

        controller.activate_scene("off")
        assert controller.fixtures["par_1"].channels[1].value == 0

        # Test emergency stop
        controller.activate_scene("red")
        controller.emergency_stop()
        assert all(ch.value == 0 for ch in fixture.channels.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
