"""Integration tests for Captioning + BSL pipeline"""

import pytest
import httpx


@pytest.mark.integration
class TestCaptioningBSLPipeline:
    """Test cases for Captioning to BSL gloss pipeline."""

    @pytest.mark.asyncio
    async def test_caption_to_bsl_flow(self):
        """Test captioning followed by BSL translation."""
        async with httpx.AsyncClient() as client:
            # Step 1: Transcribe audio
            caption_response = await client.post(
                "http://captioning-agent:8002/api/v1/transcribe",
                json={"audio_data": "base64_encoded_audio_placeholder"},
            )

            caption_text = caption_response.json()["text"]

            # Step 2: Translate to BSL gloss
            bsl_response = await client.post(
                "http://bsl-text2gloss-agent:8003/api/v1/translate",
                json={"text": caption_text},
            )

            result = bsl_response.json()
            assert "gloss" in result
            assert result["language"] == "bsl"
