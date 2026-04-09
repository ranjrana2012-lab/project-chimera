#!/usr/bin/env python3
"""
DMX Controller Example Usage

Demonstrates how to use the DMX512 lighting controller service.
"""

import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dmx_controller import (
    DMXController,
    DMXChannel,
    Fixture,
    Scene
)


def create_sample_fixtures():
    """Create sample lighting fixtures for demonstration."""
    fixtures = []

    # Moving Head 1
    mh1_channels = {
        1: DMXChannel(1, 0, "intensity"),
        2: DMXChannel(2, 0, "pan"),
        3: DMXChannel(3, 0, "tilt"),
        4: DMXChannel(4, 0, "color_red"),
        5: DMXChannel(5, 0, "color_green"),
        6: DMXChannel(6, 0, "color_blue"),
        7: DMXChannel(7, 0, "gobo"),
        8: DMXChannel(8, 0, "shutter"),
    }
    mh1 = Fixture(
        id="mh_1",
        name="Moving Head 1",
        start_address=1,
        channel_count=8,
        channels=mh1_channels
    )
    fixtures.append(mh1)

    # Moving Head 2
    mh2_channels = {
        1: DMXChannel(1, 0, "intensity"),
        2: DMXChannel(2, 0, "pan"),
        3: DMXChannel(3, 0, "tilt"),
        4: DMXChannel(4, 0, "color_red"),
        5: DMXChannel(5, 0, "color_green"),
        6: DMXChannel(6, 0, "color_blue"),
    }
    mh2 = Fixture(
        id="mh_2",
        name="Moving Head 2",
        start_address=9,
        channel_count=6,
        channels=mh2_channels
    )
    fixtures.append(mh2)

    # PAR Can (simple RGB)
    par_channels = {
        1: DMXChannel(1, 0, "intensity"),
        2: DMXChannel(2, 0, "color_red"),
        3: DMXChannel(3, 0, "color_green"),
        4: DMXChannel(4, 0, "color_blue"),
    }
    par = Fixture(
        id="par_1",
        name="PAR Can 1",
        start_address=15,
        channel_count=4,
        channels=par_channels
    )
    fixtures.append(par)

    return fixtures


def example_basic_control(controller):
    """Example: Basic fixture control."""
    print("\n=== Example: Basic Fixture Control ===")

    # Set individual channels
    print("Setting MH1 intensity to 50%")
    controller.set_fixture_channel("mh_1", 1, 128)

    print("Setting MH1 color to red")
    controller.set_fixture_channels("mh_1", {
        4: 255,  # Red
        5: 0,    # Green
        6: 0     # Blue
    })

    print(f"MH1 state: {controller.get_fixture_state('mh_1')}")


def example_scene_creation(controller):
    """Example: Creating and activating scenes."""
    print("\n=== Example: Scene Creation ===")

    # Create a "Happy" scene (warm colors)
    controller.create_scene(
        name="happy",
        fixture_values={
            "mh_1": {
                1: 255,  # Full intensity
                4: 255,  # Red
                5: 200,  # Green
                6: 0     # No blue
            },
            "mh_2": {
                1: 255,
                4: 255,
                5: 180,
                6: 0
            },
            "par_1": {
                1: 255,
                2: 255,
                3: 200,
                4: 0
            }
        },
        transition_time_ms=2000
    )

    # Create a "Sad" scene (cool colors)
    controller.create_scene(
        name="sad",
        fixture_values={
            "mh_1": {
                1: 150,  # Lower intensity
                4: 0,    # No red
                5: 100,  # Some green
                6: 255   # Full blue
            },
            "mh_2": {
                1: 150,
                4: 0,
                5: 80,
                6: 255
            },
            "par_1": {
                1: 150,
                2: 0,
                3: 100,
                4: 255
            }
        },
        transition_time_ms=3000
    )

    # Create an "Off" scene
    controller.create_scene(
        name="off",
        fixture_values={
            "mh_1": {1: 0},
            "mh_2": {1: 0},
            "par_1": {1: 0}
        },
        transition_time_ms=1000
    )

    print(f"Created {len(controller.scenes)} scenes")

    # Activate happy scene
    print("\nActivating 'happy' scene...")
    controller.activate_scene("happy")
    print(f"Current scene: {controller.current_scene}")


def example_emergency_stop(controller):
    """Example: Emergency stop functionality."""
    print("\n=== Example: Emergency Stop ===")

    # Activate a scene first
    controller.activate_scene("happy")
    print(f"Scene activated: {controller.current_scene}")

    # Simulate emergency stop
    print("\n!!! EMERGENCY STOP ACTIVATED !!!")
    controller.emergency_stop()

    # Check all values are zero
    mh1_state = controller.get_fixture_state("mh_1")
    all_zero = all(v == 0 for v in mh1_state.values())
    print(f"All channels zero: {all_zero}")
    print(f"Controller state: {controller.state.value}")

    # Reset from emergency
    print("\nResetting from emergency...")
    controller.reset_from_emergency()
    print(f"Controller state after reset: {controller.state.value}")


def example_status_monitoring(controller):
    """Example: Monitoring controller status."""
    print("\n=== Example: Status Monitoring ===")

    status = controller.get_status()
    print(f"Universe: {status['universe']}")
    print(f"State: {status['state']}")
    print(f"Refresh Rate: {status['refresh_rate']} Hz")
    print(f"Fixture Count: {status['fixture_count']}")
    print(f"Scene Count: {status['scene_count']}")
    print(f"Current Scene: {status['current_scene']}")


def example_all_fixtures_state(controller):
    """Example: Getting state of all fixtures."""
    print("\n=== Example: All Fixtures State ===")

    all_states = controller.get_all_fixtures_state()
    for fixture_id, channels in all_states.items():
        print(f"\n{fixture_id}:")
        for channel, value in channels.items():
            print(f"  Channel {channel}: {value}")


def main():
    """Main example function."""
    print("=" * 60)
    print("DMX Controller Example Usage")
    print("=" * 60)

    # Create controller
    controller = DMXController(universe=1, refresh_rate=44)
    print(f"\nCreated DMX Controller: Universe {controller.universe}")

    # Add fixtures
    fixtures = create_sample_fixtures()
    for fixture in fixtures:
        controller.add_fixture(fixture)
        print(f"Added fixture: {fixture.name}")

    # Run examples
    example_basic_control(controller)
    example_scene_creation(controller)
    example_status_monitoring(controller)
    example_all_fixtures_state(controller)
    example_emergency_stop(controller)

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
