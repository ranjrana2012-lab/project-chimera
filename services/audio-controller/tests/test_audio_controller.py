#!/usr/bin/env python3
"""
Audio Controller Service Tests

Test suite for audio system controller functionality.
"""

import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_controller import (
    AudioController,
    AudioState,
    AudioTrack,
    AudioOutput
)


class TestAudioTrack:
    """Test audio track creation and management."""

    def test_create_valid_track(self):
        """Test creating a valid audio track."""
        track = AudioTrack(
            id="dialogue",
            name="AI Dialogue",
            url="/assets/dialogue.mp3",
            volume_db=-20.0
        )
        assert track.id == "dialogue"
        assert track.name == "AI Dialogue"
        assert track.url == "/assets/dialogue.mp3"
        assert track.volume_db == -20.0
        assert track.is_playing == False
        assert track.is_muted == False

    def test_default_values(self):
        """Test track with default values."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        assert track.volume_db == -20.0  # Default
        assert track.max_volume_db == -6.0  # Default
        assert track.is_playing == False
        assert track.is_muted == False

    def test_volume_too_high_raises_error(self):
        """Test that volume exceeding maximum raises ValueError."""
        with pytest.raises(ValueError, match="Volume .* exceeds maximum"):
            AudioTrack(
                id="test",
                name="Test",
                url="/test.mp3",
                volume_db=0.0,  # Exceeds default max of -6
                max_volume_db=-6.0
            )

    def test_volume_below_minimum_raises_error(self):
        """Test that volume below -60dB raises ValueError."""
        with pytest.raises(ValueError, match="Volume .* below minimum -60dB"):
            AudioTrack(
                id="test",
                name="Test",
                url="/test.mp3",
                volume_db=-70.0
            )

    def test_set_volume(self):
        """Test setting track volume."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        track.set_volume(-15.0)
        assert track.volume_db == -15.0

    def test_set_volume_clamps_to_max(self):
        """Test that set_volume clamps to maximum."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3",
            max_volume_db=-10.0
        )
        track.set_volume(-5.0)  # Exceeds max
        assert track.volume_db == -10.0  # Clamped to max

    def test_set_volume_clamps_to_minimum(self):
        """Test that set_volume clamps to minimum."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        track.set_volume(-100.0)  # Below minimum
        assert track.volume_db == -60.0  # Clamped to minimum

    def test_adjust_volume_positive(self):
        """Test adjusting volume up."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3",
            volume_db=-20.0
        )
        track.adjust_volume(5.0)
        assert track.volume_db == -15.0

    def test_adjust_volume_negative(self):
        """Test adjusting volume down."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3",
            volume_db=-20.0
        )
        track.adjust_volume(-3.0)
        assert track.volume_db == -23.0

    def test_adjust_volume_clamps(self):
        """Test that adjust_volume clamps to limits."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3",
            volume_db=-20.0,
            max_volume_db=-10.0
        )
        track.adjust_volume(20.0)  # Would exceed max
        assert track.volume_db == -10.0  # Clamped

    def test_play(self):
        """Test playing a track."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        track.play()
        assert track.is_playing == True
        assert track.is_muted == False

    def test_stop(self):
        """Test stopping a track."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        track.play()
        track.stop()
        assert track.is_playing == False

    def test_mute(self):
        """Test muting a track."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        track.mute()
        assert track.is_muted == True

    def test_unmute(self):
        """Test unmuting a track."""
        track = AudioTrack(
            id="test",
            name="Test",
            url="/test.mp3"
        )
        track.mute()
        track.unmute()
        assert track.is_muted == False


class TestAudioOutput:
    """Test audio output configuration."""

    def test_create_output(self):
        """Test creating an audio output."""
        output = AudioOutput(
            id="main",
            name="Main Speakers",
            output_type="stereo",
            channels=[1, 2]
        )
        assert output.id == "main"
        assert output.name == "Main Speakers"
        assert output.output_type == "stereo"
        assert output.channels == [1, 2]


class TestAudioController:
    """Test audio controller functionality."""

    @pytest.fixture
    def controller(self):
        """Create an audio controller for testing."""
        return AudioController(sample_rate=48000, bit_depth=24)

    @pytest.fixture
    def sample_track(self):
        """Create a sample audio track."""
        return AudioTrack(
            id="dialogue",
            name="AI Dialogue",
            url="/assets/dialogue.mp3",
            volume_db=-20.0
        )

    def test_controller_initialization(self, controller):
        """Test controller initializes with correct values."""
        assert controller.sample_rate == 48000
        assert controller.bit_depth == 24
        assert controller.state == AudioState.IDLE
        assert len(controller.tracks) == 0
        assert len(controller.outputs) == 3  # Default outputs

    def test_default_outputs_created(self, controller):
        """Test that default outputs are created."""
        assert "main" in controller.outputs
        assert "monitor" in controller.outputs
        assert "subwoofer" in controller.outputs

    def test_add_track(self, controller, sample_track):
        """Test adding a track to controller."""
        controller.add_track(sample_track)
        assert "dialogue" in controller.tracks
        assert controller.tracks["dialogue"].name == "AI Dialogue"

    def test_remove_track(self, controller, sample_track):
        """Test removing a track from controller."""
        controller.add_track(sample_track)
        controller.remove_track("dialogue")
        assert "dialogue" not in controller.tracks

    def test_remove_nonexistent_track(self, controller):
        """Test removing non-existent track doesn't raise error."""
        # Should not raise exception
        controller.remove_track("nonexistent")

    def test_play_track(self, controller, sample_track):
        """Test playing a track."""
        controller.add_track(sample_track)
        controller.play_track("dialogue")
        assert controller.tracks["dialogue"].is_playing == True
        assert controller.state == AudioState.PLAYING

    def test_play_nonexistent_track(self, controller):
        """Test playing non-existent track raises ValueError."""
        with pytest.raises(ValueError, match="Track nonexistent not found"):
            controller.play_track("nonexistent")

    def test_stop_track(self, controller, sample_track):
        """Test stopping a track."""
        controller.add_track(sample_track)
        controller.play_track("dialogue")
        controller.stop_track("dialogue")
        assert controller.tracks["dialogue"].is_playing == False

    def test_stop_all(self, controller):
        """Test stopping all tracks."""
        track1 = AudioTrack(id="t1", name="Track 1", url="/t1.mp3")
        track2 = AudioTrack(id="t2", name="Track 2", url="/t2.mp3")
        controller.add_track(track1)
        controller.add_track(track2)

        controller.play_track("t1")
        controller.play_track("t2")
        assert controller.state == AudioState.PLAYING

        controller.stop_all()
        assert track1.is_playing == False
        assert track2.is_playing == False
        assert controller.state == AudioState.IDLE

    def test_set_track_volume(self, controller, sample_track):
        """Test setting individual track volume."""
        controller.add_track(sample_track)
        controller.set_track_volume("dialogue", -15.0)
        assert controller.tracks["dialogue"].volume_db == -15.0

    def test_set_master_volume(self, controller):
        """Test setting master volume affects all tracks."""
        track1 = AudioTrack(id="t1", name="T1", url="/t1.mp3", volume_db=-20.0)
        track2 = AudioTrack(id="t2", name="T2", url="/t2.mp3", volume_db=-30.0)
        controller.add_track(track1)
        controller.add_track(track2)

        controller.set_master_volume(-10.0)
        assert controller.tracks["t1"].volume_db == -10.0
        assert controller.tracks["t2"].volume_db == -10.0

    def test_mute_track(self, controller, sample_track):
        """Test muting a specific track."""
        controller.add_track(sample_track)
        controller.mute_track("dialogue")
        assert controller.tracks["dialogue"].is_muted == True

    def test_unmute_track(self, controller, sample_track):
        """Test unmuting a specific track."""
        controller.add_track(sample_track)
        controller.mute_track("dialogue")
        controller.unmute_track("dialogue")
        assert controller.tracks["dialogue"].is_muted == False

    def test_mute_all(self, controller):
        """Test muting all tracks."""
        track1 = AudioTrack(id="t1", name="T1", url="/t1.mp3")
        track2 = AudioTrack(id="t2", name="T2", url="/t2.mp3")
        controller.add_track(track1)
        controller.add_track(track2)

        controller.mute_all()
        assert controller.tracks["t1"].is_muted == True
        assert controller.tracks["t2"].is_muted == True
        assert controller.state == AudioState.MUTED

    def test_unmute_all(self, controller):
        """Test unmuting all tracks."""
        track1 = AudioTrack(id="t1", name="T1", url="/t1.mp3")
        track2 = AudioTrack(id="t2", name="T2", url="/t2.mp3")
        controller.add_track(track1)
        controller.add_track(track2)

        controller.mute_all()
        controller.unmute_all()
        assert controller.tracks["t1"].is_muted == False
        assert controller.tracks["t2"].is_muted == False

    def test_emergency_mute(self, controller):
        """Test emergency mute functionality."""
        track1 = AudioTrack(id="t1", name="T1", url="/t1.mp3", volume_db=-20.0)
        track2 = AudioTrack(id="t2", name="T2", url="/t2.mp3", volume_db=-30.0)
        controller.add_track(track1)
        controller.add_track(track2)
        controller.play_track("t1")

        controller.emergency_mute()

        assert controller.state == AudioState.EMERGENCY_MUTE
        assert controller.tracks["t1"].is_muted == True
        assert controller.tracks["t2"].is_muted == True

    def test_reset_from_emergency(self, controller):
        """Test resetting from emergency mute state."""
        track = AudioTrack(id="t1", name="T1", url="/t1.mp3", volume_db=-20.0)
        controller.add_track(track)
        controller.emergency_mute()

        assert controller.state == AudioState.EMERGENCY_MUTE
        controller.reset_from_emergency()
        assert controller.state == AudioState.IDLE
        # Volume should be reset to safe default
        assert controller.tracks["t1"].volume_db == -20.0

    def test_reset_when_not_in_emergency(self, controller):
        """Test that reset when not in emergency doesn't change state."""
        controller.state = AudioState.IDLE
        controller.reset_from_emergency()
        # State should remain IDLE (with warning logged)
        assert controller.state == AudioState.IDLE

    def test_command_blocked_in_emergency_mute(self, controller, sample_track):
        """Test that commands are blocked during emergency mute."""
        controller.add_track(sample_track)
        controller.emergency_mute()

        with pytest.raises(RuntimeError, match="System in emergency mute state"):
            controller.play_track("dialogue")

    def test_get_track_state(self, controller, sample_track):
        """Test getting state of a specific track."""
        controller.add_track(sample_track)
        controller.set_track_volume("dialogue", -15.0)
        state = controller.get_track_state("dialogue")
        assert state["id"] == "dialogue"
        assert state["name"] == "AI Dialogue"
        assert state["volume_db"] == -15.0
        assert state["is_playing"] == False
        assert state["is_muted"] == False

    def test_get_nonexistent_track_state(self, controller):
        """Test getting state of non-existent track raises ValueError."""
        with pytest.raises(ValueError, match="Track nonexistent not found"):
            controller.get_track_state("nonexistent")

    def test_get_all_tracks_state(self, controller):
        """Test getting state of all tracks."""
        track1 = AudioTrack(id="t1", name="T1", url="/t1.mp3", volume_db=-20.0)
        track2 = AudioTrack(id="t2", name="T2", url="/t2.mp3", volume_db=-30.0)
        controller.add_track(track1)
        controller.add_track(track2)

        all_states = controller.get_all_tracks_state()
        assert "t1" in all_states
        assert "t2" in all_states
        assert all_states["t1"]["volume_db"] == -20.0
        assert all_states["t2"]["volume_db"] == -30.0

    def test_get_status(self, controller):
        """Test getting controller status."""
        track1 = AudioTrack(id="t1", name="T1", url="/t1.mp3")
        track2 = AudioTrack(id="t2", name="T2", url="/t2.mp3")
        controller.add_track(track1)
        controller.add_track(track2)
        controller.play_track("t1")
        controller.mute_track("t2")

        status = controller.get_status()
        assert status["sample_rate"] == 48000
        assert status["bit_depth"] == 24
        assert status["state"] == "playing"
        assert status["track_count"] == 2
        assert status["output_count"] == 3
        assert "t1" in status["playing_tracks"]
        assert "t2" in status["muted_tracks"]

    def test_emergency_mute_callback(self, controller):
        """Test emergency mute callback is called."""
        callback_called = []

        def test_callback():
            callback_called.append(True)

        controller.set_emergency_mute_callback(test_callback)
        controller.emergency_mute()

        assert len(callback_called) == 1


@pytest.mark.integration
class TestAudioControllerIntegration:
    """Integration tests for audio controller."""

    def test_full_audio_sequence(self):
        """Test a complete audio sequence."""
        controller = AudioController(sample_rate=48000)

        # Create tracks
        dialogue = AudioTrack(
            id="dialogue",
            name="AI Dialogue",
            url="/dialogue.mp3",
            volume_db=-20.0
        )
        music = AudioTrack(
            id="music",
            name="Background Music",
            url="/music.mp3",
            volume_db=-30.0
        )
        controller.add_track(dialogue)
        controller.add_track(music)

        # Play dialogue
        controller.play_track("dialogue")
        assert dialogue.is_playing == True
        assert controller.state == AudioState.PLAYING

        # Fade in music
        controller.play_track("music", fade_in_ms=2000)
        assert music.is_playing == True

        # Adjust volumes
        controller.set_track_volume("dialogue", -15.0)
        assert dialogue.volume_db == -15.0

        # Stop dialogue with fade out
        controller.stop_track("dialogue", fade_out_ms=1000)
        assert dialogue.is_playing == False

        # Music still playing
        assert music.is_playing == True
        assert controller.state == AudioState.PLAYING

        # Stop all
        controller.stop_all(fade_out_ms=2000)
        assert music.is_playing == False
        assert controller.state == AudioState.IDLE

    def test_emergency_mute_scenario(self):
        """Test emergency mute scenario."""
        controller = AudioController()

        # Multiple tracks playing at different volumes
        for i in range(3):
            track = AudioTrack(
                id=f"track_{i}",
                name=f"Track {i}",
                url=f"/track{i}.mp3",
                volume_db=-20.0 - (i * 5)
            )
            controller.add_track(track)
            controller.play_track(f"track_{i}")

        # All playing
        assert all(t.is_playing for t in controller.tracks.values())

        # Emergency mute activated
        controller.emergency_mute()
        assert controller.state == AudioState.EMERGENCY_MUTE
        assert all(t.is_muted for t in controller.tracks.values())

        # Commands blocked
        with pytest.raises(RuntimeError):
            controller.play_track("track_0")

        # Reset from emergency
        controller.reset_from_emergency()
        assert controller.state == AudioState.IDLE
        # All volumes at safe default
        assert all(t.volume_db == -20.0 for t in controller.tracks.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
