"""
Tests for shared/resilience module.

Tests retry logic and resilience patterns for Project Chimera.
"""

import pytest
import sys
import asyncio
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add top-level shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from resilience import (
    RetryStrategy,
    RetryConfig,
    _calculate_delay,
    retry_on_exception,
    retry_on_condition,
    async_retry_on_exception,
    RetryTracker,
    RETRY_CONFIGS,
)


class TestRetryStrategy:
    """Tests for RetryStrategy enum."""

    def test_has_exponential_backoff(self):
        """Verify EXPONENTIAL_BACKOFF strategy exists."""
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"

    def test_has_fixed_delay(self):
        """Verify FIXED_DELAY strategy exists."""
        assert RetryStrategy.FIXED_DELAY.value == "fixed_delay"

    def test_has_linear_backoff(self):
        """Verify LINEAR_BACKOFF strategy exists."""
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_values(self):
        """Verify default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.jitter is True
        assert config.jitter_amount == 0.1

    def test_custom_values(self):
        """Verify custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            jitter=False,
            jitter_amount=0.2
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.strategy == RetryStrategy.LINEAR_BACKOFF
        assert config.jitter is False
        assert config.jitter_amount == 0.2


class TestCalculateDelay:
    """Tests for _calculate_delay function."""

    def test_exponential_backoff(self):
        """Verify exponential backoff calculation."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        assert _calculate_delay(0, config) == 1.0
        assert _calculate_delay(1, config) == 2.0
        assert _calculate_delay(2, config) == 4.0

    def test_fixed_delay(self):
        """Verify fixed delay calculation."""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=2.0,
            jitter=False
        )
        assert _calculate_delay(0, config) == 2.0
        assert _calculate_delay(1, config) == 2.0
        assert _calculate_delay(2, config) == 2.0

    def test_linear_backoff(self):
        """Verify linear backoff calculation."""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=1.0,
            jitter=False
        )
        assert _calculate_delay(0, config) == 1.0
        assert _calculate_delay(1, config) == 2.0
        assert _calculate_delay(2, config) == 3.0

    def test_max_delay_clamping(self):
        """Verify delay is clamped to max_delay."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=10.0,
            jitter=False
        )
        delay = _calculate_delay(10, config)
        assert delay == 5.0

    def test_no_negative_delay(self):
        """Verify delay never goes negative (with jitter)."""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=0.1,
            jitter=True,
            jitter_amount=0.5
        )
        delay = _calculate_delay(0, config)
        assert delay >= 0

    def test_jitter_adds_variation(self):
        """Verify jitter adds random variation."""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=1.0,
            jitter=True,
            jitter_amount=0.5
        )
        delays = [_calculate_delay(0, config) for _ in range(10)]
        # With jitter, delays should vary
        assert len(set(delays)) > 1

    def test_no_jitter_consistent(self):
        """Verify no jitter produces consistent delays."""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=1.0,
            jitter=False
        )
        delays = [_calculate_delay(0, config) for _ in range(10)]
        # Without jitter, delays should be identical
        assert all(d == 1.0 for d in delays)


class TestRetryOnException:
    """Tests for retry_on_exception decorator."""

    def test_success_on_first_try(self):
        """Verify function succeeds on first try."""
        @retry_on_exception(ValueError)
        def func():
            return "success"

        assert func() == "success"

    def test_retry_on_exception_success_after_retry(self):
        """Verify function retries and succeeds."""
        attempts = [0]

        @retry_on_exception(ValueError, config=RetryConfig(max_attempts=3, base_delay=0.01))
        def func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("fail")
            return "success"

        assert func() == "success"
        assert attempts[0] == 2

    def test_retry_on_exception_fails_after_max_attempts(self):
        """Verify function raises after max attempts."""
        @retry_on_exception(ValueError, config=RetryConfig(max_attempts=3, base_delay=0.01))
        def func():
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fail"):
            func()

    def test_retry_on_specific_exception(self):
        """Verify only specified exceptions trigger retry."""
        @retry_on_exception(ValueError, config=RetryConfig(max_attempts=2, base_delay=0.01))
        def func():
            raise TypeError("fail")

        with pytest.raises(TypeError):
            func()

    def test_retry_on_multiple_exception_types(self):
        """Verify multiple exception types can be specified."""
        attempts = [0]

        @retry_on_exception(ValueError, TypeError, config=RetryConfig(max_attempts=4, base_delay=0.01))
        def func():
            attempts[0] += 1
            if attempts[0] == 1:
                raise ValueError("fail1")
            elif attempts[0] == 2:
                raise TypeError("fail2")
            return "success"

        assert func() == "success"

    def test_default_config(self):
        """Verify default config is used when not provided."""
        @retry_on_exception(ValueError)
        def func():
            raise ValueError("fail")

        # Should use default max_attempts=3
        with pytest.raises(ValueError):
            func()

    def test_no_exception_types_defaults_to_exception(self):
        """Verify empty exception_types defaults to catching Exception."""
        @retry_on_exception(config=RetryConfig(max_attempts=2, base_delay=0.01))
        def func():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            func()


class TestRetryOnCondition:
    """Tests for retry_on_condition decorator."""

    def test_condition_met_returns(self):
        """Verify function returns when condition is not met."""
        @retry_on_condition(lambda x: x is None, config=RetryConfig(max_attempts=3, base_delay=0.01))
        def func():
            return "value"

        assert func() == "value"

    def test_condition_not_met_retries(self):
        """Verify function retries when condition is met."""
        attempts = [0]

        @retry_on_condition(lambda x: x is None, config=RetryConfig(max_attempts=3, base_delay=0.01))
        def func():
            attempts[0] += 1
            if attempts[0] < 2:
                return None
            return "value"

        assert func() == "value"
        assert attempts[0] == 2

    def test_condition_always_met_returns_after_max_attempts(self):
        """Verify function returns after max attempts even if condition met."""
        @retry_on_condition(lambda x: x is None, config=RetryConfig(max_attempts=2, base_delay=0.01))
        def func():
            return None

        result = func()
        assert result is None

    def test_condition_with_false_value(self):
        """Verify condition works with false values."""
        @retry_on_condition(lambda x: x == 0, config=RetryConfig(max_attempts=2, base_delay=0.01))
        def func():
            return 1

        assert func() == 1


class TestAsyncRetryOnException:
    """Tests for async_retry_on_exception decorator."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Verify async function succeeds on first try."""
        @async_retry_on_exception(ValueError)
        async def func():
            return "success"

        assert await func() == "success"

    @pytest.mark.asyncio
    async def test_retry_on_exception_success_after_retry(self):
        """Verify async function retries and succeeds."""
        attempts = [0]

        @async_retry_on_exception(ValueError, config=RetryConfig(max_attempts=3, base_delay=0.01))
        async def func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("fail")
            return "success"

        assert await func() == "success"
        assert attempts[0] == 2

    @pytest.mark.asyncio
    async def test_retry_on_exception_fails_after_max_attempts(self):
        """Verify async function raises after max attempts."""
        @async_retry_on_exception(ValueError, config=RetryConfig(max_attempts=3, base_delay=0.01))
        async def func():
            raise ValueError("fail")

        with pytest.raises(ValueError, match="fail"):
            await func()

    @pytest.mark.asyncio
    async def test_uses_asyncio_sleep(self):
        """Verify async retry uses asyncio.sleep."""
        @async_retry_on_exception(ValueError, config=RetryConfig(max_attempts=2, base_delay=0.01))
        async def func():
            raise ValueError("fail")

        start = time.time()
        try:
            await func()
        except ValueError:
            pass
        elapsed = time.time() - start

        # Should have slept at least base_delay
        assert elapsed >= 0.01


class TestRetryTracker:
    """Tests for RetryTracker class."""

    def test_initialization(self):
        """Verify tracker initializes correctly."""
        tracker = RetryTracker("test-service")
        assert tracker.service_name == "test-service"
        assert tracker.attempts == {}
        assert tracker.failures == {}
        assert tracker.successes == {}

    def test_record_attempt(self):
        """Verify attempt recording."""
        tracker = RetryTracker("test-service")
        tracker.record_attempt("operation1")
        tracker.record_attempt("operation1")
        tracker.record_attempt("operation2")

        assert tracker.attempts["operation1"] == 2
        assert tracker.attempts["operation2"] == 1

    def test_record_failure(self):
        """Verify failure recording."""
        tracker = RetryTracker("test-service")
        tracker.record_failure("operation1")
        tracker.record_failure("operation1")
        tracker.record_failure("operation2")

        assert tracker.failures["operation1"] == 2
        assert tracker.failures["operation2"] == 1

    def test_record_success(self):
        """Verify success recording."""
        tracker = RetryTracker("test-service")
        tracker.record_success("operation1")
        tracker.record_success("operation1")
        tracker.record_success("operation2")

        assert tracker.successes["operation1"] == 2
        assert tracker.successes["operation2"] == 1

    def test_get_stats(self):
        """Verify getting stats for operation."""
        tracker = RetryTracker("test-service")
        tracker.record_attempt("op1")
        tracker.record_attempt("op1")
        tracker.record_success("op1")
        tracker.record_failure("op1")

        stats = tracker.get_stats("op1")
        assert stats["attempts"] == 2
        assert stats["successes"] == 1
        assert stats["failures"] == 1

    def test_get_stats_returns_zeros_for_unknown_operation(self):
        """Verify stats returns zeros for unknown operation."""
        tracker = RetryTracker("test-service")
        stats = tracker.get_stats("unknown")
        assert stats == {"attempts": 0, "failures": 0, "successes": 0}

    def test_get_all_stats(self):
        """Verify getting all stats."""
        tracker = RetryTracker("test-service")
        tracker.record_attempt("op1")
        tracker.record_success("op1")
        tracker.record_failure("op2")

        all_stats = tracker.get_all_stats()
        assert "op1" in all_stats
        assert "op2" in all_stats
        assert all_stats["op1"]["attempts"] == 1
        assert all_stats["op2"]["failures"] == 1

    def test_multiple_operations_tracked_separately(self):
        """Verify operations are tracked separately."""
        tracker = RetryTracker("test-service")
        tracker.record_attempt("op1")
        tracker.record_attempt("op2")
        tracker.record_success("op1")
        tracker.record_failure("op2")

        stats1 = tracker.get_stats("op1")
        stats2 = tracker.get_stats("op2")

        assert stats1["attempts"] == 1
        assert stats1["successes"] == 1
        assert stats2["attempts"] == 1
        assert stats2["failures"] == 1


class TestRetryConfigsPresets:
    """Tests for RETRY_CONFIGS presets."""

    def test_has_network_config(self):
        """Verify network config exists."""
        assert "network" in RETRY_CONFIGS
        config = RETRY_CONFIGS["network"]
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

    def test_has_database_config(self):
        """Verify database config exists."""
        assert "database" in RETRY_CONFIGS
        config = RETRY_CONFIGS["database"]
        assert config.max_attempts == 3
        assert config.base_delay == 0.5

    def test_has_ml_inference_config(self):
        """Verify ml_inference config exists."""
        assert "ml_inference" in RETRY_CONFIGS
        config = RETRY_CONFIGS["ml_inference"]
        assert config.max_attempts == 2
        assert config.base_delay == 2.0

    def test_has_external_api_config(self):
        """Verify external_api config exists."""
        assert "external_api" in RETRY_CONFIGS
        config = RETRY_CONFIGS["external_api"]
        assert config.max_attempts == 3
        assert config.max_delay == 60.0


class TestModuleExports:
    """Tests for module exports."""

    def test_expected_exports(self):
        """Verify expected exports exist."""
        import resilience

        expected = [
            'RetryStrategy',
            'RetryConfig',
            '_calculate_delay',
            'retry_on_exception',
            'retry_on_condition',
            'async_retry_on_exception',
            'RetryTracker',
            'RETRY_CONFIGS',
        ]

        for export in expected:
            assert hasattr(resilience, export)
