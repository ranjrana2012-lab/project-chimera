"""Tests for edge cases in resilience retry logic."""
import pytest
import time
from shared.resilience import (
    retry_on_exception,
    retry_on_condition,
    RetryConfig,
    RetryStrategy,
)


class TestRetryEdgeCases:
    """Tests for edge cases and uncovered lines."""

    def test_retry_with_no_exception_types(self):
        """Test retry with no exception types specified (defaults to Exception)."""
        call_count = 0

        @retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.01))
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Some error")
            return "success"

        result = raise_value_error()
        assert result == "success"
        assert call_count == 3

    def test_retry_without_jitter(self):
        """Test retry without jitter (deterministic delays)."""
        call_count = 0

        @retry_on_exception(
            ConnectionError,
            config=RetryConfig(max_attempts=3, base_delay=0.05, jitter=False)
        )
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Failed")
            return "success"

        start = time.time()
        result = failing_function()
        elapsed = time.time() - start

        assert result == "success"
        # With jitter=False and base_delay=0.05, delays should be: 0.05, 0.10
        # So total should be at least 0.15
        assert elapsed >= 0.14  # Allow some tolerance

    def test_retry_condition_max_attempts_return_last_result(self):
        """Test retry_on_condition returns last result after max attempts."""
        @retry_on_condition(
            lambda x: x is None,
            config=RetryConfig(max_attempts=3, base_delay=0.01)
        )
        def always_return_none():
            return None

        # Should return None after max attempts
        result = always_return_none()
        assert result is None

    def test_linear_backoff_strategy(self):
        """Test linear backoff strategy."""
        delays = []

        @retry_on_exception(
            ConnectionError,
            config=RetryConfig(
                max_attempts=4,
                base_delay=0.01,
                strategy=RetryStrategy.LINEAR_BACKOFF,
                jitter=False,
            )
        )
        def track_delays():
            delays.append(time.time())
            if len(delays) < 4:
                raise ConnectionError("Failed")
            return "success"

        track_delays()

        # Calculate delays between attempts
        actual_delays = [delays[i+1] - delays[i] for i in range(len(delays)-1)]
        # Linear backoff: base_delay * (attempt + 1)
        # First retry: 0.01, Second: 0.02, Third: 0.03
        assert len(actual_delays) == 3
        assert actual_delays[0] >= 0.005  # ~0.01
        assert actual_delays[1] >= 0.015  # ~0.02
        assert actual_delays[2] >= 0.025  # ~0.03

    def test_retry_with_default_exception_type(self):
        """Test that retry defaults to catching Exception when no types specified."""
        call_count = 0

        @retry_on_exception(config=RetryConfig(max_attempts=2, base_delay=0.01))
        def raise_runtime_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Runtime error")
            return "success"

        result = raise_runtime_error()
        assert result == "success"
        assert call_count == 2

    def test_retry_condition_immediate_success(self):
        """Test retry_on_condition when condition is immediately false."""
        @retry_on_condition(lambda x: x > 10)
        def return_large_number():
            return 100

        result = return_large_number()
        assert result == 100

    def test_retry_condition_with_valid_result(self):
        """Test retry_on_condition returns valid result when condition becomes false."""
        call_count = 0

        @retry_on_condition(
            lambda x: x is None,
            config=RetryConfig(max_attempts=5, base_delay=0.01)
        )
        def eventually_returns_value():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return None
            return "value"

        result = eventually_returns_value()
        assert result == "value"
        assert call_count == 3


class TestRetryConfigPresets:
    """Tests for RETRY_CONFIGS presets."""

    def test_network_config_attributes(self):
        """Test network config has expected attributes."""
        from shared.resilience import RETRY_CONFIGS
        config = RETRY_CONFIGS["network"]
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.base_delay == 1.0
        assert config.jitter is True

    def test_database_config_attributes(self):
        """Test database config has expected attributes."""
        from shared.resilience import RETRY_CONFIGS
        config = RETRY_CONFIGS["database"]
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

    def test_ml_inference_config_attributes(self):
        """Test ML inference config has expected attributes."""
        from shared.resilience import RETRY_CONFIGS
        config = RETRY_CONFIGS["ml_inference"]
        assert config.max_attempts == 2

    def test_external_api_config_attributes(self):
        """Test external API config has expected attributes."""
        from shared.resilience import RETRY_CONFIGS
        config = RETRY_CONFIGS["external_api"]
        assert config.max_attempts == 3
