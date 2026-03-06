"""
Unit tests for Pattern Matcher.

Tests pattern-based content filtering including:
- Profanity detection
- PII detection
- Harmful content detection
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pattern_matcher import PatternMatcher
from models import ModerationLevel


class TestPatternMatcher:
    """Test pattern matcher functionality."""

    def test_initialization(self):
        """Pattern matcher initializes with default policy."""
        matcher = PatternMatcher(policy="family")
        assert matcher.policy == "family"
        assert matcher.get_pattern_count() > 0

    def test_profanity_detection_family_policy(self):
        """Family policy detects common profanity."""
        matcher = PatternMatcher(policy="family")

        # Test profanity words
        test_cases = [
            ("damn this is hell", True),
            ("what the fuck", True),
            ("this is bullshit", True),
            ("hello world", False),
        ]

        for content, should_match in test_cases:
            is_safe, matched = matcher.check(content)
            if should_match:
                assert not is_safe, f"Should block: {content}"
                assert len(matched) > 0
            else:
                assert is_safe, f"Should allow: {content}"

    def test_pii_detection(self):
        """PII patterns detect emails, phones, SSNs."""
        matcher = PatternMatcher(policy="family")

        # Test email
        is_safe, matched = matcher.check("Contact me at test@example.com")
        assert not is_safe
        assert any("email" in m.type for m in matched)

        # Test phone
        is_safe, matched = matcher.check("Call me at 555-123-4567")
        assert not is_safe
        assert any("phone" in m.type for m in matched)

        # Test SSN
        is_safe, matched = matcher.check("SSN: 123-45-6789")
        assert not is_safe
        assert any("ssn" in m.type for m in matched)

    def test_harmful_content_detection(self):
        """Harmful content patterns detect threats."""
        matcher = PatternMatcher(policy="family")

        # Test violence threat
        is_safe, matched = matcher.check("I want to kill that person")
        assert not is_safe
        assert any("violence" in m.type for m in matched)

        # Test cyberthreat
        is_safe, matched = matcher.check("I will hack the system")
        assert not is_safe
        assert any("cyber" in m.type for m in matched)

        # Test self harm
        is_safe, matched = matcher.check("I want to kill myself")
        assert not is_safe
        assert any("self_harm" in m.type for m in matched)

    def test_case_insensitive_matching(self):
        """Pattern matching is case-insensitive."""
        matcher = PatternMatcher(policy="family")

        # Different cases of same word
        for variant in ["DAMN", "DaMn", "damn", "DaMn"]:
            is_safe, _ = matcher.check(variant)
            assert not is_safe, f"Should block: {variant}"

    def test_policy_configuration(self):
        """Different policies have different strictness."""
        family = PatternMatcher(policy="family")
        adult = PatternMatcher(policy="adult")

        # Adult policy should have fewer patterns
        assert family.get_pattern_count() >= adult.get_pattern_count()

    def test_custom_pattern_addition(self):
        """Custom patterns can be added."""
        matcher = PatternMatcher(policy="family")
        initial_count = matcher.get_pattern_count()

        # Add custom pattern
        matcher.add_custom_pattern(
            r'\btestword\b',
            "custom",
            ModerationLevel.LOW
        )

        # Pattern count should increase
        assert matcher.get_pattern_count() >= initial_count

        # Custom pattern should match
        is_safe, matched = matcher.check("this is testword here")
        assert not is_safe
        assert any("custom" in m.type for m in matched)

    def test_pattern_category_removal(self):
        """Pattern categories can be removed."""
        matcher = PatternMatcher(policy="family")
        initial_count = matcher.get_pattern_count()

        # Remove a category
        if "profanity" in matcher._compiled_patterns:
            matcher.remove_pattern_category("profanity")
            # Pattern count should decrease
            assert matcher.get_pattern_count() < initial_count

    def test_multiple_pattern_matches(self):
        """Multiple patterns in content are all detected."""
        matcher = PatternMatcher(policy="family")

        # Content with multiple violations
        content = "damn it, email me at test@example.com"
        is_safe, matched = matcher.check(content)

        assert not is_safe
        assert len(matched) >= 2

    def test_safe_content_passes(self):
        """Safe content passes all checks."""
        matcher = PatternMatcher(policy="family")

        safe_contents = [
            "Hello, how are you today?",
            "The weather is nice.",
            "I enjoyed the performance.",
            "Thank you for coming.",
        ]

        for content in safe_contents:
            is_safe, matched = matcher.check(content)
            assert is_safe, f"Should allow: {content}"
            assert len(matched) == 0

    def test_pattern_position_tracking(self):
        """Pattern positions are tracked correctly."""
        matcher = PatternMatcher(policy="family")

        is_safe, matched = matcher.check("hello damn world")
        assert not is_safe

        # Find the profanity match
        profanity_match = next((m for m in matched if "profanity" in m.type), None)
        assert profanity_match is not None
        assert profanity_match.position is not None
        assert profanity_match.position > 0  # Should be after "hello "

    def test_severity_levels(self):
        """Pattern categories have appropriate severity levels."""
        matcher = PatternMatcher(policy="family")

        # PII should be HIGH severity
        is_safe, matched = matcher.check("test@example.com")
        pii_match = next((m for m in matched if "pii" in m.type), None)
        assert pii_match.severity == ModerationLevel.HIGH

        # Profanity should be LOW severity
        is_safe, matched = matcher.check("damn")
        profanity_match = next((m for m in matched if "profanity" in m.type), None)
        assert profanity_match.severity == ModerationLevel.LOW
