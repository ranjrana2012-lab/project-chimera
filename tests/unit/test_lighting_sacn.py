"""Unit tests for sACN controller."""

import pytest
from services.lighting_control.src.core.sacn_controller import sACNController


@pytest.mark.unit
@pytest.mark.asyncio
class TestsACNController:
    """Test cases for sACN controller."""

    @pytest.fixture
    def controller(self):
        """Create a test controller."""
        return sACNController(universe=1, priority=100)

    async def test_controller_initialization(self, controller):
        """Test controller initialization."""
        assert controller.universe == 1
        assert controller.priority == 100
        assert controller.is_active is False
        assert controller.dmx_data == [0] * 512

    async def test_set_channel(self, controller):
        """Test setting a single channel."""
        result = await controller.set_channel(1, 255)
        assert result is True
        assert controller.dmx_data[0] == 255

    async def test_set_channel_invalid(self, controller):
        """Test setting invalid channel."""
        result = await controller.set_channel(0, 255)
        assert result is False

        result = await controller.set_channel(513, 255)
        assert result is False

    async def test_set_channel_invalid_value(self, controller):
        """Test setting invalid value."""
        result = await controller.set_channel(1, -1)
        assert result is False

        result = await controller.set_channel(1, 256)
        assert result is False

    async def test_set_channels(self, controller):
        """Test setting multiple channels."""
        result = await controller.set_channels({1: 255, 2: 200, 5: 180})
        assert result is True
        assert controller.dmx_data[0] == 255
        assert controller.dmx_data[1] == 200
        assert controller.dmx_data[4] == 180

    async def test_set_channels_range(self, controller):
        """Test setting a range of channels."""
        result = await controller.set_channels_range(1, [255, 200, 180, 100])
        assert result is True
        assert controller.dmx_data[0] == 255
        assert controller.dmx_data[1] == 200
        assert controller.dmx_data[2] == 180
        assert controller.dmx_data[3] == 100

    async def test_get_channel(self, controller):
        """Test getting channel value."""
        await controller.set_channel(10, 128)
        value = await controller.get_channel(10)
        assert value == 128

    async def test_get_channel_invalid(self, controller):
        """Test getting invalid channel."""
        value = await controller.get_channel(0)
        assert value is None

        value = await controller.get_channel(513)
        assert value is None

    async def test_get_all_channels(self, controller):
        """Test getting all channels."""
        await controller.set_channels({1: 255, 2: 200})
        channels = await controller.get_all_channels()
        assert len(channels) == 512
        assert channels[0] == 255
        assert channels[1] == 200

    async def test_blackout(self, controller):
        """Test blackout."""
        await controller.set_channels({1: 255, 2: 200})
        result = await controller.blackout()
        assert result is True
        assert controller.dmx_data == [0] * 512

    async def test_register_fixture(self, controller):
        """Test fixture registration."""
        result = controller.register_fixture("stage_left", 1, 3)
        assert result is True
        assert "stage_left" in controller.fixtures
        assert controller.fixtures["stage_left"].dmx_address == 1

    async def test_register_fixture_invalid_range(self, controller):
        """Test registering fixture that exceeds DMX range."""
        result = controller.register_fixture("test", 510, 5)
        assert result is False

    async def test_set_fixture(self, controller):
        """Test setting fixture values."""
        controller.register_fixture("stage_left", 1, 3)
        result = await controller.set_fixture("stage_left", [255, 200, 180], 1.0)
        assert result is True
        assert controller.dmx_data[0] == 255
        assert controller.dmx_data[1] == 200

    async def test_set_fixture_with_intensity(self, controller):
        """Test setting fixture with intensity modifier."""
        controller.register_fixture("stage_left", 1, 3)
        result = await controller.set_fixture("stage_left", [255, 200, 180], 0.5)
        assert result is True
        assert controller.dmx_data[0] == 127  # 255 * 0.5

    async def test_get_fixture_state(self, controller):
        """Test getting fixture state."""
        controller.register_fixture("stage_left", 1, 3)
        await controller.set_fixture("stage_left", [255, 200, 180])
        state = await controller.get_fixture_state("stage_left")
        assert state is not None
        assert state.fixture_id == "stage_left"
        assert state.channel_values == [255, 200, 180]

    async def test_get_all_fixtures(self, controller):
        """Test getting all fixtures."""
        controller.register_fixture("stage_left", 1, 3)
        controller.register_fixture("stage_right", 5, 3)
        fixtures = await controller.get_all_fixtures()
        assert len(fixtures) == 2
        assert "stage_left" in fixtures
        assert "stage_right" in fixtures

    async def test_set_priority(self, controller):
        """Test setting priority."""
        result = controller.set_priority(150)
        assert result is True
        assert controller.priority == 150

    async def test_set_priority_invalid(self, controller):
        """Test setting invalid priority."""
        result = controller.set_priority(201)
        assert result is False

        result = controller.set_priority(-1)
        assert result is False

    async def test_close(self, controller):
        """Test closing controller."""
        # Should not raise exception
        await controller.close()
        assert controller.is_active is False
