"""Tests for LTX client"""

import pytest
from unittest.mock import AsyncMock, patch
from ltx_client import LTXAPIClient
from models import LTXVideoRequest, Resolution, LTXModel


@pytest.mark.asyncio
async def test_ltx_client_initialization():
    """Test LTX client initialization"""

    client = LTXAPIClient(
        api_key="test-key",
        api_base="https://api.test.com/v1"
    )

    assert client.api_key == "test-key"
    assert client.api_base == "https://api.test.com/v1"


@pytest.mark.asyncio
async def test_text_to_video_request_format():
    """Test that video generation request is formatted correctly"""

    request = LTXVideoRequest(
        prompt="Test video",
        duration=10,
        resolution=Resolution.HD,
        fps=24,
        model=LTXModel.PRO,
        generate_audio=True
    )

    assert request.prompt == "Test video"
    assert request.duration == 10
    assert request.resolution == Resolution.HD
    assert request.fps == 24
    assert request.model == LTXModel.PRO
