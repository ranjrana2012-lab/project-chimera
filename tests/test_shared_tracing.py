"""
Tests for top-level shared tracing module.

Tests the OpenTelemetry tracing setup including:
- NoOpTracer
- NoOpSpan
- setup_tracing
- instrument_fastapi
- add_span_attributes
- record_error
- trace_operation
- SpanAttributes
"""

import pytest
import os
import sys
from pathlib import Path

# Add top-level shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from unittest.mock import Mock, patch, MagicMock, AsyncMock
from opentelemetry.trace import Status, StatusCode

from tracing import (
    NoOpTracer,
    NoOpSpan,
    setup_tracing,
    instrument_fastapi,
    add_span_attributes,
    record_error,
    trace_operation,
    SpanAttributes,
    create_service_attributes,
    create_operation_attributes,
)


class TestNoOpTracer:
    """Tests for NoOpTracer fallback class."""

    def test_has_name_property(self):
        """Verify NoOpTracer has a name property."""
        tracer = NoOpTracer()
        assert hasattr(tracer, 'start_as_current_span')

    def test_start_as_current_span_returns_context(self):
        """Verify start_as_current_span returns context manager."""
        tracer = NoOpTracer()
        context = tracer.start_as_current_span("test")
        assert context is not None

    def test_start_span_returns_noop_span(self):
        """Verify start_span returns NoOpSpan."""
        tracer = NoOpTracer()
        span = tracer.start_span("test")
        assert isinstance(span, NoOpSpan)


class TestNoOpSpan:
    """Tests for NoOpSpan fallback class."""

    def test_context_manager_protocol(self):
        """Verify NoOpSpan supports context manager protocol."""
        span = NoOpSpan()
        assert hasattr(span, '__enter__')
        assert hasattr(span, '__exit__')

    def test_enter_returns_self(self):
        """Verify __enter__ returns the span itself."""
        span = NoOpSpan()
        result = span.__enter__()
        assert result is span

    def test_exit_accepts_exception_args(self):
        """Verify __exit__ accepts exception arguments."""
        span = NoOpSpan()
        # Should not raise
        span.__exit__(None, None, None)

    def test_set_attribute_does_nothing(self):
        """Verify set_attribute does nothing (no-op)."""
        span = NoOpSpan()
        # Should not raise
        span.set_attribute("key", "value")
        span.set_attributes({"key": "value"})

    def test_record_exception_does_nothing(self):
        """Verify record_exception does nothing (no-op)."""
        span = NoOpSpan()
        # Should not raise
        try:
            raise ValueError("test error")
        except ValueError as e:
            span.record_exception(e)

    def test_set_status_does_nothing(self):
        """Verify set_status does nothing (no-op)."""
        span = NoOpSpan()
        # Should not raise
        span.set_status(Status(StatusCode.OK))

    def test_add_event_does_nothing(self):
        """Verify add_event does nothing (no-op)."""
        span = NoOpSpan()
        # Should not raise
        span.add_event("test event")

    def test_end_does_nothing(self):
        """Verify end does nothing (no-op)."""
        span = NoOpSpan()
        # Should not raise
        span.end()


class TestSetupTracing:
    """Tests for setup_tracing function."""

    def test_returns_noop_tracer_when_otel_unavailable(self):
        """Verify NoOpTracer returned when OpenTelemetry not available."""
        with patch('tracing.OTEL_AVAILABLE', False):
            tracer = setup_tracing("test-service")
            assert isinstance(tracer, NoOpTracer)

    def test_accepts_service_name(self):
        """Verify function accepts service_name parameter."""
        with patch('tracing.OTEL_AVAILABLE', False):
            tracer = setup_tracing("my-service")
            assert tracer is not None

    def test_accepts_service_version(self):
        """Verify function accepts service_version parameter."""
        with patch('tracing.OTEL_AVAILABLE', False):
            tracer = setup_tracing("my-service", service_version="2.0.0")
            assert tracer is not None

    def test_accepts_custom_otlp_endpoint(self):
        """Verify function accepts custom otlp_endpoint parameter."""
        with patch('tracing.OTEL_AVAILABLE', False):
            tracer = setup_tracing("my-service", otlp_endpoint="http://custom:4317")
            assert tracer is not None

    def test_accepts_environment_parameter(self):
        """Verify function accepts environment parameter."""
        with patch('tracing.OTEL_AVAILABLE', False):
            tracer = setup_tracing("my-service", environment="production")
            assert tracer is not None


class TestInstrumentFastAPI:
    """Tests for instrument_fastapi function."""

    def test_does_nothing_when_otel_unavailable(self):
        """Verify function returns gracefully when OpenTelemetry unavailable."""
        mock_app = Mock()

        with patch('tracing.OTEL_AVAILABLE', False):
            result = instrument_fastapi(mock_app)
            assert result is None

    def test_accepts_fastapi_app(self):
        """Verify function accepts FastAPI app parameter."""
        mock_app = Mock()
        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            instrument_fastapi(mock_app)


class TestAddSpanAttributes:
    """Tests for add_span_attributes function."""

    def test_does_nothing_when_span_is_none(self):
        """Verify function handles None span gracefully."""
        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            add_span_attributes(None, {"key": "value"})

    def test_does_nothing_when_otel_unavailable(self):
        """Verify function handles missing OpenTelemetry gracefully."""
        mock_span = Mock()

        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            add_span_attributes(mock_span, {"key": "value"})

    def test_ignores_none_values_in_attributes(self):
        """Verify None values in attributes are ignored."""
        mock_span = Mock()

        with patch('tracing.OTEL_AVAILABLE', True):
            # Should not raise
            add_span_attributes(mock_span, {"key1": "value1", "key2": None})

    def test_accepts_dict_of_attributes(self):
        """Verify function accepts dict of attributes."""
        mock_span = Mock()

        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            add_span_attributes(mock_span, {"attr1": "val1", "attr2": "val2"})


class TestRecordError:
    """Tests for record_error function."""

    def test_does_nothing_when_span_is_none(self):
        """Verify function handles None span gracefully."""
        error = ValueError("test error")

        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            record_error(None, error)

    def test_does_nothing_when_otel_unavailable(self):
        """Verify function handles missing OpenTelemetry gracefully."""
        mock_span = Mock()
        error = Exception("test error")

        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            record_error(mock_span, error)

    def test_accepts_exception_and_optional_attributes(self):
        """Verify function accepts exception and optional attributes dict."""
        mock_span = Mock()
        error = RuntimeError("test error")
        attributes = {"context": "test"}

        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            record_error(mock_span, error, attributes)

    def test_works_without_attributes(self):
        """Verify function works without optional attributes."""
        mock_span = Mock()
        error = IOError("test error")

        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            record_error(mock_span, error)


class TestTraceOperation:
    """Tests for trace_operation context manager."""

    def test_works_when_otel_unavailable(self):
        """Verify context manager works when OpenTelemetry unavailable."""
        with patch('tracing.OTEL_AVAILABLE', False):
            with trace_operation("test_operation"):
                # Should not raise
                pass

    def test_accepts_operation_name(self):
        """Verify function accepts operation_name parameter."""
        with patch('tracing.OTEL_AVAILABLE', False):
            with trace_operation("my_operation"):
                pass

    def test_accepts_optional_attributes(self):
        """Verify function accepts optional attributes parameter."""
        with patch('tracing.OTEL_AVAILABLE', False):
            with trace_operation("my_operation", {"key": "value"}):
                pass


class TestSpanAttributes:
    """Tests for SpanAttributes class."""

    def test_has_service_attributes(self):
        """Verify SpanAttributes has service-related constants."""
        assert hasattr(SpanAttributes, 'SERVICE_NAME')
        assert hasattr(SpanAttributes, 'SERVICE_VERSION')
        assert hasattr(SpanAttributes, 'SERVICE_NAMESPACE')

    def test_has_operation_attributes(self):
        """Verify SpanAttributes has operation-related constants."""
        assert hasattr(SpanAttributes, 'OPERATION_NAME')
        assert hasattr(SpanAttributes, 'OPERATION_TYPE')

    def test_has_request_attributes(self):
        """Verify SpanAttributes has request-related constants."""
        assert hasattr(SpanAttributes, 'REQUEST_ID')
        assert hasattr(SpanAttributes, 'SHOW_ID')
        assert hasattr(SpanAttributes, 'SCENE_NUMBER')

    def test_has_model_attributes(self):
        """Verify SpanAttributes has model-related constants."""
        assert hasattr(SpanAttributes, 'MODEL_NAME')
        assert hasattr(SpanAttributes, 'MODEL_TYPE')
        assert hasattr(SpanAttributes, 'MODEL_VERSION')

    def test_has_performance_attributes(self):
        """Verify SpanAttributes has performance-related constants."""
        assert hasattr(SpanAttributes, 'LATENCY_MS')
        assert hasattr(SpanAttributes, 'TOKENS_INPUT')
        assert hasattr(SpanAttributes, 'TOKENS_OUTPUT')


class TestCreateServiceAttributes:
    """Tests for create_service_attributes function."""

    def test_creates_service_name_attribute(self):
        """Verify service name is in attributes."""
        attrs = create_service_attributes("my-service", "1.0.0")
        assert attrs[SpanAttributes.SERVICE_NAME] == "my-service"

    def test_creates_service_version_attribute(self):
        """Verify service version is in attributes."""
        attrs = create_service_attributes("my-service", "1.0.0")
        assert attrs[SpanAttributes.SERVICE_VERSION] == "1.0.0"

    def test_creates_namespace_attribute(self):
        """Verify namespace is set to project-chimera."""
        attrs = create_service_attributes("my-service", "1.0.0")
        assert attrs[SpanAttributes.SERVICE_NAMESPACE] == "project-chimera"


class TestCreateOperationAttributes:
    """Tests for create_operation_attributes function."""

    def test_creates_operation_name_attribute(self):
        """Verify operation name is in attributes."""
        attrs = create_operation_attributes("generate", "llm")
        assert attrs[SpanAttributes.OPERATION_NAME] == "generate"

    def test_creates_operation_type_attribute(self):
        """Verify operation type is in attributes."""
        attrs = create_operation_attributes("generate", "llm")
        assert attrs[SpanAttributes.OPERATION_TYPE] == "llm"

    def test_includes_show_id_when_provided(self):
        """Verify show_id is included when provided."""
        attrs = create_operation_attributes("generate", "llm", show_id="show-123")
        assert attrs[SpanAttributes.SHOW_ID] == "show-123"

    def test_includes_request_id_when_provided(self):
        """Verify request_id is included when provided."""
        attrs = create_operation_attributes("generate", "llm", request_id="req-456")
        assert attrs[SpanAttributes.REQUEST_ID] == "req-456"

    def test_excludes_optional_params_when_not_provided(self):
        """Verify optional params excluded when not provided."""
        attrs = create_operation_attributes("generate", "llm")
        assert SpanAttributes.SHOW_ID not in attrs
        assert SpanAttributes.REQUEST_ID not in attrs
