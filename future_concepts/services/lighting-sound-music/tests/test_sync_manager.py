"""
Tests for Sync Manager.

Tests synchronization of lighting and audio cues.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sync_manager import SyncManager
from dmx_controller import DMXController
from audio_controller import AudioController


@pytest.fixture
async def sync_manager():
    """Create a sync manager instance"""
    dmx = DMXController()
    audio = AudioController()
    await dmx.initialize()
    await audio.initialize()

    manager = SyncManager(dmx, audio)
    return manager


@pytest.mark.asyncio
async def test_trigger_scene(sync_manager):
    """Test triggering a synchronized scene"""
    # Mock the controllers
    sync_manager.dmx_controller.set_scene = AsyncMock(
        return_value={"success": True, "channels_set": 3}
    )
    sync_manager.audio_controller.play_audio = AsyncMock(
        return_value={"success": True, "file": "/test.mp3"}
    )

    result = await sync_manager.trigger_scene(
        lighting_channels={1: 255, 2: 128, 3: 0},
        audio_file="/test.mp3",
        audio_volume=0.8,
        delay_ms=0
    )

    assert result["success"] is True
    assert result["lighting_success"] is True
    assert result["audio_success"] is True
    assert "lighting_time" in result
    assert "audio_time" in result
    assert "sync_offset_ms" in result


@pytest.mark.asyncio
async def test_trigger_scene_with_delay(sync_manager):
    """Test triggering a scene with delay"""
    # Mock the controllers
    sync_manager.dmx_controller.set_scene = AsyncMock(
        return_value={"success": True, "channels_set": 2}
    )
    sync_manager.audio_controller.play_audio = AsyncMock(
        return_value={"success": True}
    )

    import time
    start = time.time()

    result = await sync_manager.trigger_scene(
        lighting_channels={1: 255},
        audio_file="/test.mp3",
        delay_ms=100  # 100ms delay
    )

    duration = time.time() - start

    # Should take at least 100ms
    assert duration >= 0.1
    assert result["success"] is True


@pytest.mark.asyncio
async def test_trigger_parallel(sync_manager):
    """Test parallel execution of lighting and audio"""
    # Mock the controllers
    sync_manager.dmx_controller.set_scene = AsyncMock(
        return_value={"success": True, "channels_set": 2}
    )
    sync_manager.audio_controller.play_audio = AsyncMock(
        return_value={"success": True}
    )

    result = await sync_manager.trigger_parallel(
        lighting_channels={1: 255, 2: 128},
        audio_file="/test.mp3",
        audio_volume=0.9
    )

    assert result["success"] is True
    assert result["lighting_success"] is True
    assert result["audio_success"] is True
    # Parallel execution should have minimal offset
    assert result["sync_offset_ms"] == 0.0


@pytest.mark.asyncio
async def test_sequence_cues(sync_manager):
    """Test executing a sequence of cues"""
    # Mock the controllers
    sync_manager.dmx_controller.set_scene = AsyncMock(
        return_value={"success": True, "channels_set": 2}
    )
    sync_manager.audio_controller.play_audio = AsyncMock(
        return_value={"success": True}
    )

    cues = [
        {
            "delay_ms": 0,
            "lighting": {"channels": {1: 255}},
            "audio": {"file": "/cue1.mp3", "volume": 0.8}
        },
        {
            "delay_ms": 100,
            "lighting": {"channels": {1: 128}}
        },
        {
            "delay_ms": 50,
            "audio": {"file": "/cue3.mp3", "volume": 1.0}
        }
    ]

    result = await sync_manager.sequence_cues(cues)

    assert result["success"] is True
    assert result["cues_executed"] == 3
    assert result["cues_total"] == 3


@pytest.mark.asyncio
async def test_sequence_cues_with_errors(sync_manager):
    """Test sequence with some cues failing"""
    # Mock controllers with mixed success
    async def mock_set_scene(channels):
        # Fail on second call
        if mock_set_scene.call_count == 2:
            return {"success": False}
        mock_set_scene.call_count += 1
        return {"success": True, "channels_set": len(channels)}

    mock_set_scene.call_count = 1

    sync_manager.dmx_controller.set_scene = mock_set_scene
    sync_manager.audio_controller.play_audio = AsyncMock(
        return_value={"success": True}
    )

    cues = [
        {
            "lighting": {"channels": {1: 255}},
            "audio": {"file": "/cue1.mp3"}
        },
        {
            "lighting": {"channels": {1: 128}}
        },
        {
            "lighting": {"channels": {1: 0}}
        }
    ]

    result = await sync_manager.sequence_cues(cues)

    # Should not be all successful
    assert result["cues_executed"] < result["cues_total"]
    assert len(result["errors"]) > 0


@pytest.mark.asyncio
async def test_trigger_scene_lighting_failure(sync_manager):
    """Test sync scene when lighting fails"""
    sync_manager.dmx_controller.set_scene = AsyncMock(
        return_value={"success": False}
    )
    sync_manager.audio_controller.play_audio = AsyncMock(
        return_value={"success": True}
    )

    result = await sync_manager.trigger_scene(
        lighting_channels={1: 255},
        audio_file="/test.mp3"
    )

    assert result["success"] is False
    assert result["lighting_success"] is False
    assert result["audio_success"] is True


@pytest.mark.asyncio
async def test_trigger_scene_audio_failure(sync_manager):
    """Test sync scene when audio fails"""
    sync_manager.dmx_controller.set_scene = AsyncMock(
        return_value={"success": True, "channels_set": 2}
    )
    sync_manager.audio_controller.play_audio = AsyncMock(
        return_value={"success": False}
    )

    result = await sync_manager.trigger_scene(
        lighting_channels={1: 255},
        audio_file="/test.mp3"
    )

    assert result["success"] is False
    assert result["lighting_success"] is True
    assert result["audio_success"] is False
