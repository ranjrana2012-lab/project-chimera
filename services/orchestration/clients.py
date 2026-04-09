#!/usr/bin/env python3
"""
Service Clients for Orchestration
Project Chimera Phase 2 - Service Communication

This module provides HTTP clients for communicating with Phase 2 services.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceClient:
    """Base client for Phase 2 services."""

    def __init__(self, base_url: str, service_name: str):
        """
        Initialize service client.

        Args:
            base_url: Base URL of the service
            service_name: Name of the service
        """
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to service.

        Args:
            method: HTTP method
            path: API path
            **kwargs: Additional arguments for request

        Returns:
            Response data
        """
        session = await self._get_session()
        url = f"{self.base_url}{path}"

        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"Service error: {response.status} - {error_text}")
                    raise Exception(f"{self.service_name} returned {response.status}")

                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling {self.service_name}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if service is healthy.

        Returns:
            True if service is healthy
        """
        try:
            await self._request("GET", "/health")
            return True
        except Exception:
            return False


class DMXClient(ServiceClient):
    """Client for DMX Controller service."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        super().__init__(base_url, "DMX Controller")

    async def activate_scene(self, scene_name: str) -> Dict[str, Any]:
        """
        Activate a lighting scene.

        Args:
            scene_name: Name of scene to activate

        Returns:
            Activation result
        """
        return await self._request("POST", f"/api/scenes/{scene_name}/activate")

    async def set_fixture_channels(
        self,
        fixture_id: str,
        channels: Dict[int, int]
    ) -> Dict[str, Any]:
        """
        Set fixture channel values.

        Args:
            fixture_id: Fixture ID
            channels: Channel values

        Returns:
            Set result
        """
        return await self._request(
            "POST",
            f"/api/fixtures/{fixture_id}/channels",
            json={"channels": channels}
        )

    async def emergency_stop(self) -> Dict[str, Any]:
        """
        Activate emergency stop.

        Returns:
            Emergency stop result
        """
        return await self._request("POST", "/api/emergency_stop")

    async def reset_emergency(self) -> Dict[str, Any]:
        """
        Reset from emergency stop.

        Returns:
            Reset result
        """
        return await self._request("POST", "/api/reset_emergency")

    async def get_status(self) -> Dict[str, Any]:
        """
        Get DMX controller status.

        Returns:
            Status information
        """
        return await self._request("GET", "/api/status")


class AudioClient(ServiceClient):
    """Client for Audio Controller service."""

    def __init__(self, base_url: str = "http://localhost:8002"):
        super().__init__(base_url, "Audio Controller")

    async def play_track(
        self,
        track_id: str,
        fade_in_ms: int = 500
    ) -> Dict[str, Any]:
        """
        Play an audio track.

        Args:
            track_id: Track ID
            fade_in_ms: Fade in duration

        Returns:
            Play result
        """
        return await self._request(
            "POST",
            f"/api/tracks/{track_id}/play",
            json={"fade_in_ms": fade_in_ms}
        )

    async def stop_track(
        self,
        track_id: str,
        fade_out_ms: int = 1000
    ) -> Dict[str, Any]:
        """
        Stop an audio track.

        Args:
            track_id: Track ID
            fade_out_ms: Fade out duration

        Returns:
            Stop result
        """
        return await self._request(
            "POST",
            f"/api/tracks/{track_id}/stop",
            json={"fade_out_ms": fade_out_ms}
        )

    async def set_track_volume(
        self,
        track_id: str,
        volume_db: float
    ) -> Dict[str, Any]:
        """
        Set track volume.

        Args:
            track_id: Track ID
            volume_db: Volume in decibels

        Returns:
            Volume set result
        """
        return await self._request(
            "POST",
            f"/api/tracks/{track_id}/volume",
            json={"volume_db": volume_db}
        )

    async def set_master_volume(
        self,
        volume_db: float
    ) -> Dict[str, Any]:
        """
        Set master volume.

        Args:
            volume_db: Volume in decibels

        Returns:
            Volume set result
        """
        return await self._request(
            "POST",
            "/api/volume/master",
            json={"volume_db": volume_db}
        )

    async def emergency_mute(self) -> Dict[str, Any]:
        """
        Activate emergency mute.

        Returns:
            Emergency mute result
        """
        return await self._request("POST", "/api/emergency_mute")

    async def reset_emergency(self) -> Dict[str, Any]:
        """
        Reset from emergency mute.

        Returns:
            Reset result
        """
        return await self._request("POST", "/api/reset_emergency")

    async def get_status(self) -> Dict[str, Any]:
        """
        Get audio controller status.

        Returns:
            Status information
        """
        return await self._request("GET", "/api/status")


class BSLClient(ServiceClient):
    """Client for BSL Avatar service."""

    def __init__(self, base_url: str = "http://localhost:8003"):
        super().__init__(base_url, "BSL Avatar Service")

    async def translate(
        self,
        text: str,
        include_non_manual: bool = True
    ) -> Dict[str, Any]:
        """
        Translate text to BSL.

        Args:
            text: Text to translate
            include_non_manual: Include non-manual features

        Returns:
            Translation result
        """
        return await self._request(
            "POST",
            "/api/translate",
            json={
                "text": text,
                "include_non_manual": include_non_manual
            }
        )

    async def render(
        self,
        text: str,
        render_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Render BSL avatar.

        Args:
            text: Text to render
            render_options: Rendering options

        Returns:
            Render result
        """
        payload = {"text": text}
        if render_options:
            payload["render_options"] = render_options

        return await self._request("POST", "/api/render", json=payload)

    async def get_gestures(self) -> Dict[str, Any]:
        """
        Get available gestures.

        Returns:
            Gestures information
        """
        return await self._request("GET", "/api/gestures")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get translation statistics.

        Returns:
            Statistics
        """
        return await self._request("GET", "/api/stats")


class ShowOrchestrator:
    """
    High-level orchestrator for live shows.

    Coordinates all Phase 2 services for adaptive performances.
    """

    def __init__(
        self,
        dmx_base_url: str = "http://localhost:8001",
        audio_base_url: str = "http://localhost:8002",
        bsl_base_url: str = "http://localhost:8003"
    ):
        """Initialize show orchestrator."""
        self.dmx = DMXClient(dmx_base_url)
        self.audio = AudioClient(audio_base_url)
        self.bsl = BSLClient(bsl_base_url)

        self._current_sentiment = "neutral"

    async def start_show(self) -> None:
        """Initialize show and start services."""
        logger.info("Starting show...")

        # Check all services are healthy
        healthy = await asyncio.gather(
            self.dmx.health_check(),
            self.audio.health_check(),
            self.bsl.health_check()
        )

        if not all(healthy):
            raise Exception("Some services are unhealthy")

        logger.info("All services healthy - show started")

    async def end_show(self) -> None:
        """End show and cleanup."""
        logger.info("Ending show...")

        # Close all connections
        await asyncio.gather(
            self.dmx.close(),
            self.audio.close(),
            self.bsl.close()
        )

        logger.info("Show ended")

    async def update_sentiment(self, sentiment: str) -> None:
        """
        Update current sentiment level.

        Args:
            sentiment: Sentiment level
        """
        self._current_sentiment = sentiment
        logger.info(f"Sentiment updated to: {sentiment}")

    async def execute_adaptive_scene(self) -> Dict[str, Any]:
        """
        Execute adaptive scene based on current sentiment.

        Returns:
            Execution result
        """
        # Map sentiment to scene
        scene_map = {
            "very_negative": "somber_scene",
            "negative": "tense_scene",
            "neutral": "neutral_scene",
            "positive": "bright_scene",
            "very_positive": "celebration_scene"
        }

        scene = scene_map.get(self._current_sentiment, "neutral_scene")

        try:
            # Activate scene
            result = await self.dmx.activate_scene(scene)
            return {"success": True, "scene": scene}
        except Exception as e:
            logger.error(f"Failed to activate scene: {e}")
            return {"success": False, "error": str(e)}

    async def execute_adaptive_audio(self) -> Dict[str, Any]:
        """
        Execute adaptive audio based on current sentiment.

        Returns:
            Execution result
        """
        # Map sentiment to audio
        audio_map = {
            "very_negative": {"track": "dark_ambient", "volume": -30},
            "negative": {"track": "tension_builder", "volume": -20},
            "neutral": {"track": "neutral_ambiance", "volume": -15},
            "positive": {"track": "uplifting_melody", "volume": -10},
            "very_positive": {"track": "celebration_fanfare", "volume": -8}
        }

        config = audio_map.get(self._current_sentiment, audio_map["neutral"])

        try:
            # Set volume and play track
            await self.audio.set_master_volume(config["volume"])
            # await self.audio.play_track(config["track"])
            return {"success": True, "config": config}
        except Exception as e:
            logger.error(f"Failed to execute audio: {e}")
            return {"success": False, "error": str(e)}

    async def execute_bsl_translation(self, text: str) -> Dict[str, Any]:
        """
        Execute BSL translation.

        Args:
            text: Text to translate

        Returns:
            Translation result
        """
        try:
            result = await self.bsl.translate(text)
            return {"success": True, "translation": result}
        except Exception as e:
            logger.error(f"Failed to translate: {e}")
            return {"success": False, "error": str(e)}

    async def execute_emergency_stop(self) -> Dict[str, Any]:
        """
        Execute emergency stop across all services.

        Returns:
            Emergency stop result
        """
        logger.warning("Executing emergency stop!")

        results = await asyncio.gather(
            self.dmx.emergency_stop(),
            self.audio.emergency_mute(),
            return_exceptions=True
        )

        success = all(not isinstance(r, Exception) for r in results)

        return {
            "success": success,
            "dmx_success": not isinstance(results[0], Exception),
            "audio_success": not isinstance(results[1], Exception)
        }


# Example usage
async def main():
    """Example usage of service clients."""

    orchestrator = ShowOrchestrator()

    try:
        # Start show
        await orchestrator.start_show()

        # Update sentiment
        await orchestrator.update_sentiment("positive")

        # Execute adaptive responses
        scene_result = await orchestrator.execute_adaptive_scene()
        print(f"Scene result: {scene_result}")

        audio_result = await orchestrator.execute_adaptive_audio()
        print(f"Audio result: {audio_result}")

        # BSL translation
        bsl_result = await orchestrator.execute_bsl_translation("Hello audience!")
        print(f"BSL result: {bsl_result}")

        # Emergency stop test
        emergency_result = await orchestrator.execute_emergency_stop()
        print(f"Emergency stop result: {emergency_result}")

    finally:
        await orchestrator.end_show()


if __name__ == "__main__":
    asyncio.run(main())
