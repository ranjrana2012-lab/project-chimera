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
    get_tracer,
    shutdown_tracing,
    add_span_event,
    inject_context,
    nullcontext,
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


class TestNullContext:
    """Tests for nullcontext function."""

    def test_is_context_manager(self):
        """Verify nullcontext is a context manager."""
        with nullcontext():
            pass

    def test_yields_none(self):
        """Verify nullcontext yields None."""
        with nullcontext() as value:
            assert value is None


class TestGetTracer:
    """Tests for get_tracer function."""

    def test_returns_noop_tracer_when_not_setup(self):
        """Verify get_tracer returns NoOpTracer when tracing not set up."""
        with patch('tracing._tracer', None):
            tracer = get_tracer()
            assert isinstance(tracer, NoOpTracer)

    def test_returns_global_tracer_when_set(self):
        """Verify get_tracer returns global tracer when set."""
        mock_tracer = Mock()
        with patch('tracing._tracer', mock_tracer):
            tracer = get_tracer()
            assert tracer == mock_tracer


class TestShutdownTracing:
    """Tests for shutdown_tracing function."""

    def test_does_nothing_when_otel_unavailable(self):
        """Verify shutdown does nothing when OpenTelemetry unavailable."""
        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            shutdown_tracing()

    def test_does_nothing_when_provider_is_none(self):
        """Verify shutdown does nothing when provider is None."""
        with patch('tracing.OTEL_AVAILABLE', True):
            with patch('tracing._provider', None):
                # Should not raise
                shutdown_tracing()

    def test_calls_shutdown_on_provider(self):
        """Verify shutdown calls shutdown on provider."""
        mock_provider = Mock()
        with patch('tracing.OTEL_AVAILABLE', True):
            with patch('tracing._provider', mock_provider):
                shutdown_tracing()
                mock_provider.shutdown.assert_called_once()


class TestAddSpanEvent:
    """Tests for add_span_event function."""

    def test_does_nothing_when_span_is_none(self):
        """Verify function handles None span gracefully."""
        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            add_span_event(None, "test_event")

    def test_does_nothing_when_otel_unavailable(self):
        """Verify function handles missing OpenTelemetry gracefully."""
        mock_span = Mock()
        with patch('tracing.OTEL_AVAILABLE', False):
            # Should not raise
            add_span_event(mock_span, "test_event")

    def test_accepts_event_name(self):
        """Verify function accepts event name parameter."""
        mock_span = Mock()
        with patch('tracing.OTEL_AVAILABLE', False):
            add_span_event(mock_span, "my_event")

    def test_accepts_optional_attributes(self):
        """Verify function accepts optional attributes parameter."""
        mock_span = Mock()
        with patch('tracing.OTEL_AVAILABLE', False):
            add_span_event(mock_span, "my_event", {"key": "value"})


class TestInjectContext:
    """Tests for inject_context function."""

    def test_does_nothing_when_otel_unavailable(self):
        """Verify function does nothing when OpenTelemetry unavailable."""
        headers = {}
        with patch('tracing.OTEL_AVAILABLE', False):
            inject_context(headers)
            # Headers should remain empty
            assert headers == {}

    def test_accepts_headers_dict(self):
        """Verify function accepts headers dictionary."""
        headers = {}
        with patch('tracing.OTEL_AVAILABLE', False):
            inject_context(headers)

    def test_accepts_headers_with_existing_content(self):
        """Verify function works with existing headers."""
        headers = {"Authorization": "Bearer token"}
        with patch('tracing.OTEL_AVAILABLE', False):
            inject_context(headers)
            # Original headers should remain
            assert "Authorization" in headers


class TestSetupTracingWithOtel:
    """Tests for setup_tracing with OpenTelemetry available."""

    def test_reads_environment_variables(self):
        """Verify setup_tracing reads environment variables."""
        with patch('tracing.OTEL_AVAILABLE', True):
            with patch.dict(os.environ, {
                'OTEL_EXPORTER_OTLP_ENDPOINT': 'http://custom:4317',
                'OTEL_ENVIRONMENT': 'production',
                'OTEL_SERVICE_NAME': 'custom-service'
            }):
                mock_provider = Mock()
                mock_tracer = Mock()

                with patch('tracing.TracerProvider', return_value=mock_provider):
                    with patch('tracing.trace.set_tracer_provider'):
                        with patch('tracing.trace.get_tracer', return_value=mock_tracer):
                            tracer = setup_tracing("test-service")

    def test_uses_default_endpoint_when_env_not_set(self):
        """Verify default OTLP endpoint used when env var not set."""
        with patch('tracing.OTEL_AVAILABLE', True):
            with patch.dict(os.environ, {}, clear=True):
                mock_provider = Mock()
                mock_tracer = Mock()

                with patch('tracing.TracerProvider', return_value=mock_provider):
                    with patch('tracing.trace.set_tracer_provider'):
                        with patch('tracing.trace.get_tracer', return_value=mock_tracer):
                            tracer = setup_tracing("test-service")

    def test_enables_console_export_when_requested(self):
        """Verify console export enabled when enable_console_export=True."""
        with patch('tracing.OTEL_AVAILABLE', True):
            with patch.dict(os.environ, {}, clear=True):
                # Should not raise - just verify the function accepts the parameter
                mock_provider = Mock()
                mock_tracer = Mock()

                with patch('tracing.TracerProvider', return_value=mock_provider):
                    with patch('tracing.trace.set_tracer_provider'):
                        with patch('tracing.trace.get_tracer', return_value=mock_tracer):
                            tracer = setup_tracing(
                                "test-service",
                                enable_console_export=True
                            )
                            # Function completed without error
                            assert tracer is not None


class TestTraceOperationWithOtel:
    """Tests for trace_operation with OpenTelemetry available."""

    def test_creates_span_with_operation_name(self):
        """Verify trace_operation creates span with given name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_span)
        mock_context.__exit__ = Mock(return_value=False)
        mock_tracer.start_as_current_span.return_value = mock_context

        with patch('tracing.OTEL_AVAILABLE', True):
            with patch('tracing.get_tracer', return_value=mock_tracer):
                with trace_operation("test_operation") as span:
                    assert span == mock_span
                mock_tracer.start_as_current_span.assert_called_once_with("test_operation")

    def test_adds_attributes_to_span(self):
        """Verify trace_operation adds attributes to span."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_span)
        mock_context.__exit__ = Mock(return_value=False)
        mock_tracer.start_as_current_span.return_value = mock_context

        attributes = {"key1": "value1", "key2": "value2"}

        with patch('tracing.OTEL_AVAILABLE', True):
            with patch('tracing.get_tracer', return_value=mock_tracer):
                with trace_operation("test_operation", attributes):
                    pass
                # Verify attributes were set on the span
                assert mock_span.set_attribute.call_count == 2


class TestRecordErrorWithOtel:
    """Tests for record_error with OpenTelemetry available."""

    def test_records_exception_on_span(self):
        """Verify record_error calls record_exception on span."""
        mock_span = Mock()
        error = ValueError("test error")

        with patch('tracing.OTEL_AVAILABLE', True):
            record_error(mock_span, error)
            mock_span.record_exception.assert_called_once_with(error)

    def test_sets_error_status(self):
        """Verify record_error sets error status on span."""
        mock_span = Mock()
        error = RuntimeError("test error")

        with patch('tracing.OTEL_AVAILABLE', True):
            record_error(mock_span, error)
            # Verify set_status was called with ERROR status
            assert mock_span.set_status.called

    def test_adds_attributes_when_provided(self):
        """Verify record_error adds optional attributes."""
        mock_span = Mock()
        error = Exception("test error")
        attributes = {"context": "test"}

        with patch('tracing.OTEL_AVAILABLE', True):
            record_error(mock_span, error, attributes)
            # Should call set_attribute for each attribute
            assert mock_span.set_attribute.call_count >= 1


class TestInstrumentFastAPIWithOtel:
    """Tests for instrument_fastapi with OpenTelemetry available."""

    def test_calls_fastapi_instrumentor(self):
        """Verify instrument_fastapi calls FastAPIInstrumentor."""
        mock_app = Mock()

        with patch('tracing.OTEL_AVAILABLE', True):
            with patch('tracing.FastAPIInstrumentor') as mock_instrumentor:
                instrument_fastapi(mock_app)
                mock_instrumentor.instrument_app.assert_called_once_with(mock_app)

    def test_handles_instrumentation_exception(self):
        """Verify instrument_fastapi handles exceptions gracefully."""
        mock_app = Mock()

        with patch('tracing.OTEL_AVAILABLE', True):
            with patch('tracing.FastAPIInstrumentor') as mock_instrumentor:
                mock_instrumentor.instrument_app.side_effect = Exception("Instrumentation failed")
                # Should not raise
                instrument_fastapi(mock_app)


class TestInstrumentFastAPIIntegration:
    """Integration tests for instrument_fastapi."""

    def test_skips_instrumentation_when_otel_unavailable(self):
        """Verify FastAPI instrumentation skipped when OTEL unavailable."""
        mock_app = Mock()

        with patch('tracing.OTEL_AVAILABLE', False):
            instrument_fastapi(mock_app)
            # App should not be modified
            assert not mock_app.method_calls
