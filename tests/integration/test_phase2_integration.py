#!/usr/bin/env python3
"""
Project Chimera Phase 2 - Integration Tests

Integration tests for DMX, Audio, and BSL Avatar services working together.
"""

import pytest
import asyncio
import sys
import os
import time
from typing import Dict, Any

# Add services to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dmx_controller import DMXController, DMXChannel, Fixture, Scene
from audio_controller import AudioController, AudioTrack
from bsl_avatar_service import BSLAvatarService, BSLGesture


class TestServiceIntegration:
    """Integration tests for Phase 2 services."""

    @pytest.fixture
    def dmx_controller(self):
        """Create DMX controller with test fixtures."""
        controller = DMXController(universe=1, refresh_rate=44)

        # Add test fixtures
        mh1_channels = {
            1: DMXChannel(1, 0, "intensity"),
            2: DMXChannel(2, 0, "pan"),
            3: DMXChannel(3, 0, "tilt"),
            4: DMXChannel(4, 0, "color_red"),
            5: DMXChannel(5, 0, "color_green"),
            6: DMXChannel(6, 0, "color_blue"),
        }
        mh1 = Fixture(
            id="mh_1",
            name="Moving Head 1",
            start_address=1,
            channel_count=6,
            channels=mh1_channels
        )
        controller.add_fixture(mh1)

        # Create scenes
        controller.create_scene(
            name="happy",
            fixture_values={
                "mh_1": {
                    1: 255,  # Full intensity
                    4: 255,  # Red
                    5: 200,  # Green
                    6: 0     # No blue
                }
            },
            transition_time_ms=2000
        )

        controller.create_scene(
            name="sad",
            fixture_values={
                "mh_1": {
                    1: 150,  # Lower intensity
                    4: 0,    # No red
                    5: 100,  # Some green
                    6: 255   # Full blue
                }
            },
            transition_time_ms=3000
        )

        return controller

    @pytest.fixture
    def audio_controller(self):
        """Create audio controller with test tracks."""
        controller = AudioController(sample_rate=48000, bit_depth=24)

        # Add test tracks
        dialogue = AudioTrack(
            id="dialogue",
            name="AI Dialogue",
            url="/assets/dialogue.mp3",
            volume_db=-20.0
        )
        music = AudioTrack(
            id="music",
            name="Background Music",
            url="/assets/music.mp3",
            volume_db=-30.0
        )

        controller.add_track(dialogue)
        controller.add_track(music)

        return controller

    @pytest.fixture
    def bsl_service(self):
        """Create BSL avatar service with test gestures."""
        library = {
            "hello": BSLGesture(
                id="hello",
                word="hello",
                part_of_speech="interjection",
                handshape="open_hand",
                orientation="palm_out",
                location="forehead",
                movement="wave",
                non_manual_features={}
            ),
            "happy": BSLGesture(
                id="happy",
                word="happy",
                part_of_speech="adjective",
                handshape="open_hand",
                orientation="palm_out",
                location="chest",
                movement="circular",
                non_manual_features={}
            ),
            "sad": BSLGesture(
                id="sad",
                word="sad",
                part_of_speech="adjective",
                handshape="flat_hand",
                orientation="palm_down",
                location="chest",
                movement="downward",
                non_manual_features={}
            )
        }

        return BSLAvatarService(library)

    def test_service_initialization(self, dmx_controller, audio_controller, bsl_service):
        """Test that all services initialize correctly."""
        # DMX Controller
        assert dmx_controller.universe == 1
        assert dmx_controller.state.value == "idle"
        assert len(dmx_controller.fixtures) == 1
        assert len(dmx_controller.scenes) == 2

        # Audio Controller
        assert audio_controller.sample_rate == 48000
        assert audio_controller.state.value == "idle"
        assert len(audio_controller.tracks) == 2

        # BSL Service
        assert bsl_service.state.value == "idle"
        assert len(bsl_service.translator.gesture_library) == 3

    @pytest.mark.asyncio
    async def test_coordinated_show_sequence(self, dmx_controller, audio_controller, bsl_service):
        """Test a coordinated show sequence with all services."""
        # This simulates a simple theatrical performance sequence

        # Scene 1: Happy greeting
        print("\n=== Scene 1: Happy Greeting ===")

        # Translate and render BSL
        await bsl_service.translate_and_render("hello happy")

        # Set lighting for happy scene
        dmx_controller.activate_scene("happy")

        # Start background music
        audio_controller.play_track("music", fade_in_ms=1000)

        # Verify states
        assert dmx_controller.current_scene == "happy"
        assert audio_controller.tracks["music"].is_playing == True

        # Wait for transition
        await asyncio.sleep(0.1)

        # Scene 2: Mood shift to sad
        print("\n=== Scene 2: Mood Shift ===")

        # Translate and render BSL
        await bsl_service.translate_and_render("hello sad")

        # Change lighting to sad scene
        dmx_controller.activate_scene("sad")

        # Adjust music volume
        audio_controller.set_track_volume("music", -35.0, ramp_ms=2000)

        # Verify states
        assert dmx_controller.current_scene == "sad"
        assert audio_controller.tracks["music"].volume_db == -35.0

        await asyncio.sleep(0.1)

        # Scene 3: Emergency stop simulation
        print("\n=== Scene 3: Emergency Stop ===")

        # Emergency stop all systems
        dmx_controller.emergency_stop()
        audio_controller.emergency_mute()

        # Verify emergency states
        assert dmx_controller.state.value == "emergency_stop"
        assert audio_controller.state.value == "emergency_mute"

        # All DMX channels should be 0
        mh1_state = dmx_controller.get_fixture_state("mh_1")
        assert all(v == 0 for v in mh1_state.values())

        # All audio tracks should be muted
        assert all(t.is_muted for t in audio_controller.tracks.values())

        # Reset from emergency
        print("\n=== Reset from Emergency ===")

        dmx_controller.reset_from_emergency()
        audio_controller.reset_from_emergency()

        # Verify reset
        assert dmx_controller.state.value == "idle"
        assert audio_controller.state.value == "idle"

    def test_emergency_coordination(self, dmx_controller, audio_controller):
        """Test that emergency procedures coordinate across services."""
        # Set up active state
        dmx_controller.activate_scene("happy")
        audio_controller.play_track("dialogue")
        audio_controller.play_track("music")

        assert dmx_controller.current_scene == "happy"
        assert audio_controller.state.value == "playing"

        # Simulate emergency situation
        dmx_controller.emergency_stop()
        audio_controller.emergency_mute()

        # Both systems should be in emergency state
        assert dmx_controller.state.value == "emergency_stop"
        assert audio_controller.state.value == "emergency_mute"

        # Commands should be blocked
        with pytest.raises(RuntimeError):
            dmx_controller.set_fixture_channel("mh_1", 1, 128)

        with pytest.raises(RuntimeError):
            audio_controller.play_track("dialogue")

        # Reset both systems
        dmx_controller.reset_from_emergency()
        audio_controller.reset_from_emergency()

        # Both should be operational again
        assert dmx_controller.state.value == "idle"
        assert audio_controller.state.value == "idle"

    def test_performance_timing(self, dmx_controller, audio_controller, bsl_service):
        """Test performance characteristics of integrated services."""
        import time

        # Measure scene activation timing
        start = time.time()
        dmx_controller.activate_scene("happy")
        dmx_time = (time.time() - start) * 1000

        # Should be very fast (no actual DMX hardware)
        assert dmx_time < 100  # Less than 100ms

        # Measure audio play timing
        start = time.time()
        audio_controller.play_track("dialogue")
        audio_time = (time.time() - start) * 1000

        # Should be very fast (no actual audio hardware)
        assert audio_time < 100  # Less than 100ms

        # Measure translation timing
        start = time.time()
        sequence = bsl_service.translator.translate("hello happy sad")
        translation_time = (time.time() - start) * 1000

        # Should be fast (no actual rendering)
        assert translation_time < 50  # Less than 50ms
        assert len(sequence.gestures) == 3

    def test_state_consistency(self, dmx_controller, audio_controller):
        """Test that service states remain consistent during operations."""
        # Perform rapid state changes
        for i in range(10):
            scene = "happy" if i % 2 == 0 else "sad"
            dmx_controller.activate_scene(scene)
            assert dmx_controller.current_scene == scene

        # Audio operations
        for i in range(10):
            if i % 2 == 0:
                audio_controller.play_track("dialogue")
            else:
                audio_controller.stop_track("dialogue")

        # Final state should be consistent
        assert dmx_controller.state.value in ["idle", "active"]
        assert audio_controller.state.value in ["idle", "playing", "muted"]

    def test_resource_cleanup(self, dmx_controller, audio_controller):
        """Test that resources are properly managed."""
        # Add and remove fixtures
        temp_channels = {
            1: DMXChannel(1, 0, "intensity")
        }
        temp_fixture = Fixture(
            id="temp",
            name="Temporary",
            start_address=100,
            channel_count=1,
            channels=temp_channels
        )

        dmx_controller.add_fixture(temp_fixture)
        assert "temp" in dmx_controller.fixtures
        assert len(dmx_controller.fixtures) == 2

        dmx_controller.remove_fixture("temp")
        assert "temp" not in dmx_controller.fixtures
        assert len(dmx_controller.fixtures) == 1

        # Add and remove tracks
        temp_track = AudioTrack(
            id="temp",
            name="Temporary",
            url="/temp.mp3"
        )

        audio_controller.add_track(temp_track)
        assert "temp" in audio_controller.tracks
        assert len(audio_controller.tracks) == 3

        audio_controller.remove_track("temp")
        assert "temp" not in audio_controller.tracks
        assert len(audio_controller.tracks) == 2

    def test_status_monitoring_integration(self, dmx_controller, audio_controller, bsl_service):
        """Test that status monitoring works across all services."""
        # Get all service statuses
        dmx_status = dmx_controller.get_status()
        audio_status = audio_controller.get_status()
        bsl_status = bsl_service.get_status()

        # Verify status structure
        assert "state" in dmx_status
        assert "state" in audio_status
        assert "state" in bsl_status

        # Verify status values
        assert dmx_status["universe"] == 1
        assert audio_status["sample_rate"] == 48000
        assert bsl_status["gesture_library_size"] == 3

        # Create combined status report
        combined_status = {
            "timestamp": time.time(),
            "dmx": dmx_status,
            "audio": audio_status,
            "bsl": bsl_status,
            "overall_status": "operational"
        }

        assert combined_status["overall_status"] == "operational"


class TestErrorHandling:
    """Test error handling across integrated services."""

    @pytest.fixture
    def controllers(self):
        """Create all controllers for testing."""
        dmx = DMXController(universe=1)
        audio = AudioController()
        bsl = BSLAvatarService({})

        # Add minimal fixtures and tracks
        channels = {1: DMXChannel(1, 0, "intensity")}
        fixture = Fixture(
            id="test",
            name="Test",
            start_address=1,
            channel_count=1,
            channels=channels
        )
        dmx.add_fixture(fixture)

        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        audio.add_track(track)

        return dmx, audio, bsl

    def test_invalid_fixture_id(self, controllers):
        """Test handling of invalid fixture ID."""
        dmx, audio, bsl = controllers

        with pytest.raises(ValueError, match="Fixture not found"):
            dmx.set_fixture_channel("nonexistent", 1, 128)

    def test_invalid_track_id(self, controllers):
        """Test handling of invalid track ID."""
        dmx, audio, bsl = controllers

        with pytest.raises(ValueError, match="Track not found"):
            audio.play_track("nonexistent")

    def test_emergency_blocking(self, controllers):
        """Test that emergency states block operations appropriately."""
        dmx, audio, bsl = controllers

        # Activate emergency states
        dmx.emergency_stop()
        audio.emergency_mute()

        # DMX operations should be blocked
        with pytest.raises(RuntimeError, match="emergency stop state"):
            dmx.set_fixture_channel("test", 1, 128)

        # Audio operations should be blocked
        with pytest.raises(RuntimeError, match="emergency mute state"):
            audio.play_track("test")

        # Reset should restore functionality
        dmx.reset_from_emergency()
        audio.reset_from_emergency()

        # Operations should work again
        dmx.set_fixture_channel("test", 1, 128)  # Should not raise
        audio.play_track("test")  # Should not raise


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarks for integrated services."""

    @pytest.fixture
    def populated_services(self):
        """Create services with populated data."""
        dmx = DMXController(universe=1)
        audio = AudioController()

        # Add multiple fixtures
        for i in range(5):
            channels = {
                1: DMXChannel(1, 0, "intensity"),
                2: DMXChannel(2, 0, "color_red"),
                3: DMXChannel(3, 0, "color_green"),
                4: DMXChannel(4, 0, "color_blue"),
            }
            fixture = Fixture(
                id=f"fixture_{i}",
                name=f"Fixture {i}",
                start_address=1 + (i * 10),
                channel_count=4,
                channels=channels
            )
            dmx.add_fixture(fixture)

        # Add multiple tracks
        for i in range(5):
            track = AudioTrack(
                id=f"track_{i}",
                name=f"Track {i}",
                url=f"/track{i}.mp3",
                volume_db=-20.0 - (i * 5)
            )
            audio.add_track(track)

        return dmx, audio

    def test_large_scene_activation(self, populated_services):
        """Test activating scene with many fixtures."""
        dmx, audio = populated_services

        # Create scene with all fixtures
        fixture_values = {}
        for i in range(5):
            fixture_values[f"fixture_{i}"] = {
                1: 255,
                2: 200 if i % 2 == 0 else 0,
                3: 150 if i % 2 == 0 else 100,
                4: 100
            }

        dmx.create_scene("all_fixtures", fixture_values)

        import time
        start = time.time()
        dmx.activate_scene("all_fixtures")
        duration = (time.time() - start) * 1000

        # Should complete quickly even with many fixtures
        assert duration < 200  # Less than 200ms

    def test_rapid_audio_operations(self, populated_services):
        """Test rapid audio operations."""
        dmx, audio = populated_services

        import time
        start = time.time()

        # Perform many operations
        for i in range(100):
            track_id = f"track_{i % 5}"
            if i % 3 == 0:
                audio.play_track(track_id)
            elif i % 3 == 1:
                audio.set_track_volume(track_id, -15.0)
            else:
                audio.stop_track(track_id)

        duration = (time.time() - start) * 1000

        # Should handle 100 operations quickly
        assert duration < 1000  # Less than 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
