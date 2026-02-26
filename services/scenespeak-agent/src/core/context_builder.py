"""
Context Builder for SceneSpeak Agent
"""

from typing import Any, Dict, List, Optional


class ContextBuilder:
    """Builds context for dialogue generation."""

    def __init__(self, settings):
        self.settings = settings

    async def build(
        self,
        scene_context: Dict[str, Any],
        dialogue_context: List[Dict[str, Any]],
        sentiment_vector: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build full context for dialogue generation.

        Args:
            scene_context: Current scene information
            dialogue_context: Recent dialogue history
            sentiment_vector: Audience sentiment (optional)

        Returns:
            Complete context dictionary
        """
        context = {
            "scene": self._process_scene_context(scene_context),
            "dialogue": self._process_dialogue_context(dialogue_context),
            "sentiment": self._process_sentiment(sentiment_vector),
            "timestamp": self._get_timestamp(),
        }

        return context

    def _process_scene_context(self, scene_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate scene context."""
        return {
            "scene_id": scene_context.get("scene_id", "unknown"),
            "title": scene_context.get("title", ""),
            "setting": scene_context.get("setting", ""),
            "mood": scene_context.get("mood", "neutral"),
            "characters": scene_context.get("characters", []),
            "stage_directions": scene_context.get("stage_directions", []),
        }

    def _process_dialogue_context(
        self, dialogue_context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process and validate dialogue context."""
        processed = []
        for turn in dialogue_context[-10:]:  # Last 10 turns
            processed.append({
                "character": turn.get("character", "UNKNOWN"),
                "text": turn.get("text", ""),
                "timestamp": turn.get("timestamp", ""),
            })
        return processed

    def _process_sentiment(
        self, sentiment_vector: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process and validate sentiment vector."""
        if not sentiment_vector:
            return {"overall": "neutral", "intensity": 0.5}

        return {
            "overall": sentiment_vector.get("overall", "neutral"),
            "intensity": sentiment_vector.get("intensity", 0.5),
            "engagement": sentiment_vector.get("engagement", 0.5),
            "emotional_arc": sentiment_vector.get("emotional_arc", []),
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
