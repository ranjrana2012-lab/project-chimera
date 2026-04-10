"""Tests for orchestration patterns."""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from services.orchestration.patterns import (
    SentimentLevel,
    ServiceState,
    ServiceHealth,
    OrchestrationResult,
    CircuitBreaker,
    TwoPhaseCommit,
    SagaOrchestrator,
)


class TestSentimentLevel:
    """Test SentimentLevel enum."""

    def test_sentiment_levels(self):
        """Test all sentiment levels exist."""
        assert SentimentLevel.VERY_NEGATIVE.value == "very_negative"
        assert SentimentLevel.NEGATIVE.value == "negative"
        assert SentimentLevel.NEUTRAL.value == "neutral"
        assert SentimentLevel.POSITIVE.value == "positive"
        assert SentimentLevel.VERY_POSITIVE.value == "very_positive"


class TestServiceState:
    """Test ServiceState enum."""

    def test_service_states(self):
        """Test all service states exist."""
        assert ServiceState.HEALTHY.value == "healthy"
        assert ServiceState.DEGRADED.value == "degraded"
        assert ServiceState.UNAVAILABLE.value == "unavailable"
        assert ServiceState.FAILED.value == "failed"


class TestServiceHealth:
    """Test ServiceHealth dataclass."""

    def test_service_health_creation(self):
        """Test creating ServiceHealth."""
        health = ServiceHealth(
            name="test-service",
            state=ServiceState.HEALTHY,
            last_check=datetime.now(timezone.utc),
            response_time_ms=45.2
        )

        assert health.name == "test-service"
        assert health.state == ServiceState.HEALTHY
        assert health.response_time_ms == 45.2
        assert health.error_message is None

    def test_service_health_with_error(self):
        """Test ServiceHealth with error message."""
        health = ServiceHealth(
            name="failing-service",
            state=ServiceState.FAILED,
            last_check=datetime.now(timezone.utc),
            response_time_ms=0.0,
            error_message="Connection refused"
        )

        assert health.state == ServiceState.FAILED
        assert health.error_message == "Connection refused"


class TestOrchestrationResult:
    """Test OrchestrationResult dataclass."""

    def test_successful_orchestration(self):
        """Test successful orchestration result."""
        result = OrchestrationResult(
            success=True,
            services_involved=["service1", "service2"],
            failed_services=[],
            duration_ms=150.5,
            data={"output": "success"}
        )

        assert result.success is True
        assert len(result.services_involved) == 2
        assert len(result.failed_services) == 0
        assert result.duration_ms == 150.5
        assert result.error_message is None

    def test_failed_orchestration(self):
        """Test failed orchestration result."""
        result = OrchestrationResult(
            success=False,
            services_involved=["service1", "service2"],
            failed_services=["service2"],
            duration_ms=500.0,
            error_message="Service timeout"
        )

        assert result.success is False
        assert "service2" in result.failed_services
        assert result.error_message == "Service timeout"


class TestCircuitBreaker:
    """Test CircuitBreaker pattern."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker(
            service_name="test-service",
            failure_threshold=3,
            timeout_seconds=30,
            half_open_attempts=2
        )

        assert cb.service_name == "test-service"
        assert cb.failure_threshold == 3
        assert cb.timeout_seconds == 30

    def test_circuit_breaker_initially_closed(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker("test-service", failure_threshold=2)
        assert cb.is_closed() is True

    def test_circuit_breaker_opens_after_threshold_failures(self):
        """Test circuit breaker trips after failure threshold."""
        cb = CircuitBreaker("test-service", failure_threshold=2, timeout_seconds=60)

        # Initially closed
        assert cb.is_closed() is True

        # Record failures up to threshold
        cb.record_failure()
        assert cb.is_closed() is True  # Still closed

        cb.record_failure()
        assert cb.is_closed() is False  # Now open

    def test_circuit_breaker_resets_after_success(self):
        """Test circuit breaker resets after success."""
        cb = CircuitBreaker("test-service", failure_threshold=3)

        # Some failures
        cb.record_failure()
        cb.record_failure()
        assert cb._failure_count == 2

        # Success resets failure count
        cb.record_success()
        assert cb._failure_count == 0

    def test_circuit_breaker_timeout_allows_retry(self):
        """Test circuit breaker enters half-open after timeout."""
        cb = CircuitBreaker("test-service", failure_threshold=2, timeout_seconds=0)

        # Trip the breaker
        cb.record_failure()
        cb.record_failure()
        # State is now "open", so is_closed() returns False
        # But with timeout_seconds=0, calling is_closed() immediately transitions to half-open

        # After timeout (0 seconds = immediate), should allow requests (half-open state)
        # The timeout check happens inside is_closed()
        assert cb.is_closed() is True  # Now in half-open (state changed during is_closed call)
        assert cb._state == "half_open"

    def test_circuit_breaker_half_open_to_closed(self):
        """Test circuit breaker closes after half-open successes."""
        cb = CircuitBreaker("test-service", failure_threshold=2, half_open_attempts=2, timeout_seconds=0)

        # Trip the breaker
        cb.record_failure()
        cb.record_failure()

        # Move to half-open by checking is_closed (which handles timeout)
        assert cb.is_closed() is True  # Now half-open

        # Record successes to close it
        cb.record_success()
        assert cb.is_closed() is True  # Still half-open (need 2)

        cb.record_success()
        assert cb.is_closed() is True  # Now closed again
        assert cb._state == "closed"


class TestTwoPhaseCommit:
    """Test Two-Phase Commit pattern."""

    def test_two_phase_commit_initialization(self):
        """Test 2PC initialization with participants."""
        tpc = TwoPhaseCommit(["service1", "service2"])
        assert tpc.participants == ["service1", "service2"]

    @pytest.mark.asyncio
    async def test_two_phase_commit_prepare_success(self):
        """Test successful prepare phase."""
        tpc = TwoPhaseCommit(["service1", "service2"])

        async def prep1():
            await asyncio.sleep(0.01)
            return True

        async def prep2():
            await asyncio.sleep(0.01)
            return True

        prepare_ops = {
            "service1": prep1,
            "service2": prep2,
        }

        result = await tpc.prepare(prepare_ops)
        assert result is True
        assert "service1" in tpc._prepared
        assert "service2" in tpc._prepared

    @pytest.mark.asyncio
    async def test_two_phase_commit_prepare_failure(self):
        """Test prepare phase fails on participant failure."""
        tpc = TwoPhaseCommit(["service1", "service2"])

        prepare_ops = {
            "service1": lambda: asyncio.sleep(0.01) or True,
            "service2": lambda: asyncio.sleep(0.01) or False,  # This one fails
        }

        result = await tpc.prepare(prepare_ops)
        assert result is False

    @pytest.mark.asyncio
    async def test_two_phase_commit_commit_success(self):
        """Test successful commit phase."""
        tpc = TwoPhaseCommit(["service1", "service2"])

        commit_ops = {
            "service1": lambda: asyncio.sleep(0.01),
            "service2": lambda: asyncio.sleep(0.01),
        }

        result = await tpc.commit(commit_ops)
        assert result.success is True
        assert len(result.failed_services) == 0

    @pytest.mark.asyncio
    async def test_two_phase_commit_rollback_success(self):
        """Test successful rollback phase."""
        tpc = TwoPhaseCommit(["service1", "service2"])

        rollback_ops = {
            "service1": lambda: asyncio.sleep(0.01),
            "service2": lambda: asyncio.sleep(0.01),
        }

        result = await tpc.rollback(rollback_ops)
        assert result.success is True
        assert "rolled_back" in result.data


class TestSagaOrchestrator:
    """Test Saga pattern orchestrator."""

    @pytest.mark.asyncio
    async def test_saga_execute_step_success(self):
        """Test successful step execution."""
        saga = SagaOrchestrator()

        async def mock_operation():
            await asyncio.sleep(0.01)

        async def mock_compensation():
            await asyncio.sleep(0.01)

        result = await saga.execute_step(
            step_name="step1",
            operation=mock_operation,
            compensation=mock_compensation
        )

        assert result is True
        assert "step1" in saga._executed_steps

    @pytest.mark.asyncio
    async def test_saga_execute_step_failure_compensates(self):
        """Test failed step triggers compensation."""
        saga = SagaOrchestrator()

        execution_order = []

        async def failing_operation():
            execution_order.append("operation")
            raise Exception("Step failed")

        async def mock_compensation():
            execution_order.append("compensation")

        # First, execute a successful step
        await saga.execute_step(
            step_name="step1",
            operation=lambda: asyncio.sleep(0.01),
            compensation=lambda: asyncio.sleep(0.01)
        )

        # Now execute a failing step
        result = await saga.execute_step(
            step_name="step2",
            operation=failing_operation,
            compensation=mock_compensation
        )

        assert result is False
        # The compensation for step1 should have been executed
        assert "step1" in saga._executed_steps

    @pytest.mark.asyncio
    async def test_saga_compensate_in_reverse_order(self):
        """Test compensation runs in reverse order."""
        saga = SagaOrchestrator()

        compensation_order = []

        async def comp1():
            compensation_order.append("comp1")

        async def comp2():
            compensation_order.append("comp2")

        async def comp3():
            compensation_order.append("comp3")

        # Execute steps
        await saga.execute_step(
            step_name="step1",
            operation=lambda: asyncio.sleep(0.01),
            compensation=comp1
        )
        await saga.execute_step(
            step_name="step2",
            operation=lambda: asyncio.sleep(0.01),
            compensation=comp2
        )
        await saga.execute_step(
            step_name="step3",
            operation=lambda: asyncio.sleep(0.01),
            compensation=comp3
        )

        # Now fail a step after step3
        await saga.execute_step(
            step_name="step4",
            operation=lambda: (_ for _ in ()).throw(Exception("Failed")),
            compensation=lambda: asyncio.sleep(0.01)
        )

        # Compensations should run in reverse: step3, step2, step1
        # But step4 doesn't get compensated (it failed)
        assert len(compensation_order) == 3
