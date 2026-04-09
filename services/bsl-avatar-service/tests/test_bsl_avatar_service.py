#!/usr/bin/env python3
"""
BSL Avatar Service Tests

Test suite for British Sign Language avatar service functionality.
"""

import pytest
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bsl_avatar_service import (
    BSLAvatarService,
    BSLTranslator,
    BSLAvatarRenderer,
    BSLState,
    BSLGesture,
    SignSequence
)


class TestBSLGesture:
    """Test BSL gesture creation and validation."""

    def test_create_valid_gesture(self):
        """Test creating a valid BSL gesture."""
        gesture = BSLGesture(
            id="hello",
            word="hello",
            part_of_speech="interjection",
            handshape="open_hand",
            orientation="palm_out",
            location="forehead",
            movement="wave",
            non_manual_features={
                "facial_expression": "friendly",
                "eyebrows": "raised"
            }
        )
        assert gesture.id == "hello"
        assert gesture.word == "hello"
        assert gesture.handshape == "open_hand"

    def test_empty_word_raises_error(self):
        """Test that empty word raises ValueError."""
        with pytest.raises(ValueError, match="Word cannot be empty"):
            BSLGesture(
                id="test",
                word="",  # Empty word
                part_of_speech="noun",
                handshape="test",
                orientation="test",
                location="test",
                movement="test",
                non_manual_features={}
            )


class TestSignSequence:
    """Test sign sequence creation and validation."""

    @pytest.fixture
    def sample_gestures(self):
        """Create sample gestures for testing."""
        return [
            BSLGesture(
                id="hello",
                word="hello",
                part_of_speech="interjection",
                handshape="open_hand",
                orientation="palm_out",
                location="forehead",
                movement="wave",
                non_manual_features={}
            ),
            BSLGesture(
                id="thank",
                word="thank",
                part_of_speech="verb",
                handshape="flat_hand",
                orientation="palm_up",
                location="chest",
                movement="circular_motion",
                non_manual_features={}
            )
        ]

    def test_create_valid_sequence(self, sample_gestures):
        """Test creating a valid sign sequence."""
        sequence = SignSequence(
            gestures=sample_gestures,
            timing_ms=[1000, 1000],
            non_manual_features=[
                {"facial_expression": "friendly"},
                {"facial_expression": "grateful"}
            ]
        )
        assert len(sequence.gestures) == 2
        assert len(sequence.timing_ms) == 2
        assert len(sequence.non_manual_features) == 2

    def test_gestures_timing_mismatch(self, sample_gestures):
        """Test that mismatched gestures and timing raises ValueError."""
        with pytest.raises(ValueError, match="Gestures and timing must have same length"):
            SignSequence(
                gestures=sample_gestures,
                timing_ms=[1000],  # Only one timing value
                non_manual_features=[{}, {}]
            )

    def test_gestures_features_mismatch(self, sample_gestures):
        """Test that mismatched gestures and features raises ValueError."""
        with pytest.raises(ValueError, match="Gestures and non-manual features must have same length"):
            SignSequence(
                gestures=sample_gestures,
                timing_ms=[1000, 1000],
                non_manual_features=[{}]  # Only one feature set
            )


class TestBSLTranslator:
    """Test BSL translator functionality."""

    @pytest.fixture
    def gesture_library(self):
        """Create a sample gesture library."""
        return {
            "hello": BSLGesture(
                id="hello",
                word="hello",
                part_of_speech="interjection",
                handshape="open_hand",
                orientation="palm_out",
                location="forehead",
                movement="wave",
                non_manual_features={}
            ),
            "thank": BSLGesture(
                id="thank",
                word="thank",
                part_of_speech="verb",
                handshape="flat_hand",
                orientation="palm_up",
                location="chest",
                movement="circular_motion",
                non_manual_features={}
            ),
            "you": BSLGesture(
                id="you",
                word="you",
                part_of_speech="pronoun",
                handshape="index_finger",
                orientation="palm_out",
                location="forward",
                movement="point",
                non_manual_features={}
            )
        }

    @pytest.fixture
    def translator(self, gesture_library):
        """Create a BSL translator."""
        return BSLTranslator(gesture_library)

    def test_translator_initialization(self, translator, gesture_library):
        """Test translator initializes correctly."""
        assert len(translator.gesture_library) == 3
        assert "hello" in translator.gesture_library

    def test_translate_simple_sentence(self, translator):
        """Test translating a simple sentence."""
        sequence = translator.translate("hello thank you")
        assert len(sequence.gestures) == 3
        assert sequence.gestures[0].word == "hello"
        assert sequence.gestures[1].word == "thank"
        assert sequence.gestures[2].word == "you"

    def test_translate_with_question(self, translator):
        """Test translating a question."""
        sequence = translator.translate("hello?")
        assert len(sequence.gestures) == 1
        # Question should have questioning facial expression
        assert sequence.non_manual_features[0]["facial_expression"] == "questioning"
        assert sequence.non_manual_features[0]["eyebrows"] == "raised"

    def test_translate_unknown_word_uses_fingerspelling(self, translator):
        """Test that unknown words use fingerspelling."""
        sequence = translator.translate("hello xyz thank")
        assert len(sequence.gestures) == 3

        # Middle gesture should be fingerspelling
        middle_gesture = sequence.gestures[1]
        assert middle_gesture.word == "xyz"
        assert middle_gesture.handshape == "fingerspelling"
        assert middle_gesture.id == "fingerspell_xyz"

    def test_fingerspelling_timing_faster(self, translator):
        """Test that fingerspelling has faster timing."""
        sequence = translator.translate("hello unknownword thank")
        # Find the fingerspelled gesture timing
        for i, gesture in enumerate(sequence.gestures):
            if gesture.handshape == "fingerspelling":
                assert sequence.timing_ms[i] == 500  # Fingerspelling is faster
                return
        pytest.fail("No fingerspelling gesture found")

    def test_case_insensitive_lookup(self, translator):
        """Test that word lookup is case-insensitive."""
        sequence1 = translator.translate("Hello")
        sequence2 = translator.translate("HELLO")
        sequence3 = translator.translate("hello")

        # All should produce same gesture
        assert sequence1.gestures[0].id == sequence2.gestures[0].id
        assert sequence2.gestures[0].id == sequence3.gestures[0].id

    def test_empty_text(self, translator):
        """Test translating empty text."""
        sequence = translator.translate("")
        assert len(sequence.gestures) == 0
        assert len(sequence.timing_ms) == 0
        assert len(sequence.non_manual_features) == 0

    def test_multiple_spaces(self, translator):
        """Test that multiple spaces are handled correctly."""
        sequence = translator.translate("hello  thank   you")
        # Should only translate non-empty words
        assert len(sequence.gestures) == 3


class TestBSLAvatarRenderer:
    """Test BSL avatar renderer functionality."""

    @pytest.fixture
    def renderer(self):
        """Create a BSL avatar renderer."""
        return BSLAvatarRenderer()

    @pytest.fixture
    def sample_sequence(self):
        """Create a sample sign sequence."""
        gestures = [
            BSLGesture(
                id="hello",
                word="hello",
                part_of_speech="interjection",
                handshape="open_hand",
                orientation="palm_out",
                location="forehead",
                movement="wave",
                non_manual_features={}
            ),
            BSLGesture(
                id="thank",
                word="thank",
                part_of_speech="verb",
                handshape="flat_hand",
                orientation="palm_up",
                location="chest",
                movement="circular_motion",
                non_manual_features={}
            )
        ]
        return SignSequence(
            gestures=gestures,
            timing_ms=[1000, 1000],
            non_manual_features=[{}, {}]
        )

    def test_renderer_initialization(self, renderer):
        """Test renderer initializes correctly."""
        assert renderer.current_gesture is None

    @pytest.mark.asyncio
    async def test_render_sign_sequence(self, renderer, sample_sequence):
        """Test rendering a sign sequence."""
        await renderer.render_sign_sequence(sample_sequence)
        # Should complete without errors

    @pytest.mark.asyncio
    async def test_render_single_gesture(self, renderer):
        """Test rendering a single gesture."""
        gesture = BSLGesture(
            id="test",
            word="test",
            part_of_speech="noun",
            handshape="test",
            orientation="test",
            location="test",
            movement="test",
            non_manual_features={}
        )
        await renderer._render_gesture(gesture, 1000)
        # Should complete without errors

    @pytest.mark.asyncio
    async def test_apply_non_manual_features(self, renderer):
        """Test applying non-manual features."""
        features = {
            "facial_expression": "questioning",
            "eyebrows": "raised",
            "body_lean": "slight_forward"
        }
        await renderer._apply_non_manual_features(features)
        # Should complete without errors


class TestBSLAvatarService:
    """Test BSL avatar service functionality."""

    @pytest.fixture
    def gesture_library(self):
        """Create a sample gesture library."""
        return {
            "hello": BSLGesture(
                id="hello",
                word="hello",
                part_of_speech="interjection",
                handshape="open_hand",
                orientation="palm_out",
                location="forehead",
                movement="wave",
                non_manual_features={}
            ),
            "thank": BSLGesture(
                id="thank",
                word="thank",
                part_of_speech="verb",
                handshape="flat_hand",
                orientation="palm_up",
                location="chest",
                movement="circular_motion",
                non_manual_features={}
            )
        }

    @pytest.fixture
    def service(self, gesture_library):
        """Create a BSL avatar service."""
        return BSLAvatarService(gesture_library)

    def test_service_initialization(self, service, gesture_library):
        """Test service initializes correctly."""
        assert service.state == BSLState.IDLE
        assert len(service.translator.gesture_library) == 2
        assert service._current_sign_sequence is None

    @pytest.mark.asyncio
    async def test_translate_and_render(self, service):
        """Test translating and rendering text."""
        await service.translate_and_render("hello thank you")
        # Should complete without errors

    @pytest.mark.asyncio
    async def test_translate_and_render_empty(self, service):
        """Test translating and rendering empty text."""
        await service.translate_and_render("")
        # Should complete without errors

    def test_get_status(self, service):
        """Test getting service status."""
        status = service.get_status()
        assert "state" in status
        assert "gesture_library_size" in status
        assert "current_sign_sequence" in status
        assert status["gesture_library_size"] == 2
        assert status["state"] == "idle"


@pytest.mark.integration
class TestBSLAvatarServiceIntegration:
    """Integration tests for BSL avatar service."""

    @pytest.fixture
    def comprehensive_library(self):
        """Create a comprehensive gesture library."""
        return {
            "hello": BSLGesture(
                id="hello",
                word="hello",
                part_of_speech="interjection",
                handshape="open_hand",
                orientation="palm_out",
                location="forehead",
                movement="wave",
                non_manual_features={}
            ),
            "thank": BSLGesture(
                id="thank",
                word="thank",
                part_of_speech="verb",
                handshape="flat_hand",
                orientation="palm_up",
                location="chest",
                movement="circular_motion",
                non_manual_features={}
            ),
            "name": BSLGesture(
                id="name",
                word="name",
                part_of_speech="noun",
                handshape="index_finger",
                orientation="palm_out",
                location="shoulder",
                movement="tap_twice",
                non_manual_features={}
            ),
            "what": BSLGesture(
                id="what",
                word="what",
                part_of_speech="pronoun",
                handshape="flat_hand",
                orientation="palm_up",
                location="chest",
                movement="shake",
                non_manual_features={}
            ),
            "your": BSLGesture(
                id="your",
                word="your",
                part_of_speech="pronoun",
                handshape="flat_hand",
                orientation="palm_out",
                location="chest",
                movement="circle",
                non_manual_features={}
            )
        }

    @pytest.mark.asyncio
    async def test_complete_translation_workflow(self, comprehensive_library):
        """Test a complete translation and rendering workflow."""
        service = BSLAvatarService(comprehensive_library)

        # Translate a question
        await service.translate_and_render("what is your name?")
        status = service.get_status()
        assert status["state"] == "idle"

        # Translate a statement
        await service.translate_and_render("hello thank you")
        status = service.get_status()
        assert status["state"] == "idle"

    @pytest.mark.asyncio
    async def test_fingerspelling_fallback_workflow(self, comprehensive_library):
        """Test fingerspelling fallback for unknown words."""
        service = BSLAvatarService(comprehensive_library)

        # Translate with unknown words
        await service.translate_and_render("hello ABCDEF thank")

        # Should complete without errors using fingerspelling
        status = service.get_status()
        assert status["state"] == "idle"

    @pytest.mark.asyncio
    async def test_multiple_translations_sequence(self, comprehensive_library):
        """Test multiple translations in sequence."""
        service = BSLAvatarService(comprehensive_library)

        phrases = [
            "hello",
            "what is your name?",
            "thank you",
            "hello thank you"
        ]

        for phrase in phrases:
            await service.translate_and_render(phrase)
            status = service.get_status()
            assert status["state"] == "idle"

    def test_service_status_tracking(self, comprehensive_library):
        """Test that service status is tracked correctly."""
        service = BSLAvatarService(comprehensive_library)

        status = service.get_status()
        assert status["gesture_library_size"] == 5
        assert status["state"] == "idle"
        assert status["current_sign_sequence"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
