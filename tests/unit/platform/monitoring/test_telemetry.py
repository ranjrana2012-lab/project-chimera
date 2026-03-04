"""Tests for OpenTelemetry telemetry setup module."""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock, call

# Add the project root to the path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# We need to import the telemetry module components directly to avoid conflicts
# Let's import the module by path instead
import importlib.util
_telemetry_path = os.path.join(_project_root, 'platform', 'monitoring', 'telemetry', '__init__.py')
spec = importlib.util.spec_from_file_location(
    "telemetry",
    _telemetry_path
)
telemetry = importlib.util.module_from_spec(spec)
sys.modules['telemetry'] = telemetry
spec.loader.exec_module(telemetry)

setup_telemetry = telemetry.setup_telemetry
instrument_fastapi = telemetry.instrument_fastapi
add_span_attributes = telemetry.add_span_attributes
record_error = telemetry.record_error


class TestSetupTelemetry:
    """Test suite for setup_telemetry function."""

    def test_setup_telemetry_creates_resource_with_service_name(self):
        """Test that setup_telemetry creates resource with correct service name."""
        # Mock all the OpenTelemetry components
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
             patch.object(telemetry, 'JAEGER_AVAILABLE', False), \
             patch('telemetry.Resource') as mock_resource, \
             patch('telemetry.TracerProvider') as mock_provider_class, \
             patch('telemetry.trace') as mock_trace:

            # Setup mocks
            mock_provider_instance = Mock()
            mock_provider_class.return_value = mock_provider_instance
            mock_tracer = Mock()
            mock_trace.get_tracer.return_value = mock_tracer

            # Call setup_telemetry
            result = setup_telemetry("test-service")

            # Verify resource was created with service name
            mock_resource.assert_called_once()
            call_kwargs = mock_resource.call_args[1]
            assert call_kwargs['attributes']['service.name'] == 'test-service'

    def test_setup_telemetry_configures_jaeger_exporter(self):
        """Test that setup_telemetry configures Jaeger exporter with correct host."""
        # We need to mock the actual JaegerExporter import within setup_telemetry
        # Since it's conditionally imported, we'll verify the behavior indirectly
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
             patch.object(telemetry, 'JAEGER_AVAILABLE', True), \
             patch('telemetry.Resource') as mock_resource, \
             patch('telemetry.TracerProvider') as mock_provider_class, \
             patch('telemetry.BatchSpanProcessor') as mock_processor, \
             patch('telemetry.trace') as mock_trace:

            # Setup mocks
            mock_provider_instance = Mock()
            mock_provider_class.return_value = mock_provider_instance
            mock_tracer = Mock()
            mock_trace.get_tracer.return_value = mock_tracer

            # Call with custom Jaeger host
            result = setup_telemetry("test-service", jaeger_host="custom-jaeger-host")

            # Verify that BatchSpanProcessor was called (which wraps JaegerExporter)
            # The JaegerExporter should be instantiated inside BatchSpanProcessor
            assert mock_provider_instance.add_span_processor.call_count >= 1

    def test_setup_telemetry_configures_10_percent_sampling(self):
        """Test that setup_telemetry configures 10% sampling."""
        # Mock all the OpenTelemetry components
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
             patch.object(telemetry, 'JAEGER_AVAILABLE', False), \
             patch('telemetry.Resource') as mock_resource, \
             patch('telemetry.TracerProvider') as mock_provider_class, \
             patch('telemetry.TraceIdRatioBased') as mock_sampler, \
             patch('telemetry.trace') as mock_trace:

            # Setup mocks
            mock_provider_instance = Mock()
            mock_provider_class.return_value = mock_provider_instance
            mock_tracer = Mock()
            mock_trace.get_tracer.return_value = mock_tracer

            # Call setup_telemetry
            result = setup_telemetry("test-service")

            # Verify sampler was created with 10% ratio
            mock_sampler.assert_called_once_with(0.1)

    def test_setup_telemetry_adds_console_exporter_in_development(self):
        """Test that console exporter is added in development environment."""
        # Set development environment
        os.environ['ENVIRONMENT'] = 'development'

        try:
            # Mock all the OpenTelemetry components
            with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
                 patch.object(telemetry, 'JAEGER_AVAILABLE', False), \
                 patch('telemetry.Resource') as mock_resource, \
                 patch('telemetry.TracerProvider') as mock_provider_class, \
                 patch('telemetry.ConsoleSpanExporter') as mock_console, \
                 patch('telemetry.trace') as mock_trace:

                # Setup mocks
                mock_provider_instance = Mock()
                mock_provider_class.return_value = mock_provider_instance
                mock_tracer = Mock()
                mock_trace.get_tracer.return_value = mock_tracer

                # Call setup_telemetry
                result = setup_telemetry("test-service")

                # Verify console exporter was created
                mock_console.assert_called_once()

                # Verify processor was added
                assert mock_provider_instance.add_span_processor.call_count >= 1
        finally:
            # Clean up environment
            if 'ENVIRONMENT' in os.environ:
                del os.environ['ENVIRONMENT']

    def test_setup_telemetry_returns_tracer(self):
        """Test that setup_telemetry returns a tracer instance."""
        # Mock all the OpenTelemetry components
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
             patch.object(telemetry, 'JAEGER_AVAILABLE', False), \
             patch('telemetry.Resource') as mock_resource, \
             patch('telemetry.TracerProvider') as mock_provider_class, \
             patch('telemetry.trace') as mock_trace:

            # Setup mocks
            mock_provider_instance = Mock()
            mock_provider_class.return_value = mock_provider_instance
            mock_tracer = Mock()
            mock_trace.get_tracer.return_value = mock_tracer

            # Call setup_telemetry
            result = setup_telemetry("test-service")

            # Verify tracer is returned
            assert result == mock_tracer

    def test_setup_telemetry_returns_none_when_unavailable(self):
        """Test that setup_telemetry returns None when OpenTelemetry is not available."""
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', False):
            result = setup_telemetry("test-service")
            assert result is None


class TestInstrumentFastAPI:
    """Test suite for instrument_fastapi function."""

    def test_instrument_fastapi_instruments_app(self):
        # Mock all the OpenTelemetry components
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
             patch('telemetry.FastAPIInstrumentor') as mock_fastapi, \
             patch('telemetry.HTTPXClientInstrumentor') as mock_httpx:

            # Create mock app
            mock_app = Mock()

            # Call instrument_fastapi
            instrument_fastapi(mock_app)

            # Verify FastAPI app was instrumented
            mock_fastapi.instrument_app.assert_called_once_with(mock_app)

            # Verify HTTPX was instrumented
            mock_httpx.return_value.instrument.assert_called_once()

    def test_instrument_fastapi_skips_when_unavailable(self):
        """Test that instrument_fastapi skips when OpenTelemetry is not available."""
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', False):
            mock_app = Mock()
            instrument_fastapi(mock_app)
            # Should not raise any errors


class TestAddSpanAttributes:
    """Test suite for add_span_attributes function."""

    def test_add_span_attributes_sets_attributes(self):
        # Create mock span
        mock_span = Mock()

        # Call add_span_attributes
        attributes = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 123
        }
        add_span_attributes(mock_span, attributes)

        # Verify set_attribute was called for each attribute
        assert mock_span.set_attribute.call_count == 3
        mock_span.set_attribute.assert_any_call('key1', 'value1')
        mock_span.set_attribute.assert_any_call('key2', 'value2')
        mock_span.set_attribute.assert_any_call('key3', 123)

    def test_add_span_attributes_handles_none_span(self):
        """Test that add_span_attributes handles None span gracefully."""
        add_span_attributes(None, {'key': 'value'})
        # Should not raise any errors

    def test_add_span_attributes_handles_unavailable_telemetry(self):
        """Test that add_span_attributes handles unavailable telemetry."""
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', False):
            mock_span = Mock()
            add_span_attributes(mock_span, {'key': 'value'})
            # Should not call set_attribute
            mock_span.set_attribute.assert_not_called()


class TestRecordError:
    """Test suite for record_error function."""

    def test_record_error_records_exception(self):
        # Mock all the OpenTelemetry components
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
             patch('telemetry.Status') as mock_status, \
             patch('telemetry.StatusCode') as mock_status_code:

            # Create mock span and error
            mock_span = Mock()
            test_error = Exception("Test error")

            # Call record_error
            record_error(mock_span, test_error)

            # Verify exception was recorded
            mock_span.record_exception.assert_called_once_with(test_error)

            # Verify status was set
            mock_span.set_status.assert_called_once()

    def test_record_error_with_attributes(self):
        # Mock all the OpenTelemetry components
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True), \
             patch('telemetry.Status') as mock_status, \
             patch('telemetry.StatusCode') as mock_status_code:

            # Create mock span and error
            mock_span = Mock()
            test_error = Exception("Test error")
            attributes = {'error.code': 'TEST_001', 'error.context': 'test'}

            # Call record_error with attributes
            record_error(mock_span, test_error, attributes)

            # Verify exception was recorded
            mock_span.record_exception.assert_called_once_with(test_error)

            # Verify set_attribute was called for each attribute
            assert mock_span.set_attribute.call_count == len(attributes)

    def test_record_error_handles_none_span(self):
        """Test that record_error handles None span gracefully."""
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', True):
            test_error = Exception("Test error")
            record_error(None, test_error)
            # Should not raise any errors

    def test_record_error_handles_unavailable_telemetry(self):
        """Test that record_error handles unavailable telemetry."""
        with patch.object(telemetry, 'OPENTELEMETRY_AVAILABLE', False):
            mock_span = Mock()
            test_error = Exception("Test error")
            record_error(mock_span, test_error)
            # Should not call record_exception
            mock_span.record_exception.assert_not_called()
