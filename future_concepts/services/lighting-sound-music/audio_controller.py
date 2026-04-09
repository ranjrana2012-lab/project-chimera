"""
Audio Controller for Lighting-Sound-Music Service.

Handles audio playback using pygame for cross-platform audio support.
"""

import logging
import asyncio
from typing import Optional, Dict
from pathlib import Path
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AudioController:
    """
    Audio playback controller using pygame.

    Provides functionality for playing audio files, controlling volume,
    and managing playback state for theatre productions.
    """

    def __init__(self):
        """Initialize the audio controller"""
        self._initialized = False
        self._enabled = settings.audio_enabled
        self._current_volume = 1.0
        self._current_channel = None
        self._is_playing = False
        self._pygame_mixer = None
        self._pygame = None

    async def initialize(self) -> bool:
        """
        Initialize the audio controller and pygame mixer.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        try:
            logger.info("Initializing audio controller")

            # Import pygame (lazy import to avoid dependency issues)
            try:
                import pygame
                self._pygame = pygame

                # Initialize pygame mixer with settings
                pygame.mixer.init(
                    frequency=settings.audio_sample_rate,
                    channels=settings.audio_channels,
                    buffer=settings.audio_buffer_size
                )

                self._pygame_mixer = pygame.mixer
                self._initialized = True

                logger.info(
                    f"Audio controller initialized: "
                    f"{settings.audio_sample_rate}Hz, "
                    f"{settings.audio_channels} channels"
                )
                return True

            except ImportError:
                logger.warning(
                    "pygame not available - audio will be simulated. "
                    "Install with: pip install pygame"
                )
                self._enabled = False
                self._initialized = True  # Mark as initialized but disabled
                return True

        except Exception as e:
            logger.error(f"Failed to initialize audio controller: {e}")
            self._enabled = False
            self._initialized = True  # Mark as initialized to avoid retries
            return False

    def is_ready(self) -> bool:
        """
        Check if the audio controller is ready.

        Returns:
            True if ready to play audio
        """
        return self._initialized and self._enabled

    async def play_audio(
        self,
        file_path: str,
        volume: float = 1.0,
        loop: bool = False
    ) -> Dict[str, any]:
        """
        Play an audio file.

        Args:
            file_path: Path to audio file
            volume: Volume level (0.0 to 1.0)
            loop: Whether to loop the audio

        Returns:
            Dict with operation result
        """
        if not self.is_ready():
            # Validate file exists first (even when simulating)
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Audio file not found: {file_path}"
                }

            logger.warning("Audio controller not ready, simulating playback")
            logger.warning("Audio controller not ready, simulating playback")
            return {
                "success": True,
                "simulated": True,
                "message": "Audio playback simulated (pygame not available)"
            }

        try:
            # Stop any currently playing audio
            if self._is_playing:
                self.stop()

            # Load and play the audio
            sound = self._pygame_mixer.Sound(str(file_path))
            loops = -1 if loop else 0
            self._current_channel = sound.play(loops=loops)

            if self._current_channel:
                # Set volume
                self._current_channel.set_volume(volume)
                self._current_volume = volume
                self._is_playing = True

                logger.info(
                    f"Playing audio: {file_path} "
                    f"(volume={volume:.2f}, loop={loop})"
                )

                return {
                    "success": True,
                    "file": file_path,
                    "volume": volume,
                    "loop": loop,
                    "channel": self._current_channel.get_busy()
                }

            else:
                raise RuntimeError("Failed to play audio - no available channel")

        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def stop_audio(self) -> Dict[str, any]:
        """
        Stop currently playing audio.

        Returns:
            Dict with operation result
        """
        if not self.is_ready():
            return {
                "success": True,
                "message": "Audio not enabled"
            }

        try:
            if self._pygame_mixer:
                self._pygame_mixer.stop()
                self._is_playing = False
                self._current_channel = None

                logger.info("Audio playback stopped")

                return {
                    "success": True,
                    "message": "Audio stopped successfully"
                }

            else:
                return {
                    "success": False,
                    "error": "Audio mixer not initialized"
                }

        except Exception as e:
            logger.error(f"Failed to stop audio: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def set_volume(self, volume: float) -> Dict[str, any]:
        """
        Set the master volume.

        Args:
            volume: Volume level (0.0 to 1.0)

        Returns:
            Dict with operation result
        """
        try:
            # Validate volume range first
            if not 0.0 <= volume <= 1.0:
                return {
                    "success": False,
                    "error": f"Volume must be between 0.0 and 1.0, got {volume}"
                }

            if not self.is_ready():
                return {
                    "success": True,
                    "volume": volume,
                    "message": "Audio not enabled"
                }

            if self._current_channel and self._is_playing:
                self._current_channel.set_volume(volume)

            self._current_volume = volume
            logger.info(f"Volume set to {volume:.2f}")

            return {
                "success": True,
                "volume": volume
            }

        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing.

        Returns:
            True if audio is playing
        """
        if not self.is_ready():
            return self._is_playing

        if self._pygame_mixer:
            return self._pygame_mixer.music.get_busy() or self._is_playing

        return self._is_playing

    async def cleanup(self) -> None:
        """
        Cleanup audio resources.
        """
        try:
            if self._pygame_mixer:
                self._pygame_mixer.stop()
                self._pygame_mixer.quit()

            self._initialized = False
            self._is_playing = False
            self._current_channel = None

            logger.info("Audio controller cleaned up")

        except Exception as e:
            logger.error(f"Error during audio cleanup: {e}")

    def stop(self):
        """Stop audio playback (synchronous for internal use)"""
        if self._pygame_mixer:
            self._pygame_mixer.stop()
            self._is_playing = False
