"""Unit tests for Safety Filter ML Filter module."""

import pytest
from services.safety_filter.src.core.ml_filter import MLFilter


@pytest.mark.unit
class TestMLFilter:
    """Test cases for MLFilter class."""

    @pytest.fixture
    def filter(self):
        """Create an MLFilter instance for testing."""
        return MLFilter(device="cpu")

    @pytest.mark.asyncio
    async def test_initialization(self, filter):
        """Test that MLFilter initializes correctly."""
        assert filter.model is None  # Not loaded yet
        assert filter.tokenizer is None
        assert filter.model_loaded is False
        assert filter.categories is not None
        assert len(filter.categories) > 0

    @pytest.mark.asyncio
    async def test_load_model(self, filter):
        """Test model loading."""
        await filter.load_model()
        # Even with fallback, model_loaded should reflect state
        # The filter will use rule-based fallback if model fails to load
        assert filter.model_version is not None

    @pytest.mark.asyncio
    async def test_classify_safe_content(self, filter):
        """Test classification of safe content."""
        await filter.load_model()
        result = await filter.classify("The performance was wonderful and the actors were amazing.")
        assert result is not None
        assert "safe" in result
        assert "confidence" in result
        assert "harm_probability" in result

    @pytest.mark.asyncio
    async def test_classify_with_details(self, filter):
        """Test classification with detailed results."""
        await filter.load_model()
        result = await filter.classify(
            "This is a test message.",
            include_details=True
        )
        assert "category_scores" in result or "fallback" in result

    @pytest.mark.asyncio
    async def test_classify_without_details(self, filter):
        """Test classification without detailed results."""
        await filter.load_model()
        result = await filter.classify(
            "Test content.",
            include_details=False
        )
        assert "prediction" in result or "fallback" in result

    @pytest.mark.asyncio
    async def test_fallback_when_model_unavailable(self, filter):
        """Test that fallback works when model is unavailable."""
        # Don't load model, force fallback
        result = await filter.classify("Test content with hate speech words.")
        assert result is not None
        assert "fallback" in result or "prediction" in result

    @pytest.mark.asyncio
    async def test_classify_batch(self, filter):
        """Test batch classification."""
        await filter.load_model()
        contents = [
            "This is safe content.",
            "Another safe message.",
            "Third safe message."
        ]
        results = await filter.classify_batch(contents)
        assert len(results) == len(contents)
        assert all("safe" in r or "fallback" in r for r in results)

    @pytest.mark.asyncio
    async def test_preprocess_text(self, filter):
        """Test text preprocessing."""
        original = "  This   has    extra   whitespace  "
        processed = filter._preprocess_text(original)
        assert "  " not in processed  # No double spaces
        assert processed.strip() == processed

    @pytest.mark.asyncio
    async def test_harm_probability_calculation(self, filter):
        """Test harm probability is calculated correctly."""
        await filter.load_model()
        result = await filter.classify("Test content.")
        assert "harm_probability" in result
        assert 0.0 <= result["harm_probability"] <= 1.0

    @pytest.mark.asyncio
    async def test_close_cleanup(self, filter):
        """Test that close cleans up resources."""
        await filter.load_model()
        await filter.close()
        # After close, resources should be cleaned
        assert filter.model_loaded is False

    @pytest.mark.asyncio
    async def test_confidence_range(self, filter):
        """Test that confidence is always in valid range."""
        await filter.load_model()
        test_cases = [
            "Safe content here.",
            "Another test message.",
            "Performance was great!"
        ]
        for content in test_cases:
            result = await filter.classify(content)
            if "confidence" in result:
                assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_category_scores_in_fallback(self, filter):
        """Test category scores in fallback mode."""
        result = await filter.classify("This contains hate speech and violence words")
        # Fallback should provide category scores
        assert "category_scores" in result

    @pytest.mark.asyncio
    async def test_empty_content(self, filter):
        """Test handling of empty content."""
        await filter.load_model()
        result = await filter.classify("")
        assert result is not None
        assert "safe" in result or "fallback" in result

    @pytest.mark.asyncio
    async def test_model_version(self, filter):
        """Test that model version is set."""
        await filter.load_model()
        result = await filter.classify("Test.")
        assert "model_version" in result
        assert result["model_version"] is not None
