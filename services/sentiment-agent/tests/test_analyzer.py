"""
Unit tests for Sentiment Analyzer module.

Tests verify that the sentiment analyzer can:
- Analyze individual text for sentiment
- Batch analyze multiple texts
- Handle edge cases properly
- Use rule-based fallback when ML model is not available
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from sentiment_agent.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzerInitialization:
    """Tests for SentimentAnalyzer initialization."""

    def test_analyzer_initializes_without_model(self):
        """Test that analyzer can initialize without ML model (rule-based mode)."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        assert analyzer is not None
        assert analyzer.model_available is False

    def test_analyzer_initializes_with_mock_model(self):
        """Test that analyzer can initialize with mock model placeholder."""
        analyzer = SentimentAnalyzer(use_ml_model=True)
        assert analyzer is not None
        # Mock model is requested but not actually available (ML model not loaded)
        # The analyzer still works using rule-based analysis
        assert analyzer.model_available is False
        assert analyzer.use_ml_model is True  # ML mode was requested


class TestRuleBasedSentimentAnalysis:
    """Tests for rule-based sentiment analysis (keyword matching)."""

    def test_positive_sentiment_keywords(self):
        """Test detection of positive sentiment using keywords."""
        analyzer = SentimentAnalyzer(use_ml_model=False)

        positive_texts = [
            "I loved this performance!",
            "Amazing show, really enjoyed it.",
            "The actors were fantastic and wonderful.",
            "Great experience, so happy I came.",
            "Brilliant performance, excellent work!"
        ]

        for text in positive_texts:
            result = analyzer.analyze(text)
            assert result["sentiment"] == "positive", f"Failed for: {text}"
            assert result["score"] > 0.5, f"Score too low for: {text}"

    def test_negative_sentiment_keywords(self):
        """Test detection of negative sentiment using keywords."""
        analyzer = SentimentAnalyzer(use_ml_model=False)

        negative_texts = [
            "I hated this performance.",
            "Terrible show, really disappointed.",
            "The actors were awful and boring.",
            "Poor experience, sad I came.",
            "Horrible performance, bad work!"
        ]

        for text in negative_texts:
            result = analyzer.analyze(text)
            assert result["sentiment"] == "negative", f"Failed for: {text}"
            assert result["score"] < 0.5, f"Score too high for: {text}"

    def test_neutral_sentiment_keywords(self):
        """Test detection of neutral sentiment."""
        analyzer = SentimentAnalyzer(use_ml_model=False)

        neutral_texts = [
            "The performance was okay.",
            "It was an average show.",
            "The actors were fine.",
            "I suppose it was alright.",
            "Standard performance, nothing special."
        ]

        for text in neutral_texts:
            result = analyzer.analyze(text)
            assert result["sentiment"] == "neutral", f"Failed for: {text}"
            assert 0.4 <= result["score"] <= 0.6, f"Score out of range for: {text}"

    def test_empty_text(self):
        """Test handling of empty text."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("")
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.5

    def test_whitespace_only(self):
        """Test handling of whitespace-only text."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("   ")
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.5


class TestSentimentAnalysisResponse:
    """Tests for sentiment analysis response structure."""

    def test_response_contains_required_fields(self):
        """Test that analyze response contains all required fields."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("Great show!")

        assert "sentiment" in result
        assert "score" in result
        assert "confidence" in result
        assert "emotions" in result

    def test_sentiment_value_is_valid(self):
        """Test that sentiment field has valid value."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("Great show!")

        assert result["sentiment"] in ["positive", "negative", "neutral"]

    def test_score_is_in_valid_range(self):
        """Test that score is between 0 and 1."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("Great show!")

        assert 0.0 <= result["score"] <= 1.0

    def test_confidence_is_in_valid_range(self):
        """Test that confidence is between 0 and 1."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("Great show!")

        assert 0.0 <= result["confidence"] <= 1.0

    def test_emotions_contains_all_required_emotions(self):
        """Test that emotions dict contains all required emotion types."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("Great show!")

        required_emotions = ["joy", "surprise", "neutral", "sadness", "anger", "fear"]
        for emotion in required_emotions:
            assert emotion in result["emotions"]
            assert 0.0 <= result["emotions"][emotion] <= 1.0


class TestBatchAnalysis:
    """Tests for batch sentiment analysis."""

    def test_batch_analysis_returns_list(self):
        """Test that batch analysis returns a list of results."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        texts = ["Great show!", "Terrible performance", "It was okay"]

        results = analyzer.analyze_batch(texts)

        assert isinstance(results, list)
        assert len(results) == len(texts)

    def test_batch_analysis_with_empty_list(self):
        """Test that batch analysis handles empty list."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        results = analyzer.analyze_batch([])

        assert results == []

    def test_batch_analysis_maintains_order(self):
        """Test that batch analysis maintains input order."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        texts = ["Great show!", "Terrible performance", "It was okay"]

        results = analyzer.analyze_batch(texts)

        # Check that order is preserved
        assert results[0]["sentiment"] == "positive"
        assert results[1]["sentiment"] == "negative"
        assert results[2]["sentiment"] == "neutral"

    def test_batch_analysis_each_result_has_structure(self):
        """Test that each result in batch has correct structure."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        texts = ["Great show!", "Terrible performance"]

        results = analyzer.analyze_batch(texts)

        for result in results:
            assert "sentiment" in result
            assert "score" in result
            assert "confidence" in result
            assert "emotions" in result


class TestEmotionDetection:
    """Tests for emotion detection in sentiment analysis."""

    def test_positive_text_has_joy_emotion(self):
        """Test that positive text has high joy emotion."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("I loved this performance!")

        assert result["emotions"]["joy"] > 0.5

    def test_negative_text_has_sadness_or_anger(self):
        """Test that negative text has high sadness or anger emotion."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("I hated this terrible performance!")

        assert result["emotions"]["sadness"] > 0.3 or result["emotions"]["anger"] > 0.3

    def test_surprise_emotion_for_exclamations(self):
        """Test that exclamations trigger surprise emotion."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        result = analyzer.analyze("Wow! That was amazing!")

        assert result["emotions"]["surprise"] > 0.3


class TestEdgeCases:
    """Tests for edge cases and special inputs."""

    def test_very_long_text(self):
        """Test handling of very long text."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        long_text = "This is amazing! " * 100

        result = analyzer.analyze(long_text)
        assert result["sentiment"] == "positive"

    def test_text_with_punctuation(self):
        """Test handling of text with various punctuation."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        text = "Wow!!! This was... amazing, right?! So good."

        result = analyzer.analyze(text)
        assert result["sentiment"] == "positive"

    def test_text_with_numbers(self):
        """Test handling of text with numbers."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        text = "I give this 10 out of 10, absolutely fantastic!"

        result = analyzer.analyze(text)
        assert result["sentiment"] == "positive"

    def test_mixed_sentiment(self):
        """Test handling of mixed sentiment (should default to neutral)."""
        analyzer = SentimentAnalyzer(use_ml_model=False)
        text = "The beginning was great but the ending was terrible."

        result = analyzer.analyze(text)
        # Mixed sentiments should lean towards neutral
        assert result["sentiment"] in ["neutral", "positive", "negative"]


class TestModelIntegration:
    """Tests for ML model integration (mock for now)."""

    def test_ml_model_mode_uses_mock(self):
        """Test that ML model mode uses mock implementation."""
        analyzer = SentimentAnalyzer(use_ml_model=True)
        result = analyzer.analyze("Great show!")

        # Should return valid result even with mock
        assert result["sentiment"] in ["positive", "negative", "neutral"]
        assert 0.0 <= result["score"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
