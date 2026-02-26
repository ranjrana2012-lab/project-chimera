"""Unit tests for captioning handler"""

import pytest
from services.captioning_agent.src.core.transcriber import Transcriber


@pytest.mark.unit
class TestTranscriber:
    """Test cases for Transcriber"""

    @pytest.fixture
    def transcriber(self):
        return Transcriber(None)

    @pytest.mark.asyncio
    async def test_transcribe(self, transcriber):
        """Test transcription."""
        audio_data = b"mock_audio_data"
        result = await transcriber.transcribe(audio_data, "en")

        assert "text" in result
        assert result["language"] == "en"
        assert "confidence" in result
