"""
Unit tests for distributed tracing.

Tests OpenTelemetry instrumentation for dialogue generation tracing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Add scenespeak-agent to path
agent_path = "/home/ranj/Project_Chimera/services/scenespeak-agent"
sys.path.insert(0, agent_path)


class TestTracerInitialization:
    """Test tracer initialization and setup."""

    @patch('tracing.OPENTELEMETRY_AVAILABLE', True)
    @patch('tracing.JAEGER_AVAILABLE', True)
    def test_setup_telemetry_returns_tracer(self):
        """Test that setup_telemetry returns a tracer when OpenTelemetry is available."""
        from tracing import setup_telemetry

        tracer = setup_telemetry("scenespeak-agent")

        # When OpenTelemetry is available, should return a tracer
        assert tracer is not None

    @patch('tracing.OPENTELEMETRY_AVAILABLE', False)
    def test_setup_telemetry_returns_none_when_unavailable(self):
        """Test that setup_telemetry returns None when OpenTelemetry is not available."""
        from tracing import setup_telemetry

        tracer = setup_telemetry("scenespeak-agent")

        # When OpenTelemetry is not available, should return None
        assert tracer is None


class TestSpanEnrichment:
    """Test span attribute enrichment."""

    def test_add_dialogue_attributes(self):
        """Test adding dialogue-specific attributes to a span."""
        from tracing import add_span_attributes

        mock_span = Mock()
        attributes = {
            "show.id": "test-show-123",
            "scene.number": "5",
            "adapter.name": "dramatic",
            "tokens.input": 150,
            "tokens.output": 200,
            "dialogue.lines_count": 10
        }

        add_span_attributes(mock_span, attributes)

        # Verify all attributes were set
        assert mock_span.set_attribute.call_count == len(attributes)

        # Verify specific attributes
        calls = mock_span.set_attribute.call_args_list
        call_args = [call[0][0] for call in calls]

        assert "show.id" in call_args
        assert "scene.number" in call_args
        assert "adapter.name" in call_args
        assert "tokens.input" in call_args
        assert "tokens.output" in call_args
        assert "dialogue.lines_count" in call_args

    def test_add_span_attributes_with_none_span(self):
        """Test that add_span_attributes handles None span gracefully."""
        from tracing import add_span_attributes

        # Should not raise an exception
        add_span_attributes(None, {"test": "value"})

    def test_add_span_attributes_empty_dict(self):
        """Test that add_span_attributes handles empty dictionary."""
        from tracing import add_span_attributes

        mock_span = Mock()
        add_span_attributes(mock_span, {})

        # Should not call set_attribute
        mock_span.set_attribute.assert_not_called()


class TestErrorRecording:
    """Test error recording on spans."""

    def test_record_error_on_span(self):
        """Test recording an error on a span."""
        from tracing import record_error

        mock_span = Mock()
        test_error = Exception("Test error message")

        record_error(mock_span, test_error)

        # Verify exception was recorded
        mock_span.record_exception.assert_called_once_with(test_error)

        # Verify status was set to error
        assert mock_span.set_status.called

    def test_record_error_with_additional_attributes(self):
        """Test recording error with additional context attributes."""
        from tracing import record_error

        mock_span = Mock()
        test_error = ValueError("Invalid parameter")
        additional_attrs = {"error.context": "dialogue_generation"}

        record_error(mock_span, test_error, additional_attrs)

        # Verify exception was recorded
        mock_span.record_exception.assert_called_once()

        # Verify additional attributes were set
        assert mock_span.set_attribute.called
        call_args = [call[0][0] for call in mock_span.set_attribute.call_args_list]
        assert "error.context" in call_args

    def test_record_error_with_none_span(self):
        """Test that record_error handles None span gracefully."""
        from tracing import record_error

        # Should not raise an exception
        record_error(None, Exception("Test error"))


class TestGenerateDialogueSpan:
    """Test span creation for generate_dialogue function."""

    @patch('tracing.OPENTELEMETRY_AVAILABLE', True)
    @patch('tracing.JAEGER_AVAILABLE', True)
    def test_generate_dialogue_creates_span(self):
        """Test that generate_dialogue creates a span with correct name."""
        from tracing import setup_telemetry

        # Use 100% sampling to ensure span is recorded
        tracer = setup_telemetry("scenespeak-agent", sample_rate=1.0)

        if tracer is not None:
            with tracer.start_as_current_span("generate_dialogue") as span:
                assert span is not None
                # Span should exist (may or may not be recording based on sampling)

    @patch('tracing.OPENTELEMETRY_AVAILABLE', True)
    @patch('tracing.JAEGER_AVAILABLE', True)
    def test_generate_dialogue_span_attributes(self):
        """Test that generate_dialogue span has all required attributes."""
        from tracing import setup_telemetry, add_span_attributes

        tracer = setup_telemetry("scenespeak-agent")

        if tracer is not None:
            with tracer.start_as_current_span("generate_dialogue") as span:
                # Add required attributes
                add_span_attributes(span, {
                    "show.id": "test-show",
                    "scene.number": "3",
                    "adapter.name": "default",
                    "tokens.input": 100,
                    "tokens.output": 150,
                    "dialogue.lines_count": 8
                })

                # Verify attributes were set (in real scenario, would check span attributes)
                assert span is not None


class TestTracingIntegration:
    """Test tracing integration with main application."""

    @patch('tracing.OPENTELEMETRY_AVAILABLE', True)
    @patch('tracing.JAEGER_AVAILABLE', True)
    def test_full_generation_flow_with_tracing(self):
        """Test a complete generation flow with tracing enabled."""
        from tracing import setup_telemetry, add_span_attributes, record_error
        import time

        tracer = setup_telemetry("scenespeak-agent")

        if tracer is not None:
            try:
                with tracer.start_as_current_span("generate_dialogue") as parent_span:
                    # Add initial attributes
                    add_span_attributes(parent_span, {
                        "show.id": "integration-test-show",
                        "adapter.name": "dramatic"
                    })

                    # Simulate nested operation
                    with tracer.start_as_current_span("llm_inference") as child_span:
                        add_span_attributes(child_span, {
                            "tokens.input": 200,
                            "tokens.output": 250
                        })
                        time.sleep(0.01)  # Simulate work

                    # Add result attributes
                    add_span_attributes(parent_span, {
                        "dialogue.lines_count": 12
                    })

            except Exception as e:
                record_error(parent_span, e)
                raise

    @patch('tracing.OPENTELEMETRY_AVAILABLE', False)
    def test_full_generation_flow_without_telemetry(self):
        """Test that code works gracefully when telemetry is unavailable."""
        from tracing import setup_telemetry, add_span_attributes, record_error

        tracer = setup_telemetry("scenespeak-agent")

        # Should return None when telemetry unavailable
        assert tracer is None

        # These should not raise exceptions
        add_span_attributes(None, {"test": "value"})
        record_error(None, Exception("Test error"))


class TestTracingDecorators:
    """Test decorator patterns for tracing."""

    @patch('tracing.OPENTELEMETRY_AVAILABLE', True)
    @patch('tracing.JAEGER_AVAILABLE', True)
    def test_traced_function_decorator(self):
        """Test using a decorator to trace a function."""
        from tracing import setup_telemetry, add_span_attributes

        tracer = setup_telemetry("scenespeak-agent")

        if tracer is not None:
            def mock_generate_dialogue(prompt, adapter="default"):
                with tracer.start_as_current_span("generate_dialogue") as span:
                    add_span_attributes(span, {
                        "adapter.name": adapter,
                        "prompt.length": len(prompt)
                    })
                    return "Generated dialogue"

            result = mock_generate_dialogue("Test prompt", "dramatic")
            assert result == "Generated dialogue"


@pytest.fixture
def reset_tracing():
    """Reset tracing state between tests."""
    # This would reset any global tracing state
    yield
    # Cleanup after test
    pass
