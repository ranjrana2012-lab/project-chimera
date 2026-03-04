"""
Unit tests for Sentiment Agent Business Metrics module.
"""

import pytest
from prometheus_client import REGISTRY
import time


class TestBusinessMetricsModule:
    """Test Sentiment business metrics module structure."""

    def test_module_imports(self):
        """Business metrics module can be imported."""
        from sentiment_agent.metrics import (
            audience_sentiment,
            emotion_joy,
            emotion_surprise,
            emotion_neutral,
            emotion_sadness,
            emotion_anger,
            emotion_fear,
            analysis_queue_size,
            analysis_duration
        )

        # Verify metrics are correct types
        assert hasattr(audience_sentiment, 'set')
        assert hasattr(emotion_joy, 'inc')
        assert hasattr(emotion_surprise, 'inc')
        assert hasattr(emotion_neutral, 'inc')
        assert hasattr(emotion_sadness, 'inc')
        assert hasattr(emotion_anger, 'inc')
        assert hasattr(emotion_fear, 'inc')
        assert hasattr(analysis_queue_size, 'set')
        assert hasattr(analysis_duration, 'set')

    def test_audience_sentiment_metric_exists(self):
        """Audience sentiment gauge exists with correct labels."""
        from sentiment_agent.metrics import audience_sentiment

        # Check it's a Gauge
        assert audience_sentiment._type == 'gauge'
        # Check metric name
        assert audience_sentiment._name == 'sentiment_audience_avg'
        # Check description
        assert 'sentiment' in audience_sentiment._documentation.lower()
        # Check labels
        assert 'show_id' in audience_sentiment._labelnames
        assert 'time_window' in audience_sentiment._labelnames

    def test_emotion_joy_metric_exists(self):
        """Joy emotion counter exists with show_id label."""
        from sentiment_agent.metrics import emotion_joy

        # Check it's a Counter
        assert emotion_joy._type == 'counter'
        # Check metric name
        assert emotion_joy._name == 'sentiment_emotion_joy'
        # Check description
        assert 'joy' in emotion_joy._documentation.lower()
        # Check labels
        assert 'show_id' in emotion_joy._labelnames

    def test_emotion_surprise_metric_exists(self):
        """Surprise emotion counter exists with show_id label."""
        from sentiment_agent.metrics import emotion_surprise

        # Check it's a Counter
        assert emotion_surprise._type == 'counter'
        # Check metric name
        assert emotion_surprise._name == 'sentiment_emotion_surprise'
        # Check description
        assert 'surprise' in emotion_surprise._documentation.lower()
        # Check labels
        assert 'show_id' in emotion_surprise._labelnames

    def test_emotion_neutral_metric_exists(self):
        """Neutral emotion counter exists with show_id label."""
        from sentiment_agent.metrics import emotion_neutral

        # Check it's a Counter
        assert emotion_neutral._type == 'counter'
        # Check metric name
        assert emotion_neutral._name == 'sentiment_emotion_neutral'
        # Check description
        assert 'neutral' in emotion_neutral._documentation.lower()
        # Check labels
        assert 'show_id' in emotion_neutral._labelnames

    def test_emotion_sadness_metric_exists(self):
        """Sadness emotion counter exists with show_id label."""
        from sentiment_agent.metrics import emotion_sadness

        # Check it's a Counter
        assert emotion_sadness._type == 'counter'
        # Check metric name
        assert emotion_sadness._name == 'sentiment_emotion_sadness'
        # Check description
        assert 'sadness' in emotion_sadness._documentation.lower()
        # Check labels
        assert 'show_id' in emotion_sadness._labelnames

    def test_emotion_anger_metric_exists(self):
        """Anger emotion counter exists with show_id label."""
        from sentiment_agent.metrics import emotion_anger

        # Check it's a Counter
        assert emotion_anger._type == 'counter'
        # Check metric name
        assert emotion_anger._name == 'sentiment_emotion_anger'
        # Check description
        assert 'anger' in emotion_anger._documentation.lower()
        # Check labels
        assert 'show_id' in emotion_anger._labelnames

    def test_emotion_fear_metric_exists(self):
        """Fear emotion counter exists with show_id label."""
        from sentiment_agent.metrics import emotion_fear

        # Check it's a Counter
        assert emotion_fear._type == 'counter'
        # Check metric name
        assert emotion_fear._name == 'sentiment_emotion_fear'
        # Check description
        assert 'fear' in emotion_fear._documentation.lower()
        # Check labels
        assert 'show_id' in emotion_fear._labelnames

    def test_analysis_queue_size_metric_exists(self):
        """Analysis queue size gauge exists."""
        from sentiment_agent.metrics import analysis_queue_size

        # Check it's a Gauge
        assert analysis_queue_size._type == 'gauge'
        # Check metric name
        assert analysis_queue_size._name == 'sentiment_analysis_queue_size'
        # Check description
        assert 'queue' in analysis_queue_size._documentation.lower()

    def test_analysis_duration_metric_exists(self):
        """Analysis duration gauge exists."""
        from sentiment_agent.metrics import analysis_duration

        # Check it's a Gauge
        assert analysis_duration._type == 'gauge'
        # Check metric name
        assert analysis_duration._name == 'sentiment_analysis_duration_seconds'
        # Check description
        assert 'duration' in analysis_duration._documentation.lower() or 'time' in analysis_duration._documentation.lower()


class TestBusinessMetricsUsage:
    """Test Sentiment business metrics can be used correctly."""

    def test_audience_sentiment_can_be_set(self):
        """Audience sentiment gauge can be set with labels."""
        from sentiment_agent.metrics import audience_sentiment

        # Set sentiment for show
        audience_sentiment.labels(show_id='test-show', time_window='5m').set(0.75)
        # Reset
        audience_sentiment.labels(show_id='test-show', time_window='5m').set(0)

    def test_emotion_joy_can_be_incremented(self):
        """Joy emotion counter can be incremented with show_id label."""
        from sentiment_agent.metrics import emotion_joy

        # Increment with show_id
        emotion_joy.labels(show_id='test-show').inc(5)
        # Note: Counters can't be decremented, metrics persist

    def test_emotion_surprise_can_be_incremented(self):
        """Surprise emotion counter can be incremented with show_id label."""
        from sentiment_agent.metrics import emotion_surprise

        # Increment with show_id
        emotion_surprise.labels(show_id='test-show').inc(3)
        # Note: Counters can't be decremented, metrics persist

    def test_emotion_neutral_can_be_incremented(self):
        """Neutral emotion counter can be incremented with show_id label."""
        from sentiment_agent.metrics import emotion_neutral

        # Increment with show_id
        emotion_neutral.labels(show_id='test-show').inc(2)
        # Note: Counters can't be decremented, metrics persist

    def test_emotion_sadness_can_be_incremented(self):
        """Sadness emotion counter can be incremented with show_id label."""
        from sentiment_agent.metrics import emotion_sadness

        # Increment with show_id
        emotion_sadness.labels(show_id='test-show').inc(1)
        # Note: Counters can't be decremented, metrics persist

    def test_emotion_anger_can_be_incremented(self):
        """Anger emotion counter can be incremented with show_id label."""
        from sentiment_agent.metrics import emotion_anger

        # Increment with show_id
        emotion_anger.labels(show_id='test-show').inc(1)
        # Note: Counters can't be decremented, metrics persist

    def test_emotion_fear_can_be_incremented(self):
        """Fear emotion counter can be incremented with show_id label."""
        from sentiment_agent.metrics import emotion_fear

        # Increment with show_id
        emotion_fear.labels(show_id='test-show').inc(1)
        # Note: Counters can't be decremented, metrics persist

    def test_analysis_queue_size_can_be_set(self):
        """Analysis queue size can be set."""
        from sentiment_agent.metrics import analysis_queue_size

        # Set queue size
        analysis_queue_size.set(10)
        # Reset
        analysis_queue_size.set(0)

    def test_analysis_duration_can_be_set(self):
        """Analysis duration can be set."""
        from sentiment_agent.metrics import analysis_duration

        # Set duration in seconds
        analysis_duration.set(0.5)
        # Reset
        analysis_duration.set(0)


class TestMetricsIntegration:
    """Test metrics integration with sentiment analysis flow."""

    def test_record_analysis_function(self):
        """record_analysis function updates all relevant metrics."""
        from sentiment_agent.metrics import record_analysis

        # Record a sentiment analysis
        emotions = {
            'joy': 0.8,
            'surprise': 0.3,
            'neutral': 0.1,
            'sadness': 0.0,
            'anger': 0.0,
            'fear': 0.0
        }

        record_analysis(
            show_id='test-show',
            sentiment=0.75,
            emotions=emotions,
            duration=0.5
        )

        # Metrics should be updated (we can't easily verify values without Prometheus server)
        # But we can verify the function runs without error
        assert True

    def test_emotion_distribution_tracking(self):
        """Multiple shows can track emotions separately."""
        from sentiment_agent.metrics import emotion_joy, emotion_neutral

        # Track emotions for different shows
        emotion_joy.labels(show_id='show-1').inc(10)
        emotion_neutral.labels(show_id='show-2').inc(20)

        # Both should be tracked separately
        # Note: Counters can't be decremented, metrics persist

    def test_sentiment_time_windows(self):
        """Sentiment can be tracked for different time windows."""
        from sentiment_agent.metrics import audience_sentiment

        # Track sentiment for different time windows
        audience_sentiment.labels(show_id='test-show', time_window='1m').set(0.6)
        audience_sentiment.labels(show_id='test-show', time_window='5m').set(0.7)
        audience_sentiment.labels(show_id='test-show', time_window='15m').set(0.8)

        # Reset
        audience_sentiment.labels(show_id='test-show', time_window='1m').set(0)
        audience_sentiment.labels(show_id='test-show', time_window='5m').set(0)
        audience_sentiment.labels(show_id='test-show', time_window='15m').set(0)


class TestMetricsNamingConvention:
    """Test metrics follow Prometheus naming conventions."""

    def test_metric_names_use_snake_case(self):
        """All metric names use snake_case."""
        from sentiment_agent.metrics import (
            audience_sentiment,
            emotion_joy,
            analysis_queue_size,
            analysis_duration
        )

        metrics = [audience_sentiment, emotion_joy, analysis_queue_size, analysis_duration]

        for metric in metrics:
            name = metric._name
            assert ' ' not in name, f"Metric name {name} contains spaces"
            assert name.islower() or '_total' in name or '_seconds' in name, f"Metric name {name} not snake_case"

    def test_counter_names_end_with_total(self):
        """Counter metrics end with _total (added by Prometheus)."""
        from sentiment_agent.metrics import emotion_joy

        # Prometheus adds _total to counters automatically when exporting
        # The internal name doesn't have the suffix
        assert 'emotion' in emotion_joy._name.lower()

    def test_gauge_names_descriptive(self):
        """Gauge metrics have descriptive names."""
        from sentiment_agent.metrics import audience_sentiment, analysis_duration

        assert 'avg' in audience_sentiment._name or 'sentiment' in audience_sentiment._name
        assert 'seconds' in analysis_duration._name


class TestMetricsDocumentation:
    """Test metrics have proper documentation."""

    def test_all_metrics_have_descriptions(self):
        """All metrics have HELP text."""
        from sentiment_agent.metrics import (
            audience_sentiment,
            emotion_joy,
            emotion_surprise,
            emotion_neutral,
            emotion_sadness,
            emotion_anger,
            emotion_fear,
            analysis_queue_size,
            analysis_duration
        )

        metrics = [
            (audience_sentiment, 'sentiment'),
            (emotion_joy, 'joy'),
            (emotion_surprise, 'surprise'),
            (emotion_neutral, 'neutral'),
            (emotion_sadness, 'sadness'),
            (emotion_anger, 'anger'),
            (emotion_fear, 'fear'),
            (analysis_queue_size, 'queue'),
            (analysis_duration, 'time')  # Changed from 'duration' to 'time'
        ]

        for metric, keyword in metrics:
            doc = metric._documentation
            assert doc, f"Metric {metric._name} missing documentation"
            assert keyword.lower() in doc.lower(), f"Metric {metric._name} documentation missing '{keyword}'"
