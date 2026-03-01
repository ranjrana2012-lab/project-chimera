import pytest
from unittest.mock import Mock, AsyncMock

from music_orchestration.websocket import MusicWebSocket


@pytest.mark.asyncio
async def test_subscribe_to_progress():
    ws = MusicWebSocket()
    websocket_mock = Mock()

    await ws.subscribe("request-123", websocket_mock)

    assert "request-123" in ws.active_connections


@pytest.mark.asyncio
async def test_publish_progress():
    ws = MusicWebSocket()
    websocket_mock = Mock()
    websocket_mock.send_json = AsyncMock()

    await ws.subscribe("request-123", websocket_mock)
    await ws.publish_progress(
        request_id="request-123",
        progress=50,
        stage="inference"
    )

    # Verify progress was stored
    assert ws.get_progress("request-123")["progress"] == 50
