"""Unit tests for safety filter"""

import pytest
from services.safety_filter.src.core.layers.pattern_matcher import PatternMatcher


@pytest.mark.unit
class TestPatternMatcher:
    """Test cases for PatternMatcher"""

    @pytest.fixture
    def matcher(self):
        return PatternMatcher()

    @pytest.mark.asyncio
    async def test_blocks_profanity(self, matcher):
        """Test that profanity is blocked."""
        result = await matcher.check("This contains [PROFANE] content")
        assert result["action"] in ["block", "flag"]

    @pytest.mark.asyncio
    async def test_allows_clean_content(self, matcher):
        """Test that clean content is allowed."""
        result = await matcher.check("The stage lights dimmed slowly.")
        assert result["action"] == "allow"
        assert len(result["matches"]) == 0

    @pytest.mark.asyncio
    async def test_performance(self, matcher):
        """Test pattern matcher performance."""
        import time
        start = time.time()
        for _ in range(1000):
            await matcher.check("Test content for performance.")
        duration = time.time() - start
        assert duration < 1.0  # Should process 1000 checks in < 1 second
