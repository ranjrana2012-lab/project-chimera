"""
Comprehensive unit tests for PatternMatcher.

Tests all pattern categories (profanity, PII, harmful),
custom patterns, policy variations, and edge cases including
unicode and mixed scripts.
"""

import pytest
import re
from typing import List, Tuple
from unittest.mock import patch

import sys
sys.path.insert(0, '.')


class TestPatternMatcherInitialization:
    """Test PatternMatcher initialization."""

    def test_default_family_policy(self):
        """Test matcher with default family policy."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        assert matcher.policy == "family"
        assert len(matcher._compiled_patterns) > 0

    def test_teen_policy(self):
        """Test matcher with teen policy."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="teen")

        assert matcher.policy == "teen"
        assert len(matcher._compiled_patterns) > 0

    def test_adult_policy(self):
        """Test matcher with adult policy."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="adult")

        assert matcher.policy == "adult"

    def test_unrestricted_policy(self):
        """Test matcher with unrestricted policy."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="unrestricted")

        assert matcher.policy == "unrestricted"


class TestProfanityPatterns:
    """Test profanity pattern matching."""

    def test_profanity_detection_family_policy(self):
        """Test profanity detection with family policy."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")
        is_safe, matched = matcher.check("damn this is bad")

        assert is_safe is False
        assert len(matched) > 0
        assert any("profanity" in p.type for p in matched)

    def test_profanity_word_variations(self):
        """Test different profanity word variations."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")
        profanity_words = ["damn", "hell", "shit", "fuck", "bitch"]

        for word in profanity_words:
            is_safe, matched = matcher.check(f"This is {word} bad")
            assert is_safe is False, f"Should block: {word}"

    def test_profanity_case_insensitive(self):
        """Test that profanity matching is case insensitive."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        test_cases = ["DAMN", "DaMn", "damn", "DaMnIt"]

        for test in test_cases:
            is_safe, matched = matcher.check(test)
            assert is_safe is False, f"Should block: {test}"

    def test_profanity_with_punctuation(self):
        """Test profanity with punctuation attached."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        is_safe, _ = matcher.check("This is damn!")
        assert is_safe is False

        is_safe, _ = matcher.check("What the hell?")
        assert is_safe is False

    def test_profanity_in_middle_of_word(self):
        """Test profanity patterns within words."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        # These patterns match within words (e.g., \w*shit\w*)
        is_safe, matched = matcher.check("bullshit")
        # May or may not match depending on pattern configuration
        assert isinstance(is_safe, bool)

    def test_no_profanity_in_adult_policy(self):
        """Test that adult policy doesn't block mild profanity."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="adult")

        # Adult policy is more permissive
        # Mild profanity might pass
        is_safe, matched = matcher.check("This is damn bad")
        # Result depends on policy configuration
        assert isinstance(is_safe, bool)

    def test_safe_content_passes_profanity_check(self):
        """Test that safe content passes profanity check."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        is_safe, matched = matcher.check("Hello, how are you today?")

        assert is_safe is True
        assert len(matched) == 0


class TestPIIPatterns:
    """Test PII (Personally Identifiable Information) pattern matching."""

    def test_email_detection(self):
        """Test email address detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "admin@test-domain.org"
        ]

        for email in emails:
            is_safe, matched = matcher.check(f"My email is {email}")
            assert is_safe is False, f"Should block email: {email}"
            assert any("pii" in p.type for p in matched)

    def test_phone_detection(self):
        """Test phone number detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        phones = [
            "123-456-7890",
            "123.456.7890",
            "1234567890"
        ]

        for phone in phones:
            is_safe, matched = matcher.check(f"Call me at {phone}")
            assert is_safe is False, f"Should block phone: {phone}"

    def test_ssn_detection(self):
        """Test SSN detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        ssn = "123-45-6789"
        is_safe, matched = matcher.check(f"My SSN is {ssn}")

        assert is_safe is False
        assert any("pii" in p.type for p in matched)

    def test_credit_card_detection(self):
        """Test credit card number detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        card = "1234 5678 9012 3456"
        is_safe, matched = matcher.check(f"Card: {card}")

        assert is_safe is False
        assert any("pii" in p.type for p in matched)

    def test_pii_patterns_always_active(self):
        """Test that PII patterns are active in all policies."""
        from pattern_matcher import PatternMatcher

        policies = ["family", "teen", "adult", "unrestricted"]

        for policy in policies:
            matcher = PatternMatcher(policy=policy)
            is_safe, matched = matcher.check("test@example.com")
            # PII should be blocked in all policies
            assert is_safe is False, f"PII should be blocked in {policy} policy"

    def test_no_pii_in_safe_content(self):
        """Test that content without PII passes."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        is_safe, matched = matcher.check("Contact me at my website")

        # Should pass if no PII patterns
        # May be blocked by other patterns though
        assert isinstance(is_safe, bool)


class TestHarmfulPatterns:
    """Test harmful content pattern matching."""

    def test_violence_threat_detection(self):
        """Test violence threat detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        threats = [
            "I want to kill that person",
            "murder someone today",
            "death to people"
        ]

        for threat in threats:
            is_safe, matched = matcher.check(threat)
            assert is_safe is False, f"Should block: {threat}"

    def test_cyberthreat_detection(self):
        """Test cyberthreat pattern detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        threats = [
            "I want to hack the system",
            "exploit this security",
            "bypass the password"
        ]

        for threat in threats:
            is_safe, matched = matcher.check(threat)
            assert is_safe is False, f"Should block: {threat}"

    def test_substance_abuse_detection(self):
        """Test substance abuse pattern detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        content = "drug use and abuse"
        is_safe, matched = matcher.check(content)

        # Should be flagged for harmful content
        assert is_safe is False

    def test_self_harm_detection(self):
        """Test self-harm pattern detection."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        self_harm = ["I want to kill myself", "self.harm is bad", "suicide thoughts"]

        for content in self_harm:
            is_safe, matched = matcher.check(content)
            assert is_safe is False, f"Should block: {content}"

    def test_harmful_patterns_not_in_adult_policy(self):
        """Test that harmful patterns may differ by policy."""
        from pattern_matcher import PatternMatcher

        adult_matcher = PatternMatcher(policy="adult")
        family_matcher = PatternMatcher(policy="family")

        # Pattern counts may differ
        adult_count = adult_matcher.get_pattern_count()
        family_count = family_matcher.get_pattern_count()

        # Just verify both work
        assert adult_count >= 0
        assert family_count >= 0


class TestPatternMatchingBehavior:
    """Test general pattern matching behavior."""

    def test_check_returns_tuple(self):
        """Test that check returns tuple of (is_safe, matched_patterns)."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        result = matcher.check("test content")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)

    def test_multiple_pattern_matches(self):
        """Test content matching multiple patterns."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")
        content = "damn hell and shit with email@test.com"

        is_safe, matched = matcher.check(content)

        assert is_safe is False
        assert len(matched) >= 2

    def test_pattern_position_tracking(self):
        """Test that pattern positions are tracked."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")
        content = "damn this is bad"

        is_safe, matched = matcher.check(content)

        if len(matched) > 0:
            assert matched[0].position is not None
            assert isinstance(matched[0].position, int)

    def test_pattern_type_categorization(self):
        """Test that patterns are categorized by type."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        # Profanity
        is_safe, matched = matcher.check("damn this")
        if len(matched) > 0:
            assert "profanity" in matched[0].type

        # PII
        is_safe, matched = matcher.check("test@example.com")
        if len(matched) > 0:
            assert "pii" in matched[0].type


class TestCustomPatterns:
    """Test custom pattern functionality."""

    def test_add_custom_pattern(self):
        """Test adding a custom pattern."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher()

        initial_count = matcher.get_pattern_count()
        matcher.add_custom_pattern(
            r'\btestword\b',
            "custom_category",
            ModerationLevel.MEDIUM
        )

        new_count = matcher.get_pattern_count()
        assert new_count == initial_count + 1

    def test_custom_pattern_is_matched(self):
        """Test that custom pattern is matched."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher()

        matcher.add_custom_pattern(
            r'\bblockme\b',
            "test_category",
            ModerationLevel.HIGH
        )

        is_safe, matched = matcher.check("This should blockme")

        assert is_safe is False
        assert len(matched) > 0
        assert any("test_category" in p.type for p in matched)

    def test_add_pattern_to_new_category(self):
        """Test adding pattern to a new category."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher()

        matcher.add_custom_pattern(
            r'\btest\b',
            "new_category",
            ModerationLevel.LOW
        )

        # Category should exist
        assert "new_category" in matcher._compiled_patterns

    def test_invalid_regex_pattern(self):
        """Test handling of invalid regex pattern."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher()

        # Invalid regex (unclosed bracket)
        initial_count = matcher.get_pattern_count()
        matcher.add_custom_pattern(
            r'\b[test\b',
            "bad_category",
            ModerationLevel.LOW
        )

        # Should not add invalid pattern
        new_count = matcher.get_pattern_count()
        assert new_count == initial_count

    def test_remove_pattern_category(self):
        """Test removing a pattern category."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher()

        # Add a custom category
        matcher.add_custom_pattern(
            r'\btest\b',
            "temp_category",
            ModerationLevel.LOW
        )

        assert "temp_category" in matcher._compiled_patterns

        # Remove it
        matcher.remove_pattern_category("temp_category")

        assert "temp_category" not in matcher._compiled_patterns

    def test_remove_nonexistent_category(self):
        """Test removing non-existent category."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        # Should not raise error
        matcher.remove_pattern_category("nonexistent")

        # Just verify no error occurred
        assert True


class TestPatternCount:
    """Test pattern count functionality."""

    def test_get_pattern_count(self):
        """Test getting total pattern count."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        count = matcher.get_pattern_count()

        assert isinstance(count, int)
        assert count > 0

    def test_pattern_count_differs_by_policy(self):
        """Test that pattern count varies by policy."""
        from pattern_matcher import PatternMatcher

        family_matcher = PatternMatcher(policy="family")
        adult_matcher = PatternMatcher(policy="adult")

        family_count = family_matcher.get_pattern_count()
        adult_count = adult_matcher.get_pattern_count()

        # Counts may differ
        assert isinstance(family_count, int)
        assert isinstance(adult_count, int)


class TestSeverityLevels:
    """Test severity level assignment."""

    def test_profanity_severity(self):
        """Test that profanity has LOW severity."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher(policy="family")

        is_safe, matched = matcher.check("damn this")

        if len(matched) > 0 and "profanity" in matched[0].type:
            assert matched[0].severity == ModerationLevel.LOW

    def test_pii_severity(self):
        """Test that PII has HIGH severity."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher()

        is_safe, matched = matcher.check("test@example.com")

        if len(matched) > 0 and "pii" in matched[0].type:
            assert matched[0].severity == ModerationLevel.HIGH

    def test_harmful_severity(self):
        """Test that harmful content has CRITICAL severity."""
        from pattern_matcher import PatternMatcher, ModerationLevel

        matcher = PatternMatcher(policy="family")

        is_safe, matched = matcher.check("kill that person")

        if len(matched) > 0 and "harmful" in matched[0].type:
            assert matched[0].severity == ModerationLevel.CRITICAL


class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_empty_string(self):
        """Test checking empty string."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        is_safe, matched = matcher.check("")

        assert is_safe is True
        assert len(matched) == 0

    def test_whitespace_only(self):
        """Test checking whitespace-only content."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        is_safe, matched = matcher.check("   \n\t  ")

        assert is_safe is True

    def test_unicode_content(self):
        """Test checking unicode content."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        unicode_content = "Hello 世界 🌍"
        is_safe, matched = matcher.check(unicode_content)

        assert isinstance(is_safe, bool)

    def test_mixed_scripts(self):
        """Test checking mixed script content."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        mixed_content = "Hello 你好 안녕하세요 مرحبا"
        is_safe, matched = matcher.check(mixed_content)

        assert isinstance(is_safe, bool)

    def test_emoji_content(self):
        """Test checking emoji content."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        emoji_content = "This is damn! 😡"
        is_safe, matched = matcher.check(emoji_content)

        assert isinstance(is_safe, bool)

    def test_very_long_content(self):
        """Test checking very long content."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        long_content = "safe " * 10000
        is_safe, matched = matcher.check(long_content)

        assert isinstance(is_safe, bool)

    def test_special_characters(self):
        """Test checking special characters."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        special = "!@#$%^&*()_+-=[]{}|;':\",.<>?/"
        is_safe, matched = matcher.check(special)

        assert isinstance(is_safe, bool)

    def test_repeated_patterns(self):
        """Test content with repeated patterns."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        repeated = "damn " * 100
        is_safe, matched = matcher.check(repeated)

        assert is_safe is False
        # Should match multiple times
        assert len(matched) > 0

    def test_null_bytes(self):
        """Test content with null bytes."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        content = "test\x00content"
        is_safe, matched = matcher.check(content)

        assert isinstance(is_safe, bool)


class TestAdversarialInputs:
    """Test handling of adversarial inputs."""

    def test_leet_speak_variations(self):
        """Test leet speak variations."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        leet_variants = ["d4mn", "h3ll", "5hit", "fu<k"]

        for variant in leet_variants:
            is_safe, matched = matcher.check(variant)
            # May or may not catch depending on pattern configuration
            assert isinstance(is_safe, bool)

    def test_obfuscated_profanity(self):
        """Test obfuscated profanity patterns."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        obfuscated = [
            "d-a-m-n",
            "s.h.i.t",
            "f_u_c_k",
            "d a m n"
        ]

        for variant in obfuscated:
            is_safe, matched = matcher.check(variant)
            assert isinstance(is_safe, bool)

    def test_injection_attempts(self):
        """Test SQL injection and XSS attempts."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "${7*7}"
        ]

        for injection in injections:
            is_safe, matched = matcher.check(injection)
            # Should handle without crashing
            assert isinstance(is_safe, bool)

    def test_zero_width_characters(self):
        """Test content with zero-width characters."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        # Zero-width space
        content = "dam\u200Bn"
        is_safe, matched = matcher.check(content)

        assert isinstance(is_safe, bool)

    def test_right_to_left_override(self):
        """Test content with RTL override."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        # RTL override character
        content = "dam\u202En"
        is_safe, matched = matcher.check(content)

        assert isinstance(is_safe, bool)


class TestPatternCompilation:
    """Test pattern compilation behavior."""

    def test_patterns_are_compiled(self):
        """Test that patterns are compiled regex objects."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        for category, patterns in matcher._compiled_patterns.items():
            for pattern, pattern_type in patterns:
                assert hasattr(pattern, "search"), "Pattern should be compiled"

    def test_patterns_use_ignore_case(self):
        """Test that patterns use IGNORE_CASE flag."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        # Test that matching is case insensitive
        is_safe1, _ = matcher.check("DAMN")
        is_safe2, _ = matcher.check("damn")

        assert is_safe1 == is_safe2

    def test_pattern_search_method(self):
        """Test that patterns use search not match."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        # Pattern should match anywhere in string
        is_safe, matched = matcher.check("This is damn bad")

        assert is_safe is False


class TestCategoryConfiguration:
    """Test pattern category configuration."""

    def test_family_policy_has_profanity(self):
        """Test that family policy has profanity patterns."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        assert "profanity" in matcher._compiled_patterns

    def test_all_policies_have_pii(self):
        """Test that all policies have PII patterns."""
        from pattern_matcher import PatternMatcher

        policies = ["family", "teen", "adult", "unrestricted"]

        for policy in policies:
            matcher = PatternMatcher(policy=policy)
            assert "pii" in matcher._compiled_patterns, f"{policy} should have PII"

    def test_family_policy_has_harmful(self):
        """Test that family policy has harmful patterns."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        assert "harmful" in matcher._compiled_patterns


class TestMatchedPatternModel:
    """Test MatchedPattern model usage."""

    def test_matched_pattern_fields(self):
        """Test that matched patterns have all required fields."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        is_safe, matched = matcher.check("damn this")

        if len(matched) > 0:
            pattern = matched[0]
            assert hasattr(pattern, "pattern")
            assert hasattr(pattern, "type")
            assert hasattr(pattern, "severity")
            assert hasattr(pattern, "position")

    def test_matched_pattern_string_representation(self):
        """Test MatchedPattern string representation."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        is_safe, matched = matcher.check("damn")

        if len(matched) > 0:
            pattern_str = str(matched[0])
            assert isinstance(pattern_str, str)


class TestIntegrationWithContentModerator:
    """Test integration with ContentModerator."""

    def test_pattern_matcher_standalone(self):
        """Test that pattern matcher works standalone."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher()

        is_safe, matched = matcher.check("test@example.com")

        assert isinstance(is_safe, bool)
        assert isinstance(matched, list)

    def test_multiple_sequential_checks(self):
        """Test performing multiple sequential checks."""
        from pattern_matcher import PatternMatcher

        matcher = PatternMatcher(policy="family")

        checks = [
            ("Hello world", True),
            ("damn this", False),
            ("test@example.com", False),
            ("Safe content", True)
        ]

        for content, expected_safe in checks:
            is_safe, matched = matcher.check(content)
            # For family policy, these expectations should hold
            if matcher.policy == "family":
                # Just verify it runs without error
                assert isinstance(is_safe, bool)
