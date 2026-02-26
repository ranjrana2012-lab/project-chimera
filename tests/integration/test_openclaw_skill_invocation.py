"""Integration tests for OpenClaw skill invocation"""

import pytest
import httpx


@pytest.mark.integration
class TestSkillInvocation:
    """Test cases for skill invocation through OpenClaw."""

    @pytest.mark.asyncio
    async def test_invoke_scenespeak(self):
        """Test SceneSpeak skill invocation."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://openclaw-orchestrator:8000/api/v1/orchestration/invoke",
                json={
                    "skill_name": "scenespeak",
                    "input": {
                        "current_scene": {"title": "Test"},
                        "dialogue_context": [],
                    },
                    "timeout_ms": 5000,
                },
                timeout=10.0,
            )
            assert response.status_code == 200
            data = response.json()
            assert "output" in data

    @pytest.mark.asyncio
    async def test_invoke_sentiment(self):
        """Test Sentiment skill invocation."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://openclaw-orchestrator:8000/api/v1/orchestration/invoke",
                json={
                    "skill_name": "sentiment",
                    "input": {"text": "This is amazing!"},
                    "timeout_ms": 1000,
                },
                timeout=5.0,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["output"]["sentiment"] == "positive"
