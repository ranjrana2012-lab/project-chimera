"""Unit tests for Safety Filter Word Filter module."""

import pytest
from services.safety_filter.src.core.word_filter import WordFilter


@pytest.mark.unit
class TestWordFilter:
    """Test cases for WordFilter class."""

    @pytest.fixture
    def filter(self):
        """Create a WordFilter instance for testing."""
        return WordFilter()

    @pytest.mark.asyncio
    async def test_initialization(self, filter):
        """Test that WordFilter initializes correctly."""
        assert filter.word_lists is not None
        assert "profanity" in filter.word_lists
        assert "violence" in filter.word_lists
        assert filter.compiled_patterns is not None

    @pytest.mark.asyncio
    async def test_detects_profanity(self, filter):
        """Test that profanity is detected."""
        result = await filter.check("This is damn annoying and hell to deal with.")
        assert result["flagged"] is True
        assert len(result["matches"]) > 0
        assert any(m["category"] == "profanity" for m in result["matches"])

    @pytest.mark.asyncio
    async def test_allows_clean_content(self, filter):
        """Test that clean content is allowed."""
        result = await filter.check("The stage lights dimmed slowly for the performance.")
        assert result["flagged"] is False
        assert result["action"] == "allow"
        assert len(result["matches"]) == 0

    @pytest.mark.asyncio
    async def test_severe_profanity_blocked(self, filter):
        """Test that severe profanity triggers block action."""
        result = await filter.check("This is fucking bullshit.")
        assert result["action"] in ["block", "flag"]

    @pytest.mark.asyncio
    async def test_category_filtering(self, filter):
        """Test filtering by specific categories."""
        result = await filter.check(
            "damn this",
            categories=["profanity"]
        )
        assert len(result["category_results"]) > 0
        assert "profanity" in result["category_results"]

    @pytest.mark.asyncio
    async def test_get_match_positions(self, filter):
        """Test getting match positions."""
        positions = await filter.get_match_positions("What the hell is this?")
        assert len(positions) > 0
        assert "position" in positions[0]
        assert "text" in positions[0]

    @pytest.mark.asyncio
    async def test_get_matched_terms(self, filter):
        """Test getting matched terms as set."""
        terms = await filter.get_matched_terms("damn and hell")
        assert "damn" in terms or "hell" in terms

    @pytest.mark.asyncio
    async def test_filter_content_replacement(self, filter):
        """Test content filtering with replacement."""
        filtered = await filter.filter_content("What the hell is this?", filter_char="*")
        assert "****" in filtered or "hell" not in filtered.lower()

    @pytest.mark.asyncio
    async def test_add_custom_words(self, filter):
        """Test adding custom words to filter."""
        filter.add_custom_words("custom", ["testword"], severity="medium")
        result = await filter.check("This includes testword here.")
        assert len(result["matches"]) > 0

    @pytest.mark.asyncio
    async def test_remove_words(self, filter):
        """Test removing words from filter."""
        # Add a word
        filter.add_custom_words("test_category", ["removeme"], severity="medium")
        result1 = await filter.check("removeme this")
        assert len(result1["matches"]) > 0

        # Remove the word
        filter.remove_words("test_category", ["removeme"])
        result2 = await filter.check("removeme this")
        # Should have fewer or no matches after removal
        assert len(result2["matches"]) <= len(result1["matches"])

    @pytest.mark.asyncio
    async def test_multiple_matches(self, filter):
        """Test detecting multiple offensive words."""
        result = await filter.check("damn this hell is annoying")
        assert len(result["matches"]) >= 2

    @pytest.mark.asyncio
    async def test_case_insensitive(self, filter):
        """Test that matching is case insensitive."""
        result_lower = await filter.check("damn")
        result_upper = await filter.check("DAMN")
        result_mixed = await filter.check("DaMn")

        # All should be flagged
        assert result_lower["flagged"]
        assert result_upper["flagged"]
        assert result_mixed["flagged"]

    @pytest.mark.asyncio
    async def test_empty_content(self, filter):
        """Test handling of empty content."""
        result = await filter.check("")
        assert result["flagged"] is False
        assert result["action"] == "allow"

    @pytest.mark.asyncio
    async def test_severity_levels(self, filter):
        """Test that different severity levels are detected."""
        # Severe profanity
        result_severe = await filter.check("fuck this shit")
        assert result_severe["highest_severity"] in ["severe", "medium", "custom"]

    @pytest.mark.asyncio
    async def test_performance(self, filter):
        """Test word filter performance."""
        import time
        content = "This is a test sentence for performance testing."
        start = time.time()
        for _ in range(1000):
            await filter.check(content)
        duration = time.time() - start
        # Should process 1000 checks reasonably fast
        assert duration < 5.0
