"""
Tests for Safety Filter Tracing Module

Tests verify that span emission includes safety.action, pattern.matched, and content.length attributes
as specified in Task 21 of the observability implementation plan.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.tracing import (
    get_tracer,
    trace_safety_check,
    record_safety_result,
    trace_layer_check,
    record_layer_result,
    trace_batch_check,
    trace_policy_evaluation
)


class TestTracingInitialization:
    """Tests for tracing module initialization."""

    @patch('api.tracing.setup_telemetry')
    def test_get_tracer_creates_tracer(self, mock_setup):
        """Test that get_tracer creates and returns a tracer instance."""
        mock_tracer = Mock()
        mock_setup.return_value = mock_tracer

        # Reset global tracer
        import api.tracing
        api.tracing._tracer = None

        result = get_tracer()

        assert result == mock_tracer
        mock_setup.assert_called_once_with("safety-filter")


class TestSafetyCheckSpan:
    """Tests for safety check span creation and attributes (Task 21 requirements)."""

    @patch('api.tracing.get_tracer')
    def test_safety_check_span_created(self, mock_get_tracer):
        """Test that safety check span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_safety_check(content="test content", policy="family"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("safety_check")

    @patch('api.tracing.get_tracer')
    def test_safety_check_span_has_content_length(self, mock_get_tracer):
        """Test that safety check span includes content.length attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        test_content = "This is a test content for safety checking"
        with trace_safety_check(content=test_content, policy="family"):
            pass

        # Check that set_attribute was called with content.length
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "content.length" and call[0][1] == len(test_content)
            for call in calls
        ), "content.length attribute not set correctly - Task 21 requirement not met"

    @patch('api.tracing.get_tracer')
    def test_safety_check_span_has_policy(self, mock_get_tracer):
        """Test that safety check span includes safety.policy attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_safety_check(content="test", policy="strict"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "safety.policy" and call[0][1] == "strict"
            for call in calls
        ), "safety.policy attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_safety_check_span_has_content_id(self, mock_get_tracer):
        """Test that safety check span includes content.id attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_safety_check(content="test", policy="family", content_id="content-123"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "content.id" and call[0][1] == "content-123"
            for call in calls
        ), "content.id attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_record_safety_result_with_action(self, mock_get_tracer):
        """Test that record_safety_result adds safety.action attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_safety_result(mock_span, is_safe=True, action="allow")

        mock_span.set_attribute.assert_any_call("safety.is_safe", True)
        mock_span.set_attribute.assert_any_call("safety.action", "allow")

    @patch('api.tracing.get_tracer')
    def test_record_safety_result_with_block_action(self, mock_get_tracer):
        """Test that record_safety_result adds block action (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_safety_result(mock_span, is_safe=False, action="block")

        mock_span.set_attribute.assert_any_call("safety.is_safe", False)
        mock_span.set_attribute.assert_any_call("safety.action", "block")

    @patch('api.tracing.get_tracer')
    def test_record_safety_result_with_matched_patterns(self, mock_get_tracer):
        """Test that record_safety_result adds pattern.matched attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        patterns = ["badword1", "badword2", "inappropriate"]
        record_safety_result(mock_span, is_safe=False, action="block", matched_patterns=patterns)

        # Check that pattern.matched was set with joined patterns
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "pattern.matched" and "badword1" in call[0][1]
            for call in calls
        ), "pattern.matched attribute not set correctly - Task 21 requirement not met"

        mock_span.set_attribute.assert_any_call("pattern.matched_count", 3)

    @patch('api.tracing.get_tracer')
    def test_record_safety_result_with_many_patterns(self, mock_get_tracer):
        """Test that record_safety_result limits patterns to first 5."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        patterns = ["word1", "word2", "word3", "word4", "word5", "word6", "word7"]
        record_safety_result(mock_span, is_safe=False, action="block", matched_patterns=patterns)

        # Should record count as 7 but only include first 5 in pattern.matched
        mock_span.set_attribute.assert_any_call("pattern.matched_count", 7)

        # Check that pattern.matched only includes first 5
        calls = mock_span.set_attribute.call_args_list
        pattern_matched_calls = [call for call in calls if call[0][0] == "pattern.matched"]
        assert len(pattern_matched_calls) == 1
        matched_value = pattern_matched_calls[0][0][1]
        assert "word1" in matched_value
        assert "word5" in matched_value
        assert "word6" not in matched_value  # Should not include 6th word
        assert "word7" not in matched_value  # Should not include 7th word

    @patch('api.tracing.get_tracer')
    def test_record_safety_result_with_severity(self, mock_get_tracer):
        """Test that record_safety_result adds severity attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_safety_result(
            mock_span,
            is_safe=False,
            action="block",
            matched_patterns=["bad"],
            severity="high"
        )

        mock_span.set_attribute.assert_any_call("safety.severity", "high")

    @patch('api.tracing.get_tracer')
    def test_safety_check_span_records_exception(self, mock_get_tracer):
        """Test that exceptions in safety check span are recorded."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        test_error = Exception("Safety check error")

        try:
            with trace_safety_check(content="test", policy="family"):
                raise test_error
        except Exception:
            pass

        mock_span.record_exception.assert_called_once_with(test_error)


class TestLayerCheckSpan:
    """Tests for layer check span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_layer_check_span_created(self, mock_get_tracer):
        """Test that layer check span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_layer_check(layer_name="keyword", content_length=100):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("layer_keyword")

    @patch('api.tracing.get_tracer')
    def test_layer_check_span_has_attributes(self, mock_get_tracer):
        """Test that layer check span includes required attributes."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_layer_check(layer_name="ml", content_length=250):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "safety.layer" and call[0][1] == "ml"
            for call in calls
        ), "safety.layer attribute not set correctly"

        assert any(
            call[0][0] == "content.length" and call[0][1] == 250
            for call in calls
        ), "content.length attribute not set on layer check"

    @patch('api.tracing.get_tracer')
    def test_record_layer_result(self, mock_get_tracer):
        """Test that record_layer_result adds layer result attributes."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_layer_result(mock_span, passed=True, matched_terms=["term1", "term2"])

        mock_span.set_attribute.assert_any_call("layer.passed", True)
        mock_span.set_attribute.assert_any_call("layer.matched_terms", "term1, term2")
        mock_span.set_attribute.assert_any_call("layer.matched_count", 2)


class TestBatchCheckSpan:
    """Tests for batch safety check span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_batch_check_span_created(self, mock_get_tracer):
        """Test that batch check span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_batch_check(content_count=15, policy="family"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("batch_safety_check")

    @patch('api.tracing.get_tracer')
    def test_batch_check_span_has_attributes(self, mock_get_tracer):
        """Test that batch check span includes required attributes."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_batch_check(content_count=30, policy="strict"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "batch.content_count" and call[0][1] == 30
            for call in calls
        ), "batch.content_count attribute not set correctly"

        assert any(
            call[0][0] == "safety.policy" and call[0][1] == "strict"
            for call in calls
        ), "safety.policy attribute not set on batch check"


class TestPolicyEvaluationSpan:
    """Tests for policy evaluation span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_policy_evaluation_span_created(self, mock_get_tracer):
        """Test that policy evaluation span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_policy_evaluation(policy_name="family"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("policy_evaluation")

    @patch('api.tracing.get_tracer')
    def test_policy_evaluation_span_has_policy(self, mock_get_tracer):
        """Test that policy evaluation span includes safety.policy attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_policy_evaluation(policy_name="teen"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "safety.policy" and call[0][1] == "teen"
            for call in calls
        ), "safety.policy attribute not set on policy evaluation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
