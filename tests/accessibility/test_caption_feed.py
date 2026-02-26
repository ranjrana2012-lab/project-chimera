"""Tests for caption feed accessibility"""

import pytest
import httpx


@pytest.mark.accessibility
class TestCaptionFeed:
    """Test caption feed for accessibility compliance."""

    @pytest.mark.asyncio
    async def test_caption_timing(self):
        """Test that captions are delivered with appropriate timing."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = httpx._main._current_time
            response = await client.post(
                "http://captioning-agent:8002/api/v1/transcribe",
                json={"audio_data": "base64_audio"},
            )

            latency_ms = (httpx._main._current_time - start) * 1000

            # Captions should be delivered quickly (< 2s for accessibility)
            assert latency_ms < 2000

    @pytest.mark.asyncio
    async def test_caption_accuracy(self):
        """Test caption accuracy metrics."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://captioning-agent:8002/api/v1/transcribe",
                json={"audio_data": "base64_audio"},
            )

            result = response.json()

            # Should include confidence score
            assert "confidence" in result

            # Confidence should be reasonably high
            assert result["confidence"] > 0.7

    @pytest.mark.asyncio
    async def test_multilingual_support(self):
        """Test multilingual caption support."""
        languages = ["en", "es", "fr", "de"]

        for lang in languages:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://captioning-agent:8002/api/v1/transcribe",
                    json={
                        "audio_data": "base64_audio",
                        "language": lang,
                    },
                )

                assert response.status_code == 200
                result = response.json()
                assert result["language"] == lang
