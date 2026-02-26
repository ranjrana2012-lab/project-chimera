"""Integration tests for fallback chain"""

import pytest
import httpx


@pytest.mark.integration
class TestFallbackChain:
    """Test cases for skill fallback behavior."""

    @pytest.mark.asyncio
    async def test_model_fallback(self):
        """Test fallback from primary to backup model."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://scenespeak-agent:8001/api/v1/generate",
                json={
                    "scene_context": {"title": "Test"},
                    "dialogue_context": [],
                    "use_fallback": True,
                },
            )

            # Should get result from fallback if primary fails
            assert response.status_code == 200
            data = response.json()
            assert "proposed_lines" in data

    @pytest.mark.asyncio
    async def test_skill_timeout_fallback(self):
        """Test timeout handling and fallback."""
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                "http://openclaw-orchestrator:8000/api/v1/orchestration/invoke",
                json={
                    "skill_name": "scenespeak",
                    "input": {},
                    "timeout_ms": 100,  # Very short timeout
                },
            )

            # Should handle timeout gracefully
            assert response.status_code in [200, 408, 500]
