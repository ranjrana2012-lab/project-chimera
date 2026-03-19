# services/nemoclaw-orchestrator/resilience/circuit_breaker.py
"""Circuit breaker pattern implementation for resilience"""
import time
import threading
from enum import Enum
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
import logging

from errors.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Circuit is open, blocking requests
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures before opening
    timeout: float = 60.0               # Seconds to wait before half-open
    success_threshold: int = 2          # Successes needed to close circuit
    call_timeout: Optional[float] = 30.0  # Timeout for individual calls


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for service resilience

    Prevents cascading failures by blocking requests to failing services.
    Transitions through three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open after threshold failures, requests blocked
    - HALF_OPEN: Testing if service has recovered, allows limited requests

    Usage:
        breaker = CircuitBreaker("my_service", failure_threshold=5, timeout=60)

        try:
            result = breaker.call(external_service, method_name, arg1, arg2)
        except CircuitBreakerOpenError:
            # Handle circuit open
            pass
    """

    def __init__(
        self,
        service_name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker

        Args:
            service_name: Name of the service being protected
            config: Circuit breaker configuration
        """
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._opened_at: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit statistics (copy)"""
        with self._lock:
            return CircuitBreakerStats(
                failure_count=self._stats.failure_count,
                success_count=self._stats.success_count,
                last_failure_time=self._stats.last_failure_time,
                last_success_time=self._stats.last_success_time,
                total_calls=self._stats.total_calls,
                total_failures=self._stats.total_failures,
                total_successes=self._stats.total_successes
            )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self._opened_at is None:
            return False

        elapsed = time.time() - self._opened_at
        return elapsed >= self.config.timeout

    def _record_success(self):
        """Record a successful call"""
        self._stats.last_success_time = time.time()
        self._stats.success_count += 1
        self._stats.total_successes += 1
        self._stats.failure_count = 0  # Reset consecutive failures

        # In HALF_OPEN, close circuit after threshold successes
        if self._state == CircuitState.HALF_OPEN:
            if self._stats.success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker for '{self.service_name}' closing "
                    f"after {self._stats.success_count} successes"
                )
                self._state = CircuitState.CLOSED
                self._stats.success_count = 0

    def _record_failure(self):
        """Record a failed call"""
        self._stats.last_failure_time = time.time()
        self._stats.failure_count += 1
        self._stats.total_failures += 1
        self._stats.success_count = 0  # Reset consecutive successes

        # Open circuit after threshold failures
        if self._state == CircuitState.CLOSED:
            if self._stats.failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit breaker for '{self.service_name}' opening "
                    f"after {self._stats.failure_count} failures"
                )
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
        elif self._state == CircuitState.HALF_OPEN:
            # Back to OPEN if failure in HALF_OPEN
            logger.warning(
                f"Circuit breaker for '{self.service_name}' returning to OPEN "
                f"after failure in HALF_OPEN state"
            )
            self._state = CircuitState.OPEN
            self._opened_at = time.time()

    def call(
        self,
        service: Any,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a service call with circuit breaker protection

        Args:
            service: Service instance (for logging)
            func: Function/method to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: If the function call raises an exception
        """
        with self._lock:
            self._stats.total_calls += 1

            # Check if we should transition to HALF_OPEN
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker for '{self.service_name}' transitioning "
                    f"to HALF_OPEN"
                )
                self._state = CircuitState.HALF_OPEN
                self._stats.success_count = 0

            # Raise error if circuit is OPEN
            if self._state == CircuitState.OPEN:
                logger.debug(
                    f"Circuit breaker for '{self.service_name}' is OPEN, "
                    f"blocking call to {func.__name__}"
                )
                raise CircuitBreakerOpenError(
                    message=f"Circuit breaker is open for service '{self.service_name}'",
                    service=self.service_name,
                    failure_count=self._stats.failure_count
                )

        # Execute the call
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            logger.error(
                f"Service call failed for '{self.service_name}': {e}",
                extra={
                    "service": self.service_name,
                    "function": func.__name__,
                    "state": self._state.value
                }
            )
            raise

    def reset(self):
        """Manually reset the circuit breaker to CLOSED state"""
        with self._lock:
            logger.info(f"Manually resetting circuit breaker for '{self.service_name}'")
            self._state = CircuitState.CLOSED
            self._stats = CircuitBreakerStats()
            self._opened_at = None

    def get_state_info(self) -> Dict[str, Any]:
        """Get detailed state information"""
        with self._lock:
            return {
                "service": self.service_name,
                "state": self._state.value,
                "failure_count": self._stats.failure_count,
                "success_count": self._stats.success_count,
                "total_calls": self._stats.total_calls,
                "total_failures": self._stats.total_failures,
                "total_successes": self._stats.total_successes,
                "last_failure_time": self._stats.last_failure_time,
                "last_success_time": self._stats.last_success_time,
                "opened_at": self._opened_at,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "timeout": self.config.timeout,
                    "success_threshold": self.config.success_threshold,
                    "call_timeout": self.config.call_timeout
                }
            }
