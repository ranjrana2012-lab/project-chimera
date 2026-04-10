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
from pathlib import Path
from typing import Dict, Any

# Get project root and add service directories to path
project_root = Path(__file__).parent.parent.parent
dmx_path = project_root / "services" / "dmx-controller"
audio_path = project_root / "services" / "audio-controller"
bsl_path = project_root / "services" / "bsl-avatar-service"

sys.path.insert(0, str(dmx_path))
sys.path.insert(0, str(audio_path))
sys.path.insert(0, str(bsl_path))

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
            scene_id="scene_red",
            name="Red Scene",
            fixture_states={"mh_1": {1: 255, 4: 255, 5: 0, 6: 0}}
        )
        controller.create_scene(
            scene_id="scene_blue",
            name="Blue Scene",
            fixture_states={"mh_1": {1: 255, 4: 0, 5: 0, 6: 255}}
        )

        yield controller
        # Cleanup
        controller.stop()

    @pytest.fixture
    def audio_controller(self):
        """Create audio controller with test tracks."""
        controller = AudioController()

        # Add test tracks
        track1 = AudioTrack(
            track_id="track_1",
            name="Background Music",
            file_path="/tmp/test_music.mp3",
            volume=0.7,
            loop=True
        )
        controller.add_track(track1)

        track2 = AudioTrack(
            track_id="track_2",
            name="Sound Effects",
            file_path="/tmp/test_sfx.mp3",
            volume=0.5,
            loop=False
        )
        controller.add_track(track2)

        yield controller
        # Cleanup
        controller.stop()

    @pytest.fixture
    def bsl_service(self):
        """Create BSL avatar service."""
        service = BSLAvatarService()
        yield service
        # Cleanup
        service.stop()

    def test_dmx_controller_initialization(self, dmx_controller):
        """Test DMX controller initializes correctly."""
        assert dmx_controller.universe == 1
        assert len(dmx_controller.fixtures) == 1
        assert len(dmx_controller.scenes) == 2

    def test_dmx_scene_activation(self, dmx_controller):
        """Test DMX scene can be activated."""
        result = dmx_controller.activate_scene("scene_red")
        assert result is True

    def test_dmx_channel_values(self, dmx_controller):
        """Test DMX channel values after scene activation."""
        dmx_controller.activate_scene("scene_red")
        fixture = dmx_controller.fixtures["mh_1"]
        assert fixture.channels[1].value == 255  # intensity
        assert fixture.channels[4].value == 255  # red

    def test_audio_controller_initialization(self, audio_controller):
        """Test audio controller initializes correctly."""
        assert len(audio_controller.tracks) == 2
        assert audio_controller.tracks[0].name == "Background Music"

    def test_audio_track_playback(self, audio_controller):
        """Test audio track can be played."""
        result = audio_controller.play_track("track_1")
        # Will fail without actual file, but tests the interface
        assert result is not None

    def test_audio_track_volume(self, audio_controller):
        """Test audio track volume can be set."""
        audio_controller.set_volume("track_1", 0.8)
        assert audio_controller.tracks[0].volume == 0.8

    def test_bsl_service_initialization(self, bsl_service):
        """Test BSL service initializes correctly."""
        assert bsl_service is not None
        assert hasattr(bsl_service, 'translate')

    def test_bsl_gesture_creation(self, bsl_service):
        """Test BSL gesture can be created."""
        gesture = BSLGesture(
            gesture_id="wave",
            name="Wave",
            duration=2.0,
            parameters={"intensity": 0.8}
        )
        assert gesture.gesture_id == "wave"
        assert gesture.duration == 2.0

    def test_bsl_translation(self, bsl_service):
        """Test BSL translation interface."""
        # Test translation interface (may return mock result without actual avatar)
        result = bsl_service.translate("Hello world")
        assert result is not None

    @pytest.mark.asyncio
    async def test_dmx_audio_integration(self, dmx_controller, audio_controller):
        """Test DMX and audio controllers work together."""
        # Activate scene
        dmx_controller.activate_scene("scene_red")

        # Play audio track
        audio_controller.play_track("track_1")

        # Verify both controllers are running
        assert dmx_controller.is_running()
        assert audio_controller.is_running()

    @pytest.mark.asyncio
    async def test_full_pipeline_integration(
        self,
        dmx_controller,
        audio_controller,
        bsl_service
    ):
        """Test full pipeline with all three services."""
        # Start all services
        dmx_controller.activate_scene("scene_blue")
        audio_controller.play_track("track_2")
        bsl_service.translate("Good morning")

        # Simulate show sequence
        await asyncio.sleep(0.1)

        # Verify services are responsive
        assert dmx_controller.is_running()
        assert audio_controller.is_running()

    @pytest.mark.asyncio
    async def test_service_error_handling(self, dmx_controller, audio_controller):
        """Test error handling across services."""
        # Test with invalid scene
        result = dmx_controller.activate_scene("invalid_scene")
        assert result is False

        # Test with invalid track
        result = audio_controller.play_track("invalid_track")
        assert result is None


class TestServiceSequences:
    """Test predefined service sequences."""

    @pytest.fixture
    def all_services(self, dmx_controller, audio_controller, bsl_service):
        """Fixture providing all services."""
        return {
            "dmx": dmx_controller,
            "audio": audio_controller,
            "bsl": bsl_service
        }

    @pytest.mark.asyncio
    async def test_show_opening_sequence(self, all_services):
        """Test a typical show opening sequence."""
        services = all_services

        # Opening: Lights up, music starts, BSL greeting
        services["dmx"].activate_scene("scene_red")
        services["audio"].play_track("track_1")
        services["bsl"].translate("Welcome to the show")

        await asyncio.sleep(0.1)

        # Verify all services active
        assert services["dmx"].is_running()
        assert services["audio"].is_running()

    @pytest.mark.asyncio
    async def test_scene_transition_sequence(self, all_services):
        """Test scene transition with coordinated services."""
        services = all_services

        # Scene 1: Red with music
        services["dmx"].activate_scene("scene_red")
        services["audio"].play_track("track_1")

        await asyncio.sleep(0.05)

        # Transition to Scene 2: Blue
        services["dmx"].activate_scene("scene_blue")
        services["audio"].play_track("track_2")

        # Verify transition
        assert services["dmx"].scenes["scene_blue"].is_active

    @pytest.mark.asyncio
    async def test_show_closing_sequence(self, all_services):
        """Test show closing sequence."""
        services = all_services

        # Closing sequence
        services["dmx"].activate_scene("scene_blue")
        services["audio"].play_track("track_2")
        services["bsl"].translate("Thank you for watching")

        await asyncio.sleep(0.1)

        # Stop all services
        services["dmx"].stop()
        services["audio"].stop()

        # Verify stopped
        assert not services["dmx"].is_running()
        assert not services["audio"].is_running()


class TestServiceSynchronization:
    """Test synchronization between services."""

    @pytest.mark.asyncio
    async def test_synchronized_scene_change(self, dmx_controller, audio_controller):
        """Test DMX and audio change in sync."""
        # Scene should change with specific audio
        dmx_controller.activate_scene("scene_red")
        audio_controller.play_track("track_1")

        # Both should be active
        assert dmx_controller.is_running()
        assert audio_controller.is_running()

    @pytest.mark.asyncio
    async def test_service_state_consistency(self, dmx_controller, audio_controller):
        """Test service states remain consistent."""
        # Initial state
        assert dmx_controller.get_current_scene() is None

        # Activate scene
        dmx_controller.activate_scene("scene_red")
        assert dmx_controller.get_current_scene() == "scene_red"

        # Change scene
        dmx_controller.activate_scene("scene_blue")
        assert dmx_controller.get_current_scene() == "scene_blue"
