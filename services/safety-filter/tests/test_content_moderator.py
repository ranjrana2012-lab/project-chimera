"""
Comprehensive unit tests for ContentModerator.

Tests all moderation paths (allow, block, flag), audit logging,
statistics, edge cases, and context-aware filtering.
"""

import pytest
import time
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, '.')


class TestContentModeratorInitialization:
    """Test ContentModerator initialization and configuration."""

    def test_default_initialization(self):
        """Test moderator with default settings."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        assert moderator.policy == "family"
        assert moderator.enable_ml_filter is False
        assert moderator.audit_log_max_size == 10000
        assert len(moderator.audit_log) == 0
        assert moderator._stats["total_checks"] == 0

    def test_custom_policy_initialization(self):
        """Test moderator with custom policy."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(policy="teen")

        assert moderator.policy == "teen"
        assert moderator.pattern_matcher.policy == "teen"

    def test_ml_filter_enabled_initialization(self):
        """Test moderator with ML filter enabled."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(enable_ml_filter=True)

        assert moderator.enable_ml_filter is True

    def test_custom_audit_log_size(self):
        """Test moderator with custom audit log size."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(audit_log_max_size=5000)

        assert moderator.audit_log_max_size == 5000


class TestModerateSafeContent:
    """Test moderation of safe content."""

    def test_safe_content_allowed(self):
        """Test that safe content is allowed."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        result = moderator.moderate("Hello, how are you today?")

        assert result.is_safe is True
        assert result.action == FilterAction.ALLOW
        assert "passed all safety checks" in result.reason.lower()

    def test_safe_content_with_context(self):
        """Test safe content with additional context."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        context = {"source": "web", "user_type": "premium"}
        result = moderator.moderate(
            "What a beautiful day!",
            context=context
        )

        assert result.is_safe is True
        assert result.action == FilterAction.ALLOW

    def test_safe_content_with_ids(self):
        """Test safe content with content, user, and session IDs."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        result = moderator.moderate(
            "Great weather today!",
            content_id="content123",
            user_id="user456",
            session_id="session789"
        )

        assert result.is_safe is True
        assert result.content_id == "content123"
        # Verify audit log contains the IDs
        assert len(moderator.audit_log) == 1
        assert moderator.audit_log[0].user_id == "user456"
        assert moderator.audit_log[0].session_id == "session789"


class TestModerateBlockedContent:
    """Test moderation of blocked content."""

    def test_profanity_blocked(self):
        """Test that profanity is blocked."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        result = moderator.moderate("This is damn bad")

        assert result.is_safe is False
        assert result.action == FilterAction.BLOCK
        assert "pattern" in result.layer.value.lower()
        assert len(result.matched_patterns) > 0

    def test_pii_blocked(self):
        """Test that PII is blocked."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        result = moderator.moderate("My email is test@example.com")

        assert result.is_safe is False
        assert result.action == FilterAction.BLOCK
        assert len(result.matched_patterns) > 0

    def test_multiple_patterns_blocked(self):
        """Test blocking content with multiple pattern matches."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        result = moderator.moderate("damn hell and shit")

        assert result.is_safe is False
        assert result.action == FilterAction.BLOCK
        assert len(result.matched_patterns) >= 2
        assert "pattern" in result.reason.lower()

    def test_blocked_content_has_severity(self):
        """Test that blocked content has severity level."""
        from content_moderator import ContentModerator
        from models import ModerationLevel

        moderator = ContentModerator()
        result = moderator.moderate("damn this")

        assert result.is_safe is False
        assert result.level in ModerationLevel
        assert result.level != ModerationLevel.SAFE


class TestModerateFlaggedContent:
    """Test moderation of flagged content."""

    def test_spam_content_flagged(self):
        """Test that spam-like content is flagged."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        spam_content = "test " * 10  # Repeated word
        context = {"check_spam": True}

        result = moderator.moderate(spam_content, context=context)

        assert result.is_safe is False
        assert result.action == FilterAction.FLAG
        assert "spam" in result.reason.lower()

    def test_long_content_flagged(self):
        """Test that overly long content is flagged."""
        from content_moderator import ContentModerator
        from models import FilterAction

        moderator = ContentModerator()
        long_content = "a" * 10001

        result = moderator.moderate(long_content)

        assert result.is_safe is False
        assert result.action == FilterAction.FLAG
        assert "exceeds maximum length" in result.reason.lower()

    def test_flagged_content_confidence(self):
        """Test that flagged content has appropriate confidence."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        context = {"check_spam": True}
        result = moderator.moderate("repeat " * 10, context=context)

        assert result.is_safe is False
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0


class TestIsSafeMethod:
    """Test the is_safe quick check method."""

    def test_is_safe_with_safe_content(self):
        """Test is_safe returns True for safe content."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        assert moderator.is_safe("Hello world") is True

    def test_is_safe_with_unsafe_content(self):
        """Test is_safe returns False for unsafe content."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        assert moderator.is_safe("damn this") is False

    def test_is_safe_with_policy_override(self):
        """Test is_safe with policy override."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(policy="family")

        # Family policy blocks profanity
        assert moderator.is_safe("damn", policy="family") is False

    def test_is_safe_does_not_log_to_audit(self):
        """Test that is_safe doesn't create audit entries."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        moderator.is_safe("test content")

        assert len(moderator.audit_log) == 0


class TestAuditLogging:
    """Test audit logging functionality."""

    def test_audit_entry_created(self):
        """Test that moderation creates audit entry."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        moderator.moderate("Hello world")

        assert len(moderator.audit_log) == 1

    def test_audit_entry_content_hash(self):
        """Test that audit entry contains content hash."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        moderator.moderate("test content")

        entry = moderator.audit_log[0]
        assert entry.content_hash is not None
        assert len(entry.content_hash) == 16  # First 16 chars of SHA256

    def test_audit_entry_content_preview(self):
        """Test that audit entry contains content preview."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        long_content = "a" * 200
        moderator.moderate(long_content)

        entry = moderator.audit_log[0]
        assert len(entry.content_preview) <= 103  # 100 + "..."
        assert "..." in entry.content_preview

    def test_audit_entry_timestamp(self):
        """Test that audit entry has timestamp."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        moderator.moderate("test")

        entry = moderator.audit_log[0]
        assert entry.timestamp is not None
        assert isinstance(entry.timestamp, datetime)

    def test_audit_entry_to_dict(self):
        """Test converting audit entry to dictionary."""
        from content_moderator import ContentModerator, AuditEntry
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        moderator = ContentModerator()
        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=10.0
        )

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            content_hash="abc123",
            content_preview="test...",
            result=result
        )

        entry_dict = entry.to_dict()
        assert "timestamp" in entry_dict
        assert "content_hash" in entry_dict
        assert "is_safe" in entry_dict
        assert "action" in entry_dict

    def test_audit_log_max_size(self):
        """Test that audit log respects max size."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(audit_log_max_size=10)

        # Add more entries than max size
        for i in range(20):
            moderator.moderate(f"test {i}")

        # Should be trimmed to half of max size when exceeded
        assert len(moderator.audit_log) <= 10

    def test_get_audit_log(self):
        """Test retrieving audit log."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        # Add some entries
        for i in range(5):
            moderator.moderate(f"test {i}")

        log = moderator.get_audit_log()
        assert len(log) == 5

    def test_get_audit_log_with_limit(self):
        """Test retrieving audit log with limit."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        # Add entries
        for i in range(10):
            moderator.moderate(f"test {i}")

        log = moderator.get_audit_log(limit=5)
        assert len(log) == 5

    def test_get_audit_log_with_user_filter(self):
        """Test filtering audit log by user ID."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        # Add entries for different users
        moderator.moderate("test1", user_id="user1")
        moderator.moderate("test2", user_id="user2")
        moderator.moderate("test3", user_id="user1")

        log = moderator.get_audit_log(user_id="user1")
        assert len(log) == 2
        assert all(e["user_id"] == "user1" for e in log)


class TestStatistics:
    """Test statistics tracking."""

    def test_statistics_initial_state(self):
        """Test initial statistics state."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        stats = moderator.get_statistics()

        assert stats["total_checks"] == 0
        assert stats["allowed"] == 0
        assert stats["blocked"] == 0
        assert stats["flagged"] == 0
        assert stats["allow_rate"] == 0.0

    def test_statistics_increment(self):
        """Test that statistics increment correctly."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        moderator.moderate("safe content")
        moderator.moderate("damn this")

        stats = moderator.get_statistics()
        assert stats["total_checks"] == 2
        assert stats["allowed"] == 1
        assert stats["blocked"] == 1

    def test_statistics_rates(self):
        """Test statistics rate calculations."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        # Add 4 safe, 1 blocked
        for i in range(4):
            moderator.moderate(f"safe {i}")
        moderator.moderate("damn")

        stats = moderator.get_statistics()
        assert stats["total_checks"] == 5
        assert stats["allow_rate"] == 0.8
        assert stats["block_rate"] == 0.2

    def test_statistics_includes_policy(self):
        """Test statistics includes current policy."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(policy="teen")

        stats = moderator.get_statistics()
        assert stats["current_policy"] == "teen"

    def test_statistics_includes_pattern_count(self):
        """Test statistics includes pattern count."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        stats = moderator.get_statistics()
        assert "pattern_count" in stats
        assert stats["pattern_count"] > 0


class TestSetPolicy:
    """Test policy changing functionality."""

    def test_set_policy_changes_policy(self):
        """Test that set_policy changes the policy."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(policy="family")
        moderator.set_policy("teen")

        assert moderator.policy == "teen"

    def test_set_policy_reloads_patterns(self):
        """Test that set_policy reloads pattern matcher."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(policy="family")
        old_pattern_count = moderator.pattern_matcher.get_pattern_count()

        moderator.set_policy("teen")
        new_pattern_count = moderator.pattern_matcher.get_pattern_count()

        # Pattern count may differ between policies
        assert moderator.pattern_matcher.policy == "teen"

    def test_set_policy_same_policy_no_reload(self):
        """Test that setting same policy doesn't reload."""
        from content_moderator import ContentModerator

        moderator = ContentModerator(policy="family")
        original_matcher = moderator.pattern_matcher

        moderator.set_policy("family")

        # Same matcher instance
        assert moderator.pattern_matcher is original_matcher


class TestContextChecking:
    """Test context-aware checking."""

    def test_context_check_without_context(self):
        """Test context check with no context provided."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        is_safe, reason = moderator._check_context("test content", None)

        assert is_safe is True
        assert reason is None

    def test_context_check_spam_detection(self):
        """Test spam detection in context check."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        spam_content = "repeat " * 10
        context = {"check_spam": True}

        is_safe, reason = moderator._check_context(spam_content, context)

        assert is_safe is False
        assert "spam" in reason.lower()

    def test_context_check_length_validation(self):
        """Test length validation in context check."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        long_content = "a" * 10001

        is_safe, reason = moderator._check_context(long_content, None)

        assert is_safe is False
        assert "exceeds maximum length" in reason.lower()

    def test_context_check_short_word_repetition(self):
        """Test that short word repetition is not flagged."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        content = "the " * 10  # "the" is only 3 chars
        context = {"check_spam": True}

        is_safe, reason = moderator._check_context(content, context)

        # Should be safe - words <= 3 chars are not flagged
        assert is_safe is True


class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_empty_string(self):
        """Test moderating empty string."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        result = moderator.moderate("")

        assert result.is_safe is True
        assert result.action.value == "allow"

    def test_whitespace_only(self):
        """Test moderating whitespace-only content."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        result = moderator.moderate("   \n\t  ")

        assert result.is_safe is True

    def test_unicode_content(self):
        """Test moderating unicode content."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        unicode_content = "Hello 世界 🌍 مرحبا"

        result = moderator.moderate(unicode_content)

        assert isinstance(result.is_safe, bool)
        assert isinstance(result.action.value, str)

    def test_mixed_scripts(self):
        """Test moderating mixed script content."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        mixed_content = "Hello 你好 안녕하세요"

        result = moderator.moderate(mixed_content)

        assert isinstance(result.is_safe, bool)

    def test_emoji_only(self):
        """Test moderating emoji-only content."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        emoji_content = "😀 😃 😄 😁 😆 😅"

        result = moderator.moderate(emoji_content)

        assert result.is_safe is True

    def test_special_characters(self):
        """Test moderating special characters."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        special_content = "!@#$%^&*()_+-=[]{}|;':\",.<>?/"

        result = moderator.moderate(special_content)

        assert isinstance(result.is_safe, bool)

    def test_very_long_safe_content(self):
        """Test moderating very long safe content."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        long_content = "safe " * 5000  # Under limit

        result = moderator.moderate(long_content)

        assert result.is_safe is True

    def test_null_bytes(self):
        """Test moderating content with null bytes."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        content_with_null = "test\x00content"

        result = moderator.moderate(content_with_null)

        assert isinstance(result.is_safe, bool)


class TestProcessingTime:
    """Test processing time tracking."""

    def test_processing_time_recorded(self):
        """Test that processing time is recorded."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        result = moderator.moderate("test content")

        assert result.processing_time_ms >= 0
        assert isinstance(result.processing_time_ms, float)

    def test_processing_time_reasonable(self):
        """Test that processing time is reasonable."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        result = moderator.moderate("test content")

        # Should complete in under 1 second
        assert result.processing_time_ms < 1000


class TestMatchedPatterns:
    """Test matched pattern details."""

    def test_matched_patterns_have_positions(self):
        """Test that matched patterns have position information."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        result = moderator.moderate("damn this")

        if len(result.matched_patterns) > 0:
            pattern = result.matched_patterns[0]
            assert pattern.position is not None
            assert isinstance(pattern.position, int)

    def test_matched_patterns_have_severity(self):
        """Test that matched patterns have severity levels."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()
        result = moderator.moderate("damn this")

        if len(result.matched_patterns) > 0:
            pattern = result.matched_patterns[0]
            assert pattern.severity is not None


class TestAdversarialInputs:
    """Test handling of adversarial inputs."""

    def test_leet_speak(self):
        """Test leet speak variations."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        # May or may not catch depending on pattern configuration
        leet_variants = ["d4mn", "h3ll", "5hit"]

        for variant in leet_variants:
            result = moderator.moderate(variant)
            assert isinstance(result.is_safe, bool)

    def test_obfuscated_profanity(self):
        """Test obfuscated profanity."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        obfuscated = ["d-a-m-n", "s.h.i.t", "f_u_c_k"]

        for variant in obfuscated:
            result = moderator.moderate(variant)
            assert isinstance(result.is_safe, bool)

    def test_injection_attempts(self):
        """Test SQL injection and XSS attempts."""
        from content_moderator import ContentModerator

        moderator = ContentModerator()

        injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "${7*7}",
        ]

        for injection in injections:
            result = moderator.moderate(injection)
            # Should handle without crashing
            assert isinstance(result.is_safe, bool)
            assert isinstance(result.reason, str)


class TestResultCreationMethods:
    """Test internal result creation methods."""

    def test_create_block_result(self):
        """Test _create_block_result method."""
        from content_moderator import ContentModerator
        from models import MatchedPattern, FilterAction, ModerationLevel, FilterLayer

        moderator = ContentModerator()
        patterns = [
            MatchedPattern(
                pattern=r'\bdamn\b',
                type="profanity_profanity",
                severity=ModerationLevel.LOW,
                position=0
            )
        ]

        result = moderator._create_block_result(patterns, "test123", time.time())

        assert result.is_safe is False
        assert result.action == FilterAction.BLOCK
        assert result.layer == FilterLayer.PATTERN
        assert result.content_id == "test123"
        assert len(result.matched_patterns) == 1

    def test_create_flag_result(self):
        """Test _create_flag_result method."""
        from content_moderator import ContentModerator
        from models import FilterAction, ModerationLevel, FilterLayer

        moderator = ContentModerator()
        reason = "Test flag reason"

        result = moderator._create_flag_result(reason, "test456", time.time())

        assert result.is_safe is False
        assert result.action == FilterAction.FLAG
        assert result.level == ModerationLevel.MEDIUM
        assert result.reason == reason
        assert result.content_id == "test456"

    def test_create_safe_result(self):
        """Test _create_safe_result method."""
        from content_moderator import ContentModerator
        from models import FilterAction, ModerationLevel, FilterLayer

        moderator = ContentModerator()

        result = moderator._create_safe_result("test789", time.time())

        assert result.is_safe is True
        assert result.action == FilterAction.ALLOW
        assert result.level == ModerationLevel.SAFE
        assert result.layer == FilterLayer.CONTEXT
        assert result.content_id == "test789"
