#!/usr/bin/env python3
"""
DMX Lighting Controller Service
Project Chimera Phase 2 - Hardware Integration Layer

This service provides DMX512 lighting control for live theatrical performances.
It implements safe DMX control with emergency stop functionality.

Author: Project Chimera Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Distributed tracing (optional)
try:
    from monitoring.distributed_tracing.tracer import get_dmx_tracer
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    logger.warning("Distributed tracing not available")


class DMXState(Enum):
    """DMX system states."""
    IDLE = "idle"
    ACTIVE = "active"
    EMERGENCY_STOP = "emergency_stop"
    FAULT = "fault"


@dataclass
class DMXChannel:
    """Represents a single DMX channel."""
    channel: int
    value: int
    label: str = ""

    def __post_init__(self):
        """Validate channel value."""
        if not 0 <= self.value <= 255:
            raise ValueError(f"Channel value must be 0-255, got {self.value}")


@dataclass
class Fixture:
    """Represents a DMX lighting fixture."""
    id: str
    name: str
    start_address: int
    channel_count: int
    channels: Dict[int, DMXChannel]

    def __post_init__(self):
        """Validate fixture configuration."""
        if self.channel_count != len(self.channels):
            raise ValueError(f"Channel count mismatch: expected {self.channel_count}, got {len(self.channels)}")

    def set_channel(self, channel: int, value: int) -> None:
        """Set a channel value."""
        if channel not in self.channels:
            raise ValueError(f"Channel {channel} not found in fixture {self.id}")
        self.channels[channel].value = value


@dataclass
class Scene:
    """Represents a lighting scene."""
    name: str
    fixtures: Dict[str, Dict[int, int]]  # fixture_id -> {channel: value}
    transition_time_ms: int = 1000

    def __post_init__(self):
        """Validate scene configuration."""
        if self.transition_time_ms < 0:
            raise ValueError("Transition time must be non-negative")


class DMXController:
    """
    DMX512 Lighting Controller

    Manages DMX fixtures and provides safe lighting control
    with emergency stop functionality.
    """

    def __init__(self, universe: int = 1, refresh_rate: int = 44):
        """
        Initialize DMX controller.

        Args:
            universe: DMX universe number (1-512)
            refresh_rate: Refresh rate in Hz (default: 44)
        """
        if not 1 <= universe <= 512:
            raise ValueError(f"Universe must be 1-512, got {universe}")

        self.universe = universe
        self.refresh_rate = refresh_rate
        self.state = DMXState.IDLE

        self.fixtures: Dict[str, Fixture] = {}
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[str] = None

        self._emergency_stop_callback = None
        self._last_update_time = None

        # Initialize distributed tracing
        self._tracer = get_dmx_tracer() if TRACING_AVAILABLE else None

        logger.info(f"DMX Controller initialized: Universe {self.universe}, {self.refresh_rate}Hz")

    def add_fixture(self, fixture: Fixture) -> None:
        """
        Add a fixture to the controller.

        Args:
            fixture: Fixture to add
        """
        self.fixtures[fixture.id] = fixture
        logger.info(f"Fixture added: {fixture.id} ({fixture.name}) at address {fixture.start_address}")

    def remove_fixture(self, fixture_id: str) -> None:
        """
        Remove a fixture from the controller.

        Args:
            fixture_id: ID of fixture to remove
        """
        if fixture_id in self.fixtures:
            del self.fixtures[fixture_id]
            logger.info(f"Fixture removed: {fixture_id}")

    def set_fixture_channel(self, fixture_id: str, channel: int, value: int) -> None:
        """
        Set a single fixture channel value.

        Args:
            fixture_id: Fixture ID
            channel: Channel number (relative to fixture)
            value: Channel value (0-255)
        """
        self._check_emergency_stop()

        if fixture_id not in self.fixtures:
            raise ValueError(f"Fixture {fixture_id} not found")

        fixture = self.fixtures[fixture_id]
        fixture.set_channel(channel, value)

        self._last_update_time = datetime.now()
        logger.debug(f"Fixture {fixture_id} channel {channel} set to {value}")

    def set_fixture_channels(self, fixture_id: str, channels: Dict[int, int]) -> None:
        """
        Set multiple fixture channel values.

        Args:
            fixture_id: Fixture ID
            channels: Dictionary of channel: value pairs
        """
        if self._tracer:
            ctx = self._tracer.trace_operation("set_fixture_channels")
            ctx.__enter__()
            try:
                self._set_fixture_channels_impl(fixture_id, channels)
            finally:
                ctx.__exit__(None, None, None)
        else:
            self._set_fixture_channels_impl(fixture_id, channels)

    def _set_fixture_channels_impl(self, fixture_id: str, channels: Dict[int, int]) -> None:
        """Internal implementation of set_fixture_channels."""
        self._check_emergency_stop()

        if fixture_id not in self.fixtures:
            raise ValueError(f"Fixture {fixture_id} not found")

        fixture = self.fixtures[fixture_id]
        for channel, value in channels.items():
            fixture.set_channel(channel, value)

        self._last_update_time = datetime.now()

        # Add tracing attributes
        if self._tracer:
            self._tracer.add_span_attributes({
                "fixture_id": fixture_id,
                "channel_count": len(channels),
                "universe": self.universe
            })

        logger.info(f"Fixture {fixture_id} {len(channels)} channels set")

    def create_scene(self, name: str, fixture_values: Dict[str, Dict[int, int]],
                     transition_time_ms: int = 1000) -> Scene:
        """
        Create a lighting scene.

        Args:
            name: Scene name
            fixture_values: Dictionary of fixture_id -> {channel: value}
            transition_time_ms: Transition time in milliseconds

        Returns:
            Created Scene object
        """
        scene = Scene(name=name, fixtures=fixture_values, transition_time_ms=transition_time_ms)
        self.scenes[name] = scene
        logger.info(f"Scene created: {name} with {len(fixture_values)} fixtures")
        return scene

    def activate_scene(self, scene_name: str) -> None:
        """
        Activate a lighting scene.

        Args:
            scene_name: Name of scene to activate
        """
        if self._tracer:
            ctx = self._tracer.trace_operation("activate_scene")
            ctx.__enter__()
            try:
                self._activate_scene_impl(scene_name)
            finally:
                ctx.__exit__(None, None, None)
        else:
            self._activate_scene_impl(scene_name)

    def _activate_scene_impl(self, scene_name: str) -> None:
        """Internal implementation of activate_scene."""
        self._check_emergency_stop()

        if scene_name not in self.scenes:
            raise ValueError(f"Scene {scene_name} not found")

        scene = self.scenes[scene_name]

        # Apply scene values to all fixtures
        for fixture_id, channels in scene.fixtures.items():
            self.set_fixture_channels(fixture_id, channels)

        self.current_scene = scene_name
        self._last_update_time = datetime.now()

        # Add tracing attributes
        if self._tracer:
            self._tracer.add_span_attributes({
                "scene_name": scene_name,
                "fixture_count": len(scene.fixtures),
                "transition_time_ms": scene.transition_time_ms
            })

        logger.info(f"Scene activated: {scene_name}")

    def get_fixture_state(self, fixture_id: str) -> Dict[int, int]:
        """
        Get current state of a fixture.

        Args:
            fixture_id: Fixture ID

        Returns:
            Dictionary of channel: value pairs
        """
        if fixture_id not in self.fixtures:
            raise ValueError(f"Fixture {fixture_id} not found")

        fixture = self.fixtures[fixture_id]
        return {ch: ch.value for ch, ch in fixture.channels.items()}

    def get_all_fixtures_state(self) -> Dict[str, Dict[int, int]]:
        """
        Get state of all fixtures.

        Returns:
            Dictionary of fixture_id -> {channel: value}
        """
        return {
            fixture_id: self.get_fixture_state(fixture_id)
            for fixture_id in self.fixtures.keys()
        }

    def emergency_stop(self) -> None:
        """
        Activate emergency stop - immediately halt all DMX output.

        This is a safety-critical function that must work instantly.
        """
        if self._tracer:
            ctx = self._tracer.trace_operation("emergency_stop")
            ctx.__enter__()
            try:
                self._emergency_stop_impl()
            finally:
                ctx.__exit__(None, None, None)
        else:
            self._emergency_stop_impl()

    def _emergency_stop_impl(self) -> None:
        """Internal implementation of emergency_stop."""
        logger.warning("EMERGENCY STOP ACTIVATED")
        self.state = DMXState.EMERGENCY_STOP

        # Set all channels to 0 (off)
        fixture_count = 0
        for fixture in self.fixtures.values():
            for channel in fixture.channels.values():
                channel.value = 0
            fixture_count += 1

        self.current_scene = None
        self._last_update_time = datetime.now()

        # Add tracing event
        if self._tracer:
            self._tracer.add_span_event("emergency_stop_activated", {
                "fixture_count": fixture_count,
                "universe": self.universe,
                "previous_scene": self.current_scene
            })

        # Call emergency stop callback if registered
        if self._emergency_stop_callback:
            self._emergency_stop_callback()

    def reset_from_emergency(self) -> None:
        """
        Reset from emergency stop state.

        This should only be called after the emergency situation is resolved.
        """
        if self.state != DMXState.EMERGENCY_STOP:
            logger.warning("Cannot reset: not in emergency stop state")
            return

        logger.info("Resetting from emergency stop")
        self.state = DMXState.IDLE

        # Fade up to safe defaults (50% intensity)
        for fixture in self.fixtures.values():
            for channel in fixture.channels.values():
                # Set to 50% (128) as safe default
                if channel.label.lower() in ['intensity', 'master', 'dimmer']:
                    channel.value = 128

        self._last_update_time = datetime.now()

    def set_emergency_stop_callback(self, callback) -> None:
        """
        Register a callback for emergency stop events.

        Args:
            callback: Function to call when emergency stop is activated
        """
        self._emergency_stop_callback = callback
        logger.info("Emergency stop callback registered")

    def _check_emergency_stop(self) -> None:
        """Check if system is in emergency stop state."""
        if self.state == DMXState.EMERGENCY_STOP:
            raise RuntimeError("System in emergency stop state - cannot execute commands")

    def get_status(self) -> Dict:
        """
        Get system status.

        Returns:
            Dictionary containing system status information
        """
        return {
            "universe": self.universe,
            "state": self.state.value,
            "refresh_rate": self.refresh_rate,
            "fixture_count": len(self.fixtures),
            "scene_count": len(self.scenes),
            "current_scene": self.current_scene,
            "last_update": self._last_update_time.isoformat() if self._last_update_time else None
        }


# Example usage and testing
async def main():
    """Example usage of DMX controller."""

    # Create controller
    controller = DMXController(universe=1, refresh_rate=44)

    # Add some fixtures (example configuration)
    moving_head_1 = Fixture(
        id="mh_1",
        name="Moving Head 1",
        start_address=1,
        channel_count=16,
        channels={
            1: DMXChannel(1, 0, "intensity"),
            2: DMXChannel(2, 0, "pan"),
            3: DMXChannel(3, 0, "tilt"),
            4: DMXChannel(4, 0, "color_red"),
            5: DMXChannel(5, 0, "color_green"),
            6: DMXChannel(6, 0, "color_blue"),
            # ... more channels
        }
    )

    controller.add_fixture(moving_head_1)

    # Set fixture channels
    controller.set_fixture_channels("mh_1", {
        1: 255,  # Full intensity
        4: 200,  # Red
        5: 100,  # Green
        6: 50,   # Blue
    })

    # Create a scene
    controller.create_scene(
        name="happy_scene",
        fixture_values={
            "mh_1": {
                1: 255,  # Full intensity
                4: 255,  # Red
                5: 200,  # Green
            }
        },
        transition_time_ms=1000
    )

    # Activate the scene
    controller.activate_scene("happy_scene")

    # Get status
    status = controller.get_status()
    print(f"DMX Controller Status: {status}")

    # Emergency stop test
    print("\nTesting emergency stop...")
    controller.emergency_stop()
    print(f"Status after emergency stop: {controller.get_status()}")

    # Reset from emergency
    print("\nResetting from emergency...")
    controller.reset_from_emergency()
    print(f"Status after reset: {controller.get_status()}")


if __name__ == "__main__":
    asyncio.run(main())
