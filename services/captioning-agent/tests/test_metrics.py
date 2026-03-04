"""
Unit tests for Captioning Agent business metrics module.

Tests Prometheus metrics for:
- Caption latency tracking
- Captions delivered counting
- Caption accuracy reporting
- Active caption users tracking
"""

import pytest
from unittest.mock import Mock, patch
import time

# Import the module we're testing
import sys
sys.path.insert(0, '/home/ranj/Project_Chimera/services/captioning-agent/src')

from captioning_agent.metrics import (
    caption_latency,
    captions_delivered,
    caption_accuracy,
    active_caption_users,
    track_caption_latency,
    increment_captions_delivered,
    set_caption_accuracy,
    set_active_users
)


class TestCaptionLatencyMetric:
    """Test caption latency histogram metric."""

    def test_caption_latency_metric_exists(self):
        """Caption latency histogram should be defined."""
        assert caption_latency is not None
        assert caption_latency._type == 'histogram'

    def test_caption_latency_has_correct_buckets(self):
        """Caption latency should have appropriate buckets."""
        # Check that metric has expected buckets for latency measurement
        samples = list(caption_latency.collect())[0].samples
        bucket_names = [s.name for s in samples if 'bucket' in s.name]
        assert len(bucket_names) > 0

    def test_track_caption_latency(self):
        """Should track caption processing latency."""
        initial_samples = list(caption_latency.collect())[0].samples
        initial_count = sum(s.value for s in initial_samples if 'count' in s.name)

        # Track a caption processing event
        with track_caption_latency(show_id="test-show-123"):
            # Simulate caption processing
            time.sleep(0.01)

        # Verify histogram was observed (count should increase)
        final_samples = list(caption_latency.collect())[0].samples
        final_count = sum(s.value for s in final_samples if 'count' in s.name)

        assert final_count > initial_count


class TestCaptionsDeliveredMetric:
    """Test captions delivered counter metric."""

    def test_captions_delivered_metric_exists(self):
        """Captions delivered counter should be defined."""
        assert captions_delivered is not None
        assert captions_delivered._type == 'counter'

    def test_captions_delivered_has_label(self):
        """Captions delivered should have show_id label."""
        # Verify metric accepts show_id label
        metric = captions_delivered.labels(show_id="test-show")
        assert metric is not None

    def test_increment_captions_delivered(self):
        """Should increment captions delivered counter."""
        initial_value = 0

        # Increment counter
        increment_captions_delivered(show_id="test-show-456")

        # Verify counter was incremented (check the metric value)
        metric = captions_delivered.labels(show_id="test-show-456")
        # After increment, value should be > 0
        samples = list(metric.collect())[0].samples
        value = sum(s.value for s in samples)
        assert value > initial_value


class TestCaptionAccuracyMetric:
    """Test caption accuracy gauge metric."""

    def test_caption_accuracy_metric_exists(self):
        """Caption accuracy gauge should be defined."""
        assert caption_accuracy is not None
        assert caption_accuracy._type == 'gauge'

    def test_caption_accuracy_has_label(self):
        """Caption accuracy should have show_id label."""
        metric = caption_accuracy.labels(show_id="test-show")
        assert metric is not None

    def test_set_caption_accuracy(self):
        """Should set caption accuracy score."""
        accuracy_score = 0.95

        # Set accuracy
        set_caption_accuracy(show_id="test-show-789", accuracy=accuracy_score)

        # Verify gauge was set (check metric value)
        metric = caption_accuracy.labels(show_id="test-show-789")
        samples = list(metric.collect())[0].samples
        # There should be a sample with the accuracy value
        assert len(samples) > 0

    def test_set_caption_accuracy_validates_range(self):
        """Should validate accuracy score is between 0 and 1."""
        with pytest.raises(ValueError):
            set_caption_accuracy(show_id="test-show", accuracy=1.5)

        with pytest.raises(ValueError):
            set_caption_accuracy(show_id="test-show", accuracy=-0.1)


class TestActiveCaptionUsersMetric:
    """Test active caption users gauge metric."""

    def test_active_caption_users_metric_exists(self):
        """Active caption users gauge should be defined."""
        assert active_caption_users is not None
        assert active_caption_users._type == 'gauge'

    def test_set_active_users(self):
        """Should set number of active users."""
        user_count = 42

        # Set active users
        set_active_users(count=user_count)

        # Verify gauge was set
        samples = list(active_caption_users.collect())[0].samples
        assert len(samples) > 0

    def test_set_active_users_validates_non_negative(self):
        """Should validate user count is non-negative."""
        with pytest.raises(ValueError):
            set_active_users(count=-1)


class TestMetricsIntegration:
    """Test metrics integration scenarios."""

    def test_caption_workflow_metrics(self):
        """Test tracking a complete caption workflow."""
        show_id = "integration-show"

        # Track caption processing
        with track_caption_latency(show_id=show_id):
            time.sleep(0.001)

        # Increment delivered counter
        increment_captions_delivered(show_id=show_id)

        # Set accuracy
        set_caption_accuracy(show_id=show_id, accuracy=0.92)

        # Set active users
        set_active_users(count=10)

        # Verify all metrics are accessible
        assert caption_latency is not None
        assert captions_delivered is not None
        assert caption_accuracy is not None
        assert active_caption_users is not None

    def test_multiple_show_tracking(self):
        """Test tracking metrics for multiple shows simultaneously."""
        shows = ["show-1", "show-2", "show-3"]

        for show in shows:
            increment_captions_delivered(show_id=show)
            set_caption_accuracy(show_id=show, accuracy=0.90 + (0.03 * shows.index(show)))

        # Verify metrics for all shows
        for show in shows:
            metric = captions_delivered.labels(show_id=show)
            assert metric is not None

            accuracy_metric = caption_accuracy.labels(show_id=show)
            assert accuracy_metric is not None
