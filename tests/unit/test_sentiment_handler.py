"""Unit tests for sentiment handler"""

import pytest
from services.sentiment_agent.src.core.sentiment_analyzer import SentimentAnalyzer


@pytest.mark.unit
class TestSentimentAnalyzer:
    """Test cases for SentimentAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer(None)

    @pytest.mark.asyncio
    async def test_analyze_positive(self, analyzer):
        """Test positive sentiment analysis."""
        result = await analyzer.analyze("This is amazing!")

        assert result["sentiment"] == "positive"
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_analyze_batch(self, analyzer):
        """Test batch sentiment analysis."""
        texts = ["Great!", "Amazing!", "Love it!"]
        results = await analyzer.analyze_batch(texts)

        assert len(results) == 3
        for result in results:
            assert "sentiment" in result
