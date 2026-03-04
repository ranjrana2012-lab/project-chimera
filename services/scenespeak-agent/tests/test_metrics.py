"""
Unit tests for business metrics.

Tests Prometheus metrics for dialogue quality tracking.
"""

import pytest
from prometheus_client import REGISTRY

# Add scenespeak-agent to path
agent_path = "/home/ranj/Project_Chimera/services/scenespeak-agent"
import sys
sys.path.insert(0, agent_path)


class TestDialogueQualityMetric:
    """Test dialogue quality metric."""

    def test_dialogue_quality_metric_registered(self):
        """Test that dialogue quality metric is registered."""
        from metrics import dialogue_quality
        assert dialogue_quality._name in {m.name for m in REGISTRY.collect()}

    def test_dialogue_quality_labels(self):
        """Test dialogue quality has correct labels."""
        from metrics import dialogue_quality
        dialogue_quality.labels(adapter="dramatic").set(0.85)
        metric = REGISTRY.get_sample_value('scenespeak_dialogue_quality', {'adapter': 'dramatic'})
        assert metric == 0.85


class TestLinesGeneratedMetric:
    """Test lines generation counter."""

    def test_lines_generated_metric_registered(self):
        """Test that lines generated metric is registered."""
        from metrics import lines_generated
        assert lines_generated._name in {m.name for m in REGISTRY.collect()}

    def test_lines_generated_metric(self):
        """Test lines generation counter."""
        from metrics import lines_generated
        lines_generated.labels(show_id="test-show").inc()
        # Verify metric exists
        metric = REGISTRY.get_sample_value('scenespeak_lines_generated_total', {'show_id': 'test-show'})
        assert metric == 1.0


class TestTokensPerLineMetric:
    """Test tokens per line histogram."""

    def test_tokens_per_line_registered(self):
        """Test that tokens per line metric is registered."""
        from metrics import tokens_per_line
        assert tokens_per_line._name in {m.name for m in REGISTRY.collect()}

    def test_tokens_per_line_observation(self):
        """Test observing token counts."""
        from metrics import tokens_per_line
        tokens_per_line.observe(50)
        # Check the _sum metric to verify observation was recorded
        metric = REGISTRY.get_sample_value('scenespeak_tokens_per_line_sum')
        assert metric == 50.0


class TestGenerationDurationMetric:
    """Test generation duration histogram."""

    def test_generation_duration_registered(self):
        """Test that generation duration metric is registered."""
        from metrics import generation_duration
        assert generation_duration._name in {m.name for m in REGISTRY.collect()}

    def test_generation_duration_observation(self):
        """Test observing generation duration."""
        from metrics import generation_duration
        generation_duration.labels(adapter="dramatic").observe(0.5)
        # Metric should have recorded observation
        metric = REGISTRY.get_sample_value('scenespeak_generation_duration_seconds_bucket', {'adapter': 'dramatic', 'le': '0.5'})
        assert metric >= 1.0


class TestCacheMetrics:
    """Test cache hit/miss counters."""

    def test_cache_hits_registered(self):
        """Test that cache hits metric is registered."""
        from metrics import cache_hits
        assert cache_hits._name in {m.name for m in REGISTRY.collect()}

    def test_cache_misses_registered(self):
        """Test that cache misses metric is registered."""
        from metrics import cache_misses
        assert cache_misses._name in {m.name for m in REGISTRY.collect()}

    def test_cache_hit_increment(self):
        """Test cache hit increment."""
        from metrics import cache_hits
        cache_hits.labels(adapter="dramatic").inc()
        metric = REGISTRY.get_sample_value('scenespeak_cache_hits_total', {'adapter': 'dramatic'})
        assert metric == 1.0

    def test_cache_miss_increment(self):
        """Test cache miss increment."""
        from metrics import cache_misses
        cache_misses.labels(adapter="dramatic").inc()
        metric = REGISTRY.get_sample_value('scenespeak_cache_misses_total', {'adapter': 'dramatic'})
        assert metric == 1.0


class TestRecordGeneration:
    """Test record_generation helper function."""

    def test_record_generation_all_metrics(self):
        """Test that record_generation updates all metrics."""
        from metrics import record_generation

        record_generation(
            show_id="test-show-unique",
            adapter="dramatic-unique",
            tokens=50,
            duration=0.5,
            quality=0.85,
            cache_hit=True
        )

        # Check lines generated
        lines = REGISTRY.get_sample_value('scenespeak_lines_generated_total', {'show_id': 'test-show-unique'})
        assert lines == 1.0

        # Check dialogue quality
        quality = REGISTRY.get_sample_value('scenespeak_dialogue_quality', {'adapter': 'dramatic-unique'})
        assert quality == 0.85

        # Check cache hits
        hits = REGISTRY.get_sample_value('scenespeak_cache_hits_total', {'adapter': 'dramatic-unique'})
        assert hits == 1.0

    def test_record_generation_cache_miss(self):
        """Test record_generation with cache miss."""
        from metrics import record_generation

        record_generation(
            show_id="test-show-2",
            adapter="default",
            tokens=100,
            duration=1.0,
            quality=0.75,
            cache_hit=False
        )

        # Check cache misses
        misses = REGISTRY.get_sample_value('scenespeak_cache_misses_total', {'adapter': 'default'})
        assert misses == 1.0
