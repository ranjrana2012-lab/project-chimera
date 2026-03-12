# tests/resilience/test_circuit_breaker.py
"""Tests for circuit breaker pattern implementation."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from shared.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerRegistry,
    with_circuit_breaker,
    get_circuit_breaker,
    get_all_circuit_breaker_stats,
    CIRCUIT_CONFIGS,
)


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig class."""

    def test_default_config(self):
        """Test default circuit breaker configuration."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 2
        assert config.timeout == 30.0

    def test_custom_config(self):
        """Test custom circuit breaker configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120.0,
            success_threshold=3,
        )
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 120.0
        assert config.success_threshold == 3


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initial_state(self):
        """Test circuit breaker starts in closed state."""
        breaker = CircuitBreaker("test_service")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    def test_successful_call(self):
        """Test successful call doesn't change state."""
        breaker = CircuitBreaker("test_service")

        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold is reached."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test_service", config)

        def failing_func():
            raise ConnectionError("Connection failed")

        # Trigger failures up to threshold
        for _ in range(config.failure_threshold):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

    def test_open_circuit_rejects_calls(self):
        """Test open circuit rejects calls immediately."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test_service", config)

        def failing_func():
            raise ConnectionError("Connection failed")

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Next call should be rejected with CircuitBreakerError
        with pytest.raises(CircuitBreakerError) as exc_info:
            breaker.call(failing_func)

        assert "Circuit breaker is open" in str(exc_info.value)

    def test_half_open_state_after_timeout(self):
        """Test circuit transitions to half-open after recovery timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,  # Short timeout for testing
        )
        breaker = CircuitBreaker("test_service", config)

        def failing_func():
            raise ConnectionError("Connection failed")

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(config.recovery_timeout + 0.05)

        # Next call should transition to half-open
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)

        assert breaker.state == CircuitState.HALF_OPEN

    def test_circuit_closes_after_successful_calls(self):
        """Test circuit closes after successful calls in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2,
        )
        breaker = CircuitBreaker("test_service", config)

        def failing_func():
            raise ConnectionError("Connection failed")

        def success_func():
            return "success"

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Wait for recovery timeout
        time.sleep(config.recovery_timeout + 0.05)

        # Make successful calls to close the circuit
        for _ in range(config.success_threshold):
            breaker.call(success_func)

        assert breaker.state == CircuitState.CLOSED

    def test_circuit_reopens_on_half_open_failure(self):
        """Test circuit reopens if call fails in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2,
        )
        breaker = CircuitBreaker("test_service", config)

        def failing_func():
            raise ConnectionError("Connection failed")

        def success_func():
            return "success"

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        # Wait for recovery timeout
        time.sleep(config.recovery_timeout + 0.05)

        # One success
        breaker.call(success_func)

        # Then failure - should reopen
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

    def test_get_stats(self):
        """Test getting circuit breaker statistics."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test_service", config)

        def success_func():
            return "success"

        def failing_func():
            raise ConnectionError("Connection failed")

        # Some successful calls
        for _ in range(2):
            breaker.call(success_func)

        # Some failed calls
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        stats = breaker.get_stats()
        assert stats["service_name"] == "test_service"
        assert stats["total_calls"] == 5
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 3
        assert stats["state"] == CircuitState.OPEN.value

    def test_reset(self):
        """Test resetting circuit breaker."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test_service", config)

        def failing_func():
            raise ConnectionError("Connection failed")

        # Open the circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry class."""

    def test_get_breaker_creates_new(self):
        """Test getting a breaker creates new one if needed."""
        registry = CircuitBreakerRegistry()
        breaker = registry.get_breaker("test_service")

        assert isinstance(breaker, CircuitBreaker)
        assert breaker.service_name == "test_service"

    def test_get_breaker_reuses_existing(self):
        """Test getting a breaker reuses existing one."""
        registry = CircuitBreakerRegistry()
        breaker1 = registry.get_breaker("test_service")
        breaker2 = registry.get_breaker("test_service")

        assert breaker1 is breaker2

    def test_get_all_stats(self):
        """Test getting stats for all breakers."""
        registry = CircuitBreakerRegistry()
        registry.get_breaker("service1")
        registry.get_breaker("service2")

        stats = registry.get_all_stats()
        assert "service1" in stats
        assert "service2" in stats

    def test_reset_breaker(self):
        """Test resetting a specific breaker."""
        registry = CircuitBreakerRegistry()
        breaker = registry.get_breaker("test_service")

        # Open the circuit
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker._config = config

        def failing_func():
            raise ConnectionError("Connection failed")

        for _ in range(config.failure_threshold):
            try:
                breaker.call(failing_func)
            except:
                pass

        assert breaker.state == CircuitState.OPEN

        # Reset via registry
        result = registry.reset_breaker("test_service")

        assert result is True
        assert breaker.state == CircuitState.CLOSED

    def test_reset_nonexistent_breaker(self):
        """Test resetting a non-existent breaker returns False."""
        registry = CircuitBreakerRegistry()
        result = registry.reset_breaker("nonexistent")
        assert result is False


class TestWithCircuitBreakerDecorator:
    """Tests for with_circuit_breaker decorator."""

    def test_decorator_protects_function(self):
        """Test decorator protects function with circuit breaker."""
        call_count = 0

        @with_circuit_breaker(
            service_name="test_service",
            config=CircuitBreakerConfig(failure_threshold=2),
        )
        def protected_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        # First two calls should fail
        with pytest.raises(ConnectionError):
            protected_function()

        with pytest.raises(ConnectionError):
            protected_function()

        # Third call should be rejected by circuit breaker
        with pytest.raises(CircuitBreakerError):
            protected_function()

    def test_decorator_with_default_service_name(self):
        """Test decorator uses function name as service name."""
        @with_circuit_breaker()
        def my_function():
            return "success"

        result = my_function()
        assert result == "success"


class TestPresetConfigs:
    """Tests for preset circuit breaker configurations."""

    def test_database_config_exists(self):
        """Test database configuration exists."""
        assert "database" in CIRCUIT_CONFIGS
        config = CIRCUIT_CONFIGS["database"]
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0

    def test_external_api_config_exists(self):
        """Test external API configuration exists."""
        assert "external_api" in CIRCUIT_CONFIGS
        config = CIRCUIT_CONFIGS["external_api"]
        assert config.failure_threshold == 3

    def test_ml_service_config_exists(self):
        """Test ML service configuration exists."""
        assert "ml_service" in CIRCUIT_CONFIGS
        config = CIRCUIT_CONFIGS["ml_service"]
        assert config.failure_threshold == 3

    def test_cache_config_exists(self):
        """Test cache configuration exists."""
        assert "cache" in CIRCUIT_CONFIGS
        config = CIRCUIT_CONFIGS["cache"]
        assert config.failure_threshold == 10


class TestGlobalFunctions:
    """Tests for global circuit breaker functions."""

    def test_get_circuit_breaker(self):
        """Test getting a circuit breaker with preset config."""
        breaker = get_circuit_breaker("my_service", "database")
        assert isinstance(breaker, CircuitBreaker)
        assert breaker.service_name == "my_service"

    def test_get_all_circuit_breaker_stats(self):
        """Test getting all circuit breaker stats."""
        get_circuit_breaker("service1", "database")
        get_circuit_breaker("service2", "external_api")

        stats = get_all_circuit_breaker_stats()
        assert "service1" in stats
        assert "service2" in stats


@pytest.mark.integration
class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker."""

    def test_end_to_end_circuit_breaker_workflow(self):
        """Test complete circuit breaker workflow."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=0.2,
            success_threshold=2,
        )
        breaker = CircuitBreaker("integration_test", config)

        call_count = 0

        def unreliable_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise ConnectionError("Service unavailable")
            return "success"

        # Phase 1: Circuit opens after failures
        for _ in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(unreliable_function)

        assert breaker.state == CircuitState.OPEN

        # Phase 2: Calls are rejected
        with pytest.raises(CircuitBreakerError):
            breaker.call(unreliable_function)

        stats = breaker.get_stats()
        assert stats["total_rejected"] >= 1

        # Phase 3: Recovery timeout passes
        time.sleep(config.recovery_timeout + 0.1)

        # Phase 4: Half-open state allows test call
        with pytest.raises(ConnectionError):
            breaker.call(unreliable_function)

        assert breaker.state == CircuitState.HALF_OPEN

        # Wait for recovery timeout again
        time.sleep(config.recovery_timeout + 0.1)

        # Phase 5: Successful calls close the circuit
        call_count = 3  # Reset to allow success
        for _ in range(config.success_threshold):
            result = breaker.call(unreliable_function)
            assert result == "success"

        assert breaker.state == CircuitState.CLOSED

    def test_concurrent_calls_protection(self):
        """Test circuit breaker handles concurrent calls."""
        import threading

        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=0.5,
        )
        breaker = CircuitBreaker("concurrent_test", config)

        call_count = 0
        lock = threading.Lock()

        def failing_function():
            nonlocal call_count
            with lock:
                call_count += 1
            raise ConnectionError("Service unavailable")

        def make_calls():
            for _ in range(3):
                try:
                    breaker.call(failing_function)
                except:
                    pass

        # Create multiple threads
        threads = [threading.Thread(target=make_calls) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Circuit should be open
        assert breaker.state == CircuitState.OPEN

        stats = breaker.get_stats()
        assert stats["total_calls"] >= call_count
