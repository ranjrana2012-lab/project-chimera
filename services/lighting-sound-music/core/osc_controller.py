"""OSC Controller for stage automation"""

from typing import Dict, Any, List
import socket


class OSCController:
    def __init__(self, settings):
        self.settings = settings
        self.socket = None
        self.is_connected = False

    async def connect(self):
        """Initialize OSC client."""
        # TODO: Implement actual OSC connection
        self.is_connected = True

    async def send_message(self, address: str, value: float | int | str):
        """Send OSC message."""
        # TODO: Implement actual OSC transmission
        pass

    async def send_scene_update(self, scene_data: Dict[str, Any]):
        """Send scene update via OSC."""
        osc_address = scene_data.get("osc_address", "/lighting/scene")
        await self.send_message(osc_address, scene_data.get("name", "unnamed"))

    async def send_cue(self, cue_data: Dict[str, Any]):
        """Send lighting cue via OSC."""
        osc_address = cue_data.get("osc_address", "/lighting/cue")
        await self.send_message(osc_address, cue_data.get("number", 1))

    def close(self):
        if self.socket:
            self.socket.close()
