#!/usr/bin/env python3
"""
Audio Controller Service
Project Chimera Phase 2 - Hardware Integration Layer

This service provides audio system control for live theatrical performances.
It implements safe audio control with emergency mute functionality.

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


class AudioState(Enum):
    """Audio system states."""
    IDLE = "idle"
    PLAYING = "playing"
    MUTED = "muted"
    EMERGENCY_MUTE = "emergency_mute"
    FAULT = "fault"


@dataclass
class AudioTrack:
    """Represents an audio track."""
    id: str
    name: str
    url: str
    volume_db: float = -20.0  # Default to -20dB (safe level)
    max_volume_db: float = -6.0   # Safety limit
    is_playing: bool = False
    is_muted: bool = False

    def __post_init__(self):
        """Validate audio track configuration."""
        if self.volume_db > self.max_volume_db:
            raise ValueError(f"Volume {self.volume_db}dB exceeds maximum {self.max_volume_db}dB")
        if self.volume_db < -60:
            raise ValueError(f"Volume {self.volume_db}dB below minimum -60dB")

    def set_volume(self, volume_db: float) -> None:
        """
        Set track volume.

        Args:
            volume_db: Volume in decibels (-60 to 0)
        """
        volume_db = max(-60, min(volume_db, self.max_volume_db))
        self.volume_db = volume_db
        logger.debug(f"Track {self.id} volume set to {volume_db}dB")

    def adjust_volume(self, adjustment_db: float) -> None:
        """
        Adjust track volume by a relative amount.

        Args:
            adjustment_db: Adjustment in decibels
        """
        new_volume = self.volume_db + adjustment_db
        self.set_volume(new_volume_db)

    def play(self) -> None:
        """Start playing the track."""
        self.is_playing = True
        self.is_muted = False
        logger.info(f"Track {self.id} ({self.name}) playing")

    def stop(self, fade_out_ms: int = 1000) -> None:
        """
        Stop playing the track.

        Args:
            fade_out_ms: Fade out time in milliseconds
        """
        if fade_out_ms > 0:
            logger.debug(f"Track {self.id} fading out over {fade_out_ms}ms")
            # In real implementation, would handle fade out
        self.is_playing = False
        logger.info(f"Track {self.id} ({self.name}) stopped")

    def mute(self) -> None:
        """Mute the track."""
        self.is_muted = True
        logger.info(f"Track {self.id} ({self.name}) muted")

    def unmute(self) -> None:
        """Unmute the track."""
        self.is_muted = False
        logger.info(f"Track {self.id} ({self.id}) unmuted")


@dataclass
class AudioOutput:
    """Represents an audio output destination."""
    id: str
    name: str
    output_type: str  # "main", "monitor", "subwoofer", etc.
    channels: List[int]  # Channel assignments


class AudioController:
    """
    Audio System Controller

    Manages audio playback for live theatrical performances
    with safe volume control and emergency mute functionality.
    """

    def __init__(self, sample_rate: int = 48000, bit_depth: int = 24):
        """
        Initialize audio controller.

        Args:
            sample_rate: Audio sample rate in Hz (default: 48000)
            bit_depth: Audio bit depth (default: 24)
        """
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.state = AudioState.IDLE

        self.tracks: Dict[str, AudioTrack] = {}
        self.outputs: Dict[str, AudioOutput] = {}

        self._emergency_mute_callback = None
        self._last_update_time = None

        # Initialize default outputs
        self._init_default_outputs()

        logger.info(f"Audio Controller initialized: {sample_rate}Hz, {bit_depth}-bit")

    def _init_default_outputs(self) -> None:
        """Initialize default audio outputs."""
        self.outputs["main"] = AudioOutput(
            id="main",
            name="Main Speakers",
            output_type="stereo",
            channels=[1, 2]
        )
        self.outputs["monitor"] = AudioOutput(
            id="monitor",
            name="Monitor Speakers",
            output_type="stereo",
            channels=[3, 4]
        )
        self.outputs["subwoofer"] = AudioOutput(
            id="sub",
            name="Subwoofer",
            output_type="mono",
            channels=[5]
        )

    def add_track(self, track: AudioTrack) -> None:
        """
        Add an audio track.

        Args:
            track: AudioTrack to add
        """
        self.tracks[track.id] = track
        logger.info(f"Track added: {track.id} ({track.name})")

    def remove_track(self, track_id: str) -> None:
        """
        Remove an audio track.

        Args:
            track_id: ID of track to remove
        """
        if track_id in self.tracks:
            del self.tracks[track_id]
            logger.info(f"Track removed: {track_id}")

    def play_track(self, track_id: str, fade_in_ms: int = 500) -> None:
        """
        Play an audio track.

        Args:
            track_id: ID of track to play
            fade_in_ms: Fade in time in milliseconds
        """
        self._check_emergency_mute()

        if track_id not in self.tracks:
            raise ValueError(f"Track {track_id} not found")

        track = self.tracks[track_id]

        if fade_in_ms > 0:
            logger.debug(f"Track {track_id} fading in over {fade_in_ms}ms")
            # In real implementation, would handle fade in

        track.play()
        self.state = AudioState.PLAYING
        self._last_update_time = datetime.now()

    def stop_track(self, track_id: str, fade_out_ms: int = 1000) -> None:
        """
        Stop an audio track.

        Args:
            track_id: ID of track to stop
            fade_out_ms: Fade out time in milliseconds
        """
        self._check_emergency_mute()

        if track_id not in self.tracks:
            raise ValueError(f"Track {track_id} not found")

        track = self.tracks[track_id]
        track.stop(fade_out_ms)

        # Check if any tracks are still playing
        if not any(t.is_playing for t in self.tracks.values()):
            self.state = AudioState.IDLE

        self._last_update_time = datetime.now()

    def stop_all(self, fade_out_ms: int = 1000) -> None:
        """
        Stop all playing tracks.

        Args:
            fade_out_ms: Fade out time in milliseconds
        """
        logger.info(f"Stopping all tracks (fade out: {fade_out_ms}ms)")

        for track in self.tracks.values():
            if track.is_playing:
                track.stop(fade_out_ms)

        self.state = AudioState.IDLE
        self._last_update_time = datetime.now()

    def set_track_volume(self, track_id: str, volume_db: float, ramp_ms: int = 500) -> None:
        """
        Set track volume.

        Args:
            track_id: ID of track
            volume_db: Volume in decibels
            ramp_ms: Volume ramp time in milliseconds
        """
        self._check_emergency_mute()

        if track_id not in self.tracks:
            raise ValueError(f"Track {track_id} not found")

        track = self.tracks[track_id]

        if ramp_ms > 0:
            logger.debug(f"Track {track_id} volume ramping to {volume_db}dB over {ramp_ms}ms")
            # In real implementation, would handle volume ramp

        track.set_volume(volume_db)
        self._last_update_time = datetime.now()

    def set_master_volume(self, volume_db: float, ramp_ms: int = 500) -> None:
        """
        Set volume for all tracks.

        Args:
            volume_db: Volume in decibels
            ramp_ms: Volume ramp time in milliseconds
        """
        self._check_emergency_mute()

        logger.info(f"Setting master volume to {volume_db}dB (ramp: {ramp_ms}ms)")

        for track in self.tracks.values():
            if ramp_ms > 0:
                logger.debug(f"Track {track.id} volume ramping to {volume_db}dB over {ramp_ms}ms")
            track.set_volume(volume_db)

        self._last_update_time = datetime.now()

    def mute_track(self, track_id: str) -> None:
        """
        Mute a specific track.

        Args:
            track_id: ID of track to mute
        """
        if track_id not in self.tracks:
            raise ValueError(f"Track {track_id} not found")

        self.tracks[track_id].mute()
        self._last_update_time = datetime.now()

    def unmute_track(self, track_id: str) -> None:
        """
        Unmute a specific track.

        Args:
            track_id: ID of track to unmute
        """
        if track_id not in self.tracks:
            raise ValueError(f"Track {track_id} not found")

        self.tracks[track_id].unmute()
        self._last_update_time = datetime.now()

    def mute_all(self) -> None:
        """Mute all tracks."""
        logger.info("Muting all tracks")
        for track in self.tracks.values():
            track.mute()
        self.state = AudioState.MUTED
        self._last_update_time = datetime.now()

    def unmute_all(self) -> None:
        """Unmute all tracks."""
        logger.info("Unmuting all tracks")
        for track in self.tracks.values():
            track.unmute()
        self.state = AudioState.IDLE if not any(t.is_playing for t in self.tracks.values()) else AudioState.PLAYING
        self._last_update_time = datetime.now()

    def emergency_mute(self) -> None:
        """
        Activate emergency mute - immediately mute all audio.

        This is a safety-critical function that must work instantly.
        """
        logger.warning("EMERGENCY MUTE ACTIVATED")
        self.state = AudioState.EMERGENCY_MUTE

        # Mute all tracks instantly
        for track in self.tracks.values():
            track.is_muted = True
            # In real implementation, would also cut audio output

        self._last_update_time = datetime.now()

        # Call emergency mute callback if registered
        if self._emergency_mute_callback:
            self._emergency_mute_callback()

    def reset_from_emergency(self) -> None:
        """
        Reset from emergency mute state.

        This should only be called after the emergency situation is resolved.
        """
        if self.state != AudioState.EMERGENCY_MUTE:
            logger.warning("Cannot reset: not in emergency mute state")
            return

        logger.info("Resetting from emergency mute")
        self.state = AudioState.IDLE

        # Unmute all tracks at safe volume (-20dB)
        for track in self.tracks.values():
            track.is_muted = False
            track.set_volume(-20.0)  # Safe default

        self._last_update_time = datetime.now()

    def set_emergency_mute_callback(self, callback) -> None:
        """
        Register a callback for emergency mute events.

        Args:
            callback: Function to call when emergency mute is activated
        """
        self._emergency_mute_callback = callback
        logger.info("Emergency mute callback registered")

    def _check_emergency_mute(self) -> None:
        """Check if system is in emergency mute state."""
        if self.state == AudioState.EMERGENCY_MUTE:
            raise RuntimeError("System in emergency mute state - cannot execute commands")

    def get_track_state(self, track_id: str) -> Dict:
        """
        Get state of an audio track.

        Args:
            track_id: Track ID

        Returns:
            Dictionary containing track state
        """
        if track_id not in self.tracks:
            raise ValueError(f"Track {track_id} not found")

        track = self.tracks[track_id]
        return {
            "id": track.id,
            "name": track.name,
            "volume_db": track.volume_db,
            "is_playing": track.is_playing,
            "is_muted": track.is_muted,
            "max_volume_db": track.max_volume_db
        }

    def get_all_tracks_state(self) -> Dict[str, Dict]:
        """
        Get state of all tracks.

        Returns:
            Dictionary of track_id -> track state
        """
        return {
            track_id: self.get_track_state(track_id)
            for track_id in self.tracks.keys()
        }

    def get_status(self) -> Dict:
        """
        Get system status.

        Returns:
            Dictionary containing system status information
        """
        playing_tracks = [tid for tid, track in self.tracks.items() if track.is_playing]
        muted_tracks = [tid for tid, track in self.tracks.items() if track.is_muted]

        return {
            "sample_rate": self.sample_rate,
            "bit_depth": self.bit_depth,
            "state": self.state.value,
            "track_count": len(self.tracks),
            "output_count": len(self.outputs),
            "playing_tracks": playing_tracks,
            "muted_tracks": muted_tracks,
            "last_update": self._last_update_time.isoformat() if self._last_update_time else None
        }


# Example usage and testing
async def main():
    """Example usage of audio controller."""

    # Create controller
    controller = AudioController(sample_rate=48000, bit_depth=24)

    # Add some tracks
    dialogue_track = AudioTrack(
        id="dialogue",
        name="AI Dialogue",
        url="/assets/dialogue.mp3",
        volume_db=-20,
        max_volume_db=-6
    )

    music_track = AudioTrack(
        id="music",
        name="Background Music",
        url="/assets/music.mp3",
        volume_db=-30,
        max_volume_db=-12
    )

    controller.add_track(dialogue_track)
    controller.add_track(music_track)

    # Play a track
    controller.play_track("dialogue", fade_in_ms=500)

    # Get status
    status = controller.get_status()
    print(f"Audio Controller Status: {status}")

    # Adjust volume
    controller.set_track_volume("dialogue", -15, ramp_ms=1000)

    # Play another track
    controller.play_track("music", fade_in_ms=1000)

    # Stop all tracks
    controller.stop_all(fade_out_ms=2000)

    # Emergency mute test
    print("\nTesting emergency mute...")
    controller.emergency_mute()
    print(f"Status after emergency mute: {controller.get_status()}")

    # Reset from emergency
    print("\nResetting from emergency...")
    controller.reset_from_emergency()
    print(f"Status after reset: {controller.get_status()}")


if __name__ == "__main__":
    asyncio.run(main())
