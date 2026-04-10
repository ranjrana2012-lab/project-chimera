"""Tests for shared tracing module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.shared.tracing import (
    NoOpTracer,
    NoOpSpan,
    setup_telemetry,
    instrument_fastapi,
    add_span_attributes,
    record_error,
)


class TestNoOpSpan:
    """Test NoOpSpan class."""

    def test_noop_span_context_manager(self):
        """Test NoOpSpan supports context manager protocol."""
        span = NoOpSpan()
        with span:
            pass  # Should not raise

    def test_noop_span_methods(self):
        """Test NoOpSpan methods do nothing."""
        span = NoOpSpan()

        # All these should do nothing without raising
        span.set_attribute("key", "value")
        span.set_attributes({"key": "value"})
        span.record_exception(Exception("test"))
        span.set_status("status")
        span.add_event("event")
        span.end()


class TestNoOpTracer:
    """Test NoOpTracer class."""

    def test_noop_tracer_creates_span(self):
        """Test NoOpTracer creates NoOpSpan."""
        tracer = NoOpTracer()
        span = tracer.start_as_current_span("test")
        assert isinstance(span, NoOpSpan)

    def test_noop_tracer_span_context_manager(self):
        """Test NoOpTracer span supports context manager."""
        tracer = NoOpTracer()
        with tracer.start_as_current_span("test") as span:
            assert isinstance(span, NoOpSpan)


class TestSetupTelemetry:
    """Test setup_telemetry function."""

    def test_setup_telemetry_without_opentelemetry(self):
        """Test setup_telemetry returns NoOpTracer when OpenTelemetry unavailable."""
        with patch('services.shared.tracing.OPENTELEMETRY_AVAILABLE', False):
            tracer = setup_telemetry("test-service")
            assert isinstance(tracer, NoOpTracer)

    def test_setup_telemetry_service_name(self):
        """Test service_name is passed correctly."""
        with patch('services.shared.tracing.OPENTELEMETRY_AVAILABLE', False):
            tracer = setup_telemetry("my-service")
            assert tracer._name == "NoOpTracer"


class TestInstrumentFastAPI:
    """Test instrument_fastapi function."""

    def test_instrument_fastapi_without_opentelemetry(self):
        """Test instrument_fastapi does nothing without OpenTelemetry."""
        mock_app = Mock()
        with patch('services.shared.tracing.OPENTELEMETRY_AVAILABLE', False):
            instrument_fastapi(mock_app)
            # Should return without doing anything
            assert mock_app.call_count == 0


class TestAddSpanAttributes:
    """Test add_span_attributes function."""

    def test_add_span_attributes_with_none_span(self):
        """Test add_span_attributes handles None span gracefully."""
        # Should not raise
        add_span_attributes(None, {"key": "value"})

    def test_add_span_attributes_with_noop_span(self):
        """Test add_span_attributes with NoOpSpan."""
        span = NoOpSpan()
        # Should not raise
        add_span_attributes(span, {"key1": "value1", "key2": "value2"})

    def test_add_span_attributes_filters_none_values(self):
        """Test add_span_attributes filters None values."""
        span = NoOpSpan()
        # Should not raise even with None values
        add_span_attributes(span, {"key1": "value1", "key2": None})


class TestRecordError:
    """Test record_error function."""

    def test_record_error_with_none_span(self):
        """Test record_error handles None span gracefully."""
        error = Exception("test error")
        # Should not raise
        record_error(None, error)

    def test_record_error_with_noop_span(self):
        """Test record_error with NoOpSpan."""
        span = NoOpSpan()
        error = Exception("test error")
        # Should not raise
        record_error(span, error)

    def test_record_error_with_attributes(self):
        """Test record_error with additional attributes."""
        span = NoOpSpan()
        error = Exception("test error")
        # Should not raise
        record_error(span, error, {"context": "test"})
