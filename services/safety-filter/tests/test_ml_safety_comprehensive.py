"""
Comprehensive unit tests for ml_safety.py.

Tests all filter layers (pattern, classification, context),
async operations, audit logging, export functionality, and edge cases.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, '.')


class TestFilterActionEnum:
    """Test FilterAction enum."""

    def test_action_values(self):
        """Test all action enum values."""
        from ml_safety import FilterAction

        assert FilterAction.ALLOW.value == "allow"
        assert FilterAction.BLOCK.value == "block"
        assert FilterAction.FLAG.value == "flag"
        assert FilterAction.MODIFY.value == "modify"

    def test_action_iteration(self):
        """Test iterating over actions."""
        from ml_safety import FilterAction

        actions = list(FilterAction)
        assert len(actions) == 4
        assert FilterAction.ALLOW in actions


class TestFilterLayerEnum:
    """Test FilterLayer enum."""

    def test_layer_values(self):
        """Test all layer enum values."""
        from ml_safety import FilterLayer

        assert FilterLayer.PATTERN.value == "pattern"
        assert FilterLayer.CLASSIFICATION.value == "classification"
        assert FilterLayer.CONTEXT.value == "context"
        assert FilterLayer.AUDIT.value == "audit"


class TestFilterResult:
    """Test FilterResult dataclass."""

    def test_result_creation_minimal(self):
        """Test creating result with minimal fields."""
        from ml_safety import FilterResult, FilterAction, FilterLayer

        result = FilterResult(
            action=FilterAction.BLOCK,
            layer=FilterLayer.PATTERN,
            confidence=1.0,
            reason="Test block"
        )

        assert result.action == FilterAction.BLOCK
        assert result.layer == FilterLayer.PATTERN
        assert result.confidence == 1.0
        assert result.reason == "Test block"
        assert result.matched_patterns == []
        assert result.model_predictions == {}

    def test_result_with_all_fields(self):
        """Test creating result with all fields."""
        from ml_safety import FilterResult, FilterAction, FilterLayer

        result = FilterResult(
            action=FilterAction.FLAG,
            layer=FilterLayer.CLASSIFICATION,
            confidence=0.85,
            reason="Classification flag",
            matched_patterns=["pattern1", "pattern2"],
            model_predictions={"toxic": 0.9, "hateful": 0.1},
            metadata={"key": "value"}
        )

        assert len(result.matched_patterns) == 2
        assert len(result.model_predictions) == 2
        assert result.metadata["key"] == "value"

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        from ml_safety import FilterResult, FilterAction, FilterLayer

        result = FilterResult(
            action=FilterAction.ALLOW,
            layer=FilterLayer.CONTEXT,
            confidence=1.0,
            reason="Safe content",
            matched_patterns=["test"],
            model_predictions={"toxic": 0.1}
        )

        result_dict = result.to_dict()

        assert result_dict["action"] == "allow"
        assert result_dict["layer"] == "context"
        assert result_dict["confidence"] == 1.0
        assert "test" in result_dict["matched_patterns"]
        assert result_dict["model_predictions"]["toxic"] == 0.1
        assert "timestamp" in result_dict

    def test_result_timestamp_default(self):
        """Test result has default timestamp."""
        from ml_safety import FilterResult, FilterAction, FilterLayer

        result = FilterResult(
            action=FilterAction.ALLOW,
            layer=FilterLayer.AUDIT,
            confidence=1.0,
            reason="Test"
        )

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)


class TestAuditEntry:
    """Test AuditEntry dataclass."""

    def test_entry_creation(self):
        """Test creating audit entry."""
        from ml_safety import AuditEntry, FilterResult, FilterAction, FilterLayer

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
            result=result,
            user_id="user123",
            session_id="session456"
        )

        assert entry.content_hash == "abc123"
        assert entry.user_id == "user123"
        assert entry.session_id == "session456"

    def test_entry_to_dict(self):
        """Test converting entry to dictionary."""
        from ml_safety import AuditEntry, FilterResult, FilterAction, FilterLayer

        result = FilterResult(
            action=FilterAction.ALLOW,
            layer=FilterLayer.CONTEXT,
            confidence=1.0,
            reason="Safe"
        )

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            content_hash="xyz789",
            content_preview="Preview...",
            result=result
        )

        entry_dict = entry.to_dict()

        assert entry_dict["content_hash"] == "xyz789"
        assert entry_dict["action"] == "allow"
        assert "timestamp" in entry_dict

    def test_entry_with_context(self):
        """Test entry with additional context."""
        from ml_safety import AuditEntry, FilterResult, FilterAction, FilterLayer

        result = FilterResult(
            action=FilterAction.FLAG,
            layer=FilterLayer.CLASSIFICATION,
            confidence=0.8,
            reason="Flagged"
        )

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            content_hash="def456",
            content_preview="Content...",
            result=result,
            context={"source": "api", "ip": "127.0.0.1"}
        )

        assert entry.context["source"] == "api"
        assert entry.context["ip"] == "127.0.0.1"


class TestPatternFilter:
    """Test PatternFilter class."""

    def test_default_initialization(self):
        """Test filter with default patterns."""
        from ml_safety import PatternFilter

        filter_obj = PatternFilter()

        assert len(filter_obj.patterns) > 0
        assert len(filter_obj.compiled_patterns) == len(filter_obj.patterns)

    def test_custom_patterns(self):
        """Test filter with custom patterns."""
        from ml_safety import PatternFilter

        custom_patterns = [r'\btest\b', r'\bexample\b']
        filter_obj = PatternFilter(patterns=custom_patterns)

        assert len(filter_obj.patterns) == 2
        assert len(filter_obj.compiled_patterns) == 2

    def test_check_safe_content(self):
        """Test checking safe content."""
        from ml_safety import PatternFilter

        filter_obj = PatternFilter()
        blocked, matched = filter_obj.check("Hello, how are you today?")

        assert blocked is False
        assert len(matched) == 0

    def test_check_blocked_content_password(self):
        """Test checking content with password pattern."""
        from ml_safety import PatternFilter

        filter_obj = PatternFilter()
        blocked, matched = filter_obj.check("Here is my password: 'secret123'")

        assert blocked is True
        assert len(matched) > 0
        assert any("password" in pattern.lower() for pattern in matched)

    def test_check_blocked_content_hack(self):
        """Test checking content with hack pattern."""
        from ml_safety import PatternFilter

        filter_obj = PatternFilter()
        blocked, matched = filter_obj.check("I want to hack the system")

        assert blocked is True
        assert len(matched) > 0

    def test_check_case_insensitive(self):
        """Test that matching is case insensitive."""
        from ml_safety import PatternFilter

        filter_obj = PatternFilter()

        # Should match regardless of case
        blocked1, _ = filter_obj.check("PASSWORD: secret")
        blocked2, _ = filter_obj.check("password: secret")
        blocked3, _ = filter_obj.check("PaSsWoRd: secret")

        assert blocked1 is True
        assert blocked2 is True
        assert blocked3 is True

    def test_check_multiple_patterns(self):
        """Test content matching multiple patterns."""
        from ml_safety import PatternFilter

        filter_obj = PatternFilter()
        content = "I want to hack and exploit the system"

        blocked, matched = filter_obj.check(content)

        assert blocked is True
        assert len(matched) >= 2


class TestClassificationFilter:
    """Test ClassificationFilter class."""

    def test_default_initialization(self):
        """Test filter with default settings."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter()

        assert filter_obj.model_path == "/models/safety_classifier"
        assert filter_obj.threshold == 0.7
        assert filter_obj._model_loaded is False
        assert len(filter_obj.labels) == 5

    def test_custom_threshold(self):
        """Test filter with custom threshold."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter(threshold=0.5)

        assert filter_obj.threshold == 0.5

    def test_custom_labels(self):
        """Test filter with custom labels."""
        from ml_safety import ClassificationFilter

        custom_labels = ["spam", "scam", "phishing"]
        filter_obj = ClassificationFilter(labels=custom_labels)

        assert filter_obj.labels == custom_labels

    def test_load_model(self):
        """Test loading model."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter()
        filter_obj.load_model()

        assert filter_obj._model_loaded is True

    def test_classify_returns_predictions(self):
        """Test classification returns predictions."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter()
        predictions = filter_obj.classify("Test content")

        assert isinstance(predictions, dict)
        assert len(predictions) > 0
        assert all(0 <= score <= 1 for score in predictions.values())

    def test_classify_has_all_labels(self):
        """Test classification includes all configured labels."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter()
        predictions = filter_obj.classify("Test")

        for label in filter_obj.labels:
            assert label in predictions

    def test_check_safe_content(self):
        """Test checking safe content."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter()
        blocked, predictions = filter_obj.check("Safe content here")

        # With default threshold of 0.7 and simulated scores < 0.3
        assert blocked is False
        assert isinstance(predictions, dict)

    def test_check_exceeds_threshold(self):
        """Test check when threshold is exceeded."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter(threshold=0.01)

        # With low threshold, simulated scores may exceed it
        blocked, predictions = filter_obj.check("Test content")

        assert isinstance(blocked, bool)
        assert isinstance(predictions, dict)

    def test_classify_loads_model_if_needed(self):
        """Test that classify loads model if not loaded."""
        from ml_safety import ClassificationFilter

        filter_obj = ClassificationFilter()
        assert filter_obj._model_loaded is False

        filter_obj.classify("Test")

        assert filter_obj._model_loaded is True


class TestContextAwareFilter:
    """Test ContextAwareFilter class."""

    def test_default_initialization(self):
        """Test filter with default settings."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()

        assert filter_obj.model_path == "/models/context_filter"
        assert filter_obj.max_length == 512
        assert filter_obj.threshold == 0.6
        assert filter_obj._model_loaded is False

    def test_custom_parameters(self):
        """Test filter with custom parameters."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter(
            model_path="/custom/path",
            max_length=1024,
            threshold=0.8
        )

        assert filter_obj.model_path == "/custom/path"
        assert filter_obj.max_length == 1024
        assert filter_obj.threshold == 0.8

    def test_load_model(self):
        """Test loading model."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()
        filter_obj.load_model()

        assert filter_obj._model_loaded is True

    def test_analyze_context(self):
        """Test context analysis."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()
        blocked, score, reason = filter_obj.analyze_context("Hello!")

        assert isinstance(blocked, bool)
        assert 0 <= score <= 1
        assert isinstance(reason, str)

    def test_analyze_context_with_history(self):
        """Test context analysis with conversation history."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()
        history = [
            {"user": "Hi there"},
            {"assistant": "Hello! How can I help?"},
            {"user": "What's the weather?"},
            {"assistant": "I don't have weather data."}
        ]

        blocked, score, reason = filter_obj.analyze_context(
            "Thanks anyway",
            conversation_history=history
        )

        assert isinstance(blocked, bool)
        assert isinstance(score, float)

    def test_analyze_context_empty_history(self):
        """Test context analysis with empty history."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()

        blocked, score, reason = filter_obj.analyze_context(
            "Test",
            conversation_history=[]
        )

        assert isinstance(blocked, bool)
        assert isinstance(score, float)

    def test_analyze_context_loads_model_if_needed(self):
        """Test that analyze_context loads model if not loaded."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()
        assert filter_obj._model_loaded is False

        filter_obj.analyze_context("Test")

        assert filter_obj._model_loaded is True

    @pytest.mark.asyncio
    async def test_analyze_context_async(self):
        """Test async context analysis."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()

        blocked, score, reason = await filter_obj.analyze_context_async("Hello!")

        assert isinstance(blocked, bool)
        assert isinstance(score, float)
        assert isinstance(reason, str)

    def test_build_context_without_history(self):
        """Test building context without history."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()
        context = filter_obj._build_context("Test content", None)

        assert context == "Test content"

    def test_build_context_with_history(self):
        """Test building context with history."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()
        history = [
            {"user": "Hello"},
            {"assistant": "Hi"},
            {"user": "How are you?"}
        ]

        context = filter_obj._build_context("Test", history)

        assert "User: Hello" in context
        assert "Assistant: Hi" in context
        assert "User: How are you?" in context
        assert "User: Test" in context

    def test_build_context_truncates_history(self):
        """Test that context building truncates long history."""
        from ml_safety import ContextAwareFilter

        filter_obj = ContextAwareFilter()
        # Create 10 turns
        history = [{"user": f"Message {i}"} for i in range(10)]

        context = filter_obj._build_context("Final", history)

        # Should only include last 5 turns
        user_count = context.count("User:")
        assert user_count <= 6  # 5 history + 1 current


class TestSafetyFilter:
    """Test SafetyFilter class."""

    def test_default_initialization(self):
        """Test filter with default settings."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        assert safety_filter.pattern_filter is not None
        assert safety_filter.classification_filter is not None
        assert safety_filter.context_filter is not None
        assert safety_filter.enable_audit is True
        assert len(safety_filter.audit_log) == 0

    def test_initialization_without_audit(self):
        """Test filter with audit disabled."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter(enable_audit=False)

        assert safety_filter.enable_audit is False

    def test_initialization_with_custom_filters(self):
        """Test filter with custom filter instances."""
        from ml_safety import SafetyFilter, PatternFilter, ClassificationFilter

        custom_pattern = PatternFilter(patterns=[r'\btest\b'])
        custom_classification = ClassificationFilter(threshold=0.5)

        safety_filter = SafetyFilter(
            pattern_filter=custom_pattern,
            classification_filter=custom_classification
        )

        assert safety_filter.pattern_filter is custom_pattern
        assert safety_filter.classification_filter is custom_classification

    @pytest.mark.asyncio
    async def test_check_safe_content(self):
        """Test checking safe content through all layers."""
        from ml_safety import SafetyFilter, FilterAction

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("Hello, how are you?")

        assert result.action == FilterAction.ALLOW
        assert result.layer.value == "audit"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_check_blocked_by_pattern(self):
        """Test content blocked by pattern layer."""
        from ml_safety import SafetyFilter, FilterAction

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("Here is my password: 'secret'")

        assert result.action == FilterAction.BLOCK
        assert result.layer.value == "pattern"
        assert len(result.matched_patterns) > 0

    @pytest.mark.asyncio
    async def test_check_with_user_context(self):
        """Test checking content with user context."""
        from ml_safety import SafetyFilter, FilterAction

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content(
            "Hello!",
            user_id="user123",
            session_id="session456",
            context={"source": "web"}
        )

        assert result.action == FilterAction.ALLOW
        # Verify audit log entry created
        assert len(safety_filter.audit_log) == 1
        assert safety_filter.audit_log[0].user_id == "user123"

    @pytest.mark.asyncio
    async def test_check_with_conversation_history(self):
        """Test checking content with conversation history."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        history = [
            {"user": "Hi"},
            {"assistant": "Hello"}
        ]

        result = await safety_filter.check_content(
            "How are you?",
            conversation_history=history
        )

        assert isinstance(result.action.value, str)

    @pytest.mark.asyncio
    async def test_statistics_tracking(self):
        """Test that statistics are tracked."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        await safety_filter.check_content("Safe content 1")
        await safety_filter.check_content("Safe content 2")
        await safety_filter.check_content("password: secret")

        stats = safety_filter.get_statistics()

        assert stats["total_checked"] == 3
        assert stats["allowed"] == 2
        assert stats["blocked"] == 1

    @pytest.mark.asyncio
    async def test_audit_log_disabled(self):
        """Test that audit log can be disabled."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter(enable_audit=False)

        await safety_filter.check_content("Test content")

        assert len(safety_filter.audit_log) == 0

    @pytest.mark.asyncio
    async def test_audit_log_entry_content_preview(self):
        """Test that audit log has content preview."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        long_content = "a" * 200

        await safety_filter.check_content(long_content)

        entry = safety_filter.audit_log[0]
        assert len(entry.content_preview) <= 103  # 100 + "..."

    def test_get_statistics(self):
        """Test getting filter statistics."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        stats = safety_filter.get_statistics()

        assert "total_checked" in stats
        assert "allowed" in stats
        assert "blocked" in stats
        assert "flagged" in stats
        assert "modified" in stats
        assert "allow_rate" in stats
        assert "block_rate" in stats
        assert "flag_rate" in stats

    def test_get_statistics_with_zero_checks(self):
        """Test statistics with no checks performed."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        stats = safety_filter.get_statistics()

        assert stats["total_checked"] == 0
        assert stats["allow_rate"] == 0.0
        assert stats["block_rate"] == 0.0
        assert stats["flag_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_with_activity(self):
        """Test statistics calculations."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        async def add_checks():
            await safety_filter.check_content("Safe 1")
            await safety_filter.check_content("Safe 2")
            await safety_filter.check_content("Safe 3")
            await safety_filter.check_content("password: test")

        asyncio.run(add_checks())
        stats = safety_filter.get_statistics()

        assert stats["total_checked"] == 4
        assert stats["allow_rate"] == 0.75
        assert stats["block_rate"] == 0.25

    def test_get_audit_log(self):
        """Test getting audit log."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        async def add_entries():
            await safety_filter.check_content("Test 1")
            await safety_filter.check_content("Test 2")

        asyncio.run(add_entries())

        log = safety_filter.get_audit_log(limit=10)
        assert len(log) == 2

    def test_get_audit_log_with_offset(self):
        """Test getting audit log with offset."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        async def add_entries():
            for i in range(5):
                await safety_filter.check_content(f"Test {i}")

        asyncio.run(add_entries())

        # Get last 3 entries
        log = safety_filter.get_audit_log(limit=3, offset=2)
        assert len(log) == 3

    def test_get_audit_log_with_user_filter(self):
        """Test filtering audit log by user ID."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        async def add_entries():
            await safety_filter.check_content("Test 1", user_id="user1")
            await safety_filter.check_content("Test 2", user_id="user2")
            await safety_filter.check_content("Test 3", user_id="user1")

        asyncio.run(add_entries())

        user1_log = safety_filter.get_audit_log(user_id="user1")
        assert len(user1_log) == 2
        assert all(e["user_id"] == "user1" for e in user1_log)

    def test_export_audit_log(self):
        """Test exporting audit log to file."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        async def add_entries():
            await safety_filter.check_content("Test 1")

        asyncio.run(add_entries())

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name

        try:
            safety_filter.export_audit_log(output_path)

            assert Path(output_path).exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert "export_timestamp" in data
            assert "statistics" in data
            assert "entries" in data
            assert len(data["entries"]) >= 1
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_audit_log_structure(self):
        """Test exported audit log has correct structure."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        async def add_entries():
            await safety_filter.check_content("Test content")

        asyncio.run(add_entries())

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name

        try:
            safety_filter.export_audit_log(output_path)

            with open(output_path, 'r') as f:
                data = json.load(f)

            # Check structure
            assert isinstance(data["export_timestamp"], str)
            assert isinstance(data["statistics"], dict)
            assert isinstance(data["entries"], list)

            # Check entry has required fields
            if len(data["entries"]) > 0:
                entry = data["entries"][0]
                assert "timestamp" in entry
                assert "content_hash" in entry
                assert "content_preview" in entry
                assert "action" in entry
        finally:
            Path(output_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_audit_log_max_size(self):
        """Test that audit log respects max size."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        # Add more than 10000 entries
        for i in range(10050):
            await safety_filter.check_content(f"Test {i}")

        # Should be trimmed to last 10000
        assert len(safety_filter.audit_log) <= 10000


class TestGlobalSafetyFilter:
    """Test global safety_filter instance."""

    def test_global_instance_exists(self):
        """Test that global instance exists."""
        from ml_safety import safety_filter, SafetyFilter

        assert safety_filter is not None
        assert isinstance(safety_filter, SafetyFilter)

    def test_global_instance_accessible(self):
        """Test that global instance is accessible."""
        from ml_safety import safety_filter

        stats = safety_filter.get_statistics()
        assert "total_checked" in stats


class TestEdgeCases:
    """Test edge cases and special inputs."""

    @pytest.mark.asyncio
    async def test_empty_content(self):
        """Test checking empty content."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("")

        assert isinstance(result.action.value, str)

    @pytest.mark.asyncio
    async def test_whitespace_only(self):
        """Test checking whitespace-only content."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("   \n\t  ")

        assert isinstance(result.action.value, str)

    @pytest.mark.asyncio
    async def test_unicode_content(self):
        """Test checking unicode content."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        unicode_content = "Hello 世界 🌍 مرحبا"

        result = await safety_filter.check_content(unicode_content)

        assert isinstance(result.action.value, str)

    @pytest.mark.asyncio
    async def test_emoji_only(self):
        """Test checking emoji-only content."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        emoji_content = "😀 😃 😄 😁"

        result = await safety_filter.check_content(emoji_content)

        assert isinstance(result.action.value, str)

    @pytest.mark.asyncio
    async def test_very_long_content(self):
        """Test checking very long content."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        long_content = "a" * 10000

        result = await safety_filter.check_content(long_content)

        assert isinstance(result.action.value, str)

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test checking special characters."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        special_content = "!@#$%^&*()_+-=[]{}|;':\",.<>?/"

        result = await safety_filter.check_content(special_content)

        assert isinstance(result.action.value, str)


class TestConfidenceScores:
    """Test confidence score handling."""

    @pytest.mark.asyncio
    async def test_confidence_in_allowed_range(self):
        """Test that confidence is always in valid range."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()

        result = await safety_filter.check_content("Test content")

        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_confidence_for_blocked_content(self):
        """Test confidence for blocked content."""
        from ml_safety import SafetyFilter, FilterAction

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("password: secret")

        if result.action == FilterAction.BLOCK:
            assert result.confidence == 1.0


class TestModelPredictions:
    """Test model predictions in results."""

    @pytest.mark.asyncio
    async def test_model_predictions_included(self):
        """Test that model predictions are included."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("Test content")

        assert isinstance(result.model_predictions, dict)

    @pytest.mark.asyncio
    async def test_model_predictions_for_safe_content(self):
        """Test model predictions for safe content."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("Safe content")

        # Should have predictions from classification layer
        assert isinstance(result.model_predictions, dict)


class TestMetadata:
    """Test metadata in results."""

    @pytest.mark.asyncio
    async def test_metadata_in_results(self):
        """Test that results can have metadata."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content("Test content")

        assert isinstance(result.metadata, dict)

    @pytest.mark.asyncio
    async def test_metadata_for_context_layer(self):
        """Test metadata for context-aware filtering."""
        from ml_safety import SafetyFilter

        safety_filter = SafetyFilter()
        result = await safety_filter.check_content(
            "Test",
            conversation_history=[{"user": "Hi"}]
        )

        # May have risk_score in metadata if context layer triggered
        assert isinstance(result.metadata, dict)
