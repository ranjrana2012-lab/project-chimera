# tests/resilience/test_retry.py
"""Tests for retry logic with exponential backoff."""

import pytest
import time
from unittest.mock import Mock, patch

from shared.resilience import (
    retry_on_exception,
    retry_on_condition,
    RetryConfig,
    RetryStrategy,
    RetryTracker,
    RETRY_CONFIGS,
)


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.jitter is True

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            strategy=RetryStrategy.FIXED_DELAY,
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.strategy == RetryStrategy.FIXED_DELAY


class TestRetryOnException:
    """Tests for retry_on_exception decorator."""

    def test_success_no_retry(self):
        """Test function succeeds on first attempt."""
        @retry_on_exception(ConnectionError)
        def failing_func():
            return "success"

        result = failing_func()
        assert result == "success"

    def test_retry_on_specific_exception(self):
        """Test retry only on specified exception types."""
        call_count = 0

        @retry_on_exception(ConnectionError, config=RetryConfig(max_attempts=3, base_delay=0.01))
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 2

    def test_max_attempts_exceeded(self):
        """Test function fails after max attempts."""
        call_count = 0

        @retry_on_exception(ConnectionError, config=RetryConfig(max_attempts=3, base_delay=0.01))
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            failing_func()

        assert call_count == 3

    def test_no_retry_on_different_exception(self):
        """Test no retry for different exception type."""
        call_count = 0

        @retry_on_exception(ConnectionError, config=RetryConfig(max_attempts=3))
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Different error")

        with pytest.raises(ValueError):
            failing_func()

        # Should only be called once since ValueError is not in the retry list
        assert call_count == 1

    def test_exponential_backoff_delays(self):
        """Test exponential backoff creates increasing delays."""
        delays = []

        @retry_on_exception(ConnectionError, config=RetryConfig(
            max_attempts=4,
            base_delay=0.1,
            exponential_base=2.0,
            jitter=False,
        ))
        def failing_func():
            raise ConnectionError("Connection failed")

        start_time = time.time()
        with pytest.raises(ConnectionError):
            failing_func()
        total_time = time.time() - start_time

        # With base_delay=0.1 and exponential_base=2.0:
        # Attempt 1 fails, wait 0.1s
        # Attempt 2 fails, wait 0.2s
        # Attempt 3 fails, wait 0.4s
        # Total delay should be approximately 0.7s
        assert total_time >= 0.6  # Allow some tolerance
        assert total_time <= 1.0

    def test_fixed_delay_strategy(self):
        """Test fixed delay strategy."""
        call_count = 0

        @retry_on_exception(ConnectionError, config=RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            strategy=RetryStrategy.FIXED_DELAY,
            jitter=False,
        ))
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        start_time = time.time()
        result = failing_func()
        elapsed = time.time() - start_time

        assert result == "success"
        assert call_count == 3
        # Should have 2 delays of 0.1s each
        assert 0.15 <= elapsed <= 0.35

    def test_jitter_added_to_delays(self):
        """Test that jitter is added to delays."""
        call_count = 0
        delays = []

        @retry_on_exception(ConnectionError, config=RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            jitter=True,
            jitter_amount=0.5,  # 50% jitter
        ))
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        # Run multiple times to ensure jitter is applied
        times = []
        for _ in range(3):
            call_count = 0
            start = time.time()
            failing_func()
            times.append(time.time() - start)

        # Times should vary due to jitter (use lower threshold for robustness)
        assert max(times) - min(times) > 0.03


class TestRetryOnCondition:
    """Tests for retry_on_condition decorator."""

    def test_condition_met_immediately(self):
        """Test function succeeds when condition is not met."""
        @retry_on_condition(lambda x: x is None, config=RetryConfig(max_attempts=3))
        def return_value():
            return "value"

        result = return_value()
        assert result == "value"

    def test_retry_until_condition_not_met(self):
        """Test retry until condition returns False."""
        call_count = 0

        @retry_on_condition(lambda x: x is None, config=RetryConfig(max_attempts=5, base_delay=0.01))
        def get_value():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return None
            return "value"

        result = get_value()
        assert result == "value"
        assert call_count == 3

    def test_condition_always_met(self):
        """Test max attempts when condition is always met."""
        call_count = 0

        @retry_on_condition(lambda x: x is None, config=RetryConfig(max_attempts=3, base_delay=0.01))
        def get_value():
            nonlocal call_count
            call_count += 1
            return None

        result = get_value()
        assert result is None
        assert call_count == 3


class TestRetryTracker:
    """Tests for RetryTracker class."""

    def test_record_attempt(self):
        """Test recording retry attempts."""
        tracker = RetryTracker("test_service")
        tracker.record_attempt("test_operation")
        tracker.record_attempt("test_operation")

        stats = tracker.get_stats("test_operation")
        assert stats["attempts"] == 2

    def test_record_failure(self):
        """Test recording failures."""
        tracker = RetryTracker("test_service")
        tracker.record_failure("test_operation")

        stats = tracker.get_stats("test_operation")
        assert stats["failures"] == 1

    def test_record_success(self):
        """Test recording successes."""
        tracker = RetryTracker("test_service")
        tracker.record_success("test_operation")

        stats = tracker.get_stats("test_operation")
        assert stats["successes"] == 1

    def test_get_all_stats(self):
        """Test getting statistics for all operations."""
        tracker = RetryTracker("test_service")
        tracker.record_attempt("op1")
        tracker.record_success("op1")
        tracker.record_attempt("op2")
        tracker.record_failure("op2")

        all_stats = tracker.get_all_stats()
        assert "op1" in all_stats
        assert "op2" in all_stats
        assert all_stats["op1"]["successes"] == 1
        assert all_stats["op2"]["failures"] == 1


class TestPresetConfigs:
    """Tests for preset retry configurations."""

    def test_network_config_exists(self):
        """Test network configuration exists."""
        assert "network" in RETRY_CONFIGS
        config = RETRY_CONFIGS["network"]
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

    def test_database_config_exists(self):
        """Test database configuration exists."""
        assert "database" in RETRY_CONFIGS
        config = RETRY_CONFIGS["database"]
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

    def test_ml_inference_config_exists(self):
        """Test ML inference configuration exists."""
        assert "ml_inference" in RETRY_CONFIGS
        config = RETRY_CONFIGS["ml_inference"]
        assert config.max_attempts == 2

    def test_external_api_config_exists(self):
        """Test external API configuration exists."""
        assert "external_api" in RETRY_CONFIGS
        config = RETRY_CONFIGS["external_api"]
        assert config.max_attempts == 3


@pytest.mark.integration
class TestRetryIntegration:
    """Integration tests for retry logic."""

    def test_retry_with_real_network_failure_simulation(self):
        """Test retry with simulated network failure."""
        call_count = 0

        @retry_on_exception(ConnectionError, config=RetryConfig(
            max_attempts=3,
            base_delay=0.05,
        ))
        def simulate_network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network unavailable")
            return {"status": "ok"}

        result = simulate_network_call()
        assert result == {"status": "ok"}
        assert call_count == 3

    def test_retry_with_multiple_exception_types(self):
        """Test retry with multiple exception types."""
        call_count = 0

        @retry_on_exception(
            ConnectionError,
            TimeoutError,
            config=RetryConfig(max_attempts=5, base_delay=0.01)
        )
        def failing_with_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection failed")
            elif call_count == 2:
                raise TimeoutError("Request timed out")
            return "success"

        result = failing_with_different_errors()
        assert result == "success"
        assert call_count == 3
