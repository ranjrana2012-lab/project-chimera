"""Unit tests for lighting control"""

import pytest
from services.lighting_control.src.core.dmx_controller import DMXController


@pytest.mark.unit
class TestDMXController:
    """Test cases for DMXController"""

    @pytest.fixture
    def controller(self):
        return DMXController(None)

    @pytest.mark.asyncio
    async def test_set_channel(self, controller):
        """Test setting DMX channel."""
        await controller.set_channel(1, 255)
        assert controller.current_state[0] == 255

    @pytest.mark.asyncio
    async def test_blackout(self, controller):
        """Test blackout."""
        await controller.set_channel(1, 255)
        result = await controller.blackout()
        assert result["success"] is True
        assert controller.current_state[0] == 0
