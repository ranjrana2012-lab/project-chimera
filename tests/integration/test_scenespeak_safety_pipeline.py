"""Integration tests for SceneSpeak + Safety pipeline"""

import pytest
import httpx


@pytest.mark.integration
class TestSceneSpeakSafetyPipeline:
    """Test cases for SceneSpeak with safety filtering."""

    @pytest.mark.asyncio
    async def test_safe_content_passes(self):
        """Test that safe content passes safety filter."""
        async with httpx.AsyncClient() as client:
            # Generate dialogue
            dialogue_response = await client.post(
                "http://scenespeak-agent:8001/api/v1/generate",
                json={
                    "scene_context": {"title": "Safe Scene"},
                    "dialogue_context": [],
                },
            )

            # Filter result
            safety_response = await client.post(
                "http://safety-filter:8006/api/v1/filter",
                json={"content": dialogue_response.json()["proposed_lines"]},
            )

            assert safety_response.json()["decision"] in ["allow", "flag"]

    @pytest.mark.asyncio
    async def test_blocked_content_stopped(self):
        """Test that blocked content is stopped."""
        async with httpx.AsyncClient() as client:
            # Content with profanity
            response = await client.post(
                "http://safety-filter:8006/api/v1/filter",
                json={"content": "This contains blocked [PROFANE] words"},
            )

            assert response.json()["decision"] == "block"
