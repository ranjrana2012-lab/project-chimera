"""Unit tests for SceneSpeak handler"""

import pytest
from services.scenespeak_agent.src.core.context_builder import ContextBuilder


@pytest.mark.unit
class TestContextBuilder:
    """Test cases for ContextBuilder"""

    @pytest.fixture
    def builder(self):
        return ContextBuilder(None)

    @pytest.mark.asyncio
    async def test_build_context(self, builder):
        """Test context building."""
        scene_context = {
            "scene_id": "scene-001",
            "title": "Test Scene",
            "setting": "A room",
            "mood": "tense",
            "characters": ["ALICE", "BOB"],
        }
        dialogue_context = [
            {"character": "ALICE", "text": "Hello", "timestamp": "2026-02-26T12:00:00Z"}
        ]

        context = await builder.build(scene_context, dialogue_context, None)

        assert context["scene"]["title"] == "Test Scene"
        assert context["scene"]["mood"] == "tense"
        assert len(context["dialogue"]) == 1
        assert context["dialogue"][0]["character"] == "ALICE"

    @pytest.mark.asyncio
    async def test_sentiment_processing(self, builder):
        """Test sentiment vector processing."""
        sentiment_vector = {
            "overall": "positive",
            "intensity": 0.8,
            "engagement": 0.9,
        }

        context = await builder.build({}, [], sentiment_vector)

        assert context["sentiment"]["overall"] == "positive"
        assert context["sentiment"]["intensity"] == 0.8
