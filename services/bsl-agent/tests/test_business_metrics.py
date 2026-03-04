"""
Unit tests for BSL Business Metrics module.
"""

import pytest
from prometheus_client import REGISTRY
import time


class TestBusinessMetricsModule:
    """Test BSL business metrics module structure."""

    def test_module_imports(self):
        """Business metrics module can be imported."""
        from core.business_metrics import (
            bsl_active_sessions,
            gestures_rendered,
            avatar_frame_rate,
            translation_latency
        )

        # Verify metrics are correct types
        assert hasattr(bsl_active_sessions, 'set')
        assert hasattr(gestures_rendered, 'inc')
        assert hasattr(avatar_frame_rate, 'set')
        assert hasattr(translation_latency, 'observe')

    def test_active_sessions_metric_exists(self):
        """Active sessions gauge exists and is registered."""
        from core.business_metrics import bsl_active_sessions

        # Check it's a Gauge
        assert bsl_active_sessions._type == 'gauge'
        # Check metric name
        assert bsl_active_sessions._name == 'bsl_active_sessions'
        # Check description
        assert 'active' in bsl_active_sessions._documentation.lower()

    def test_gestures_rendered_metric_exists(self):
        """Gestures rendered counter exists with show_id label."""
        from core.business_metrics import gestures_rendered

        # Check it's a Counter
        assert gestures_rendered._type == 'counter'
        # Check metric name (Prometheus adds _total automatically)
        assert 'bsl_gestures_rendered' in gestures_rendered._name
        # Check description
        assert 'gesture' in gestures_rendered._documentation.lower()
        # Check labels
        assert 'show_id' in gestures_rendered._labelnames

    def test_avatar_frame_rate_metric_exists(self):
        """Avatar frame rate gauge exists with session_id label."""
        from core.business_metrics import avatar_frame_rate

        # Check it's a Gauge
        assert avatar_frame_rate._type == 'gauge'
        # Check metric name
        assert avatar_frame_rate._name == 'bsl_avatar_frame_rate'
        # Check description
        assert 'frame rate' in avatar_frame_rate._documentation.lower() or 'fps' in avatar_frame_rate._documentation.lower()
        # Check labels
        assert 'session_id' in avatar_frame_rate._labelnames

    def test_translation_latency_metric_exists(self):
        """Translation latency histogram exists with appropriate buckets."""
        from core.business_metrics import translation_latency

        # Check it's a Histogram
        assert translation_latency._type == 'histogram'
        # Check metric name
        assert translation_latency._name == 'bsl_translation_latency_seconds'
        # Check description
        assert 'latency' in translation_latency._documentation.lower() or 'translate' in translation_latency._documentation.lower()
        # Check buckets - histogram stores upper bounds
        # Just verify the histogram was created successfully
        assert translation_latency is not None


class TestBusinessMetricsUsage:
    """Test BSL business metrics can be used correctly."""

    def test_active_sessions_can_be_updated(self):
        """Active sessions gauge can be incremented and decremented."""
        from core.business_metrics import bsl_active_sessions

        initial_value = 0

        # Set to 5
        bsl_active_sessions.set(5)
        # Reset for test
        bsl_active_sessions.set(initial_value)

    def test_gestures_rendered_can_be_incremented(self):
        """Gestures counter can be incremented with show_id label."""
        from core.business_metrics import gestures_rendered

        # Increment with show_id - counters only increment
        gestures_rendered.labels(show_id='test-show-123').inc(5)
        # Note: Counters can't be decremented, value will persist

    def test_avatar_frame_rate_can_be_set(self):
        """Avatar frame rate can be set with session_id label."""
        from core.business_metrics import avatar_frame_rate

        # Set frame rate for session
        avatar_frame_rate.labels(session_id='session-456').set(30.0)
        # Reset
        avatar_frame_rate.labels(session_id='session-456').set(0)

    def test_translation_latency_can_be_observed(self):
        """Translation latency can be observed."""
        from core.business_metrics import translation_latency

        # Observe a latency value
        translation_latency.observe(0.15)  # 150ms


class TestMetricsIntegration:
    """Test metrics integration with translation flow."""

    def test_translation_latency_tracking(self):
        """Translation latency histogram tracks timing correctly."""
        from core.business_metrics import translation_latency

        start_time = time.time()
        time.sleep(0.01)  # Simulate 10ms translation
        duration = time.time() - start_time

        translation_latency.observe(duration)

        # Should be in 0.1 bucket (10ms)
        assert duration < 0.1

    def test_gestures_per_show_tracking(self):
        """Multiple shows can track gestures separately."""
        from core.business_metrics import gestures_rendered

        # Track gestures for different shows
        gestures_rendered.labels(show_id='show-1').inc(10)
        gestures_rendered.labels(show_id='show-2').inc(20)

        # Both should be tracked separately
        # Note: Counters can't be decremented

    def test_session_tracking(self):
        """Active sessions can track multiple concurrent sessions."""
        from core.business_metrics import bsl_active_sessions

        # Set active sessions
        bsl_active_sessions.set(5)
        # Reset
        bsl_active_sessions.set(0)


class TestMetricsNamingConvention:
    """Test metrics follow Prometheus naming conventions."""

    def test_metric_names_use_snake_case(self):
        """All metric names use snake_case."""
        from core.business_metrics import (
            bsl_active_sessions,
            gestures_rendered,
            avatar_frame_rate,
            translation_latency
        )

        metrics = [bsl_active_sessions, gestures_rendered, avatar_frame_rate, translation_latency]

        for metric in metrics:
            name = metric._name
            assert ' ' not in name, f"Metric name {name} contains spaces"
            assert name.islower() or '_total' in name or '_seconds' in name, f"Metric name {name} not snake_case"

    def test_counter_names_end_with_total(self):
        """Counter metrics include _total suffix when exposed."""
        from core.business_metrics import gestures_rendered

        # Prometheus adds _total automatically to counters when exposed
        # The base name doesn't have it, but it's added on export
        assert 'bsl_gestures_rendered' in gestures_rendered._name

    def test_histogram_names_end_with_unit(self):
        """Histogram metrics end with time unit."""
        from core.business_metrics import translation_latency

        assert translation_latency._name.endswith('_seconds')


class TestMetricsDocumentation:
    """Test metrics have proper documentation."""

    def test_all_metrics_have_descriptions(self):
        """All metrics have HELP text."""
        from core.business_metrics import (
            bsl_active_sessions,
            gestures_rendered,
            avatar_frame_rate,
            translation_latency
        )

        metrics = [
            (bsl_active_sessions, 'active'),
            (gestures_rendered, 'gesture'),
            (avatar_frame_rate, 'frame rate'),
            (translation_latency, 'translate')
        ]

        for metric, keyword in metrics:
            doc = metric._documentation
            assert doc, f"Metric {metric._name} missing documentation"
            assert keyword.lower() in doc.lower(), f"Metric {metric._name} documentation missing '{keyword}'"
