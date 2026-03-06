"""
Unit tests for Content Moderator.

Tests multi-layer content moderation including:
- Pattern-based filtering
- Context-aware analysis
- Audit logging
- Statistics tracking
"""

import pytest
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_moderator import ContentModerator
from models import FilterAction, FilterLayer, ModerationLevel


class TestContentModerator:
    """Test content moderator functionality."""

    def test_initialization(self):
        """Content moderator initializes with defaults."""
        moderator = ContentModerator()

        assert moderator.policy == "family"
        assert moderator.enable_ml_filter is False
        assert len(moderator.audit_log) == 0
        assert moderator._stats["total_checks"] == 0

    def test_custom_initialization(self):
        """Content moderator accepts custom settings."""
        moderator = ContentModerator(
            policy="teen",
            enable_ml_filter=True,
            audit_log_max_size=5000
        )

        assert moderator.policy == "teen"
        assert moderator.enable_ml_filter is True
        assert moderator.audit_log_max_size == 5000

    def test_moderate_safe_content(self):
        """Safe content returns ALLOW action."""
        moderator = ContentModerator()

        result = moderator.moderate("Hello, how are you today?")

        assert result.is_safe is True
        assert result.action == FilterAction.ALLOW
        assert result.level == ModerationLevel.SAFE
        assert result.layer == FilterLayer.CONTEXT
        assert len(result.matched_patterns) == 0
        assert result.processing_time_ms >= 0

    def test_moderate_unsafe_content(self):
        """Unsafe content returns BLOCK action."""
        moderator = ContentModerator()

        result = moderator.moderate("damn this content")

        assert result.is_safe is False
        assert result.action == FilterAction.BLOCK
        assert result.layer == FilterLayer.PATTERN
        assert len(result.matched_patterns) > 0

    def test_moderate_with_content_id(self):
        """Content ID is preserved in result."""
        moderator = ContentModerator()

        result = moderator.moderate(
            "Hello world",
            content_id="msg-123"
        )

        assert result.content_id == "msg-123"

    def test_moderate_with_user_context(self):
        """User and session context is preserved."""
        moderator = ContentModerator()

        moderator.moderate(
            "Hello world",
            user_id="user-456",
            session_id="session-789"
        )

        # Check audit log
        assert len(moderator.audit_log) == 1
        entry = moderator.audit_log[0]
        assert entry.user_id == "user-456"
        assert entry.session_id == "session-789"

    def test_audit_logging(self):
        """All moderation events are logged."""
        moderator = ContentModerator()

        # Moderate multiple items
        moderator.moderate("Hello world")
        moderator.moderate("damn content")
        moderator.moderate("How are you?")

        # Check audit log
        assert len(moderator.audit_log) == 3

        # Check first entry
        entry = moderator.audit_log[0]
        assert hasattr(entry, "timestamp")
        assert hasattr(entry, "content_hash")
        assert hasattr(entry, "content_preview")
        assert hasattr(entry, "result")

    def test_statistics_tracking(self):
        """Statistics accurately track moderation activity."""
        moderator = ContentModerator()

        # Moderate safe content
        moderator.moderate("Hello")
        moderator.moderate("World")

        # Moderate unsafe content
        moderator.moderate("damn")

        stats = moderator.get_statistics()

        assert stats["total_checks"] == 3
        assert stats["allowed"] == 2
        assert stats["blocked"] == 1
        assert stats["allow_rate"] == pytest.approx(2/3, rel=0.01)
        assert stats["block_rate"] == pytest.approx(1/3, rel=0.01)

    def test_is_safe_quick_check(self):
        """Quick boolean check works correctly."""
        moderator = ContentModerator()

        assert moderator.is_safe("Hello world") is True
        assert moderator.is_safe("damn this") is False

    def test_is_safe_with_policy_override(self):
        """Policy can be overridden for quick check."""
        moderator = ContentModerator(policy="family")

        # Family policy blocks "damn"
        assert moderator.is_safe("damn") is False

        # Unrestricted policy allows it
        assert moderator.is_safe("damn", policy="unrestricted") is True

    def test_policy_change(self):
        """Policy can be changed after initialization."""
        moderator = ContentModerator(policy="family")

        # Family policy blocks profanity
        assert moderator.is_safe("damn") is False

        # Change to unrestricted
        moderator.set_policy("unrestricted")

        # Now should allow
        assert moderator.is_safe("damn") is True

    def test_context_spam_detection(self):
        """Repeated words are flagged as potential spam."""
        moderator = ContentModerator()

        # Content with repeated word
        spam_content = "test " * 10
        result = moderator.moderate(
            spam_content,
            context={"check_spam": True}
        )

        assert result.is_safe is False
        assert result.action == FilterAction.FLAG
        assert "spam" in result.reason.lower()

    def test_context_length_check(self):
        """Very long content is flagged."""
        moderator = ContentModerator()

        # Very long content
        long_content = "word " * 10000
        result = moderator.moderate(long_content)

        assert result.is_safe is False
        assert result.action == FilterAction.FLAG
        assert "length" in result.reason.lower()

    def test_audit_log_retrieval(self):
        """Audit log can be retrieved with limits."""
        moderator = ContentModerator()

        # Add multiple entries
        for i in range(10):
            moderator.moderate(f"content {i}")

        # Get all entries
        all_entries = moderator.get_audit_log(limit=100)
        assert len(all_entries) == 10

        # Get limited entries
        limited_entries = moderator.get_audit_log(limit=5)
        assert len(limited_entries) == 5

    def test_audit_log_user_filtering(self):
        """Audit log can be filtered by user ID."""
        moderator = ContentModerator()

        # Add entries for different users
        moderator.moderate("content 1", user_id="user-a")
        moderator.moderate("content 2", user_id="user-b")
        moderator.moderate("content 3", user_id="user-a")

        # Get entries for user-a
        user_a_entries = moderator.get_audit_log(limit=10, user_id="user-a")
        assert len(user_a_entries) == 2

        # Get entries for user-b
        user_b_entries = moderator.get_audit_log(limit=10, user_id="user-b")
        assert len(user_b_entries) == 1

    def test_audit_log_size_limit(self):
        """Audit log respects maximum size limit."""
        moderator = ContentModerator(audit_log_max_size=5)

        # Add more entries than limit
        for i in range(10):
            moderator.moderate(f"content {i}")

        # Log should be trimmed to half max size
        assert len(moderator.audit_log) <= 5

    def test_processing_time_recorded(self):
        """Processing time is recorded in results."""
        moderator = ContentModerator()

        result = moderator.moderate("Hello world")

        assert result.processing_time_ms >= 0
        assert result.processing_time_ms < 1000  # Should be fast

    def test_confidence_scores(self):
        """Confidence scores are appropriate for results."""
        moderator = ContentModerator()

        # Safe content should have high confidence
        safe_result = moderator.moderate("Hello world")
        assert safe_result.confidence == 1.0

        # Blocked content should have high confidence
        blocked_result = moderator.moderate("damn this")
        assert blocked_result.confidence == 1.0

        # Flagged content should have moderate confidence
        flag_result = moderator.moderate("test " * 10, context={"check_spam": True})
        assert 0.0 <= flag_result.confidence <= 1.0

    def test_multiple_pattern_matches_reported(self):
        """All pattern matches are reported in result."""
        moderator = ContentModerator()

        # Content with multiple violations
        result = moderator.moderate("damn it, email at test@example.com")

        assert len(result.matched_patterns) >= 1

    def test_performance_target(self):
        """Moderation completes within performance target."""
        moderator = ContentModerator()

        start = time.time()
        moderator.moderate("Hello world, this is a test of the moderation system")
        elapsed = time.time() - start

        # Should complete in less than 50ms
        assert elapsed < 0.05


class TestModerationLayers:
    """Test multi-layer moderation."""

    def test_layer_1_pattern_matching(self):
        """Layer 1 (pattern matching) catches violations."""
        moderator = ContentModerator()

        result = moderator.moderate("damn this")

        assert result.layer == FilterLayer.PATTERN
        assert result.is_safe is False

    def test_layer_2_context_analysis(self):
        """Layer 2 (context) catches spam."""
        moderator = ContentModerator()

        result = moderator.moderate(
            "test " * 10,
            context={"check_spam": True}
        )

        assert result.layer == FilterLayer.CONTEXT
        assert result.is_safe is False

    def test_safe_content_passes_all_layers(self):
        """Safe content passes all layers."""
        moderator = ContentModerator()

        result = moderator.moderate("Hello, welcome to the show!")

        assert result.layer == FilterLayer.CONTEXT
        assert result.is_safe is True
        assert result.action == FilterAction.ALLOW
