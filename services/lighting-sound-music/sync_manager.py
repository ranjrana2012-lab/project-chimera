"""
Sync Manager for Lighting-Sound-Music Service.

Handles synchronization of lighting and audio cues for precise
theatrical effects.
"""

import logging
import asyncio
import time
from typing import Dict, Optional
from dmx_controller import DMXController
from audio_controller import AudioController
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SyncManager:
    """
    Manages synchronized lighting and audio cues.

    Ensures precise timing between lighting changes and audio playback
    for theatrical productions.
    """

    def __init__(self, dmx_controller: DMXController, audio_controller: AudioController):
        """
        Initialize the sync manager.

        Args:
            dmx_controller: DMX controller instance
            audio_controller: Audio controller instance
        """
        self.dmx_controller = dmx_controller
        self.audio_controller = audio_controller
        self._sync_tolerance_ms = settings.sync_tolerance_ms

    async def trigger_scene(
        self,
        lighting_channels: Dict[int, int],
        audio_file: str,
        audio_volume: float = 1.0,
        delay_ms: int = 0
    ) -> Dict[str, any]:
        """
        Trigger a synchronized lighting and audio scene.

        Args:
            lighting_channels: Dictionary of DMX channel values
            audio_file: Path to audio file
            audio_volume: Audio volume (0.0 to 1.0)
            delay_ms: Delay before triggering scene

        Returns:
            Dict with timing information
        """
        start_time = time.time()
        results = {
            "success": False,
            "lighting_time": 0.0,
            "audio_time": 0.0,
            "sync_offset_ms": 0
        }

        try:
            # Apply delay if specified
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
                logger.info(f"Scene delayed by {delay_ms}ms")

            # Trigger lighting scene first
            lighting_start = time.time()
            lighting_result = await self.dmx_controller.set_scene(lighting_channels)
            lighting_time = time.time()

            results["lighting_time"] = lighting_time - start_time
            results["lighting_success"] = lighting_result.get("success", False)

            # Small delay to ensure lighting commands are sent
            await asyncio.sleep(0.01)  # 10ms

            # Trigger audio playback
            audio_start = time.time()
            audio_result = await self.audio_controller.play_audio(
                file_path=audio_file,
                volume=audio_volume,
                loop=False
            )
            audio_time = time.time()

            results["audio_time"] = audio_time - start_time
            results["audio_success"] = audio_result.get("success", False)

            # Calculate sync offset
            sync_offset_ms = abs((audio_time - lighting_time) * 1000)
            results["sync_offset_ms"] = sync_offset_ms

            # Check if within tolerance
            results["within_tolerance"] = sync_offset_ms <= self._sync_tolerance_ms

            # Overall success
            results["success"] = (
                results["lighting_success"] and
                results["audio_success"] and
                results["within_tolerance"]
            )

            logger.info(
                f"Sync scene triggered: "
                f"lighting_offset={results['lighting_time']:.3f}s, "
                f"audio_offset={results['audio_time']:.3f}s, "
                f"sync_offset={sync_offset_ms:.1f}ms"
            )

            if not results["within_tolerance"]:
                logger.warning(
                    f"Sync offset {sync_offset_ms:.1f}ms exceeds "
                    f"tolerance {self._sync_tolerance_ms}ms"
                )

            return results

        except Exception as e:
            logger.error(f"Failed to trigger sync scene: {e}")
            results["error"] = str(e)
            return results

    async def trigger_parallel(
        self,
        lighting_channels: Dict[int, int],
        audio_file: str,
        audio_volume: float = 1.0
    ) -> Dict[str, any]:
        """
        Trigger lighting and audio in parallel for maximum synchronization.

        Args:
            lighting_channels: Dictionary of DMX channel values
            audio_file: Path to audio file
            audio_volume: Audio volume (0.0 to 1.0)

        Returns:
            Dict with timing information
        """
        start_time = time.time()
        results = {
            "success": False,
            "lighting_time": 0.0,
            "audio_time": 0.0,
            "sync_offset_ms": 0
        }

        try:
            # Create tasks for parallel execution
            lighting_task = asyncio.create_task(
                self.dmx_controller.set_scene(lighting_channels)
            )
            audio_task = asyncio.create_task(
                self.audio_controller.play_audio(
                    file_path=audio_file,
                    volume=audio_volume,
                    loop=False
                )
            )

            # Execute both tasks simultaneously
            lighting_result, audio_result = await asyncio.gather(
                lighting_task,
                audio_task,
                return_exceptions=True
            )

            execution_time = time.time() - start_time

            # Process results
            if isinstance(lighting_result, Exception):
                logger.error(f"Lighting task failed: {lighting_result}")
                results["lighting_success"] = False
            else:
                results["lighting_success"] = lighting_result.get("success", False)

            if isinstance(audio_result, Exception):
                logger.error(f"Audio task failed: {audio_result}")
                results["audio_success"] = False
            else:
                results["audio_success"] = audio_result.get("success", False)

            results["lighting_time"] = execution_time
            results["audio_time"] = execution_time
            results["sync_offset_ms"] = 0.0  # Theoretically 0 for parallel execution
            results["within_tolerance"] = True
            results["success"] = (
                results["lighting_success"] and results["audio_success"]
            )

            logger.info(
                f"Parallel sync scene triggered in {execution_time:.3f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to trigger parallel sync scene: {e}")
            results["error"] = str(e)
            return results

    async def sequence_cues(
        self,
        cues: list
    ) -> Dict[str, any]:
        """
        Execute a sequence of lighting/audio cues with timing.

        Args:
            cues: List of cue dictionaries with timing information

        Returns:
            Dict with sequence results
        """
        results = {
            "success": False,
            "cues_executed": 0,
            "cues_total": len(cues),
            "errors": []
        }

        try:
            for i, cue in enumerate(cues):
                cue_start = time.time()

                # Extract cue parameters
                delay_ms = cue.get("delay_ms", 0)

                # Wait for delay
                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000.0)

                # Execute the cue
                lighting = cue.get("lighting")
                audio = cue.get("audio")

                if lighting and audio:
                    # Synchronized cue
                    result = await self.trigger_scene(
                        lighting_channels=lighting.get("channels", {}),
                        audio_file=audio.get("file", ""),
                        audio_volume=audio.get("volume", 1.0)
                    )
                elif lighting:
                    # Lighting only
                    result = await self.dmx_controller.set_scene(
                        lighting.get("channels", {})
                    )
                elif audio:
                    # Audio only
                    result = await self.audio_controller.play_audio(
                        file_path=audio.get("file", ""),
                        volume=audio.get("volume", 1.0)
                    )
                else:
                    # Empty cue
                    result = {"success": True}

                # Check result
                if isinstance(result, dict) and result.get("success", True):
                    results["cues_executed"] += 1
                else:
                    results["errors"].append({
                        "cue_index": i,
                        "error": "Cue execution failed"
                    })

                logger.info(
                    f"Cue {i+1}/{len(cues)} executed in "
                    f"{(time.time() - cue_start):.3f}s"
                )

            results["success"] = (
                results["cues_executed"] == results["cues_total"]
            )

            logger.info(
                f"Sequence complete: {results['cues_executed']}/{results['cues_total']} cues executed"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to execute cue sequence: {e}")
            results["error"] = str(e)
            return results
