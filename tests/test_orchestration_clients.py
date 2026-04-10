"""Tests for orchestration service clients."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.orchestration.clients import (
    ServiceClient,
    DMXClient,
    AudioClient,
    BSLClient,
    ShowOrchestrator,
)


class TestServiceClient:
    """Test base ServiceClient class."""

    def test_service_client_initialization(self):
        """Test service client initialization."""
        client = ServiceClient("http://localhost:8001/", "Test Service")
        assert client.base_url == "http://localhost:8001"
        assert client.service_name == "Test Service"

    def test_service_client_removes_trailing_slash(self):
        """Test base_url trailing slash is removed."""
        client = ServiceClient("http://localhost:8001/", "Test Service")
        assert client.base_url == "http://localhost:8001"

    def test_service_client_session_starts_none(self):
        """Test session starts as None."""
        client = ServiceClient("http://localhost:8001", "Test Service")
        assert client._session is None


class TestDMXClient:
    """Test DMXClient class."""

    def test_dmx_client_initialization(self):
        """Test DMX client with default URL."""
        client = DMXClient()
        assert client.base_url == "http://localhost:8001"
        assert client.service_name == "DMX Controller"

    def test_dmx_client_custom_url(self):
        """Test DMX client with custom URL."""
        client = DMXClient("http://dmx.example.com")
        assert client.base_url == "http://dmx.example.com"

    @pytest.mark.asyncio
    async def test_dmx_activate_scene_builds_correct_path(self):
        """Test activate_scene builds correct API path."""
        client = DMXClient()
        # Mock the _request method
        client._request = AsyncMock(return_value={"status": "ok"})

        await client.activate_scene("bright_scene")

        # Verify the correct path was used
        client._request.assert_called_once_with("POST", "/api/scenes/bright_scene/activate")

    @pytest.mark.asyncio
    async def test_dmx_set_fixture_channels_payload(self):
        """Test set_fixture_channels sends correct payload."""
        client = DMXClient()
        client._request = AsyncMock(return_value={"status": "ok"})

        await client.set_fixture_channels("fixture1", {1: 255, 2: 128})

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[0][0] == "POST"
        assert "/fixtures/fixture1/channels" in call_args[0][1]
        assert call_args[1]["json"]["channels"] == {1: 255, 2: 128}

    @pytest.mark.asyncio
    async def test_dmx_emergency_stop_path(self):
        """Test emergency_stop builds correct path."""
        client = DMXClient()
        client._request = AsyncMock(return_value={"status": "stopped"})

        await client.emergency_stop()

        client._request.assert_called_once_with("POST", "/api/emergency_stop")

    @pytest.mark.asyncio
    async def test_dmx_reset_emergency_path(self):
        """Test reset_emergency builds correct path."""
        client = DMXClient()
        client._request = AsyncMock(return_value={"status": "reset"})

        await client.reset_emergency()

        client._request.assert_called_once_with("POST", "/api/reset_emergency")

    @pytest.mark.asyncio
    async def test_dmx_get_status_path(self):
        """Test get_status builds correct path."""
        client = DMXClient()
        client._request = AsyncMock(return_value={"status": "running"})

        await client.get_status()

        client._request.assert_called_once_with("GET", "/api/status")


class TestAudioClient:
    """Test AudioClient class."""

    def test_audio_client_initialization(self):
        """Test audio client with default URL."""
        client = AudioClient()
        assert client.base_url == "http://localhost:8002"
        assert client.service_name == "Audio Controller"

    def test_audio_client_custom_url(self):
        """Test audio client with custom URL."""
        client = AudioClient("http://audio.example.com")
        assert client.base_url == "http://audio.example.com"

    @pytest.mark.asyncio
    async def test_audio_play_track_with_default_fade(self):
        """Test play_track with default fade."""
        client = AudioClient()
        client._request = AsyncMock(return_value={"status": "playing"})

        await client.play_track("track1")

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["fade_in_ms"] == 500

    @pytest.mark.asyncio
    async def test_audio_play_track_with_custom_fade(self):
        """Test play_track with custom fade."""
        client = AudioClient()
        client._request = AsyncMock(return_value={"status": "playing"})

        await client.play_track("track1", fade_in_ms=1000)

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["fade_in_ms"] == 1000

    @pytest.mark.asyncio
    async def test_audio_stop_track_with_default_fade(self):
        """Test stop_track with default fade."""
        client = AudioClient()
        client._request = AsyncMock(return_value={"status": "stopped"})

        await client.stop_track("track1")

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["fade_out_ms"] == 1000

    @pytest.mark.asyncio
    async def test_audio_set_track_volume_payload(self):
        """Test set_track_volume sends correct payload."""
        client = AudioClient()
        client._request = AsyncMock(return_value={"status": "ok"})

        await client.set_track_volume("track1", -12.5)

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["volume_db"] == -12.5

    @pytest.mark.asyncio
    async def test_audio_set_master_volume_payload(self):
        """Test set_master_volume sends correct payload."""
        client = AudioClient()
        client._request = AsyncMock(return_value={"status": "ok"})

        await client.set_master_volume(-6.0)

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["volume_db"] == -6.0

    @pytest.mark.asyncio
    async def test_audio_emergency_mute_path(self):
        """Test emergency_mute builds correct path."""
        client = AudioClient()
        client._request = AsyncMock(return_value={"status": "muted"})

        await client.emergency_mute()

        client._request.assert_called_once_with("POST", "/api/emergency_mute")


class TestBSLClient:
    """Test BSLClient class."""

    def test_bsl_client_initialization(self):
        """Test BSL client with default URL."""
        client = BSLClient()
        assert client.base_url == "http://localhost:8003"
        assert client.service_name == "BSL Avatar Service"

    def test_bsl_client_custom_url(self):
        """Test BSL client with custom URL."""
        client = BSLClient("http://bsl.example.com")
        assert client.base_url == "http://bsl.example.com"

    @pytest.mark.asyncio
    async def test_bsl_translate_default_options(self):
        """Test translate with default options."""
        client = BSLClient()
        client._request = AsyncMock(return_value={"translation": "..."})

        await client.translate("Hello")

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["text"] == "Hello"
        assert call_args[1]["json"]["include_non_manual"] is True

    @pytest.mark.asyncio
    async def test_bsl_translate_custom_options(self):
        """Test translate with custom options."""
        client = BSLClient()
        client._request = AsyncMock(return_value={"translation": "..."})

        await client.translate("Hello", include_non_manual=False)

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["include_non_manual"] is False

    @pytest.mark.asyncio
    async def test_bsl_render_without_options(self):
        """Test render without options."""
        client = BSLClient()
        client._request = AsyncMock(return_value={"render": "..."})

        await client.render("Hello")

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["text"] == "Hello"
        assert "render_options" not in call_args[1]["json"]

    @pytest.mark.asyncio
    async def test_bsl_render_with_options(self):
        """Test render with options."""
        client = BSLClient()
        client._request = AsyncMock(return_value={"render": "..."})

        await client.render("Hello", render_options={"quality": "high"})

        client._request.assert_called_once()
        call_args = client._request.call_args
        assert call_args[1]["json"]["render_options"] == {"quality": "high"}

    @pytest.mark.asyncio
    async def test_bsl_get_gestures_path(self):
        """Test get_gestures builds correct path."""
        client = BSLClient()
        client._request = AsyncMock(return_value={"gestures": []})

        await client.get_gestures()

        client._request.assert_called_once_with("GET", "/api/gestures")

    @pytest.mark.asyncio
    async def test_bsl_get_stats_path(self):
        """Test get_stats builds correct path."""
        client = BSLClient()
        client._request = AsyncMock(return_value={"stats": {}})

        await client.get_stats()

        client._request.assert_called_once_with("GET", "/api/stats")


class TestShowOrchestrator:
    """Test ShowOrchestrator class."""

    def test_orchestrator_initialization_default_urls(self):
        """Test orchestrator with default URLs."""
        orchestrator = ShowOrchestrator()
        assert isinstance(orchestrator.dmx, DMXClient)
        assert isinstance(orchestrator.audio, AudioClient)
        assert isinstance(orchestrator.bsl, BSLClient)
        assert orchestrator._current_sentiment == "neutral"

    def test_orchestrator_initialization_custom_urls(self):
        """Test orchestrator with custom URLs."""
        orchestrator = ShowOrchestrator(
            dmx_base_url="http://dmx.local",
            audio_base_url="http://audio.local",
            bsl_base_url="http://bsl.local"
        )
        assert orchestrator.dmx.base_url == "http://dmx.local"
        assert orchestrator.audio.base_url == "http://audio.local"
        assert orchestrator.bsl.base_url == "http://bsl.local"

    @pytest.mark.asyncio
    async def test_orchestrator_update_sentiment(self):
        """Test update_sentiment changes current sentiment."""
        orchestrator = ShowOrchestrator()
        await orchestrator.update_sentiment("positive")
        assert orchestrator._current_sentiment == "positive"

    @pytest.mark.asyncio
    async def test_orchestrator_execute_adaptive_scene_neutral(self):
        """Test execute_adaptive_scene with neutral sentiment."""
        orchestrator = ShowOrchestrator()
        orchestrator.dmx.activate_scene = AsyncMock(return_value={"status": "activated"})

        result = await orchestrator.execute_adaptive_scene()

        assert result["success"] is True
        assert result["scene"] == "neutral_scene"

    @pytest.mark.asyncio
    async def test_orchestrator_execute_adaptive_scene_positive(self):
        """Test execute_adaptive_scene with positive sentiment."""
        orchestrator = ShowOrchestrator()
        await orchestrator.update_sentiment("positive")
        orchestrator.dmx.activate_scene = AsyncMock(return_value={"status": "activated"})

        result = await orchestrator.execute_adaptive_scene()

        assert result["success"] is True
        assert result["scene"] == "bright_scene"

    @pytest.mark.asyncio
    async def test_orchestrator_execute_adaptive_scene_handles_error(self):
        """Test execute_adaptive_scene handles errors gracefully."""
        orchestrator = ShowOrchestrator()
        orchestrator.dmx.activate_scene = AsyncMock(side_effect=Exception("DMX down"))

        result = await orchestrator.execute_adaptive_scene()

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_orchestrator_execute_adaptive_audio_neutral(self):
        """Test execute_adaptive_audio with neutral sentiment."""
        orchestrator = ShowOrchestrator()
        orchestrator.audio.set_master_volume = AsyncMock(return_value={"status": "ok"})

        result = await orchestrator.execute_adaptive_audio()

        assert result["success"] is True
        assert result["config"]["track"] == "neutral_ambiance"
        assert result["config"]["volume"] == -15

    @pytest.mark.asyncio
    async def test_orchestrator_execute_adaptive_audio_very_positive(self):
        """Test execute_adaptive_audio with very_positive sentiment."""
        orchestrator = ShowOrchestrator()
        await orchestrator.update_sentiment("very_positive")
        orchestrator.audio.set_master_volume = AsyncMock(return_value={"status": "ok"})

        result = await orchestrator.execute_adaptive_audio()

        assert result["success"] is True
        assert result["config"]["track"] == "celebration_fanfare"
        assert result["config"]["volume"] == -8

    @pytest.mark.asyncio
    async def test_orchestrator_execute_bsl_translation(self):
        """Test execute_bsl_translation."""
        orchestrator = ShowOrchestrator()
        orchestrator.bsl.translate = AsyncMock(return_value={"translation": "..."})

        result = await orchestrator.execute_bsl_translation("Hello audience")

        assert result["success"] is True
        orchestrator.bsl.translate.assert_called_once_with("Hello audience")

    @pytest.mark.asyncio
    async def test_orchestrator_execute_bsl_translation_handles_error(self):
        """Test execute_bsl_translation handles errors gracefully."""
        orchestrator = ShowOrchestrator()
        orchestrator.bsl.translate = AsyncMock(side_effect=Exception("BSL down"))

        result = await orchestrator.execute_bsl_translation("Hello")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_orchestrator_execute_emergency_stop(self):
        """Test execute_emergency_stop calls all services."""
        orchestrator = ShowOrchestrator()
        orchestrator.dmx.emergency_stop = AsyncMock(return_value={"status": "stopped"})
        orchestrator.audio.emergency_mute = AsyncMock(return_value={"status": "muted"})

        result = await orchestrator.execute_emergency_stop()

        assert result["success"] is True
        assert result["dmx_success"] is True
        assert result["audio_success"] is True
        orchestrator.dmx.emergency_stop.assert_called_once()
        orchestrator.audio.emergency_mute.assert_called_once()

    @pytest.mark.asyncio
    async def test_orchestrator_execute_emergency_stop_partial_failure(self):
        """Test execute_emergency_stop with partial failure."""
        orchestrator = ShowOrchestrator()
        orchestrator.dmx.emergency_stop = AsyncMock(side_effect=Exception("DMX failed"))
        orchestrator.audio.emergency_mute = AsyncMock(return_value={"status": "muted"})

        result = await orchestrator.execute_emergency_stop()

        assert result["success"] is False
        assert result["dmx_success"] is False
        assert result["audio_success"] is True

    @pytest.mark.asyncio
    async def test_orchestrator_end_show_closes_connections(self):
        """Test end_show closes all client connections."""
        orchestrator = ShowOrchestrator()
        orchestrator.dmx.close = AsyncMock()
        orchestrator.audio.close = AsyncMock()
        orchestrator.bsl.close = AsyncMock()

        await orchestrator.end_show()

        orchestrator.dmx.close.assert_called_once()
        orchestrator.audio.close.assert_called_once()
        orchestrator.bsl.close.assert_called_once()
