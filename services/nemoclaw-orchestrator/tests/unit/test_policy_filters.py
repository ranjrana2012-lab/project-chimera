# services/nemoclaw-orchestrator/tests/unit/test_policy_filters.py
import pytest
from policy.filters import InputSanitizer, OutputFilter

class TestInputSanitizer:
    @pytest.mark.asyncio
    async def test_removes_profanity(self):
        sanitizer = InputSanitizer()
        result = await sanitizer.sanitize({"text": "This is f***ing bad"})
        assert "f***ing" not in result["text"]

    @pytest.mark.asyncio
    async def test_truncates_long_text(self):
        sanitizer = InputSanitizer(max_length=100)
        long_text = "x" * 1000
        result = await sanitizer.sanitize({"dialogue": long_text})
        assert len(result["dialogue"]) <= 100

class TestOutputFilter:
    @pytest.mark.asyncio
    async def test_filters_pii_from_output(self):
        filter = OutputFilter()
        result = await filter.filter(
            {"text": "Call me at 555-123-4567"},
            "scenespeak-agent"
        )
        assert "555-123-4567" not in result["text"]
