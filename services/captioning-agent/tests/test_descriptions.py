"""
Unit tests for Accessibility Description Generator.
"""

import pytest
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, '/home/ranj/Project_Chimera/services/captioning-agent')

from core.descriptions import (
    AccessibilityDescriptionGenerator,
    VisualElement,
    SceneElementType,
    generate_descriptions_for_transcription
)


class TestSceneDescriptionGeneration:
    """Test scene description generation from visual elements."""

    def test_character_movement_description(self):
        """Generate description for character movement."""
        generator = AccessibilityDescriptionGenerator()

        element = VisualElement(
            element_type=SceneElementType.MOVEMENT,
            description="Alice walks across stage",
            position="center"
        )

        result = generator.generate_scene_description([element])

        assert "Alice" in result
        assert "walks" in result

    def test_lighting_change_description(self):
        """Generate description for lighting changes."""
        generator = AccessibilityDescriptionGenerator()

        element = VisualElement(
            element_type=SceneElementType.LIGHTING,
            description="Lights dim to blue",
            position=None
        )

        result = generator.generate_scene_description([element])

        assert "light" in result.lower() or "lights" in result.lower()

    def test_character_entry_description(self):
        """Generate description for character entering."""
        generator = AccessibilityDescriptionGenerator()

        element = VisualElement(
            element_type=SceneElementType.CHARACTER,
            description="Bob enters from stage left",
            position="stage left"
        )

        result = generator.generate_scene_description([element])

        assert "Bob" in result
        assert "enters" in result or "enter" in result.lower()

    def test_multiple_elements_combined(self):
        """Combine multiple visual elements coherently."""
        generator = AccessibilityDescriptionGenerator()

        elements = [
            VisualElement(
                element_type=SceneElementType.CHARACTER,
                description="Alice enters from stage left",
                position="stage left"
            ),
            VisualElement(
                element_type=SceneElementType.LIGHTING,
                description="Spotlight on Alice",
                position="stage left"
            )
        ]

        result = generator.generate_scene_description(elements, {
            "characters": ["Alice", "Bob"]
        })

        assert "Alice" in result
        assert "enters" in result.lower()

    def test_empty_elements_returns_empty(self):
        """Empty visual elements list returns empty description."""
        generator = AccessibilityDescriptionGenerator()

        result = generator.generate_scene_description([])

        assert result == ""

    def test_stage_direction_extraction(self):
        """Extract correct stage direction phrases."""
        generator = AccessibilityDescriptionGenerator()

        assert "left" in generator._extract_stage_direction("from stage left")
        assert "right" in generator._extract_stage_direction("to stage right")
        assert "center" in generator._extract_stage_direction("center stage")

    def test_character_extraction_from_context(self):
        """Extract character from context when available."""
        generator = AccessibilityDescriptionGenerator()

        context = {"characters": ["HAMLET", "MACBETH"]}

        character = generator._extract_character("HAMLET walks forward", context)

        assert character == "HAMLET"

    def test_character_extraction_default(self):
        """Return default character when no context."""
        generator = AccessibilityDescriptionGenerator()

        character = generator._extract_character("Someone walks", None)

        assert character in ["A character", "Someone", "Unknown"]


class TestAudioDescriptionGeneration:
    """Test audio event descriptions."""

    def test_loud_sound_description(self):
        """Generate description for loud sounds."""
        generator = AccessibilityDescriptionGenerator()

        audio_context = {"loudness": 0.8}

        result = generator.generate_audio_description(audio_context)

        assert "loud" in result.lower()

    def test_music_playing_description(self):
        """Generate description for music."""
        generator = AccessibilityDescriptionGenerator()

        audio_context = {"music": True, "loudness": 0.5}

        result = generator.generate_audio_description(audio_context)

        assert "music" in result.lower()

    def test_silence_description(self):
        """Generate description for silence."""
        generator = AccessibilityDescriptionGenerator()

        audio_context = {"silence": True}

        result = generator.generate_audio_description(audio_context)

        assert "quiet" in result.lower() or "silence" in result.lower()

    def test_no_audio_returns_empty(self):
        """Empty audio context returns empty description."""
        generator = AccessibilityDescriptionGenerator()

        result = generator.generate_audio_description({})

        assert result == ""


class TestTranscriptionEnhancement:
    """Test enhancing transcriptions with visual descriptions."""

    def test_enhance_with_visual_elements(self):
        """Enhance transcription with visual description."""
        generator = AccessibilityDescriptionGenerator()

        visual_elements = [
            VisualElement(
                element_type=SceneElementType.CHARACTER,
                description="Alice enters",
                position="stage left"
            )
        ]

        result = generator.enhance_transcription_with_scene(
            transcription_text="Hello world",
            visual_elements=visual_elements,
            context={"characters": ["Alice"]}
        )

        assert result["transcription"] == "Hello world"
        assert result["visual_description"]
        assert result["has_visual_content"] is True

    def test_enhance_without_context_returns_placeholder(self):
        """Return placeholder when no visual context."""
        generator = AccessibilityDescriptionGenerator()

        result = generator.enhance_transcription_with_scene(
            transcription_text="Hello",
            visual_elements=[],
            context=None
        )

        assert result["transcription"] == "Hello"
        assert result["visual_description"]
        assert result["has_visual_content"] is True

    def test_placeholder_scenarios(self):
        """Generate appropriate placeholder for different scenarios."""
        generator = AccessibilityDescriptionGenerator()

        assert "stage" in generator.generate_placeholder_description("stage_change").lower()
        assert "light" in generator.generate_placeholder_description("lighting").lower()


class TestConvenienceFunction:
    """Test the convenience function for adding descriptions."""

    def test_add_descriptions_with_context(self):
        """Convenience function adds descriptions with context."""
        transcription_result = {
            "text": "Hello",
            "language": "en"
        }

        scene_context = {
            "characters": ["Alice"],
            "visual_elements": [
                VisualElement(
                    element_type=SceneElementType.MOVEMENT,
                    description="Alice waves",
                    position="center"
                )
            ]
        }

        result = generate_descriptions_for_transcription(
            transcription_result,
            scene_context=scene_context
        )

        assert result["text"] == "Hello"
        assert "visual_description" in result
        assert result["has_visual_content"] is True

    def test_add_descriptions_without_context(self):
        """Convenience function adds placeholder without context."""
        transcription_result = {
            "text": "Hello",
            "language": "en"
        }

        result = generate_descriptions_for_transcription(
            transcription_result,
            scene_context=None
        )

        assert result["text"] == "Hello"
        assert "visual_description" in result
        assert result["has_visual_content"] is True

    def test_preserves_original_fields(self):
        """Convenience function preserves all original fields."""
        transcription_result = {
            "text": "Test",
            "language": "en",
            "duration": 1.5,
            "confidence": 0.9
        }

        result = generate_descriptions_for_transcription(
            transcription_result,
            scene_context=None
        )

        assert result["text"] == "Test"
        assert result["language"] == "en"
        assert result["duration"] == 1.5
        assert result["confidence"] == 0.9
