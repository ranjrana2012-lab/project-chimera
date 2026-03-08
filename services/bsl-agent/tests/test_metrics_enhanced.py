"""
Enhanced tests for BSL Agent Metrics module.

Tests Prometheus metrics recording and management.
"""

import pytest
from unittest.mock import patch, MagicMock
from prometheus_client import REGISTRY
from metrics import (
    translation_quality,
    words_translated,
    translation_duration,
    gloss_word_count,
    render_duration,
    gestures_rendered,
    avatar_queue_depth,
    record_translation,
    record_render,
    update_queue_depth
)


class TestMetricsDefinitions:
    """Test metrics definitions and properties"""

    def test_translation_quality_metric_exists(self):
        """Test translation quality metric is defined"""
        assert translation_quality is not None
        assert translation_quality._name == "bsl_translation_quality"
        assert translation_quality._documentation == "BSL translation accuracy and quality score"
        assert "show_id" in translation_quality._labelnames

    def test_words_translated_metric_exists(self):
        """Test words translated metric is defined"""
        assert words_translated is not None
        assert words_translated._name == "bsl_words_translated_total"
        assert "show_id" in words_translated._labelnames

    def test_translation_duration_metric_exists(self):
        """Test translation duration metric is defined"""
        assert translation_duration is not None
        assert translation_duration._name == "bsl_translation_duration_seconds"

    def test_gloss_word_count_metric_exists(self):
        """Test gloss word count metric is defined"""
        assert gloss_word_count is not None
        assert gloss_word_count._name == "bsl_gloss_word_count"

    def test_render_duration_metric_exists(self):
        """Test render duration metric is defined"""
        assert render_duration is not None
        assert render_duration._name == "bsl_avatar_render_duration_seconds"

    def test_gestures_rendered_metric_exists(self):
        """Test gestures rendered metric is defined"""
        assert gestures_rendered is not None
        assert gestures_rendered._name == "bsl_gestures_rendered_total"
        assert "show_id" in gestures_rendered._labelnames

    def test_avatar_queue_depth_metric_exists(self):
        """Test avatar queue depth metric is defined"""
        assert avatar_queue_depth is not None
        assert avatar_queue_depth._name == "bsl_avatar_queue_depth"
        assert "session_id" in avatar_queue_depth._labelnames


class TestRecordTranslation:
    """Test translation metrics recording"""

    @patch('metrics.logger')
    def test_record_translation_basic(self, mock_logger):
        """Test basic translation recording"""
        record_translation(
            show_id="test-show",
            words=10,
            duration=0.5,
            quality=0.85,
            gloss_words=8
        )
        # Should not raise an error
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_translation_with_zero_words(self, mock_logger):
        """Test recording with zero words"""
        record_translation(
            show_id="test-show",
            words=0,
            duration=0.1,
            quality=0.5,
            gloss_words=0
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_translation_with_large_numbers(self, mock_logger):
        """Test recording with large numbers"""
        record_translation(
            show_id="test-show",
            words=10000,
            duration=5.0,
            quality=0.95,
            gloss_words=8000
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_translation_edge_case_quality(self, mock_logger):
        """Test recording with edge case quality values"""
        # Quality at minimum
        record_translation(
            show_id="test-show",
            words=5,
            duration=0.3,
            quality=0.0,
            gloss_words=4
        )
        assert not mock_logger.error.called

        # Quality at maximum
        record_translation(
            show_id="test-show",
            words=5,
            duration=0.3,
            quality=1.0,
            gloss_words=4
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_translation_different_show_ids(self, mock_logger):
        """Test recording with different show IDs"""
        show_ids = ["show1", "show2", "test-show-123"]
        for show_id in show_ids:
            record_translation(
                show_id=show_id,
                words=5,
                duration=0.3,
                quality=0.8,
                gloss_words=4
            )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_translation_logs_debug(self, mock_logger):
        """Test that recording logs debug message"""
        record_translation(
            show_id="test-show",
            words=10,
            duration=0.5,
            quality=0.85,
            gloss_words=8
        )
        assert mock_logger.debug.called


class TestRecordRender:
    """Test render metrics recording"""

    @patch('metrics.logger')
    def test_record_render_basic(self, mock_logger):
        """Test basic render recording"""
        record_render(
            show_id="test-show",
            gesture_count=5,
            duration=1.0,
            session_id="session-123"
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_render_without_session_id(self, mock_logger):
        """Test recording without session ID"""
        record_render(
            show_id="test-show",
            gesture_count=5,
            duration=1.0
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_render_with_zero_gestures(self, mock_logger):
        """Test recording with zero gestures"""
        record_render(
            show_id="test-show",
            gesture_count=0,
            duration=0.1,
            session_id="session-123"
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_render_with_large_gesture_count(self, mock_logger):
        """Test recording with large gesture count"""
        record_render(
            show_id="test-show",
            gesture_count=10000,
            duration=10.0,
            session_id="session-123"
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_render_different_session_ids(self, mock_logger):
        """Test recording with different session IDs"""
        session_ids = ["session-1", "session-2", "test-session-123"]
        for session_id in session_ids:
            record_render(
                show_id="test-show",
                gesture_count=5,
                duration=1.0,
                session_id=session_id
            )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_record_render_logs_debug(self, mock_logger):
        """Test that recording logs debug message"""
        record_render(
            show_id="test-show",
            gesture_count=5,
            duration=1.0,
            session_id="session-123"
        )
        assert mock_logger.debug.called


class TestUpdateQueueDepth:
    """Test queue depth metric updates"""

    @patch('metrics.logger')
    def test_update_queue_depth_basic(self, mock_logger):
        """Test basic queue depth update"""
        update_queue_depth(session_id="session-123", depth=5)
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_update_queue_depth_zero(self, mock_logger):
        """Test updating queue depth to zero"""
        update_queue_depth(session_id="session-123", depth=0)
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_update_queue_depth_large_value(self, mock_logger):
        """Test updating queue depth with large value"""
        update_queue_depth(session_id="session-123", depth=10000)
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_update_queue_depth_different_sessions(self, mock_logger):
        """Test updating queue depth for different sessions"""
        session_ids = ["session-1", "session-2", "test-session-123"]
        for session_id in session_ids:
            update_queue_depth(session_id=session_id, depth=5)
        assert not mock_logger.error.called


class TestMetricsErrorHandling:
    """Test error handling in metrics recording"""

    @patch('metrics.words_translated.labels')
    def test_record_translation_handles_exception(self, mock_labels):
        """Test that recording handles exceptions gracefully"""
        mock_labels.side_effect = Exception("Metric error")
        # Should not raise exception
        record_translation(
            show_id="test-show",
            words=10,
            duration=0.5,
            quality=0.85,
            gloss_words=8
        )

    @patch('metrics.gestures_rendered.labels')
    def test_record_render_handles_exception(self, mock_labels):
        """Test that render recording handles exceptions gracefully"""
        mock_labels.side_effect = Exception("Metric error")
        # Should not raise exception
        record_render(
            show_id="test-show",
            gesture_count=5,
            duration=1.0,
            session_id="session-123"
        )

    @patch('metrics.avatar_queue_depth.labels')
    def test_update_queue_depth_handles_exception(self, mock_labels):
        """Test that queue depth update handles exceptions gracefully"""
        mock_labels.side_effect = Exception("Metric error")
        # Should not raise exception
        update_queue_depth(session_id="session-123", depth=5)


class TestMetricsIntegration:
    """Test integration scenarios"""

    @patch('metrics.logger')
    def test_full_translation_workflow(self, mock_logger):
        """Test metrics for full translation workflow"""
        # Simulate translation
        record_translation(
            show_id="my-show",
            words=15,
            duration=0.75,
            quality=0.9,
            gloss_words=12
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_full_render_workflow(self, mock_logger):
        """Test metrics for full render workflow"""
        # Simulate render
        record_render(
            show_id="my-show",
            gesture_count=10,
            duration=2.0,
            session_id="user-session"
        )
        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_combined_translation_and_render(self, mock_logger):
        """Test combined translation and render metrics"""
        # Translate
        record_translation(
            show_id="my-show",
            words=10,
            duration=0.5,
            quality=0.85,
            gloss_words=8
        )

        # Render
        record_render(
            show_id="my-show",
            gesture_count=8,
            duration=1.5,
            session_id="user-session"
        )

        # Update queue
        update_queue_depth(session_id="user-session", depth=0)

        assert not mock_logger.error.called

    @patch('metrics.logger')
    def test_multiple_show_metrics(self, mock_logger):
        """Test metrics for multiple shows"""
        shows = ["show1", "show2", "show3"]
        for show in shows:
            record_translation(
                show_id=show,
                words=10,
                duration=0.5,
                quality=0.85,
                gloss_words=8
            )
            record_render(
                show_id=show,
                gesture_count=8,
                duration=1.5,
                session_id=f"session-{show}"
            )
        assert not mock_logger.error.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
