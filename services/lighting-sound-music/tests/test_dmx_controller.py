"""
Tests for DMX Controller.

Tests DMX channel control, scene setting, and mock implementation.
"""

import pytest
import asyncio
from dmx_controller import DMXController


@pytest.fixture
async def controller():
    """Create a DMX controller instance"""
    controller = DMXController()
    await controller.initialize()
    return controller


@pytest.mark.asyncio
async def test_initialize(controller):
    """Test DMX controller initialization"""
    assert controller.is_ready()


@pytest.mark.asyncio
async def test_set_single_channel(controller):
    """Test setting a single DMX channel"""
    result = await controller.set_channel(1, 255)

    assert result["success"] is True
    assert result["channel"] == 1
    assert result["value"] == 255

    # Verify the value was stored
    stored_value = await controller.get_channel_value(1)
    assert stored_value == 255


@pytest.mark.asyncio
async def test_set_invalid_channel(controller):
    """Test setting an invalid DMX channel"""
    with pytest.raises(ValueError, match="Invalid DMX channel"):
        await controller.set_channel(0, 255)

    with pytest.raises(ValueError, match="Invalid DMX channel"):
        await controller.set_channel(513, 255)


@pytest.mark.asyncio
async def test_set_invalid_value(controller):
    """Test setting an invalid DMX value"""
    with pytest.raises(ValueError, match="Invalid DMX value"):
        await controller.set_channel(1, -1)

    with pytest.raises(ValueError, match="Invalid DMX value"):
        await controller.set_channel(1, 256)


@pytest.mark.asyncio
async def test_set_scene(controller):
    """Test setting a lighting scene with multiple channels"""
    channels = {
        1: 255,
        2: 128,
        3: 0,
        10: 200
    }

    result = await controller.set_scene(channels)

    assert result["success"] is True
    assert result["channels_set"] == len(channels)

    # Verify all values were stored
    all_values = await controller.get_all_values()
    for channel, value in channels.items():
        assert all_values[channel] == value


@pytest.mark.asyncio
async def test_set_scene_with_invalid_channels(controller):
    """Test setting a scene with some invalid channels"""
    channels = {
        1: 255,
        0: 128,  # Invalid channel
        513: 100,  # Invalid channel
        3: 0
    }

    result = await controller.set_scene(channels)

    assert result["success"] is True
    # Should only set valid channels
    assert result["channels_set"] == 2


@pytest.mark.asyncio
async def test_reset(controller):
    """Test resetting all DMX channels"""
    # Set some channels
    await controller.set_channel(1, 255)
    await controller.set_channel(2, 128)

    # Reset
    result = await controller.reset()

    assert result is True

    # Verify all channels are 0
    value1 = await controller.get_channel_value(1)
    value2 = await controller.get_channel_value(2)
    assert value1 == 0
    assert value2 == 0


@pytest.mark.asyncio
async def test_blackout(controller):
    """Test blackout functionality"""
    # Set some channels
    await controller.set_channel(1, 255)
    await controller.set_channel(2, 200)

    # Blackout
    result = await controller.blackout()

    assert result is True

    # Verify all channels are 0
    value1 = await controller.get_channel_value(1)
    assert value1 == 0


@pytest.mark.asyncio
async def test_get_channel_value_unset(controller):
    """Test getting value of unset channel"""
    value = await controller.get_channel_value(999)
    assert value is None


@pytest.mark.asyncio
async def test_get_all_values_empty(controller):
    """Test getting all values when no channels set"""
    values = await controller.get_all_values()
    assert isinstance(values, dict)
    # May be empty or have channels set to 0
