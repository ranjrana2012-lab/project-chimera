"""
Captioning Agent - Accessibility Descriptions Module

Generates accessibility descriptions for visual content in theatre performances.

Features:
- Scene descriptions for visually impaired
- Character movement descriptions
- Lighting/visual effect descriptions
- Integration with transcription responses
"""

import logging
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


# Configure logging
logger = logging.getLogger(__name__)


class SceneElementType(Enum):
    """Types of visual elements in a scene."""
    CHARACTER = "character"
    LIGHTING = "lighting"
    PROP = "prop"
    MOVEMENT = "movement"
    EFFECT = "effect"
    TRANSITION = "transition"


@dataclass
class VisualElement:
    """Represents a visual element in the scene."""
    element_type: SceneElementType
    description: str
    position: Optional[str] = None  # "stage left", "center", etc.
    duration: Optional[float] = None
    confidence: float = 1.0


class AccessibilityDescriptionGenerator:
    """
    Generates accessibility descriptions for visual content.

    Uses rule-based templates and contextual inference to create
    descriptions for blind/visually impaired audience members.
    """

    # Description templates for different scene types
    TEMPLATES = {
        "entry": "A {character} enters from {direction}, wearing {description}",
        "exit": "{character} exits toward {direction}",
        "movement": "{character} moves {direction} across the stage",
        "gesture": "{character} {gesture}",
        "lighting": "The lighting changes to {description}",
        "prop": "{character} picks up a {prop}",
        "effect": "A {effect} effect occurs"
    }

    # Common stage directions
    STAGE_POSITIONS = {
        "stage left": "left side of the stage",
        "stage right": "right side of the stage",
        "center stage": "center of the stage",
        "upstage": "rear of the stage",
        "downstage": "front of the stage"
    }

    # Character movements
    MOVEMENTS = {
        "walks": "walks",
        "runs": "runs",
        "stumbles": "stumbles",
        "kneels": "kneels down",
        "stands": "stands up",
        "approaches": "approaches",
        "retreats": "moves away from"
    }

    # Gestures
    GESTURES = {
        "waves": "waves",
        "points": "points",
        "nods": "nods",
        "shakes head": "shakes their head",
        "bows": "bows"
    }

    def __init__(self, enable_ml: bool = False):
        """
        Initialize description generator.

        Args:
            enable_ml: Enable ML-based description enhancement (future)
        """
        self.enable_ml = enable_ml

    def generate_scene_description(
        self,
        visual_elements: List[VisualElement],
        context: Optional[dict] = None
    ) -> str:
        """
        Generate a natural language description from visual elements.

        Args:
            visual_elements: List of detected visual elements
            context: Optional context (current scene, characters, etc.)

        Returns:
            Natural language description
        """
        if not visual_elements:
            return ""

        descriptions = []

        for element in visual_elements:
            desc = self._describe_element(element, context)
            if desc:
                descriptions.append(desc)

        return self._combine_descriptions(descriptions)

    def _describe_element(self, element: VisualElement, context: Optional[dict]) -> Optional[str]:
        """Generate description for a single visual element."""
        element_type = element.element_type
        desc = element.description.lower()

        # Character movements
        if element_type == SceneElementType.MOVEMENT:
            for movement, phrase in self.MOVEMENTS.items():
                if movement in desc:
                    character = self._extract_character(desc, context)
                    return f"{character} {phrase}"

        # Gestures
        elif element_type == SceneElementType.GESTURE:
            for gesture, phrase in self.GESTURES.items():
                if gesture in desc:
                    character = self._extract_character(desc, context)
                    return f"{character} {phrase}"

        # Lighting changes
        elif element_type == SceneElementType.LIGHTING:
            if "dim" in desc:
                return "The lights dim"
            elif "bright" in desc or "up" in desc:
                return "The lights brighten"
            elif "spotlight" in desc:
                character = self._extract_character(desc, context)
                return f"A spotlight illuminates {character}"
            elif "color" in desc:
                # Extract color if mentioned
                return f"The lighting changes color"

        # Stage directions
        elif element_type == SceneElementType.CHARACTER:
            direction = self._extract_stage_direction(desc)
            character = self._extract_character(desc, context)
            if "enter" in desc:
                return f"{character} enters from {direction}"
            elif "exit" in desc:
                return f"{character} exits toward {direction}"

        # Props
        elif element_type == SceneElementType.PROP:
            character = self._extract_character(desc, context)
            return f"{character} interacts with {desc}"

        # Effects
        elif element_type == SceneElementType.EFFECT:
            return f"A {element.description} effect occurs"

        return element.description

    def _extract_character(self, description: str, context: Optional[dict]) -> str:
        """Extract character name from description or context."""
        # Common character name patterns
        if context and "characters" in context:
            for char in context["characters"]:
                if char.lower() in description.lower():
                    return char

        # Default character names
        for name in ["alice", "bob", "protagonist", "character"]:
            if name in description.lower():
                return name.capitalize()

        return "A character"

    def _extract_stage_direction(self, description: str) -> str:
        """Extract stage direction from description."""
        for position, phrase in self.STAGE_POSITIONS.items():
            if position in description.lower():
                return phrase

        return "stage"

    def _combine_descriptions(self, descriptions: List[str]) -> str:
        """Combine multiple descriptions into a coherent narrative."""
        if not descriptions:
            return ""

        if len(descriptions) == 1:
            return descriptions[0]

        # Combine with appropriate conjunctions
        result = descriptions[0]
        for desc in descriptions[1:]:
            result += f". Meanwhile, {desc.lower()}"

        return result

    def generate_audio_description(self, audio_context: dict) -> str:
        """
        Generate description of audio events for accessibility.

        Args:
            audio_context: Audio analysis results (volume, tone, etc.)

        Returns:
            Description of audio events
        """
        descriptions = []

        # Loud sounds
        if audio_context.get("loudness", 0) > 0.7:
            descriptions.append("There is a loud sound")

        # Music
        if audio_context.get("music"):
            descriptions.append("Music plays")

        # Silence
        if audio_context.get("silence"):
            descriptions.append("It becomes quiet")

        return ". ".join(descriptions) if descriptions else ""

    def enhance_transcription_with_scene(
        self,
        transcription_text: str,
        visual_elements: List[VisualElement],
        context: Optional[dict] = None
    ) -> dict:
        """
        Combine transcription with visual scene description.

        Args:
            transcription_text: Spoken dialogue
            visual_elements: Visual elements in scene
            context: Scene context

        Returns:
            Enhanced response with accessibility description
        """
        scene_description = self.generate_scene_description(visual_elements, context)

        return {
            "transcription": transcription_text,
            "visual_description": scene_description,
            "has_visual_content": bool(scene_description),
            "description_level": "detailed" if context else "basic"
        }

    def generate_placeholder_description(self, scenario: str) -> str:
        """
        Generate a placeholder description for missing visual info.

        Args:
            scenario: Type of placeholder needed

        Returns:
            Generic description
        """
        placeholders = {
            "unknown": "Visual content is occurring",
            "stage_change": "The scene changes",
            "lighting": "The lighting shifts",
            "movement": "Characters are moving"
        }

        return placeholders.get(scenario, "Something is happening on stage")


def generate_descriptions_for_transcription(
    transcription_result: dict,
    scene_context: Optional[dict] = None  # Changed from context to scene_context
) -> dict:
    """
    Convenience function to add accessibility descriptions to transcription.

    Args:
        transcription_result: Transcription response from transcription service
        scene_context: Optional scene context

    Returns:
        Enhanced result with visual_description field
    """
    generator = AccessibilityDescriptionGenerator()

    # Generate placeholder description if no context
    if not scene_context:
        placeholder = generator.generate_placeholder_description("unknown")
        return {
            **transcription_result,
            "visual_description": placeholder,
            "has_visual_content": True
        }

    # Generate from visual elements if available
    visual_elements = scene_context.get("visual_elements", [])
    if visual_elements:
        scene_description = generator.generate_scene_description(
            visual_elements, scene_context
        )
        return {
            **transcription_result,
            "visual_description": scene_description,
            "has_visual_content": bool(scene_description)
        }

    # No visual info available
    return transcription_result
