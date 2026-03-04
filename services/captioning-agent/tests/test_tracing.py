"""
Tests for Captioning Agent Tracing Module

Tests verify that span emission includes caption_latency_ms attribute
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
    trace_transcription,
    trace_streaming_session,
    trace_cache_lookup,
    record_cache_result
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
        mock_setup.assert_called_once_with("captioning-agent")

    @patch('api.tracing.setup_telemetry')
    def test_get_tracer_reuses_instance(self, mock_setup):
        """Test that get_tracer reuses existing tracer instance."""
        mock_tracer = Mock()
        mock_setup.return_value = mock_tracer

        # Set global tracer
        import api.tracing
        api.tracing._tracer = mock_tracer

        result = get_tracer()

        assert result == mock_tracer
        # Should not call setup_telemetry again
        assert mock_setup.call_count == 0


class TestTranscriptionSpan:
    """Tests for transcription span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_transcription_span_created(self, mock_get_tracer):
        """Test that transcription span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_transcription(audio_size_bytes=1000, language="en"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("transcription")

    @patch('api.tracing.get_tracer')
    def test_transcription_span_has_audio_size_attribute(self, mock_get_tracer):
        """Test that transcription span includes audio.size_bytes attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_transcription(audio_size_bytes=5000):
            pass

        # Check that set_attribute was called with audio size
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "audio.size_bytes" and call[0][1] == 5000
            for call in calls
        ), "audio.size_bytes attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_transcription_span_has_language_attribute(self, mock_get_tracer):
        """Test that transcription span includes transcription.language attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_transcription(audio_size_bytes=1000, language="es"):
            pass

        # Check that set_attribute was called with language
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "transcription.language" and call[0][1] == "es"
            for call in calls
        ), "transcription.language attribute not set correctly"

    @patch('api.tracing.get_tracer')
    @patch('time.time')
    def test_transcription_span_has_caption_latency_ms(self, mock_time, mock_get_tracer):
        """Test that transcription span includes caption_latency_ms attribute (Task 21 requirement)."""
        # Mock time to return values 1 second apart
        mock_time.side_effect = [0.0, 1.0]

        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_transcription():
            pass

        # Check that set_attribute was called with caption_latency_ms
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "caption_latency_ms" and call[0][1] == 1000
            for call in calls
        ), "caption_latency_ms attribute not set correctly - Task 21 requirement not met"

    @patch('api.tracing.get_tracer')
    def test_transcription_span_records_exception(self, mock_get_tracer):
        """Test that exceptions in transcription span are recorded."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        test_error = Exception("Test error")

        try:
            with trace_transcription():
                raise test_error
        except Exception:
            pass

        # Verify exception was recorded
        mock_span.record_exception.assert_called_once_with(test_error)


class TestStreamingSessionSpan:
    """Tests for streaming session span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_streaming_span_created(self, mock_get_tracer):
        """Test that streaming session span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_streaming_session("test-session-123"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("streaming_session")

    @patch('api.tracing.get_tracer')
    def test_streaming_span_has_session_id(self, mock_get_tracer):
        """Test that streaming span includes session_id attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_streaming_session("session-abc"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "streaming.session_id" and call[0][1] == "session-abc"
            for call in calls
        ), "streaming.session_id attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_streaming_span_has_protocol(self, mock_get_tracer):
        """Test that streaming span includes protocol attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_streaming_session("session-xyz"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "streaming.protocol" and call[0][1] == "websocket"
            for call in calls
        ), "streaming.protocol attribute not set correctly"


class TestCacheLookupSpan:
    """Tests for cache lookup span creation and attributes."""

    @patch('api.tracing.get_tracer')
    def test_cache_lookup_span_created(self, mock_get_tracer):
        """Test that cache lookup span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_cache_lookup("cache-key-123"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("cache_lookup")

    @patch('api.tracing.get_tracer')
    def test_cache_lookup_span_has_key(self, mock_get_tracer):
        """Test that cache lookup span includes cache.key attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_cache_lookup("my-cache-key"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "cache.key" and call[0][1] == "my-cache-key"
            for call in calls
        ), "cache.key attribute not set correctly"

    @patch('api.tracing.get_tracer')
    def test_record_cache_result(self, mock_get_tracer):
        """Test that record_cache_result adds cache.hit attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_cache_result(mock_span, hit=True)

        mock_span.set_attribute.assert_any_call("cache.hit", True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
