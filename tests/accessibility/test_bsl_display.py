"""Tests for BSL display accessibility"""

import pytest
import httpx


@pytest.mark.accessibility
class TestBSLDisplay:
    """Test BSL gloss display for accessibility."""

    @pytest.mark.asyncio
    async def test_gloss_formatting(self):
        """Test BSL gloss is properly formatted."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://bsl-text2gloss-agent:8003/api/v1/translate",
                json={"text": "Hello world"},
            )

            result = response.json()

            # Gloss should be space-separated words
            gloss = result["gloss"]
            words = gloss.split()

            # All words should be uppercase
            assert all(w.isupper() for w in words)

    @pytest.mark.asyncio
    async def test_gloss_breakdown(self):
        """Test BSL gloss includes breakdown."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://bsl-text2gloss-agent:8003/api/v1/translate",
                json={"text": "How are you today?"},
            )

            result = response.json()

            # Should include breakdown
            assert "breakdown" in result

            # Breakdown should match gloss words
            breakdown = result["breakdown"]
            gloss = result["gloss"]

            assert len(breakdown) > 0
            assert all(word in gloss for word in breakdown)

    @pytest.mark.asyncio
    async def test_timing_consistency(self):
        """Test BSL translation timing consistency."""
        import time

        latencies = []

        async with httpx.AsyncClient() as client:
            for _ in range(10):
                start = time.time()
                await client.post(
                    "http://bsl-text2gloss-agent:8003/api/v1/translate",
                    json={"text": "Test message"},
                )
                latencies.append((time.time() - start) * 1000)

        # Latency should be consistent (low variance)
        import statistics
        variance = statistics.variance(latencies)
        assert variance < 100, f"Latency variance {variance} too high"

    @pytest.mark.asyncio
    async def test_regional_signs(self):
        """Test handling of regional sign variations."""
        regional_tests = [
            ("Hello", "HELLO"),
            ("Thank you", "THANK YOU"),
            ("Sorry", "SORRY"),
        ]

        for text, expected_word in regional_tests:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://bsl-text2gloss-agent:8003/api/v1/translate",
                    json={"text": text},
                )

                result = response.json()
                assert expected_word in result["gloss"]
