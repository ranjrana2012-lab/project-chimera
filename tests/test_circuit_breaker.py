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
