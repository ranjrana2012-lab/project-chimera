#!/usr/bin/env python3
"""
Audio Controller Example Usage

Demonstrates how to use the audio system controller service.
"""

import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_controller import (
    AudioController,
    AudioTrack,
    AudioOutput
)


def create_sample_tracks():
    """Create sample audio tracks for demonstration."""
    tracks = [
        AudioTrack(
            id="dialogue",
            name="AI Dialogue",
            url="/assets/dialogue.mp3",
            volume_db=-20.0,
            max_volume_db=-6.0
        ),
        AudioTrack(
            id="music",
            name="Background Music",
            url="/assets/music.mp3",
            volume_db=-30.0,
            max_volume_db=-12.0
        ),
        AudioTrack(
            id="sfx",
            name="Sound Effects",
            url="/assets/sfx.mp3",
            volume_db=-25.0,
            max_volume_db=-10.0
        )
    ]
    return tracks


def example_basic_playback(controller):
    """Example: Basic audio playback."""
    print("\n=== Example: Basic Audio Playback ===")

    # Play dialogue track
    print("Playing dialogue track...")
    controller.play_track("dialogue", fade_in_ms=500)
    track_state = controller.get_track_state("dialogue")
    print(f"Dialogue playing: {track_state['is_playing']}")
    print(f"Dialogue volume: {track_state['volume_db']} dB")

    # Play music track
    print("\nPlaying music track...")
    controller.play_track("music", fade_in_ms=1000)
    print(f"Music playing: {controller.tracks['music'].is_playing}")


def example_volume_control(controller):
    """Example: Volume control."""
    print("\n=== Example: Volume Control ===")

    # Set individual track volume
    print("Setting dialogue volume to -15 dB...")
    controller.set_track_volume("dialogue", -15.0, ramp_ms=500)
    print(f"Dialogue volume: {controller.tracks['dialogue'].volume_db} dB")

    # Adjust volume relatively
    print("Increasing dialogue volume by 3 dB...")
    controller.tracks["dialogue"].adjust_volume(3.0)
    print(f"Dialogue volume: {controller.tracks['dialogue'].volume_db} dB")

    # Set master volume
    print("\nSetting master volume to -10 dB...")
    controller.set_master_volume(-10.0, ramp_ms=1000)
    for track_id, track in controller.tracks.items():
        print(f"{track_id} volume: {track.volume_db} dB")


def example_mute_control(controller):
    """Example: Mute control."""
    print("\n=== Example: Mute Control ===")

    # Mute individual track
    print("Muting SFX track...")
    controller.mute_track("sfx")
    print(f"SFX muted: {controller.tracks['sfx'].is_muted}")

    # Unmute
    print("Unmuting SFX track...")
    controller.unmute_track("sfx")
    print(f"SFX muted: {controller.tracks['sfx'].is_muted}")

    # Mute all
    print("\nMuting all tracks...")
    controller.mute_all()
    all_muted = all(t.is_muted for t in controller.tracks.values())
    print(f"All tracks muted: {all_muted}")
    print(f"Controller state: {controller.state.value}")

    # Unmute all
    print("\nUnmuting all tracks...")
    controller.unmute_all()
    print(f"Controller state: {controller.state.value}")


def example_track_management(controller):
    """Example: Track management."""
    print("\n=== Example: Track Management ===")

    # Add a new track
    print("Adding narration track...")
    narration = AudioTrack(
        id="narration",
        name="Narration",
        url="/assets/narration.mp3",
        volume_db=-18.0
    )
    controller.add_track(narration)
    print(f"Track count: {len(controller.tracks)}")

    # Remove track
    print("\nRemoving SFX track...")
    controller.remove_track("sfx")
    print(f"Track count: {len(controller.tracks)}")


def example_emergency_mute(controller):
    """Example: Emergency mute functionality."""
    print("\n=== Example: Emergency Mute ===")

    # Play some tracks first
    controller.play_track("dialogue")
    controller.play_track("music")
    print(f"Controller state: {controller.state.value}")

    # Emergency mute
    print("\n!!! EMERGENCY MUTE ACTIVATED !!!")
    controller.emergency_mute()

    # Check state
    print(f"Controller state: {controller.state.value}")
    all_muted = all(t.is_muted for t in controller.tracks.values())
    print(f"All tracks muted: {all_muted}")

    # Try to play (should fail)
    try:
        controller.play_track("dialogue")
    except RuntimeError as e:
        print(f"Command blocked: {e}")

    # Reset from emergency
    print("\nResetting from emergency...")
    controller.reset_from_emergency()
    print(f"Controller state: {controller.state.value}")
    print(f"All tracks at safe volume (-20 dB):")
    for track_id, track in controller.tracks.items():
        print(f"  {track_id}: {track.volume_db} dB")


def example_status_monitoring(controller):
    """Example: Monitoring controller status."""
    print("\n=== Example: Status Monitoring ===")

    status = controller.get_status()
    print(f"Sample Rate: {status['sample_rate']} Hz")
    print(f"Bit Depth: {status['bit_depth']}-bit")
    print(f"State: {status['state']}")
    print(f"Track Count: {status['track_count']}")
    print(f"Output Count: {status['output_count']}")
    print(f"Playing Tracks: {status['playing_tracks']}")
    print(f"Muted Tracks: {status['muted_tracks']}")


def example_all_tracks_state(controller):
    """Example: Getting state of all tracks."""
    print("\n=== Example: All Tracks State ===")

    all_states = controller.get_all_tracks_state()
    for track_id, state in all_states.items():
        print(f"\n{track_id}:")
        print(f"  Name: {state['name']}")
        print(f"  Volume: {state['volume_db']} dB")
        print(f"  Max Volume: {state['max_volume_db']} dB")
        print(f"  Playing: {state['is_playing']}")
        print(f"  Muted: {state['is_muted']}")


def example_audio_sequence(controller):
    """Example: Complete audio sequence."""
    print("\n=== Example: Complete Audio Sequence ===")

    print("1. Play dialogue...")
    controller.play_track("dialogue", fade_in_ms=500)

    print("2. Fade in music...")
    controller.play_track("music", fade_in_ms=2000)

    print("3. Adjust dialogue up...")
    controller.set_track_volume("dialogue", -12.0, ramp_ms=1000)

    print("4. Stop dialogue with fade out...")
    controller.stop_track("dialogue", fade_out_ms=1500)

    print("5. Music continues...")
    print(f"Music playing: {controller.tracks['music'].is_playing}")

    print("6. Stop all...")
    controller.stop_all(fade_out_ms=2000)
    print(f"Controller state: {controller.state.value}")


def main():
    """Main example function."""
    print("=" * 60)
    print("Audio Controller Example Usage")
    print("=" * 60)

    # Create controller
    controller = AudioController(sample_rate=48000, bit_depth=24)
    print(f"\nCreated Audio Controller: {controller.sample_rate}Hz, {controller.bit_depth}-bit")

    # Add tracks
    tracks = create_sample_tracks()
    for track in tracks:
        controller.add_track(track)
        print(f"Added track: {track.name}")

    # Run examples
    example_basic_playback(controller)
    example_volume_control(controller)
    example_mute_control(controller)
    example_status_monitoring(controller)
    example_all_tracks_state(controller)
    example_track_management(controller)
    example_audio_sequence(controller)
    example_emergency_mute(controller)

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
