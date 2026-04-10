"""Tests for async retry functionality."""
import pytest
import asyncio
from shared.resilience import (
    async_retry_on_exception,
    RetryConfig,
    RetryStrategy,
)


class TestAsyncRetryOnException:
    """Tests for async_retry_on_exception decorator."""

    @pytest.mark.asyncio
    async def test_async_success_no_retry(self):
        """Test async function that succeeds without retry."""
        @async_retry_on_exception(ConnectionError)
        async def async_function():
            return {"status": "ok"}

        result = await async_function()
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_async_retry_on_specific_exception(self):
        """Test async retry on specific exception type."""
        call_count = 0

        @async_retry_on_exception(ConnectionError, config=RetryConfig(
            max_attempts=3,
            base_delay=0.01,
        ))
        async def failing_async_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return {"status": "ok"}

        result = await failing_async_function()
        assert result == {"status": "ok"}
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_max_attempts_exceeded(self):
        """Test async function raises after max attempts."""
        @async_retry_on_exception(ConnectionError, config=RetryConfig(
            max_attempts=2,
            base_delay=0.01,
        ))
        async def always_failing_async_function():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError) as exc_info:
            await always_failing_async_function()

        assert "Always fails" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_no_retry_on_different_exception(self):
        """Test async function doesn't retry on different exception."""
        call_count = 0

        @async_retry_on_exception(TimeoutError)
        async def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Different error")

        with pytest.raises(ValueError):
            await raise_value_error()

        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_async_retry_with_default_config(self):
        """Test async retry with default configuration."""
        call_count = 0

        @async_retry_on_exception(ConnectionError)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Failed")
            return "success"

        result = await failing_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_retry_multiple_exception_types(self):
        """Test async retry with multiple exception types."""
        call_count = 0

        @async_retry_on_exception(
            ConnectionError,
            TimeoutError,
            config=RetryConfig(max_attempts=4, base_delay=0.01)
        )
        async def failing_with_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection failed")
            elif call_count == 2:
                raise TimeoutError("Request timed out")
            return "success"

        result = await failing_with_different_errors()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_delay_between_retries(self):
        """Test async function has delay between retries."""
        import time
        call_count = 0

        @async_retry_on_exception(ConnectionError, config=RetryConfig(
            max_attempts=3,
            base_delay=0.05,
        ))
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Failed")
            return "success"

        start = time.time()
        result = await failing_function()
        elapsed = time.time() - start

        assert result == "success"
        assert call_count == 3
        # Should have at least 2 delays (after attempt 1 and 2)
        assert elapsed >= 0.1  # 2 * 0.05 minimum

    @pytest.mark.asyncio
    async def test_async_retry_with_different_strategies(self):
        """Test async retry with different backoff strategies."""
        for strategy in [RetryStrategy.EXPONENTIAL_BACKOFF, RetryStrategy.FIXED_DELAY, RetryStrategy.LINEAR_BACKOFF]:
            call_count = 0

            @async_retry_on_exception(ConnectionError, config=RetryConfig(
                max_attempts=3,
                base_delay=0.01,
                strategy=strategy,
            ))
            async def failing_function():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ConnectionError("Failed")
                return f"success-{strategy.value}"

            result = await failing_function()
            assert result == f"success-{strategy.value}"
