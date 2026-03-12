# shared/circuit_breaker.py
"""Circuit breaker pattern implementation for Project Chimera.

This module provides circuit breaker functionality to prevent cascading failures
and allow services to degrade gracefully when dependencies are failing.
"""

import logging
import threading
import time
from enum import Enum
from typing import Any, Callable, TypeVar, cast, ParamSpec
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')
P = ParamSpec('P')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, service_name: str, message: str | None = None):
        """Initialize circuit breaker error.

        Args:
            service_name: Name of the protected service
            message: Optional error message
        """
        self.service_name = service_name
        super().__init__(message or f"Circuit breaker is open for service: {service_name}")


class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        timeout: float = 30.0,
        half_open_max_calls: int | None = None,
    ):
        """Initialize circuit breaker configuration.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Successes needed to close circuit in half-open state
            timeout: Seconds before timing out a call
            half_open_max_calls: Max calls allowed in half-open state (defaults to success_threshold)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls or success_threshold


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(
        self,
        service_name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        """Initialize circuit breaker.

        Args:
            service_name: Name of the service being protected
            config: Circuit breaker configuration
        """
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._opened_at: datetime | None = None
        self._half_open_calls = 0

        self._lock = threading.RLock()

        # Statistics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._total_rejected = 0
        self._total_timeouts = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        with self._lock:
            return self._failure_count

    @property
    def success_count(self) -> int:
        """Get current success count."""
        with self._lock:
            return self._success_count

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset.

        Returns:
            True if enough time has passed to try recovery
        """
        if self._opened_at is None:
            return False

        elapsed = (datetime.now() - self._opened_at).total_seconds()
        return elapsed >= self.config.recovery_timeout

    def _record_failure(self) -> None:
        """Record a failure and potentially open circuit."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        self._total_failures += 1

        if self._state == CircuitState.HALF_OPEN:
            # Failed during recovery, go back to open
            logger.warning(
                f"Circuit breaker for {self.service_name} failed during half-open state. "
                f"Reopening circuit."
            )
            self._state = CircuitState.OPEN
            self._opened_at = datetime.now()
            self._half_open_calls = 0
        elif self._failure_count >= self.config.failure_threshold:
            # Threshold reached, open circuit
            logger.error(
                f"Circuit breaker for {self.service_name} opening after "
                f"{self._failure_count} failures."
            )
            self._state = CircuitState.OPEN
            self._opened_at = datetime.now()

    def _record_success(self) -> None:
        """Record a success and potentially close circuit."""
        self._total_successes += 1

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1

            if self._success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker for {self.service_name} closing after "
                    f"{self._success_count} consecutive successes."
                )
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._opened_at = None
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on successful call
            self._failure_count = 0

    def call(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute a function through the circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function return value

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function raises an exception
        """
        with self._lock:
            self._total_calls += 1

            # Check if we should attempt recovery
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker for {self.service_name} attempting recovery. "
                    f"Transitioning to half-open state."
                )
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0

            # Reject calls if circuit is open
            if self._state == CircuitState.OPEN:
                self._total_rejected += 1
                raise CircuitBreakerError(
                    self.service_name,
                    f"Circuit breaker is open for {self.service_name}. "
                    f"Rejecting call. Attempting recovery in "
                    f"{self.config.recovery_timeout - (datetime.now() - self._opened_at).total_seconds():.1f}s"
                )

            # Limit calls in half-open state
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._total_rejected += 1
                    raise CircuitBreakerError(
                        self.service_name,
                        f"Circuit breaker for {self.service_name} is in half-open state. "
                        f"Maximum test calls reached."
                    )
                self._half_open_calls += 1

        try:
            # Execute with timeout
            import signal

            def timeout_handler(signum: int, frame: Any) -> None:
                raise TimeoutError(f"Call to {self.service_name} timed out")

            if self.config.timeout > 0:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.config.timeout))

            result = func(*args, **kwargs)

            if self.config.timeout > 0:
                signal.alarm(0)

            with self._lock:
                self._record_success()

            return result

        except Exception as e:
            with self._lock:
                if isinstance(e, TimeoutError):
                    self._total_timeouts += 1
                self._record_failure()
            raise

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics.

        Returns:
            Dictionary with current state and statistics
        """
        with self._lock:
            return {
                "service_name": self.service_name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "total_calls": self._total_calls,
                "total_failures": self._total_failures,
                "total_successes": self._total_successes,
                "total_rejected": self._total_rejected,
                "total_timeouts": self._total_timeouts,
                "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "opened_at": self._opened_at.isoformat() if self._opened_at else None,
            }

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self._lock:
            logger.info(f"Resetting circuit breaker for {self.service_name}")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._opened_at = None
            self._half_open_calls = 0


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        """Initialize circuit breaker registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def get_breaker(
        self,
        service_name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker for a service.

        Args:
            service_name: Name of the service
            config: Optional configuration (only used on first creation)

        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if service_name not in self._breakers:
                self._breakers[service_name] = CircuitBreaker(service_name, config)
            return self._breakers[service_name]

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers.

        Returns:
            Dictionary mapping service names to their stats
        """
        with self._lock:
            return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()

    def reset_breaker(self, service_name: str) -> bool:
        """Reset a specific circuit breaker.

        Args:
            service_name: Name of the service

        Returns:
            True if breaker was found and reset, False otherwise
        """
        with self._lock:
            if service_name in self._breakers:
                self._breakers[service_name].reset()
                return True
            return False


# Global circuit breaker registry
_global_registry = CircuitBreakerRegistry()


def with_circuit_breaker(
    service_name: str | None = None,
    config: CircuitBreakerConfig | None = None,
    registry: CircuitBreakerRegistry | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to protect function calls with circuit breaker.

    Args:
        service_name: Name of the service (defaults to function name)
        config: Circuit breaker configuration
        registry: Circuit breaker registry (uses global if None)

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @with_circuit_breaker(
            service_name="external_api",
            config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)
        )
        def fetch_external_data(url: str) -> dict:
            return requests.get(url).json()
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        name = service_name or func.__name__
        reg = registry or _global_registry

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            breaker = reg.get_breaker(name, config)
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


# Default circuit breaker configurations for common scenarios
CIRCUIT_CONFIGS = {
    "database": CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=2,
        timeout=10.0,
    ),
    "external_api": CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=120.0,
        success_threshold=2,
        timeout=30.0,
    ),
    "ml_service": CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=180.0,
        success_threshold=2,
        timeout=60.0,
    ),
    "cache": CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=30.0,
        success_threshold=3,
        timeout=5.0,
    ),
}


def get_circuit_breaker(service_name: str, config_type: str = "external_api") -> CircuitBreaker:
    """Get a circuit breaker with predefined configuration.

    Args:
        service_name: Name of the service
        config_type: Type of configuration to use

    Returns:
        CircuitBreaker instance
    """
    config = CIRCUIT_CONFIGS.get(config_type, CIRCUIT_CONFIGS["external_api"])
    return _global_registry.get_breaker(service_name, config)


def get_all_circuit_breaker_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all circuit breakers in the global registry.

    Returns:
        Dictionary mapping service names to their stats
    """
    return _global_registry.get_all_stats()
