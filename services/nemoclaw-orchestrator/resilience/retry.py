# services/nemoclaw-orchestrator/resilience/retry.py
"""Retry logic with exponential backoff for resilient service calls"""
import asyncio
import time
from typing import Any, Callable, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

from errors.exceptions import RetryExhaustedError, AgentUnavailableError
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


class FallbackMode(str, Enum):
    """Fallback behavior when retries are exhausted"""
    GRACEFUL = "graceful"       # Return degraded response
    CACHED = "cached"           # Return cached data if available
    ERROR = "error"             # Raise error


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0     # Base delay in seconds
    max_delay: float = 10.0     # Maximum delay between retries
    exponential_base: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True         # Add random jitter to delays
    fallback_mode: FallbackMode = FallbackMode.GRACEFUL
    retryable_exceptions: tuple = (
        ConnectionError,
        TimeoutError,
        AgentUnavailableError,
    )


@dataclass
class CallResult:
    """Result of a service call attempt"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempt: int = 0
    total_duration: float = 0.0


class ResilientAgentCaller:
    """
    Resilient agent caller with retry logic and circuit breaker

    Combines exponential backoff retry with circuit breaker pattern
    for maximum resilience when calling external agent services.

    Usage:
        caller = ResilientAgentCaller(
            agent_name="scenespeak",
            agent_url="http://localhost:8001",
            max_retries=3
        )

        try:
            result = await caller.call_with_retry(
                method="generate_scene",
                payload={"prompt": "A sunny day"}
            )
        except RetryExhaustedError:
            # Handle exhausted retries
            pass
    """

    def __init__(
        self,
        agent_name: str,
        agent_url: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize resilient agent caller

        Args:
            agent_name: Name of the agent service
            agent_url: URL of the agent service
            retry_config: Retry configuration
            circuit_config: Circuit breaker configuration
        """
        self.agent_name = agent_name
        self.agent_url = agent_url
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(
            service_name=agent_name,
            config=circuit_config or CircuitBreakerConfig()
        )
        self._cache: Dict[str, Any] = {}

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt with exponential backoff

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )

        if self.retry_config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def _is_retryable(self, error: Exception) -> bool:
        """
        Check if an error is retryable

        Args:
            error: Exception to check

        Returns:
            True if error should trigger a retry
        """
        return isinstance(error, self.retry_config.retryable_exceptions)

    def _fallback_response(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback response when retries are exhausted

        Args:
            method: Method name that was called
            payload: Original payload

        Returns:
            Fallback response dictionary
        """
        logger.warning(
            f"Using fallback response for {self.agent_name}.{method}",
            extra={"agent": self.agent_name, "method": method}
        )

        # Check cache first
        if self.retry_config.fallback_mode == FallbackMode.CACHED:
            cache_key = f"{self.agent_name}:{method}:{hash(str(payload))}"
            if cache_key in self._cache:
                logger.info(f"Returning cached response for {cache_key}")
                return self._cache[cache_key]

        # Return graceful degraded response
        return {
            "status": "degraded",
            "agent": self.agent_name,
            "method": method,
            "message": "Service unavailable, returning degraded response",
            "timestamp": time.time(),
            "data": None
        }

    def call_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function call with retry logic and circuit breaker

        Synchronous version.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the function call

        Raises:
            RetryExhaustedError: If all retries are exhausted
            CircuitBreakerOpenError: If circuit breaker is open
        """
        start_time = time.time()
        last_error = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Use circuit breaker for the call
                result = self.circuit_breaker.call(
                    service=self.agent_name,
                    func=func,
                    *args,
                    **kwargs
                )

                # Cache successful result if using cached fallback
                if attempt == 0 and self.retry_config.fallback_mode == FallbackMode.CACHED:
                    cache_key = f"{self.agent_name}:{func.__name__}:{hash(str(args) + str(kwargs))}"
                    self._cache[cache_key] = result

                duration = time.time() - start_time
                logger.info(
                    f"Agent call succeeded for {self.agent_name}.{func.__name__} "
                    f"on attempt {attempt + 1}",
                    extra={
                        "agent": self.agent_name,
                        "method": func.__name__,
                        "attempt": attempt + 1,
                        "duration": duration
                    }
                )

                return result

            except Exception as e:
                last_error = e

                # Check if error is retryable
                if not self._is_retryable(e):
                    logger.error(
                        f"Non-retryable error for {self.agent_name}.{func.__name__}: {e}",
                        extra={"agent": self.agent_name, "method": func.__name__}
                    )
                    raise

                # Check if we should retry
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Agent call failed for {self.agent_name}.{func.__name__} "
                        f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {e}",
                        extra={
                            "agent": self.agent_name,
                            "method": func.__name__,
                            "attempt": attempt + 1,
                            "next_delay": delay
                        }
                    )
                    time.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(
                        f"All retries exhausted for {self.agent_name}.{func.__name__}: {e}",
                        extra={
                            "agent": self.agent_name,
                            "method": func.__name__,
                            "attempts": attempt + 1
                        }
                    )

                    # Handle based on fallback mode
                    if self.retry_config.fallback_mode == FallbackMode.ERROR:
                        raise RetryExhaustedError(
                            message=f"Retries exhausted for {self.agent_name}.{func.__name__}",
                            attempts=attempt + 1,
                            last_error=str(e)
                        )
                    else:
                        # Return fallback response
                        return self._fallback_response(
                            func.__name__,
                            kwargs.get("payload", {})
                        )

    async def call_with_retry_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an async function call with retry logic and circuit breaker

        Async version.

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the function call

        Raises:
            RetryExhaustedError: If all retries are exhausted
            CircuitBreakerOpenError: If circuit breaker is open
        """
        start_time = time.time()
        last_error = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # For async, we need to handle differently
                # Circuit breaker call is synchronous, so we wrap the async func
                result = await func(*args, **kwargs)

                # Cache successful result if using cached fallback
                if attempt == 0 and self.retry_config.fallback_mode == FallbackMode.CACHED:
                    cache_key = f"{self.agent_name}:{func.__name__}:{hash(str(args) + str(kwargs))}"
                    self._cache[cache_key] = result

                duration = time.time() - start_time
                logger.info(
                    f"Async agent call succeeded for {self.agent_name}.{func.__name__} "
                    f"on attempt {attempt + 1}",
                    extra={
                        "agent": self.agent_name,
                        "method": func.__name__,
                        "attempt": attempt + 1,
                        "duration": duration
                    }
                )

                # Record success in circuit breaker
                self.circuit_breaker._record_success()
                return result

            except Exception as e:
                last_error = e

                # Record failure in circuit breaker
                self.circuit_breaker._record_failure()

                # Check if error is retryable
                if not self._is_retryable(e):
                    logger.error(
                        f"Non-retryable error for {self.agent_name}.{func.__name__}: {e}",
                        extra={"agent": self.agent_name, "method": func.__name__}
                    )
                    raise

                # Check if we should retry
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Async agent call failed for {self.agent_name}.{func.__name__} "
                        f"(attempt {attempt + 1}/{self.retry_config.max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {e}",
                        extra={
                            "agent": self.agent_name,
                            "method": func.__name__,
                            "attempt": attempt + 1,
                            "next_delay": delay
                        }
                    )
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(
                        f"All retries exhausted for {self.agent_name}.{func.__name__}: {e}",
                        extra={
                            "agent": self.agent_name,
                            "method": func.__name__,
                            "attempts": attempt + 1
                        }
                    )

                    # Handle based on fallback mode
                    if self.retry_config.fallback_mode == FallbackMode.ERROR:
                        raise RetryExhaustedError(
                            message=f"Retries exhausted for {self.agent_name}.{func.__name__}",
                            attempts=attempt + 1,
                            last_error=str(e)
                        )
                    else:
                        # Return fallback response
                        return self._fallback_response(
                            func.__name__,
                            kwargs.get("payload", {})
                        )

    def get_circuit_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return self.circuit_breaker.get_state_info()

    def reset_circuit(self):
        """Reset the circuit breaker"""
        self.circuit_breaker.reset()

    def clear_cache(self):
        """Clear the response cache"""
        self._cache.clear()
