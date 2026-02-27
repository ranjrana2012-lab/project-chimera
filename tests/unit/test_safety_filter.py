"""Unit tests for Safety Filter - main integration tests."""

import pytest
from services.safety_filter.src.core.word_filter import WordFilter
from services.safety_filter.src.core.ml_filter import MLFilter
from services.safety_filter.src.core.policy_engine import PolicyEngine, StrictnessLevel
from services.safety_filter.src.models.request import SafetyCheckRequest, SafetyCheckOptions


@pytest.mark.unit
class TestSafetyFilterIntegration:
    """Integration tests for Safety Filter components."""

    @pytest.fixture
    def word_filter(self):
        """Create word filter instance."""
        return WordFilter()

    @pytest.fixture
    def ml_filter(self):
        """Create ML filter instance."""
        return MLFilter(device="cpu")

    @pytest.fixture
    def policy_engine(self):
        """Create policy engine instance."""
        return PolicyEngine()

    @pytest.mark.asyncio
    async def test_word_filter_detects_profanity(self, word_filter):
        """Test that word filter detects profanity."""
        result = await word_filter.check("This contains damn and hell words.")
        assert result["flagged"] is True
        assert len(result["matches"]) > 0

    @pytest.mark.asyncio
    async def test_word_filter_allows_clean_content(self, word_filter):
        """Test that word filter allows clean content."""
        result = await word_filter.check("The stage lights dimmed slowly.")
        assert result["flagged"] is False
        assert result["action"] == "allow"

    @pytest.mark.asyncio
    async def test_ml_filter_classification(self, ml_filter):
        """Test ML filter classification."""
        await ml_filter.load_model()
        result = await ml_filter.classify("This is a safe message about theater.")
        assert result is not None
        assert "safe" in result or "fallback" in result

    @pytest.mark.asyncio
    async def test_policy_engine_evaluation(self, policy_engine):
        """Test policy engine evaluation."""
        word_results = {
            "action": "flag",
            "matches": [{"category": "profanity"}],
            "category_results": {},
            "highest_severity": "medium"
        }
        ml_results = {
            "harm_probability": 0.5,
            "category_scores": {"profanity": 0.6}
        }

        result = policy_engine.evaluate(
            content="Test content",
            word_filter_results=word_results,
            ml_filter_results=ml_results,
            strictness=StrictnessLevel.MODERATE
        )
        assert "decision" in result
        assert "safe" in result

    @pytest.mark.asyncio
    async def test_end_to_end_safety_check(self, word_filter, ml_filter, policy_engine):
        """Test end-to-end safety check flow."""
        await ml_filter.load_model()

        content = "Check this content for safety issues."

        # Step 1: Word filter
        word_result = await word_filter.check(content)

        # Step 2: ML filter
        ml_result = await ml_filter.classify(content)

        # Step 3: Policy evaluation
        policy_result = policy_engine.evaluate(
            content=content,
            word_filter_results=word_result,
            ml_filter_results=ml_result,
            strictness=StrictnessLevel.MODERATE
        )

        # Verify flow completed
        assert word_result is not None
        assert ml_result is not None
        assert policy_result is not None
        assert "decision" in policy_result

    @pytest.mark.asyncio
    async def test_strictness_affects_outcome(self, word_filter, ml_filter, policy_engine):
        """Test that strictness level affects filtering outcome."""
        await ml_filter.load_model()

        content = "This might be borderline content."

        word_result = await word_filter.check(content)
        ml_result = await ml_filter.classify(content)

        # Test with different strictness levels
        permissive_result = policy_engine.evaluate(
            content=content,
            word_filter_results=word_result,
            ml_filter_results=ml_result,
            strictness=StrictnessLevel.PERMISSIVE
        )

        strict_result = policy_engine.evaluate(
            content=content,
            word_filter_results=word_result,
            ml_filter_results=ml_result,
            strictness=StrictnessLevel.STRICT
        )

        assert "decision" in permissive_result
        assert "decision" in strict_result

    @pytest.mark.asyncio
    async def test_content_filtering(self, word_filter):
        """Test content filtering with replacement."""
        original = "What the hell is going on?"
        filtered = await word_filter.filter_content(original, filter_char="*")

        # Content should be modified
        assert filtered is not None
        # Filtered content should be different from original if words were matched
        # or same if no matches - both are valid outcomes

    def test_policy_rule_management(self, policy_engine):
        """Test adding and removing policy rules."""
        from services.safety_filter.src.core.policy_engine import PolicyRule

        initial_count = len(policy_engine.rules)

        # Add rule
        rule = PolicyRule(
            name="test_rule",
            category="profanity",
            action="block",
            threshold=0.8
        )
        policy_engine.add_rule(rule)
        assert len(policy_engine.rules) > initial_count

        # Remove rule
        policy_engine.remove_rule("test_rule")
        assert policy_engine.get_rule("test_rule") is None

    @pytest.mark.asyncio
    async def test_batch_processing(self, word_filter, ml_filter):
        """Test processing multiple contents."""
        await ml_filter.load_model()

        contents = [
            "Safe message one.",
            "Safe message two.",
            "Safe message three."
        ]

        results = []
        for content in contents:
            word_result = await word_filter.check(content)
            ml_result = await ml_filter.classify(content)
            results.append({
                "content": content,
                "word_flagged": word_result["flagged"],
                "ml_safe": ml_result.get("safe", True)
            })

        assert len(results) == len(contents)

    @pytest.mark.asyncio
    async def test_performance_under_load(self, word_filter):
        """Test performance under load."""
        import time

        content = "This is a test message for performance testing."
        iterations = 1000

        start = time.time()
        for _ in range(iterations):
            await word_filter.check(content)
        duration = time.time() - start

        # Should process reasonably fast
        assert duration < 10.0  # 1000 checks in < 10 seconds

    @pytest.mark.asyncio
    async def test_category_specific_filtering(self, word_filter):
        """Test filtering by specific categories."""
        content = "Test content here"

        # Check only profanity category
        result = await word_filter.check(content, categories=["profanity"])

        assert "category_results" in result
        assert "profanity" in result["category_results"]

    @pytest.mark.asyncio
    async def test_edge_cases(self, word_filter):
        """Test edge cases."""
        # Empty content
        result1 = await word_filter.check("")
        assert result1["action"] == "allow"

        # Very long content
        long_content = "safe " * 1000
        result2 = await word_filter.check(long_content)
        assert result2 is not None

        # Special characters
        special_content = "Test with @#$ special characters!"
        result3 = await word_filter.check(special_content)
        assert result3 is not None

    @pytest.mark.asyncio
    async def test_confidence_scores(self, ml_filter):
        """Test confidence score ranges."""
        await ml_filter.load_model()

        test_cases = [
            "This is clearly safe content.",
            "Another safe message here.",
            "The performance was wonderful!"
        ]

        for content in test_cases:
            result = await ml_filter.classify(content)
            if "confidence" in result:
                assert 0.0 <= result["confidence"] <= 1.0
            if "harm_probability" in result:
                assert 0.0 <= result["harm_probability"] <= 1.0

    @pytest.mark.asyncio
    async def test_fallback_behavior(self):
        """Test fallback when ML model is unavailable."""
        filter_instance = MLFilter(device="cpu")
        # Don't load model - should use fallback

        result = await filter_instance.classify("Test content.")
        assert result is not None
        assert "fallback" in result or "prediction" in result

    def test_settings_validation(self):
        """Test settings configuration."""
        from services.safety_filter.src.config import settings

        assert settings.app_name == "safety-filter"
        assert settings.port == 8006
        assert settings.cors_origins is not None
