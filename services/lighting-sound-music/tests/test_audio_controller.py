"""
Tests for Audio Controller.

Tests audio playback, volume control, and pygame integration.
"""

import pytest
from unittest.mock import patch, MagicMock
from audio_controller import AudioController


@pytest.fixture
async def controller():
    """Create an audio controller instance"""
    controller = AudioController()
    await controller.initialize()
    return controller


@pytest.mark.asyncio
async def test_initialize(controller):
    """Test audio controller initialization"""
    result = await controller.initialize()
    assert result is True


@pytest.mark.asyncio
async def test_is_ready(controller):
    """Test if controller is ready"""
    # Controller may not be ready if pygame is not installed
    is_ready = controller.is_ready()
    assert isinstance(is_ready, bool)


@pytest.mark.asyncio
async def test_play_audio_simulated(controller):
    """Test playing audio (simulated if pygame not available)"""
    with patch('pathlib.Path.exists', return_value=True):
        result = await controller.play_audio(
            file_path="/test/audio.mp3",
            volume=0.8,
            loop=False
        )

        # Should succeed (either real or simulated)
        assert result["success"] is True


@pytest.mark.asyncio
async def test_play_audio_file_not_found(controller):
    """Test playing non-existent audio file"""
    with patch('pathlib.Path.exists', return_value=False):
        result = await controller.play_audio(
            file_path="/nonexistent/audio.mp3"
        )

        assert result["success"] is False
        assert "error" in result


@pytest.mark.asyncio
async def test_stop_audio(controller):
    """Test stopping audio playback"""
    result = await controller.stop_audio()

    assert result["success"] is True


@pytest.mark.asyncio
async def test_set_volume(controller):
    """Test setting volume"""
    result = await controller.set_volume(0.5)

    assert result["success"] is True
    assert result["volume"] == 0.5


@pytest.mark.asyncio
async def test_set_volume_invalid_high(controller):
    """Test setting invalid volume (too high)"""
    result = await controller.set_volume(1.5)
    assert result["success"] is False


@pytest.mark.asyncio
async def test_set_volume_invalid_low(controller):
    """Test setting invalid volume (negative)"""
    result = await controller.set_volume(-0.1)
    assert result["success"] is False


@pytest.mark.asyncio
async def test_is_playing(controller):
    """Test checking if audio is playing"""
    controller._is_playing = True
    assert controller.is_playing() is True

    controller._is_playing = False
    assert controller.is_playing() is False


@pytest.mark.asyncio
async def test_cleanup(controller):
    """Test cleanup"""
    await controller.cleanup()

    assert not controller._initialized


@pytest.mark.asyncio
async def test_play_audio_without_pygame(controller):
    """Test playing audio when pygame is not available"""
    controller._enabled = False
    controller._initialized = True

    # Mock file existence
    with patch('pathlib.Path.exists', return_value=True):
        result = await controller.play_audio(
            file_path="/test/audio.mp3"
        )

        # Should return success but with simulated flag
        assert result["success"] is True
        assert result.get("simulated") is True
