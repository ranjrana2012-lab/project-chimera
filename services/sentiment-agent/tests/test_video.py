"""Tests for sentiment agent video capabilities"""

import pytest
from unittest.mock import AsyncMock, patch
from sentiment_agent.video.briefing import SentimentBriefingGenerator


@pytest.mark.asyncio
async def test_sentiment_briefing_generation():
    """Test sentiment briefing generation"""
    generator = SentimentBriefingGenerator(
        visual_core_url="http://visual-core:8014"
    )

    with patch.object(generator, "_generate_video", return_value="http://example.com/video.mp4"):
        result = await generator.create_briefing(
            topic="Test Brand",
            timeframe="7d",
            style="corporate_briefing",
            duration=60
        )

        assert "briefing_id" in result
        assert result["video_url"] == "http://example.com/video.mp4"
        assert result["topic"] == "Test Brand"
