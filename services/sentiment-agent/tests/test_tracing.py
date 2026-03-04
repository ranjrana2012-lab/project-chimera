"""
Tests for Sentiment Agent Tracing Module

Tests verify that span emission includes sentiment.score and audience.size attributes
as specified in Task 21 of the observability implementation plan.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from sentiment_agent.tracing import (
    get_tracer,
    trace_sentiment_analysis,
    record_sentiment_score,
    trace_emotion_detection,
    record_emotion_scores,
    trace_batch_analysis,
    trace_aggregation
)


class TestTracingInitialization:
    """Tests for tracing module initialization."""

    @patch('sentiment_agent.tracing.setup_telemetry')
    def test_get_tracer_creates_tracer(self, mock_setup):
        """Test that get_tracer creates and returns a tracer instance."""
        mock_tracer = Mock()
        mock_setup.return_value = mock_tracer

        # Reset global tracer
        import sentiment_agent.tracing
        sentiment_agent.tracing._tracer = None

        result = get_tracer()

        assert result == mock_tracer
        mock_setup.assert_called_once_with("sentiment-agent")


class TestSentimentAnalysisSpan:
    """Tests for sentiment analysis span creation and attributes (Task 21 requirements)."""

    @patch('sentiment_agent.tracing.get_tracer')
    def test_sentiment_analysis_span_created(self, mock_get_tracer):
        """Test that sentiment analysis span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_sentiment_analysis(audience_size=100):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("sentiment_analysis")

    @patch('sentiment_agent.tracing.get_tracer')
    def test_sentiment_analysis_span_has_audience_size(self, mock_get_tracer):
        """Test that sentiment analysis span includes audience.size attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_sentiment_analysis(audience_size=250):
            pass

        # Check that set_attribute was called with audience.size
        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "audience.size" and call[0][1] == 250
            for call in calls
        ), "audience.size attribute not set correctly - Task 21 requirement not met"

    @patch('sentiment_agent.tracing.get_tracer')
    def test_sentiment_analysis_span_has_text_length(self, mock_get_tracer):
        """Test that sentiment analysis span includes analysis.text_length attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_sentiment_analysis(audience_size=100, text_length=500):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "analysis.text_length" and call[0][1] == 500
            for call in calls
        ), "analysis.text_length attribute not set correctly"

    @patch('sentiment_agent.tracing.get_tracer')
    @patch('time.time')
    def test_sentiment_analysis_span_has_duration(self, mock_time, mock_get_tracer):
        """Test that sentiment analysis span includes analysis.duration_ms attribute."""
        mock_time.side_effect = [0.0, 0.3]

        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_sentiment_analysis(audience_size=50):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "analysis.duration_ms" and call[0][1] == 300
            for call in calls
        ), "analysis.duration_ms attribute not set correctly"

    @patch('sentiment_agent.tracing.get_tracer')
    def test_record_sentiment_score(self, mock_get_tracer):
        """Test that record_sentiment_score adds sentiment.score attribute (Task 21 requirement)."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_sentiment_score(mock_span, score=0.75, confidence=0.9)

        mock_span.set_attribute.assert_any_call("sentiment.score", 0.75)
        mock_span.set_attribute.assert_any_call("sentiment.confidence", 0.9)

    @patch('sentiment_agent.tracing.get_tracer')
    def test_record_sentiment_score_without_confidence(self, mock_get_tracer):
        """Test that record_sentiment_score works without confidence."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_sentiment_score(mock_span, score=-0.5)

        mock_span.set_attribute.assert_called_with("sentiment.score", -0.5)

    @patch('sentiment_agent.tracing.get_tracer')
    def test_sentiment_analysis_span_records_exception(self, mock_get_tracer):
        """Test that exceptions in sentiment analysis span are recorded."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        test_error = Exception("Sentiment analysis error")

        try:
            with trace_sentiment_analysis(audience_size=100):
                raise test_error
        except Exception:
            pass

        mock_span.record_exception.assert_called_once_with(test_error)


class TestEmotionDetectionSpan:
    """Tests for emotion detection span creation and attributes."""

    @patch('sentiment_agent.tracing.get_tracer')
    def test_emotion_detection_span_created(self, mock_get_tracer):
        """Test that emotion detection span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_emotion_detection(audience_size=150):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("emotion_detection")

    @patch('sentiment_agent.tracing.get_tracer')
    def test_emotion_detection_span_has_audience_size(self, mock_get_tracer):
        """Test that emotion detection span includes audience.size attribute."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_emotion_detection(audience_size=75):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "audience.size" and call[0][1] == 75
            for call in calls
        ), "audience.size attribute not set correctly on emotion detection"

    @patch('sentiment_agent.tracing.get_tracer')
    def test_record_emotion_scores(self, mock_get_tracer):
        """Test that record_emotion_scores adds emotion attributes."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        emotions = {
            "joy": 0.8,
            "surprise": 0.3,
            "neutral": 0.5,
            "sadness": 0.1,
            "anger": 0.0,
            "fear": 0.2
        }

        record_emotion_scores(mock_span, emotions)

        # Verify all emotions were recorded
        mock_span.set_attribute.assert_any_call("emotion.joy", 0.8)
        mock_span.set_attribute.assert_any_call("emotion.surprise", 0.3)
        mock_span.set_attribute.assert_any_call("emotion.neutral", 0.5)
        mock_span.set_attribute.assert_any_call("emotion.sadness", 0.1)
        mock_span.set_attribute.assert_any_call("emotion.anger", 0.0)
        mock_span.set_attribute.assert_any_call("emotion.fear", 0.2)

    @patch('sentiment_agent.tracing.get_tracer')
    def test_record_emotion_scores_records_dominant(self, mock_get_tracer):
        """Test that record_emotion_scores records dominant emotion."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        emotions = {
            "joy": 0.9,
            "surprise": 0.4,
            "neutral": 0.3
        }

        record_emotion_scores(mock_span, emotions)

        mock_span.set_attribute.assert_any_call("emotion.dominant", "joy")

    @patch('sentiment_agent.tracing.get_tracer')
    def test_record_emotion_scores_with_empty_dict(self, mock_get_tracer):
        """Test that record_emotion_scores handles empty dictionary."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_get_tracer.return_value = mock_tracer

        record_emotion_scores(mock_span, {})

        # Should not set dominant emotion for empty dict
        assert not any(
            call[0][0] == "emotion.dominant"
            for call in mock_span.set_attribute.call_args_list
        )


class TestBatchAnalysisSpan:
    """Tests for batch sentiment analysis span creation and attributes."""

    @patch('sentiment_agent.tracing.get_tracer')
    def test_batch_analysis_span_created(self, mock_get_tracer):
        """Test that batch analysis span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_batch_analysis(audience_size=200, text_count=10):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("batch_sentiment_analysis")

    @patch('sentiment_agent.tracing.get_tracer')
    def test_batch_analysis_span_has_attributes(self, mock_get_tracer):
        """Test that batch analysis span includes required attributes."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_batch_analysis(audience_size=300, text_count=20):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "audience.size" and call[0][1] == 300
            for call in calls
        ), "audience.size attribute not set on batch analysis"

        assert any(
            call[0][0] == "batch.text_count" and call[0][1] == 20
            for call in calls
        ), "batch.text_count attribute not set correctly"


class TestAggregationSpan:
    """Tests for sentiment aggregation span creation and attributes."""

    @patch('sentiment_agent.tracing.get_tracer')
    def test_aggregation_span_created(self, mock_get_tracer):
        """Test that aggregation span is created with correct name."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_aggregation(show_id="show-123", time_window="5m"):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("sentiment_aggregation")

    @patch('sentiment_agent.tracing.get_tracer')
    def test_aggregation_span_has_attributes(self, mock_get_tracer):
        """Test that aggregation span includes required attributes."""
        mock_tracer = Mock()
        mock_span = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        with trace_aggregation(show_id="show-456", time_window="1h"):
            pass

        calls = mock_span.set_attribute.call_args_list
        assert any(
            call[0][0] == "show_id" and call[0][1] == "show-456"
            for call in calls
        ), "show_id attribute not set correctly"

        assert any(
            call[0][0] == "aggregation.time_window" and call[0][1] == "1h"
            for call in calls
        ), "aggregation.time_window attribute not set correctly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
