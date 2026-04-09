#!/usr/bin/env python3
"""
Distributed Tracing Test Script
Project Chimera Phase 2 - Observability

This script tests the distributed tracing integration with Phase 2 services.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.dmx_controller.dmx_controller import DMXController, Fixture, DMXChannel, Scene
from services.audio_controller.audio_controller import AudioController, AudioTrack
from services.bsl_avatar_service.bsl_avatar_service import (
    BSLAvatarService, BSLGesture
)


def test_dmx_tracing():
    """Test DMX controller tracing."""
    print("\n=== Testing DMX Controller Tracing ===")

    controller = DMXController(universe=1, refresh_rate=44)

    # Add a test fixture
    fixture = Fixture(
        id="test_fixture",
        name="Test Moving Head",
        start_address=1,
        channel_count=6,
        channels={
            1: DMXChannel(1, 0, "intensity"),
            2: DMXChannel(2, 0, "pan"),
            3: DMXChannel(3, 0, "tilt"),
            4: DMXChannel(4, 0, "red"),
            5: DMXChannel(5, 0, "green"),
            6: DMXChannel(6, 0, "blue"),
        }
    )
    controller.add_fixture(fixture)

    # Create a scene
    controller.create_scene(
        name="test_scene",
        fixture_values={
            "test_fixture": {
                1: 255,
                4: 200,
                5: 100,
            }
        },
        transition_time_ms=1000
    )

    # Activate scene (should create trace)
    print("Activating scene...")
    controller.activate_scene("test_scene")

    # Emergency stop (should create trace)
    print("Testing emergency stop...")
    controller.emergency_stop()

    # Reset
    print("Resetting from emergency...")
    controller.reset_from_emergency()

    print("DMX Controller tracing test complete!")


def test_audio_tracing():
    """Test audio controller tracing."""
    print("\n=== Testing Audio Controller Tracing ===")

    controller = AudioController(sample_rate=48000, bit_depth=24)

    # Add a test track
    track = AudioTrack(
        id="test_track",
        name="Test Track",
        url="/test.mp3",
        volume_db=-20,
        max_volume_db=-6
    )
    controller.add_track(track)

    # Play track (should create trace)
    print("Playing track...")
    controller.play_track("test_track", fade_in_ms=500)

    # Set volume (should create trace)
    print("Setting volume...")
    controller.set_track_volume("test_track", -15, ramp_ms=1000)

    # Emergency mute (should create trace)
    print("Testing emergency mute...")
    controller.emergency_mute()

    # Reset
    print("Resetting from emergency...")
    controller.reset_from_emergency()

    print("Audio Controller tracing test complete!")


async def test_bsl_tracing():
    """Test BSL avatar service tracing."""
    print("\n=== Testing BSL Avatar Service Tracing ===")

    # Create sample gesture library
    gesture_library = {
        "hello": BSLGesture(
            id="hello",
            word="hello",
            part_of_speech="interjection",
            handshape="open_hand",
            orientation="palm_out",
            location="forehead",
            movement="wave",
            non_manual_features={
                "facial_expression": "friendly",
                "eyebrows": "raised",
                "body_lean": "slight_forward"
            }
        ),
        "thank": BSLGesture(
            id="thank",
            word="thank",
            part_of_speech="verb",
            handshape="flat_hand",
            orientation="palm_up",
            location="chest",
            movement="circular_motion",
            non_manual_features={
                "facial_expression": "grateful",
                "eyebrows": "relaxed",
                "body_lean": "slight_forward"
            }
        ),
    }

    service = BSLAvatarService(gesture_library)

    # Translate and render (should create trace)
    print("Translating and rendering 'hello thank you'...")
    await service.translate_and_render("hello thank you")

    print("BSL Avatar Service tracing test complete!")


async def main():
    """Run all tracing tests."""
    print("=" * 60)
    print("Project Chimera Phase 2 - Distributed Tracing Tests")
    print("=" * 60)

    # Check if tracing is available
    try:
        from monitoring.distributed_tracing.tracer import get_dmx_tracer
        print("\n✓ Distributed tracing is available")
        tracer = get_dmx_tracer()
        print(f"✓ DMX tracer initialized: {tracer.tracer is not None}")
    except ImportError as e:
        print(f"\n✗ Distributed tracing not available: {e}")
        print("Install with: pip install -r monitoring/distributed-tracing/requirements.txt")
        return

    # Run tests
    test_dmx_tracing()
    test_audio_tracing()
    await test_bsl_tracing()

    print("\n" + "=" * 60)
    print("All tracing tests complete!")
    print("=" * 60)
    print("\nCheck Jaeger UI at http://localhost:16686 to view traces:")
    print("  - Service: dmx-controller")
    print("  - Service: audio-controller")
    print("  - Service: bsl-avatar-service")
    print("\nSearch for traces from the last 5 minutes to see test results.")


if __name__ == "__main__":
    asyncio.run(main())
