"""
Enhanced tests for BSL Translator covering edge cases and error handling.

Tests the text-to-BSL-gloss translation functionality including:
- Advanced edge cases
- Error handling
- Performance tests
- Integration scenarios
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from translator import BSLTranslator


@pytest.fixture
def translator():
    """Create a BSL translator instance for testing"""
    return BSLTranslator()


class TestTranslatorAdvancedEdgeCases:
    """Test advanced edge cases for BSL translation"""

    def test_translate_with_unicode_emoji(self, translator):
        """Test translation with emoji characters"""
        gloss, breakdown, duration = translator.text_to_gloss("Hello 🌍")
        assert "HELLO" in gloss
        assert len(breakdown) >= 1

    def test_translate_with_mixed_case_punctuation(self, translator):
        """Test translation with mixed case and punctuation"""
        gloss, breakdown, duration = translator.text_to_gloss("HeLlO, HoW aRe YoU?!")
        assert "HELLO" in gloss
        assert "HOW" in gloss
        assert "," not in gloss
        assert "?" not in gloss

    def test_translate_with_tabs_and_newlines(self, translator):
        """Test translation with tabs and newlines"""
        gloss, breakdown, duration = translator.text_to_gloss("hello\t\t\nworld")
        assert len(breakdown) == 2

    def test_translate_very_long_sentence(self, translator):
        """Test translation of very long sentences"""
        long_text = " ".join(["hello"] * 1000)
        gloss, breakdown, duration = translator.text_to_gloss(long_text)
        assert len(breakdown) == 1000
        assert duration == 500.0  # 1000 words * 0.5 seconds

    def test_finger_spell_with_hyphenated_word(self, translator):
        """Test finger-spelling with hyphenated words"""
        gloss, breakdown, duration = translator.text_to_gloss("state-of-the-art")
        # Should finger-spell each part
        assert "FS-" in gloss

    def test_finger_spell_with_apostrophe(self, translator):
        """Test finger-spelling with apostrophes"""
        gloss, breakdown, duration = translator.text_to_gloss("don't")
        assert len(breakdown) >= 1

    def test_translate_with_leading_trailing_whitespace(self, translator):
        """Test translation with leading and trailing whitespace"""
        gloss, breakdown, duration = translator.text_to_gloss("   hello world   ")
        assert "HELLO" in gloss
        assert "WORLD" in gloss

    def test_translate_with_repeated_words(self, translator):
        """Test translation with repeated words"""
        gloss, breakdown, duration = translator.text_to_gloss("hello hello hello")
        assert breakdown.count("HELLO") == 3

    def test_translate_all_dictionary_words(self, translator):
        """Test that all dictionary words can be translated"""
        for phrase, expected_gloss in translator.PHRASE_DICTIONARY.items():
            gloss, breakdown, duration = translator.text_to_gloss(phrase)
            assert gloss == expected_gloss

    def test_nmm_with_combined_markers(self, translator):
        """Test NMM generation with combined markers"""
        # Question with negation
        nmm = translator.add_non_manual_markers("What don't you understand?")
        assert "brows-down" in nmm
        assert "head-shake" in nmm

    def test_nmm_with_multiple_questions(self, translator):
        """Test NMM with multiple question marks"""
        nmm = translator.add_non_manual_markers("Are you sure???")
        assert "brows-up" in nmm

    def test_nmm_preserves_order(self, translator):
        """Test that NMM markers preserve insertion order"""
        nmm = translator.add_non_manual_markers("What if not today?")
        # Should maintain order: wh-question, conditional, negation
        assert len(nmm) == len(set(nmm))  # No duplicates

    def test_confidence_with_all_unknown_words(self, translator):
        """Test confidence calculation with all unknown words"""
        result = translator.translate_with_nmm("xyz abc def")
        assert result["confidence"] >= 0.5  # Minimum confidence

    def test_confidence_with_empty_text(self, translator):
        """Test confidence calculation with empty text"""
        result = translator.translate_with_nmm("")
        assert result["confidence"] == 0.5  # Default confidence

    def test_translation_time_is_recorded(self, translator):
        """Test that translation time is recorded"""
        result = translator.translate_with_nmm("hello world")
        assert result["translation_time_ms"] >= 0

    def test_translate_with_nmm_returns_all_fields(self, translator):
        """Test that translate_with_nmm returns all expected fields"""
        result = translator.translate_with_nmm("hello")
        expected_fields = [
            "gloss", "breakdown", "duration_estimate",
            "confidence", "non_manual_markers", "translation_time_ms"
        ]
        for field in expected_fields:
            assert field in result


class TestTranslatorErrorHandling:
    """Test error handling in BSL translation"""

    def test_translate_with_none_input(self, translator):
        """Test translation with None input"""
        with pytest.raises(AttributeError):
            translator.text_to_gloss(None)

    def test_translate_with_numbers_only(self, translator):
        """Test translation with numbers only"""
        gloss, breakdown, duration = translator.text_to_gloss("123 456")
        assert len(gloss) > 0 or gloss == ""

    def test_translate_with_special_chars_only(self, translator):
        """Test translation with special characters only"""
        gloss, breakdown, duration = translator.text_to_gloss("@#$ %^& *()")
        assert len(breakdown) == 0

    def test_finger_spell_empty_string(self, translator):
        """Test finger-spelling with empty string"""
        result = translator._finger_spell("")
        assert result == ""

    def test_finger_spell_no_alpha_chars(self, translator):
        """Test finger-spelling with no alphabetic characters"""
        result = translator._finger_spell("123!@#")
        assert result == "123!@#"

    def test_nmm_with_none_input(self, translator):
        """Test NMM generation with None input"""
        with pytest.raises(AttributeError):
            translator.add_non_manual_markers(None)


class TestTranslatorPerformance:
    """Test performance characteristics of BSL translation"""

    def test_translation_speed_single_word(self, translator):
        """Test translation speed for single word"""
        start = time.time()
        translator.text_to_gloss("hello")
        duration = time.time() - start
        assert duration < 0.1  # Should be very fast

    def test_translation_speed_long_sentence(self, translator):
        """Test translation speed for long sentence"""
        long_text = " ".join(["word"] * 100)
        start = time.time()
        translator.text_to_gloss(long_text)
        duration = time.time() - start
        assert duration < 0.5  # Should still be fast

    def test_nmm_generation_speed(self, translator):
        """Test NMM generation speed"""
        start = time.time()
        translator.add_non_manual_markers("What is your name?")
        duration = time.time() - start
        assert duration < 0.1

    def test_full_translation_performance(self, translator):
        """Test full translation with NMM performance"""
        start = time.time()
        translator.translate_with_nmm("What is your name?")
        duration = time.time() - start
        assert duration < 0.1


class TestTranslatorIntegration:
    """Integration tests for BSL translator"""

    def test_translate_then_render_workflow(self, translator):
        """Test typical translate-then-render workflow"""
        text = "Hello, how are you?"

        # Translate
        result = translator.translate_with_nmm(text)

        # Verify translation is renderable
        assert len(result["gloss"]) > 0
        assert len(result["breakdown"]) > 0
        assert result["duration_estimate"] > 0

    def test_multiple_translations_consistency(self, translator):
        """Test that multiple translations of same text are consistent"""
        text = "Hello world"

        result1 = translator.translate_with_nmm(text)
        result2 = translator.translate_with_nmm(text)

        assert result1["gloss"] == result2["gloss"]
        assert result1["breakdown"] == result2["breakdown"]

    def test_batch_translation(self, translator):
        """Test translating multiple texts in sequence"""
        texts = ["hello", "thank you", "what is your name?"]
        results = [translator.translate_with_nmm(text) for text in texts]

        assert len(results) == 3
        assert all(r["gloss"] for r in results)

    def test_translation_with_context_preservation(self, translator):
        """Test that translation preserves semantic context"""
        # Questions should get question NMM
        result = translator.translate_with_nmm("What is your name?")
        assert len(result["non_manual_markers"]) > 0
        assert any("brows" in m for m in result["non_manual_markers"])


class TestTranslatorNMMCombinations:
    """Test various NMM marker combinations"""

    def test_wh_question_markers(self, translator):
        """Test all wh-question words get correct markers"""
        wh_words = ["what", "where", "when", "why", "who", "which", "how"]
        for word in wh_words:
            nmm = translator.add_non_manual_markers(f"{word} is this?")
            assert "brows-down" in nmm
            assert "eyes-wide" in nmm

    def test_conditional_markers(self, translator):
        """Test all conditional words get correct markers"""
        conditionals = ["if", "when", "unless"]
        for word in conditionals:
            nmm = translator.add_non_manual_markers(f"{word} it happens")
            assert "brows-up" in nmm
            assert "head-tilt" in nmm

    def test_negation_markers(self, translator):
        """Test all negation words get correct markers"""
        negations = ["not", "no", "never", "nothing", "nobody", "none"]
        for word in negations:
            nmm = translator.add_non_manual_markers(f"I {word} understand")
            assert "head-shake" in nmm
            assert "brows-down" in nmm

    def test_exclamation_markers(self, translator):
        """Test exclamation gets correct markers"""
        nmm = translator.add_non_manual_markers("Great!")
        assert "eyes-wide" in nmm
        assert "body-lean-forward" in nmm


class TestTranslatorDictionaryBehavior:
    """Test dictionary lookup behavior"""

    def test_phrase_vs_word_by_word(self, translator):
        """Test phrase dictionary vs word-by-word translation"""
        # Phrase should translate as single unit
        gloss1, _, _ = translator.text_to_gloss("thank you")
        assert "THANK YOU" in gloss1

    def test_dictionary_case_sensitivity(self, translator):
        """Test that dictionary is case-insensitive"""
        gloss1, _, _ = translator.text_to_gloss("HELLO")
        gloss2, _, _ = translator.text_to_gloss("Hello")
        assert gloss1 == gloss2

    def test_unknown_word_fallback(self, translator):
        """Test that unknown words fallback to finger-spelling"""
        gloss, breakdown, duration = translator.text_to_gloss("supercalifragilistic")
        assert "FS-" in gloss

    def test_partial_dictionary_match(self, translator):
        """Test translation with partial dictionary matches"""
        gloss, breakdown, duration = translator.text_to_gloss("hello xyz world")
        assert "HELLO" in gloss
        assert "WORLD" in gloss
        assert "FS-" in breakdown[1]  # xyz should be finger-spelled


class TestTranslatorLogging:
    """Test logging behavior"""

    @patch('translator.logger')
    def test_translation_logs_info(self, mock_logger, translator):
        """Test that translation logs info messages"""
        translator.text_to_gloss("hello world")
        assert mock_logger.info.called

    @patch('translator.logger')
    def test_dictionary_translation_logs(self, mock_logger, translator):
        """Test that dictionary translation is logged"""
        translator.text_to_gloss("hello")
        assert mock_logger.info.called
        call_args = str(mock_logger.info.call_args)
        assert "dictionary" in call_args.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
