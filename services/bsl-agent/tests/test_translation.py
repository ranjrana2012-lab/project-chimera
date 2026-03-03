"""
Unit tests for BSL Translation module.
"""

import pytest
from unittest.mock import Mock, patch
import time

import sys
sys.path.insert(0, '.')

from core.translation import (
    BSLTranslator,
    TranslationRequest,
    GlossFormat,
    translate_and_enrich
)


class TestBSLTranslator:
    """Test BSL translator functionality."""

    def test_translator_initialization(self):
        """Translator initializes with default config."""
        translator = BSLTranslator()

        assert translator.cache_ttl == 86400
        assert translator.degraded_mode is True  # No redis

    def test_simple_phrase_translation(self):
        """Translate simple phrases from dictionary."""
        translator = BSLTranslator()

        request = TranslationRequest(text="hello")
        result = translator.translate(request)

        assert "HELLO" in result.gloss
        assert "[right]" in result.gloss or "wave" in result.gloss.lower()
        assert result.confidence > 0.8

    def test_unknown_word_finger_spelled(self):
        """Unknown words are finger-spelt."""
        translator = BSLTranslator()

        request = TranslationRequest(text="xyzword")
        result = translator.translate(request)

        assert "FS-X" in result.gloss
        assert "FS-Y" in result.gloss
        assert "FS-Z" in result.gloss

    def test_sentence_translation(self):
        """Translate sentences word-by-word."""
        translator = BSLTranslator()

        request = TranslationRequest(text="thank you very much")
        result = translator.translate(request)

        # "thank you" should be in dictionary
        assert "THANK-YOU" in result.gloss or "FS-T" in result.gloss

    def test_batch_translation(self):
        """Translate multiple texts in batch."""
        translator = BSLTranslator()

        requests = [
            TranslationRequest(text="hello"),
            TranslationRequest(text="yes"),
            TranslationRequest(text="no")
        ]

        results = translator.translate_batch(requests)

        assert len(results) == 3
        assert all(r.gloss for r in results)

    def test_caching_with_redis(self):
        """Translation results are cached."""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex = Mock()

        translator = BSLTranslator(redis_client=redis_mock)

        request = TranslationRequest(text="hello")

        # First call - not cached
        result1 = translator.translate(request)
        assert result1.from_cache is False

        # Second call - cached
        redis_mock.get.return_value = b"HELLO[right]wave"
        result2 = translator.translate(request)
        assert result2.from_cache is True

    def test_degraded_mode_without_redis(self):
        """Service works in degraded mode without Redis."""
        translator = BSLTranslator(redis_client=None)

        assert translator.degraded_mode is True

        request = TranslationRequest(text="hello")
        result = translator.translate(request)

        assert result.gloss  # Still works
        assert result.degraded is True

    def test_confidence_scores(self):
        """Different translations have different confidence scores."""
        translator = BSLTranslator()

        # Dictionary phrase - high confidence
        result1 = translator.translate(TranslationRequest(text="hello"))
        assert result1.confidence >= 0.8

        # Unknown word - lower confidence
        result2 = translator.translate(TranslationRequest(text="unknown"))
        assert result2.confidence >= 0.4  # Fallback finger-spelling

    def test_translation_duration_estimation(self):
        """Duration is estimated based on word count."""
        translator = BSLTranslator()

        request = TranslationRequest(text="hello")
        result = translator.translate(request)

        # Should be ~0.5 seconds per word
        assert result.duration > 0

    def test_gloss_format_default(self):
        """Default gloss format is SignSpell."""
        request = TranslationRequest(text="hello")

        assert request.gloss_format == GlossFormat.SIGN_SPELL

    def test_breakdown_created(self):
        """Breakdown splits gloss into signs."""
        translator = BSLTranslator()

        request = TranslationRequest(text="hello thank you")
        result = translator.translate(request)

        assert isinstance(result.breakdown, list)
        assert len(result.breakdown) > 0

    def test_error_returns_fallback(self):
        """Translation errors return fallback finger-spelling."""
        translator = BSLTranslator()

        # Force an error by patching
        with patch.object(translator, '_translate_text', side_effect=Exception("Fail")):
            result = translator.translate(TranslationRequest(text="test"))

        assert result.error is not None
        assert "FS-T" in result.gloss  # Fallback finger-spelling


class TestConvenienceFunction:
    """Test convenience function."""

    def test_translate_and_enrich(self):
        """Convenience function returns dict format."""
        result = translate_and_enrich("hello")

        assert result["source_text"] == "hello"
        assert "gloss" in result
        assert result["gloss_format"] == "singspell"
        assert isinstance(result["breakdown"], list)

    def test_convenience_function_with_options(self):
        """Convenience function accepts options."""
        result = translate_and_enrich(
            "hello",
            gloss_format=GlossFormat.HAMNOSYS
        )

        assert result["gloss_format"] == "hamnosys"


class TestPerformanceTargets:
    """Test BSL agent performance targets."""

    def test_translation_under_200ms(self):
        """Single translation completes in <200ms."""
        translator = BSLTranslator()

        start = time.time()
        translator.translate(TranslationRequest(text="hello"))
        elapsed = time.time() - start

        assert elapsed < 0.2

    def test_batch_of_10_under_1s(self):
        """Batch of 10 translations completes in <1 second."""
        translator = BSLTranslator()

        requests = [
            TranslationRequest(text=f"word{i}")
            for i in range(10)
        ]

        start = time.time()
        translator.translate_batch(requests)
        elapsed = time.time() - start

        assert elapsed < 1.0

    def test_cache_hit_under_1ms(self):
        """Cache hit returns in <1ms."""
        redis_mock = Mock()
        redis_mock.get.return_value = b"CACHED gloss"

        translator = BSLTranslator(redis_client=redis_mock)

        start = time.time()
        translator.translate(TranslationRequest(text="hello"))
        elapsed = time.time() - start

        # Should be very fast (cached)
        assert elapsed < 0.01
        assert elapsed < 0.001  # Ideally <1ms


class TestReliabilityFeatures:
    """Test BSL agent reliability."""

    def test_survives_redis_failure(self):
        """Service continues when Redis fails."""
        redis_mock = Mock()
        redis_mock.get.side_effect = Exception("Redis down")
        redis_mock.setex.side_effect = Exception("Redis down")

        translator = BSLTranslator(redis_client=redis_mock)

        request = TranslationRequest(text="hello")
        result = translator.translate(request)

        # Should still work
        assert result.gloss
        assert result.degraded is True

    def test_handles_empty_text(self):
        """Empty text is handled gracefully."""
        translator = BSLTranslator()

        request = TranslationRequest(text="")
        result = translator.translate(request)

        # Should return empty or finger-spelled empty
        assert isinstance(result.gloss, str)

    def test_handles_very_long_text(self):
        """Very long text is handled."""
        translator = BSLTranslator()

        long_text = " ".join(["word"] * 100)
        request = TranslationRequest(text=long_text)

        result = translator.translate(request)

        # Should complete without error
        assert result.gloss
        assert result.duration > 0  # Longer duration
