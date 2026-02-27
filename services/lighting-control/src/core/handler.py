"""Core handler for Lighting Control service."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..config import settings
from .sacn_controller import sACNController
from .osc_handler import OSCHandler
from .fixture_manager import FixtureManager
from .cue_executor import CueExecutor

logger = logging.getLogger(__name__)


class LightingHandler:
    """Main handler for lighting control operations.

    Integrates sACN, OSC, fixture management, and cue execution.
    """

    def __init__(self, config: settings):
        """Initialize lighting handler.

        Args:
            config: Configuration settings
        """
        self.settings = config

        # Initialize sACN controller
        self.sacn = sACNController(
            universe=config.sacn_universe,
            priority=config.sacn_priority,
            source_name=config.sacn_source_name
        )

        # Initialize OSC handler
        self.osc = OSCHandler(
            server_host=config.osc_server_host,
            server_port=config.osc_server_port,
            client_host=config.osc_client_host,
            client_port=config.osc_client_port
        )

        # Initialize fixture manager
        self.fixture_manager = FixtureManager(
            preset_path=config.preset_path
        )

        # Initialize cue executor
        self.cue_executor = CueExecutor()

        # Register callback for cue executor
        self.cue_executor.register_lighting_callback(self._apply_cue_lighting)

        # Track connection state
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all lighting subsystems."""
        if self._initialized:
            return

        logger.info("Initializing Lighting Handler...")

        # Start sACN
        if self.settings.sacn_enabled:
            if await self.sacn.start():
                logger.info("sACN controller started")
            else:
                logger.warning("sACN controller failed to start")

        # Connect OSC client
        if self.settings.osc_enabled:
            if await self.osc.connect():
                logger.info("OSC client connected")
            else:
                logger.warning("OSC client connection failed")

        # Load fixtures from config
        await self._load_fixtures()

        # Load presets
        preset_count = await self.fixture_manager.load_presets()
        logger.info(f"Loaded {preset_count} presets")

        # Create default cue list
        self.cue_executor.create_cue_list(self.settings.default_cue_list)

        # Start OSC server with command mapping
        if self.settings.osc_enabled:
            if await self.osc.start_server(self):
                logger.info("OSC server started")

        self._initialized = True
        logger.info("Lighting Handler initialized")

    async def _load_fixtures(self) -> None:
        """Load fixtures from configuration."""
        fixtures_config = self.settings.default_fixtures

        for fixture_id, config in fixtures_config.items():
            address = config.get("address", 1)
            channels = config.get("channels", 3)

            # Register with both fixture manager and sACN
            if self.fixture_manager.register_fixture(fixture_id, address, channels):
                self.sacn.register_fixture(fixture_id, address, channels)

    async def _apply_cue_lighting(
        self,
        values: Dict[int, int],
        fade_time: float
    ) -> None:
        """Apply lighting values from cue execution.

        Args:
            values: Channel values to apply
            fade_time: Fade time in seconds
        """
        await self.sacn.set_channels(values)

        if fade_time > 0:
            import asyncio
            await asyncio.sleep(fade_time)

    async def set_scene(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a lighting scene.

        Args:
            scene_data: Scene configuration

        Returns:
            Result dictionary
        """
        import time
        start_time = time.time()

        # Extract channel data
        channels = scene_data.get("channels", {})
        name = scene_data.get("name", "unnamed")

        # Set channels via sACN
        success = await self.sacn.set_channels(channels)

        # Send OSC notification
        osc_address = scene_data.get("osc_address", "/lighting/scene")
        await self.osc.send(osc_address, name)

        elapsed = time.time() - start_time

        return {
            "success": success,
            "scene": name,
            "channels_updated": len(channels),
            "time": elapsed
        }

    async def set_channel(self, channel: int, value: int) -> bool:
        """Set a single DMX channel.

        Args:
            channel: Channel number (1-512)
            value: DMX value (0-255)

        Returns:
            True if successful
        """
        return await self.sacn.set_channel(channel, value)

    async def set_fixture(
        self,
        fixture_id: str,
        channel_values: list,
        intensity: float = 1.0
    ) -> bool:
        """Set values for a fixture.

        Args:
            fixture_id: Fixture identifier
            channel_values: Channel values
            intensity: Intensity modifier

        Returns:
            True if successful
        """
        # Update fixture manager
        self.fixture_manager.update_fixture(fixture_id, channel_values, intensity)

        # Apply via sACN
        return await self.sacn.set_fixture(fixture_id, channel_values, intensity)

    async def recall_preset(
        self,
        preset_name: str,
        fade_time: Optional[float] = None
    ) -> bool:
        """Recall a lighting preset.

        Args:
            preset_name: Preset name
            fade_time: Optional fade time override

        Returns:
            True if successful
        """
        values = await self.fixture_manager.apply_preset(preset_name, fade_time)
        if values is None:
            return False

        fade = fade_time or self.fixture_manager.get_preset_fade_time(preset_name)
        return await self.sacn.set_channels(values)

    async def execute_cue(self, cue_number: str) -> Dict[str, Any]:
        """Execute a lighting cue.

        Args:
            cue_number: Cue identifier

        Returns:
            Execution result
        """
        from ..models.request import CueRequest

        request = CueRequest(
            cue_number=cue_number,
            cue_list=self.settings.default_cue_list
        )

        response = await self.cue_executor.execute_cue(request)

        return {
            "cue_number": response.cue_number,
            "executed": response.executed,
            "status": response.status,
            "timing": response.timing
        }

    async def blackout(self) -> Dict[str, Any]:
        """Blackout all lighting.

        Returns:
            Result dictionary
        """
        success = await self.sacn.blackout()
        self.fixture_manager.clear_active_preset()

        # Send OSC notification
        await self.osc.send("/lighting/blackout", 1)

        return {
            "success": success,
            "action": "blackout"
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get current lighting status.

        Returns:
            Status dictionary
        """
        return {
            "sACN": {
                "connected": self.sacn.is_active,
                "universe": self.sacn.universe,
                "priority": self.sacn.priority
            },
            "OSC": {
                "client_connected": self.osc.client_connected,
                "server_running": self.osc.server_running
            },
            "fixtures": {
                "count": len(self.fixture_manager.fixtures),
                "active": list(self.fixture_manager.fixtures.keys())
            },
            "presets": {
                "count": len(self.fixture_manager.presets),
                "active": self.fixture_manager.get_active_preset()
            },
            "cues": {
                "current": self.cue_executor.get_current_cue(),
                "statistics": self.cue_executor.get_statistics()
            }
        }

    async def close(self) -> None:
        """Close all connections and cleanup."""
        logger.info("Closing Lighting Handler...")

        # Stop cue executor
        await self.cue_executor.stop_all()

        # Close sACN
        await self.sacn.close()

        # Close OSC
        await self.osc.close()

        self._initialized = False
        logger.info("Lighting Handler closed")
