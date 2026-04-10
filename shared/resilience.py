# shared/resilience.py
"""Retry logic and resilience patterns for Project Chimera.

This module provides decorators and utilities for implementing retry logic
with exponential backoff, making services more resilient to transient failures.
"""

import functools
import logging
import time
from typing import Any, Callable, TypeVar, cast, ParamSpec
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')
P = ParamSpec('P')


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter: bool = True,
        jitter_amount: float = 0.1,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (including initial attempt)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            strategy: Retry strategy to use
            jitter: Whether to add jitter to delays
            jitter_amount: Amount of jitter (0.1 = 10% variation)
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.strategy = strategy
        self.jitter = jitter
        self.jitter_amount = jitter_amount


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for a given attempt.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        delay = config.base_delay * (config.exponential_base ** attempt)
    elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
        delay = config.base_delay * (attempt + 1)
    else:  # FIXED_DELAY
        delay = config.base_delay

    delay = min(delay, config.max_delay)

    if config.jitter:
        jitter_range = delay * config.jitter_amount
        import random
        delay += random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def retry_on_exception(
    *exception_types: type[Exception],
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to retry function on specific exceptions.

    Args:
        *exception_types: Exception types to catch and retry on
        config: Retry configuration (uses default if None)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_exception(ConnectionError, TimeoutError, config=RetryConfig(max_attempts=3))
        def fetch_data(url: str) -> dict:
            return requests.get(url).json()
    """
    if config is None:
        config = RetryConfig()

    if not exception_types:
        exception_types = (Exception,)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e

                    if attempt == config.max_attempts - 1:
                        # Last attempt, raise the exception
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise

                    delay = _calculate_delay(attempt, config)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)

            # This should never be reached, but mypy needs it
            assert last_exception is not None
            raise cast(Exception, last_exception)

        return wrapper

    return decorator


def retry_on_condition(
    condition: Callable[[Any], bool],
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to retry function based on a condition.

    Args:
        condition: Function that takes return value and returns True if should retry
        config: Retry configuration

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_condition(lambda x: x is None, config=RetryConfig(max_attempts=3))
        def get_user(user_id: str) -> dict | None:
            return db.query(user_id)
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(config.max_attempts):
                result = func(*args, **kwargs)

                if not condition(result):
                    return result

                if attempt == config.max_attempts - 1:
                    logger.error(
                        f"Function {func.__name__} did not meet condition after {config.max_attempts} attempts"
                    )
                    return result

                delay = _calculate_delay(attempt, config)
                logger.warning(
                    f"Function {func.__name__} did not meet condition (attempt {attempt + 1}/{config.max_attempts}). "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)

            # Should not be reached
            return cast(T, None)

        return wrapper

    return decorator


def async_retry_on_exception(
    *exception_types: type[Exception],
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """Async decorator to retry function on specific exceptions.

    Args:
        *exception_types: Exception types to catch and retry on
        config: Retry configuration

    Returns:
        Decorated async function with retry logic

    Example:
        @async_retry_on_exception(aiohttp.ClientError, config=RetryConfig(max_attempts=3))
        async def fetch_data(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """
    if config is None:
        config = RetryConfig()

    if not exception_types:
        exception_types = (Exception,)

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            import asyncio

            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e

                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"Async function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise

                    delay = _calculate_delay(attempt, config)
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

            # Should not be reached
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator


class RetryTracker:
    """Track retry statistics for monitoring."""

    def __init__(self, service_name: str):
        """Initialize retry tracker.

        Args:
            service_name: Name of the service being tracked
        """
        self.service_name = service_name
        self.attempts: dict[str, int] = {}
        self.failures: dict[str, int] = {}
        self.successes: dict[str, int] = {}

    def record_attempt(self, operation: str) -> None:
        """Record a retry attempt.

        Args:
            operation: Name of the operation
        """
        self.attempts[operation] = self.attempts.get(operation, 0) + 1

    def record_failure(self, operation: str) -> None:
        """Record a failed operation.

        Args:
            operation: Name of the operation
        """
        self.failures[operation] = self.failures.get(operation, 0) + 1

    def record_success(self, operation: str) -> None:
        """Record a successful operation.

        Args:
            operation: Name of the operation
        """
        self.successes[operation] = self.successes.get(operation, 0) + 1

    def get_stats(self, operation: str) -> dict[str, int]:
        """Get statistics for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Dictionary with attempts, failures, and successes
        """
        return {
            "attempts": self.attempts.get(operation, 0),
            "failures": self.failures.get(operation, 0),
            "successes": self.successes.get(operation, 0),
        }

    def get_all_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all operations.

        Returns:
            Dictionary mapping operation names to their statistics
        """
        operations = set(self.attempts) | set(self.failures) | set(self.successes)
        return {op: self.get_stats(op) for op in operations}


# Default retry configurations for common scenarios
RETRY_CONFIGS = {
    "network": RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True,
    ),
    "database": RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=10.0,
        exponential_base=2.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True,
    ),
    "ml_inference": RetryConfig(
        max_attempts=2,
        base_delay=2.0,
        max_delay=10.0,
        exponential_base=2.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True,
    ),
    "external_api": RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True,
    ),
}
