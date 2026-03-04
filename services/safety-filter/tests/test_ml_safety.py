"""
Unit tests for ML-based safety filter.

Tests multi-layer filtering, audit logging, and statistics.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add safety-filter to path
filter_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(filter_path))

from ml_safety import (
    FilterAction,
    FilterLayer,
    FilterResult,
    AuditEntry,
    PatternFilter,
    ClassificationFilter,
    ContextAwareFilter,
    SafetyFilter,
    safety_filter
)


class TestFilterAction:
    """Test filter action enum."""

    def test_action_values(self):
        """Test action enum values."""
        assert FilterAction.ALLOW.value == "allow"
        assert FilterAction.BLOCK.value == "block"
        assert FilterAction.FLAG.value == "flag"
        assert FilterAction.MODIFY.value == "modify"


class TestFilterResult:
    """Test filter result dataclass."""

    def test_result_creation(self):
        """Test creating a filter result."""
        result = FilterResult(
            action=FilterAction.BLOCK,
            layer=FilterLayer.PATTERN,
            confidence=1.0,
            reason="Test block"
        )
        assert result.action == FilterAction.BLOCK
        assert result.layer == FilterLayer.PATTERN
        assert result.confidence == 1.0

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = FilterResult(
            action=FilterAction.ALLOW,
            layer=FilterLayer.CLASSIFICATION,
            confidence=0.95,
            reason="Safe content",
            matched_patterns=["pattern1"]
        )

        data = result.to_dict()
        assert data["action"] == "allow"
        assert data["layer"] == "classification"
        assert data["confidence"] == 0.95
        assert "pattern1" in data["matched_patterns"]


class TestAuditEntry:
    """Test audit log entry."""

    def test_entry_creation(self):
        """Test creating audit entry."""
        result = FilterResult(
            action=FilterAction.BLOCK,
            layer=FilterLayer.PATTERN,
            confidence=1.0,
            reason="Blocked"
        )

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            content_hash="abc123",
            content_preview="Test content...",
            result=result
        )
        assert entry.content_hash == "abc123"
        assert entry.result.action == FilterAction.BLOCK


class TestPatternFilter:
    """Test pattern-based filter."""

    def test_filter_initialization(self):
        """Test filter creation."""
        filter = PatternFilter()
        assert len(filter.patterns) > 0
        assert len(filter.compiled_patterns) == len(filter.patterns)

    def test_check_safe_content(self):
        """Test checking safe content."""
        filter = PatternFilter()
        blocked, patterns = filter.check("Hello, how are you today?")
        assert blocked is False
        assert len(patterns) == 0

    def test_check_blocked_content(self):
        """Test checking blocked content."""
        filter = PatternFilter()
        blocked, patterns = filter.check("Here is my password: 'secret123'")
        assert blocked is True
        assert len(patterns) > 0

    def test_custom_patterns(self):
        """Test filter with custom patterns."""
        custom_patterns = [r'\btest\b']
        filter = PatternFilter(patterns=custom_patterns)
        blocked, _ = filter.check("This is a test")
        assert blocked is True


class TestClassificationFilter:
    """Test ML classification filter."""

    def test_filter_initialization(self):
        """Test filter creation."""
        filter = ClassificationFilter()
        assert filter.threshold == 0.7
        assert filter._model_loaded is False

    def test_load_model(self):
        """Test loading model."""
        filter = ClassificationFilter()
        filter.load_model()
        assert filter._model_loaded is True

    def test_classify(self):
        """Test content classification."""
        filter = ClassificationFilter()
        predictions = filter.classify("Safe content here")
        assert "toxic" in predictions
        assert "hateful" in predictions

    def test_check(self):
        """Test checking content."""
        filter = ClassificationFilter()
        # With simulated low scores, should pass
        blocked, predictions = filter.check("Safe content")
        # Default threshold is 0.7, simulated scores are < 0.3
        assert blocked is False


class TestContextAwareFilter:
    """Test context-aware filter."""

    def test_filter_initialization(self):
        """Test filter creation."""
        filter = ContextAwareFilter()
        assert filter.max_length == 512
        assert filter.threshold == 0.6

    def test_load_model(self):
        """Test loading model."""
        filter = ContextAwareFilter()
        filter.load_model()
        assert filter._model_loaded is True

    def test_analyze_context(self):
        """Test context analysis."""
        filter = ContextAwareFilter()
        blocked, score, reason = filter.analyze_context("Hello!")
        assert isinstance(blocked, bool)
        assert 0 <= score <= 1
        assert isinstance(reason, str)

    def test_analyze_with_history(self):
        """Test context analysis with conversation history."""
        filter = ContextAwareFilter()
        history = [
            {"user": "Hi there"},
            {"assistant": "Hello! How can I help?"}
        ]

        blocked, score, reason = filter.analyze_context("What's the weather?", history)
        assert isinstance(blocked, bool)


class TestSafetyFilter:
    """Test multi-layer safety filter."""

    @pytest.fixture
    def filter_instance(self):
        """Create safety filter instance."""
        return SafetyFilter(enable_audit=True)

    def test_filter_initialization(self, filter_instance):
        """Test filter creation."""
        assert filter_instance.pattern_filter is not None
        assert filter_instance.classification_filter is not None
        assert filter_instance.context_filter is not None
        assert filter_instance.enable_audit is True

    @pytest.mark.asyncio
    async def test_check_safe_content(self, filter_instance):
        """Test checking safe content."""
        result = await filter_instance.check_content(
            "Hello, how can I help you today?"
        )
        assert result.action == FilterAction.ALLOW
        assert result.layer == FilterLayer.AUDIT

    @pytest.mark.asyncio
    async def test_check_blocked_content(self, filter_instance):
        """Test checking blocked content."""
        result = await filter_instance.check_content(
            "Here is my password: 'secret123'"
        )
        assert result.action == FilterAction.BLOCK
        assert result.layer == FilterLayer.PATTERN

    @pytest.mark.asyncio
    async def test_check_with_user_context(self, filter_instance):
        """Test checking content with user context."""
        result = await filter_instance.check_content(
            "Hello!",
            user_id="user123",
            session_id="session456",
            context={"source": "web"}
        )
        assert result.action == FilterAction.ALLOW
        # Verify audit log entry created
        assert len(filter_instance.audit_log) == 1

    def test_get_statistics(self, filter_instance):
        """Test getting filter statistics."""
        stats = filter_instance.get_statistics()
        assert "total_checked" in stats
        assert "allowed" in stats
        assert "blocked" in stats
        assert "flagged" in stats

    def test_get_audit_log(self, filter_instance):
        """Test getting audit log."""
        # Add some entries first
        async def add_entries():
            await filter_instance.check_content("Test 1")
            await filter_instance.check_content("Test 2")

        asyncio.run(add_entries())

        log = filter_instance.get_audit_log(limit=10)
        assert len(log) >= 2

    def test_get_audit_log_with_user_filter(self, filter_instance):
        """Test filtering audit log by user."""
        # Add entries for different users
        async def add_entries():
            await filter_instance.check_content("Test 1", user_id="user1")
            await filter_instance.check_content("Test 2", user_id="user2")

        asyncio.run(add_entries())

        user1_log = filter_instance.get_audit_log(user_id="user1")
        assert all(e["user_id"] == "user1" for e in user1_log)

    def test_export_audit_log(self, filter_instance, tmp_path):
        """Test exporting audit log."""
        output_file = tmp_path / "audit_log.json"

        async def add_entries():
            await filter_instance.check_content("Test 1")

        asyncio.run(add_entries())
        filter_instance.export_audit_log(str(output_file))

        assert output_file.exists()


class TestGlobalSafetyFilter:
    """Test global safety filter instance."""

    def test_global_filter(self):
        """Test global filter is accessible."""
        assert safety_filter is not None
        assert isinstance(safety_filter, SafetyFilter)
