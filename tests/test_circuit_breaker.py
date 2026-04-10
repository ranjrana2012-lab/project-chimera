"""
Tests for shared circuit_breaker module.

Tests the circuit breaker pattern implementation.
"""

import pytest
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from threading import Thread
import threading

# Add top-level shared to path
shared_dir = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from circuit_breaker import (
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitBreakerRegistry,
    with_circuit_breaker,
    CIRCUIT_CONFIGS,
    get_circuit_breaker,
    get_all_circuit_breaker_stats,
)


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_has_closed_state(self):
        """Verify CLOSED state exists."""
        assert CircuitState.CLOSED.value == "closed"

    def test_has_open_state(self):
        """Verify OPEN state exists."""
        assert CircuitState.OPEN.value == "open"

    def test_has_half_open_state(self):
        """Verify HALF_OPEN state exists."""
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_values(self):
        """Verify default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 2
        assert config.timeout == 30.0

    def test_custom_values(self):
        """Verify custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120.0,
            success_threshold=3,
            timeout=60.0
        )
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 120.0
        assert config.success_threshold == 3
        assert config.timeout == 60.0


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initialization(self):
        """Verify circuit breaker initializes correctly."""
        cb = CircuitBreaker("test-service")
        assert cb.service_name == "test-service"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_successful_call_in_closed_state(self):
        """Verify successful call works in CLOSED state."""
        cb = CircuitBreaker("test-service")

        def successful_func():
            return "success"

        result = cb.call(successful_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    def test_failure_opens_circuit_after_threshold(self):
        """Verify circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test-service", config)

        def failing_func():
            raise ConnectionError("Connection failed")

        # Trigger failures up to threshold
        for _ in range(3):
            try:
                cb.call(failing_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_rejects_calls(self):
        """Verify open circuit raises CircuitBreakerError."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        for _ in range(2):
            try:
                cb.call(failing_func)
            except ConnectionError:
                pass

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            cb.call(failing_func)

    def test_statistics_tracking(self):
        """Verify statistics are tracked."""
        cb = CircuitBreaker("test-service")

        def success_func():
            return "ok"

        def failing_func():
            raise ValueError("Error")

        # Success
        cb.call(success_func)

        # Failure
        try:
            cb.call(failing_func)
        except ValueError:
            pass

        stats = cb.get_stats()
        assert stats["total_calls"] == 2
        assert stats["total_successes"] == 1
        assert stats["total_failures"] == 1

    def test_reset_resets_circuit(self):
        """Verify reset() closes circuit."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        for _ in range(2):
            try:
                cb.call(failing_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestCircuitBreakerHalfOpenState:
    """Tests for circuit breaker half-open state."""

    def test_transitions_to_half_open_after_timeout(self):
        """Verify circuit transitions to half-open after recovery timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1  # Short timeout for testing
        )
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        for _ in range(2):
            try:
                cb.call(failing_func)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Next call should transition to half-open
        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_success_threshold_in_half_open(self):
        """Verify circuit closes after success threshold in half-open."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2
        )
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        for _ in range(2):
            try:
                cb.call(failing_func)
            except ConnectionError:
                pass

        # Wait for recovery timeout
        time.sleep(0.15)

        # First success in half-open
        def success_func():
            return "success"

        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.success_count == 1

        # Second success should close circuit
        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        """Verify circuit reopens on failure in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=3
        )
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        for _ in range(2):
            try:
                cb.call(failing_func)
            except ConnectionError:
                pass

        # Wait for recovery timeout
        time.sleep(0.15)

        # Success in half-open
        def success_func():
            return "success"

        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN

        # Failure in half-open should reopen
        try:
            cb.call(failing_func)
        except ConnectionError:
            pass

        assert cb.state == CircuitState.OPEN

    def test_half_open_max_calls_limit(self):
        """Verify half-open state limits calls when configured."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2,
            half_open_max_calls=1  # Only 1 call allowed in half-open
        )
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        for _ in range(2):
            try:
                cb.call(failing_func)
            except ConnectionError:
                pass

        # Wait for recovery timeout
        time.sleep(0.15)

        # First call in half-open should succeed
        def success_func():
            return "success"

        cb.call(success_func)

        # Second call should be rejected
        with pytest.raises(CircuitBreakerError, match="Maximum test calls"):
            cb.call(success_func)


class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry class."""

    def test_get_or_create_breaker(self):
        """Verify get_breaker creates or returns existing breaker."""
        registry = CircuitBreakerRegistry()

        # First call creates breaker
        cb1 = registry.get_breaker("service-a")
        assert cb1.service_name == "service-a"

        # Second call returns same instance
        cb2 = registry.get_breaker("service-a")
        assert cb1 is cb2

        # Different service gets different breaker
        cb3 = registry.get_breaker("service-b")
        assert cb3 is not cb1

    def test_get_breaker_with_config(self):
        """Verify config only used on first creation."""
        registry = CircuitBreakerRegistry()

        config1 = CircuitBreakerConfig(failure_threshold=10)
        config2 = CircuitBreakerConfig(failure_threshold=20)

        # First call with config1
        cb1 = registry.get_breaker("service-a", config1)
        assert cb1.config.failure_threshold == 10

        # Second call with config2 is ignored
        cb2 = registry.get_breaker("service-a", config2)
        assert cb1 is cb2
        assert cb1.config.failure_threshold == 10  # Still 10, not 20

    def test_get_all_stats(self):
        """Verify get_all_stats returns stats for all breakers."""
        registry = CircuitBreakerRegistry()

        # Create multiple breakers
        registry.get_breaker("service-a")
        registry.get_breaker("service-b")

        stats = registry.get_all_stats()
        assert "service-a" in stats
        assert "service-b" in stats

    def test_reset_all(self):
        """Verify reset_all resets all breakers."""
        registry = CircuitBreakerRegistry()

        # Create and open a breaker
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = registry.get_breaker("service-a", config)

        def failing_func():
            raise ConnectionError("Failed")

        try:
            cb.call(failing_func)
        except ConnectionError:
            pass

        assert cb.state == CircuitState.OPEN

        # Reset all
        registry.reset_all()
        assert cb.state == CircuitState.CLOSED

    def test_reset_breaker(self):
        """Verify reset_breaker resets specific breaker."""
        registry = CircuitBreakerRegistry()

        # Create two breakers with separate configs to avoid any shared state
        config_a = CircuitBreakerConfig(failure_threshold=1)
        config_b = CircuitBreakerConfig(failure_threshold=1)
        cb1 = registry.get_breaker("service-a", config_a)
        cb2 = registry.get_breaker("service-b", config_b)

        # Verify they're different instances
        assert cb1 is not cb2

        # Open both
        def failing_func():
            raise ConnectionError("Failed")

        # Open cb1
        try:
            cb1.call(failing_func)
        except ConnectionError:
            pass
        assert cb1.state == CircuitState.OPEN, f"cb1 should be OPEN after failure, but got {cb1.state}"

        # Open cb2
        try:
            cb2.call(failing_func)
        except ConnectionError:
            pass
        assert cb2.state == CircuitState.OPEN, f"cb2 should be OPEN after failure, but got {cb2.state}"

        # Reset only one
        result = registry.reset_breaker("service-a")
        assert result is True
        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.OPEN  # service-b should still be open

    def test_reset_breaker_nonexistent(self):
        """Verify reset_breaker returns False for nonexistent breaker."""
        registry = CircuitBreakerRegistry()
        result = registry.reset_breaker("nonexistent")
        assert result is False


class TestCircuitBreakerDecorator:
    """Tests for with_circuit_breaker decorator."""

    def test_decorator_protects_function(self):
        """Verify decorator adds circuit breaker protection."""
        # Create registry for testing
        registry = CircuitBreakerRegistry()
        config = CircuitBreakerConfig(failure_threshold=2)

        call_count = [0]

        @with_circuit_breaker(service_name="test_func", config=config, registry=registry)
        def test_function(value: int) -> int:
            call_count[0] += 1
            if call_count[0] <= 2:
                raise ConnectionError("Failed")
            return value * 2

        # First two calls fail
        for _ in range(2):
            try:
                test_function(5)
            except ConnectionError:
                pass

        # Third call raises CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            test_function(5)

    def test_decorator_uses_function_name_by_default(self):
        """Verify decorator uses function name when service_name not provided."""
        registry = CircuitBreakerRegistry()

        @with_circuit_breaker(registry=registry)
        def my_function():
            return "result"

        result = my_function()
        assert result == "result"

        # Check that breaker was created with function name
        stats = registry.get_all_stats()
        assert "my_function" in stats


class TestCircuitBreakerConfigs:
    """Tests for CIRCUIT_CONFIGS presets."""

    def test_database_config_exists(self):
        """Verify database configuration preset exists."""
        assert "database" in CIRCUIT_CONFIGS

    def test_external_api_config_exists(self):
        """Verify external_api configuration preset exists."""
        from circuit_breaker import CIRCUIT_CONFIGS
        assert "external_api" in CIRCUIT_CONFIGS

    def test_ml_service_config_exists(self):
        """Verify ml_service configuration preset exists."""
        from circuit_breaker import CIRCUIT_CONFIGS
        assert "ml_service" in CIRCUIT_CONFIGS

    def test_cache_config_exists(self):
        """Verify cache configuration preset exists."""
        from circuit_breaker import CIRCUIT_CONFIGS
        assert "cache" in CIRCUIT_CONFIGS


class TestCircuitBreakerUtilityFunctions:
    """Tests for utility functions."""

    def test_get_circuit_breaker(self):
        """Verify get_circuit_breaker returns configured breaker."""
        cb = get_circuit_breaker("my-service", "database")
        assert cb.service_name == "my-service"
        assert cb.config.failure_threshold == 5  # database config has 5

        # Should be in global stats
        stats = get_all_circuit_breaker_stats()
        assert "my-service" in stats

    def test_get_all_circuit_breaker_stats(self):
        """Verify get_all_circuit_breaker_stats returns all stats."""
        # Create some breakers
        get_circuit_breaker("service-1", "database")
        get_circuit_breaker("service-2", "external_api")

        stats = get_all_circuit_breaker_stats()
        assert "service-1" in stats
        assert "service-2" in stats
        assert stats["service-1"]["service_name"] == "service-1"


class TestCircuitBreakerStatistics:
    """Tests for circuit breaker statistics."""

    def test_get_stats_includes_all_fields(self):
        """Verify get_stats includes all statistical fields."""
        cb = CircuitBreaker("test-service")
        stats = cb.get_stats()

        expected_fields = {
            "service_name", "state", "failure_count", "success_count",
            "total_calls", "total_failures", "total_successes",
            "total_rejected", "total_timeouts", "last_failure_time", "opened_at"
        }

        assert set(stats.keys()) == expected_fields

    def test_rejected_calls_counted(self):
        """Verify rejected calls are tracked."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        try:
            cb.call(failing_func)
        except ConnectionError:
            pass

        # Try to call again - should be rejected
        try:
            cb.call(failing_func)
        except CircuitBreakerError:
            pass

        stats = cb.get_stats()
        assert stats["total_rejected"] == 1

    def test_success_count_in_half_open(self):
        """Verify success count is tracked in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,
            success_threshold=3
        )
        cb = CircuitBreaker("test-service", config)

        # Open the circuit
        def failing_func():
            raise ConnectionError("Failed")

        try:
            cb.call(failing_func)
        except ConnectionError:
            pass

        # Wait for recovery timeout
        time.sleep(0.15)

        # Success in half-open
        def success_func():
            return "success"

        cb.call(success_func)
        assert cb.success_count == 1
