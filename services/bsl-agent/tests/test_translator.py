"""
Tests for BSL Translator.

Tests the text-to-BSL-gloss translation functionality including:
- Phrase dictionary translation
- Word-by-word translation
- Non-manual marker generation
- Finger-spelling fallback
"""

import pytest
from translator import BSLTranslator


@pytest.fixture
def translator():
    """Create a BSL translator instance for testing"""
    return BSLTranslator()


class TestBSLTranslator:
    """Test suite for BSLTranslator class"""

    def test_initialization(self, translator):
        """Test translator initialization"""
        assert translator is not None
        assert hasattr(translator, 'PHRASE_DICTIONARY')
        assert hasattr(translator, 'NMM_MARKERS')
        assert len(translator.PHRASE_DICTIONARY) > 0

    def test_translate_common_phrase(self, translator):
        """Test translation of common phrases from dictionary"""
        gloss, breakdown, duration = translator.text_to_gloss("hello")
        assert gloss == "HELLO"
        assert breakdown == ["HELLO"]
        assert duration == 0.5

    def test_translate_phrase_multiple_words(self, translator):
        """Test translation of multi-word phrases"""
        gloss, breakdown, duration = translator.text_to_gloss("good morning")
        assert gloss == "GOOD MORNING"
        assert breakdown == ["GOOD MORNING"]
        assert duration == 0.5

    def test_translate_word_by_word(self, translator):
        """Test word-by-word translation for unknown phrases"""
        gloss, breakdown, duration = translator.text_to_gloss("hello world")
        assert "HELLO" in gloss
        assert len(breakdown) == 2
        assert duration == 1.0  # 2 words * 0.5 seconds

    def test_finger_spelling_unknown_word(self, translator):
        """Test finger-spelling for unknown words"""
        gloss, breakdown, duration = translator.text_to_gloss("xyz")
        assert "FS-" in gloss
        assert "X" in gloss
        assert "Y" in gloss
        assert "Z" in gloss

    def test_text_cleaning(self, translator):
        """Test that text is cleaned properly"""
        gloss, breakdown, duration = translator.text_to_gloss("Hello!")
        assert gloss == "HELLO"

    def test_add_nmm_wh_question(self, translator):
        """Test NMM generation for wh-questions"""
        nmm = translator.add_non_manual_markers("What is your name?")
        assert "brows-down" in nmm
        assert "head-tilt" in nmm
        assert "hold-last-sign" in nmm

    def test_add_nmm_yes_no_question(self, translator):
        """Test NMM generation for yes/no questions"""
        nmm = translator.add_non_manual_markers("Are you okay?")
        assert "brows-up" in nmm
        assert "head-tilt" in nmm

    def test_add_nmm_negation(self, translator):
        """Test NMM generation for negation"""
        nmm = translator.add_non_manual_markers("I do not understand")
        assert "head-shake" in nmm
        assert "brows-down" in nmm

    def test_add_nmm_conditional(self, translator):
        """Test NMM generation for conditionals"""
        nmm = translator.add_non_manual_markers("If it rains, we stay inside")
        assert "brows-up" in nmm
        assert "head-tilt" in nmm

    def test_add_nmm_exclamation(self, translator):
        """Test NMM generation for exclamations"""
        nmm = translator.add_non_manual_markers("Great!")
        assert "eyes-wide" in nmm
        assert "body-lean-forward" in nmm

    def test_add_nmm_empty_text(self, translator):
        """Test NMM generation for empty text"""
        nmm = translator.add_non_manual_markers("")
        assert nmm == []

    def test_translate_with_nmm(self, translator):
        """Test complete translation with NMM"""
        result = translator.translate_with_nmm("What is your name?")

        assert "gloss" in result
        assert "breakdown" in result
        assert "duration_estimate" in result
        assert "confidence" in result
        assert "non_manual_markers" in result
        assert "translation_time_ms" in result

        # The translator preserves word order, so "what" comes last after dictionary lookup
        assert "WHAT" in result["gloss"]
        assert "NAME" in result["gloss"]
        assert "YOUR" in result["gloss"]
        assert len(result["non_manual_markers"]) > 0
        assert result["confidence"] > 0

    def test_confidence_calculation(self, translator):
        """Test confidence score calculation"""
        # All words in dictionary should have high confidence
        result = translator.translate_with_nmm("hello thank you")
        assert result["confidence"] >= 0.8

        # Mixed dictionary/non-dictionary words
        result = translator.translate_with_nmm("hello xyz world")
        assert result["confidence"] >= 0.5
        assert result["confidence"] < 1.0

    def test_empty_text_translation(self, translator):
        """Test translation of empty text"""
        gloss, breakdown, duration = translator.text_to_gloss("")
        assert gloss == ""
        assert breakdown == []
        assert duration == 0

    def test_punctuation_removal(self, translator):
        """Test that punctuation is removed from translation"""
        gloss, breakdown, duration = translator.text_to_gloss("Hello, how are you?")
        assert "," not in gloss
        assert "?" not in gloss

    def test_case_insensitive_translation(self, translator):
        """Test that translation is case-insensitive"""
        gloss1, _, _ = translator.text_to_gloss("HELLO")
        gloss2, _, _ = translator.text_to_gloss("hello")
        gloss3, _, _ = translator.text_to_gloss("HeLLo")

        assert gloss1 == gloss2 == gloss3

    def test_duration_calculation(self, translator):
        """Test duration calculation based on word count"""
        # Single word
        _, _, duration = translator.text_to_gloss("hello")
        assert duration == 0.5

        # Multiple words
        _, _, duration = translator.text_to_gloss("hello thank you")
        assert duration == 1.5  # 3 words * 0.5 seconds


class TestBSLTranslatorEdgeCases:
    """Test edge cases and error handling"""

    def test_translate_only_punctuation(self, translator):
        """Test translation of text with only punctuation"""
        gloss, breakdown, duration = translator.text_to_gloss("!?,.;:")
        assert gloss == ""
        assert breakdown == []

    def test_translate_multiple_spaces(self, translator):
        """Test translation with multiple spaces"""
        gloss, breakdown, duration = translator.text_to_gloss("hello    world")
        assert len(breakdown) == 2  # Should ignore extra spaces

    def test_finger_spell_with_numbers(self, translator):
        """Test finger-spelling with numbers in text"""
        gloss, breakdown, duration = translator.text_to_gloss("abc123")
        # Numbers are removed, letters are finger-spelled as FS-A-B-C
        assert "FS-" in gloss
        assert "A" in gloss or "B" in gloss or "C" in gloss

    def test_very_long_word(self, translator):
        """Test translation of very long words"""
        long_word = "supercalifragilisticexpialidocious"
        gloss, breakdown, duration = translator.text_to_gloss(long_word)
        assert "FS-" in gloss
        assert len(breakdown) == 1

    def test_translate_with_special_characters(self, translator):
        """Test translation with special characters"""
        gloss, breakdown, duration = translator.text_to_gloss("hello@world.com")
        # Should handle special characters gracefully
        assert len(gloss) > 0
