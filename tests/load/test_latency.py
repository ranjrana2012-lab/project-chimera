"""Latency benchmark tests"""

import pytest
import httpx
import time
import statistics


@pytest.mark.load
class TestLatency:
    """Test latency under various conditions."""

    @pytest.mark.asyncio
    async def test_scenespeak_p95_latency(self):
        """Measure p95 latency for SceneSpeak."""
        latencies = []

        async with httpx.AsyncClient() as client:
            for _ in range(100):
                start = time.time()
                response = await client.post(
                    "http://scenespeak-agent:8001/api/v1/generate",
                    json={
                        "scene_context": {"title": "Latency Test"},
                        "dialogue_context": [],
                    },
                    timeout=10.0,
                )
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)

        p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        assert p95 < 3000, f"P95 latency {p95}ms exceeds 3000ms threshold"

    @pytest.mark.asyncio
    async def test_sentiment_p95_latency(self):
        """Measure p95 latency for Sentiment."""
        latencies = []

        async with httpx.AsyncClient() as client:
            for _ in range(100):
                start = time.time()
                response = await client.post(
                    "http://sentiment-agent:8004/api/v1/analyze",
                    json={"text": "Test message for latency benchmark"},
                    timeout=5.0,
                )
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)

        p95 = statistics.quantiles(latencies, n=20)[18]
        assert p95 < 500, f"P95 latency {p95}ms exceeds 500ms threshold"
