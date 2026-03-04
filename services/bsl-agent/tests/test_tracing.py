"""
Tests for BSL Agent Tracing Module

Tests verify that span emission includes translation.request_id and sign_language attributes
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
    trace_translation,
    trace_gloss_generation,
    record_gloss_result,
    trace_batch_translation,
    trace_non_manual_markers
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
        mock_setup.assert_called_once_with("bsl-agent")


class TestTranslationSpan:
    """Tests for translation span creation and attributes (Task 21 requirements)."""

    @patch('api.tracing.get_tracer')
    def test_translation_span_created(self, mock_get_tracer):
        """Test that translation span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_translation(request_id="req-123"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("translation")

    @patch('api.tracing.get_tracer')
    def test_translation_span_has_request_id(self, mock_get_tracer):
        """Test that translation span includes translation.request_id attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_translation(request_id="translation-request-456"):
            pass

        # Check that set_attribute was called with request_id
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "translation.request_id" and call[0][1] == "translation-request-456"
            for call in calls
        ), "translation.request_id attribute not set correctly - Task 21 requirement not met"

    @patch('api.tracing.get_tracer')
    def test_translation_span_has_sign_language(self, mock_get_tracer):
        """Test that translation span includes sign_language attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_translation(request_id="req-789", sign_language="bsl"):
            pass

        # Check that set_attribute was called with sign_language
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "sign_language" and call[0][1] == "bsl"
            for call in calls
        ), "sign_language attribute not set correctly - Task 21 requirement not met"

    @patch('api.tracing.get_tracer')
    def test_translation_span_has_source_language(self, mock_get_tracer):
        """Test that translation span includes translation.source_language attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_translation(request_id="req-101", source_language="en"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "translation.source_language" and call[0][1] == "en"
            for call in calls
        ), "translation.source_language attribute not set correctly"

    @patch('api.tracing.get_tracer')
    @patch('time.time')
    def test_translation_span_has_duration(self, mock_time, mock_get_tracer):
        """Test that translation span includes translation.duration_ms attribute."""
        mock_time.side_effect = [0.0, 0.5]

        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_translation(request_id="req-202"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "translation.duration_ms" and call[0][1] == 500
            for call in calls
        ), "translation.duration_ms attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_translation_span_records_exception(self, mock_get_tracer):
        """Test that exceptions in translation span are recorded."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        test_error = Exception("Translation error")

        try:
            with trace_translation(request_id="req-303"):
                raise test_error
        except Exception:
            pass

        mock_span.record_exception.assert_called_once_with(test_error)


class TestGlossGenerationSpan:
    """Tests for gloss generation span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_gloss_generation_span_created(self, mock_get_tracer):
        """Test that gloss generation span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_gloss_generation(request_id="req-404", gloss_format="singspell"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("gloss_generation")

    @patch('api.tracing.get_tracer')
    def test_gloss_generation_span_has_format(self, mock_get_tracer):
        """Test that gloss generation span includes gloss.format attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_gloss_generation(request_id="req-505", gloss_format="singspell"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "gloss.format" and call[0][1] == "singspell"
            for call in calls
        ), "gloss.format attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_record_gloss_result(self, mock_get_tracer):
        """Test that record_gloss_result adds gloss attributes."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_gloss_result(mock_span, gloss_length=150, confidence=0.85)

        mock_span.set_attribute.assert_any_call("gloss.length", 150)
        mock_span.set_attribute.assert_any_call("gloss.confidence", 0.85)


class TestBatchTranslationSpan:
    """Tests for batch translation span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_batch_translation_span_created(self, mock_get_tracer):
        """Test that batch translation span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_batch_translation(request_count=10):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("batch_translation")

    @patch('api.tracing.get_tracer')
    def test_batch_translation_span_has_request_count(self, mock_get_tracer):
        """Test that batch translation span includes batch.request_count attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_batch_translation(request_count=25):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "batch.request_count" and call[0][1] == 25
            for call in calls
        ), "batch.request_count attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_batch_translation_span_has_sign_language(self, mock_get_tracer):
        """Test that batch translation span includes sign_language attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_batch_translation(request_count=5):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "sign_language" and call[0][1] == "bsl"
            for call in calls
        ), "sign_language attribute not set on batch translation - Task 21 requirement not met"


class TestNonManualMarkersSpan:
    """Tests for non-manual markers span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_non_manual_markers_span_created(self, mock_get_tracer):
        """Test that non-manual markers span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_non_manual_markers(request_id="req-606"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("non_manual_markers")

    @patch('api.tracing.get_tracer')
    def test_non_manual_markers_span_has_request_id(self, mock_get_tracer):
        """Test that non-manual markers span includes translation.request_id attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_non_manual_markers(request_id="req-707"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "translation.request_id" and call[0][1] == "req-707"
            for call in calls
        ), "translation.request_id attribute not set on non-manual markers span"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
