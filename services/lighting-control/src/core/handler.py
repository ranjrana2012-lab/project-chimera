"""Core handler for Lighting Control"""

from typing import Dict, Any
from .dmx_controller import DMXController
from .osc_controller import OSCController


class LightingHandler:
    def __init__(self, settings):
        self.settings = settings
        self.dmx = DMXController(settings)
        self.osc = OSCController(settings)

    async def initialize(self):
        await self.dmx.connect()
        await self.osc.connect()

    async def set_scene(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply lighting scene."""
        result = await self.dmx.set_scene(scene_data)
        await self.osc.send_scene_update(scene_data)
        return result

    async def blackout(self) -> Dict[str, Any]:
        """Blackout all lights."""
        return await self.dmx.blackout()

    async def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "dmx_connected": self.dmx.is_connected,
            "osc_connected": self.osc.is_connected,
            "current_scene": await self.dmx.get_current_scene(),
        }

    async def close(self):
        await self.dmx.close()
        await self.osc.close()
