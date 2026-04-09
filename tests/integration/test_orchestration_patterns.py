#!/usr/bin/env python3
"""
Project Chimera Phase 2 - Orchestration Patterns Tests

Unit and integration tests for orchestration patterns including:
- Circuit Breaker
- Two-Phase Commit
- Saga Pattern
- Adaptive Orchestrator
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Callable

# Add services to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.orchestration.patterns import (
    CircuitBreaker,
    TwoPhaseCommit,
    SagaOrchestrator,
    AdaptiveOrchestrator,
    SentimentLevel,
    ServiceState,
    ServiceHealth,
    OrchestrationResult
)


class TestCircuitBreaker:
    """Test Circuit Breaker pattern implementation."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker with test thresholds."""
        return CircuitBreaker(
            service_name="test-service",
            failure_threshold=3,
            timeout_seconds=5,
            half_open_attempts=2
        )

    def test_initial_state(self, circuit_breaker):
        """Test circuit breaker starts in closed state."""
        assert circuit_breaker.is_closed() == True
        assert circuit_breaker._state == "closed"
        assert circuit_breaker._failure_count == 0

    def test_success_recording(self, circuit_breaker):
        """Test recording successes resets failure count."""
        # Record some failures
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        assert circuit_breaker._failure_count == 2

        # Record success
        circuit_breaker.record_success()
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker._state == "closed"

    def test_tripping_on_threshold(self, circuit_breaker):
        """Test circuit breaker trips after threshold."""
        # Record failures up to threshold
        for i in range(3):
            circuit_breaker.record_failure()

        # Should trip to open state
        assert circuit_breaker.is_closed() == False
        assert circuit_breaker._state == "open"

    def test_timeout_recovery(self, circuit_breaker):
        """Test circuit breaker recovers after timeout."""
        # Trip the circuit
        for i in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.is_closed() == False

        # Set last failure time to past (simulate timeout)
        circuit_breaker._last_failure_time = datetime.now() - timedelta(seconds=6)

        # Should enter half-open state
        assert circuit_breaker.is_closed() == True
        assert circuit_breaker._state == "half_open"

    def test_half_open_to_closed(self, circuit_breaker):
        """Test circuit breaker closes after successful half-open attempts."""
        # Trip and move to half-open
        for i in range(3):
            circuit_breaker.record_failure()
        circuit_breaker._last_failure_time = datetime.now() - timedelta(seconds=6)
        circuit_breaker.is_closed()  # Trigger state check

        # Record successful half-open attempts
        for i in range(2):
            circuit_breaker.record_success()

        # Should close
        assert circuit_breaker._state == "closed"
        assert circuit_breaker._failure_count == 0

    def test_half_open_failure_reopens(self, circuit_breaker):
        """Test circuit breaker reopens on half-open failure."""
        # Trip and move to half-open
        for i in range(3):
            circuit_breaker.record_failure()
        circuit_breaker._last_failure_time = datetime.now() - timedelta(seconds=6)
        circuit_breaker.is_closed()  # Trigger state check

        # Record failure in half-open state
        circuit_breaker.record_failure()

        # Should reopen
        assert circuit_breaker._state == "open"


class TestTwoPhaseCommit:
    """Test Two-Phase Commit pattern implementation."""

    @pytest.fixture
    def two_phase_commit(self):
        """Create 2PC coordinator."""
        return TwoPhaseCommit(["service_a", "service_b", "service_c"])

    @pytest.mark.asyncio
    async def test_successful_prepare(self, two_phase_commit):
        """Test successful prepare phase."""
        prepare_ops = {
            "service_a": lambda: asyncio.sleep(0.01) or True,
            "service_b": lambda: asyncio.sleep(0.01) or True,
            "service_c": lambda: asyncio.sleep(0.01) or True,
        }

        result = await two_phase_commit.prepare(prepare_ops)
        assert result == True
        assert len(two_phase_commit._prepared) == 3

    @pytest.mark.asyncio
    async def test_prepare_failure(self, two_phase_commit):
        """Test prepare phase with failure."""
        prepare_ops = {
            "service_a": lambda: asyncio.sleep(0.01) or True,
            "service_b": lambda: asyncio.sleep(0.01) or False,  # This fails
            "service_c": lambda: asyncio.sleep(0.01) or True,
        }

        result = await two_phase_commit.prepare(prepare_ops)
        assert result == False

    @pytest.mark.asyncio
    async def test_successful_commit(self, two_phase_commit):
        """Test successful commit phase."""
        # First prepare
        prepare_ops = {
            "service_a": lambda: asyncio.sleep(0.01) or True,
            "service_b": lambda: asyncio.sleep(0.01) or True,
        }
        await two_phase_commit.prepare(prepare_ops)

        # Then commit
        commit_ops = {
            "service_a": lambda: asyncio.sleep(0.01),
            "service_b": lambda: asyncio.sleep(0.01),
        }

        result = await two_phase_commit.commit(commit_ops)
        assert result.success == True
        assert len(result.services_involved) == 2
        assert len(result.failed_services) == 0

    @pytest.mark.asyncio
    async def test_partial_commit_failure(self, two_phase_commit):
        """Test commit with partial failures."""
        # First prepare
        prepare_ops = {
            "service_a": lambda: asyncio.sleep(0.01) or True,
            "service_b": lambda: asyncio.sleep(0.01) or True,
            "service_c": lambda: asyncio.sleep(0.01) or True,
        }
        await two_phase_commit.prepare(prepare_ops)

        # Commit with one failure
        async def failing_commit():
            raise Exception("Commit failed")

        commit_ops = {
            "service_a": lambda: asyncio.sleep(0.01),
            "service_b": failing_commit,
            "service_c": lambda: asyncio.sleep(0.01),
        }

        result = await two_phase_commit.commit(commit_ops)
        assert result.success == False
        assert len(result.failed_services) == 1
        assert "service_b" in result.failed_services

    @pytest.mark.asyncio
    async def test_rollback(self, two_phase_commit):
        """Test rollback phase."""
        rollback_ops = {
            "service_a": lambda: asyncio.sleep(0.01),
            "service_b": lambda: asyncio.sleep(0.01),
        }

        result = await two_phase_commit.rollback(rollback_ops)
        assert result.success == True
        assert len(two_phase_commit._rolled_back) == 2


class TestSagaOrchestrator:
    """Test Saga pattern implementation."""

    @pytest.fixture
    def saga(self):
        """Create Saga orchestrator."""
        return SagaOrchestrator()

    @pytest.mark.asyncio
    async def test_successful_execution(self, saga):
        """Test successful saga execution."""
        executed_steps = []

        async def step1():
            executed_steps.append("step1")
            return True

        async def compensate1():
            executed_steps.append("compensate1")

        async def step2():
            executed_steps.append("step2")
            return True

        async def compensate2():
            executed_steps.append("compensate2")

        # Execute steps
        result1 = await saga.execute_step("step1", step1, compensate1)
        result2 = await saga.execute_step("step2", step2, compensate2)

        assert result1 == True
        assert result2 == True
        assert executed_steps == ["step1", "step2"]

    @pytest.mark.asyncio
    async def test_failure_compensation(self, saga):
        """Test compensation on failure."""
        executed_steps = []

        async def step1():
            executed_steps.append("step1")
            return True

        async def compensate1():
            executed_steps.append("compensate1")

        async def step2():
            executed_steps.append("step2")
            raise Exception("Step 2 failed")

        async def compensate2():
            executed_steps.append("compensate2")

        async def step3():
            executed_steps.append("step3")
            return True

        async def compensate3():
            executed_steps.append("compensate3")

        # Execute steps
        await saga.execute_step("step1", step1, compensate1)
        result = await saga.execute_step("step2", step2, compensate2)

        assert result == False
        # Should have compensated step1
        assert "compensate1" in executed_steps

    @pytest.mark.asyncio
    async def test_reverse_compensation_order(self, saga):
        """Test that compensation happens in reverse order."""
        executed_steps = []

        async def step1():
            executed_steps.append("step1")
            return True

        async def compensate1():
            executed_steps.append("compensate1")

        async def step2():
            executed_steps.append("step2")
            return True

        async def compensate2():
            executed_steps.append("compensate2")

        async def step3():
            executed_steps.append("step3")
            raise Exception("Step 3 failed")

        async def compensate3():
            executed_steps.append("compensate3")

        # Execute steps
        await saga.execute_step("step1", step1, compensate1)
        await saga.execute_step("step2", step2, compensate2)
        await saga.execute_step("step3", step3, compensate3)

        # Compensation should happen in reverse: step2, step1
        compensate_indices = [i for i, s in enumerate(executed_steps) if "compensate" in s]
        assert executed_steps[compensate_indices[0]] == "compensate2"
        assert executed_steps[compensate_indices[1]] == "compensate1"


class TestAdaptiveOrchestrator:
    """Test Adaptive Orchestrator implementation."""

    @pytest.fixture
    def orchestrator(self):
        """Create adaptive orchestrator."""
        return AdaptiveOrchestrator(
            dmx_client=None,
            audio_client=None,
            bsl_client=None
        )

    def test_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert len(orchestrator.circuit_breakers) == 3
        assert len(orchestrator.scene_mappings) == 5
        assert len(orchestrator.audio_mappings) == 5

    def test_scene_mappings(self, orchestrator):
        """Test sentiment to scene mappings."""
        assert orchestrator.scene_mappings[SentimentLevel.VERY_NEGATIVE] == "somber_scene"
        assert orchestrator.scene_mappings[SentimentLevel.NEUTRAL] == "neutral_scene"
        assert orchestrator.scene_mappings[SentimentLevel.VERY_POSITIVE] == "celebration_scene"

    def test_audio_mappings(self, orchestrator):
        """Test sentiment to audio mappings."""
        very_negative = orchestrator.audio_mappings[SentimentLevel.VERY_NEGATIVE]
        assert very_negative["volume"] == -30
        assert very_negative["track"] == "ambient_dark"

        very_positive = orchestrator.audio_mappings[SentimentLevel.VERY_POSITIVE]
        assert very_positive["volume"] == -8
        assert very_positive["track"] == "celebration_fanfare"

    @pytest.mark.asyncio
    async def test_adaptive_response_without_clients(self, orchestrator):
        """Test adaptive response gracefully handles no clients."""
        result = await orchestrator.execute_adaptive_response(
            sentiment=SentimentLevel.POSITIVE,
            dialogue_text="Hello world"
        )

        # Should succeed but with no services invoked
        assert result.success == True
        assert len(result.services_involved) == 0

    @pytest.mark.asyncio
    async def test_emergency_stop_without_clients(self, orchestrator):
        """Test emergency stop gracefully handles no clients."""
        result = await orchestrator.execute_emergency_stop()

        # Should succeed
        assert result.success == True
        assert result.data["operation"] == "emergency_stop"


class TestOrchestrationResult:
    """Test OrchestrationResult dataclass."""

    def test_success_result(self):
        """Test successful result creation."""
        result = OrchestrationResult(
            success=True,
            services_involved=["dmx", "audio"],
            failed_services=[],
            duration_ms=150.5,
            data={"scene": "happy"}
        )

        assert result.success == True
        assert len(result.services_involved) == 2
        assert len(result.failed_services) == 0
        assert result.duration_ms == 150.5

    def test_failure_result(self):
        """Test failed result creation."""
        result = OrchestrationResult(
            success=False,
            services_involved=["dmx", "audio"],
            failed_services=["audio"],
            duration_ms=50.0,
            error_message="Audio service timeout"
        )

        assert result.success == False
        assert "audio" in result.failed_services
        assert result.error_message == "Audio service timeout"


class TestServiceHealth:
    """Test ServiceHealth dataclass."""

    def test_health_creation(self):
        """Test service health creation."""
        health = ServiceHealth(
            name="test-service",
            state=ServiceState.HEALTHY,
            last_check=datetime.now(),
            response_time_ms=25.5
        )

        assert health.name == "test-service"
        assert health.state == ServiceState.HEALTHY
        assert health.response_time_ms == 25.5
        assert health.error_message is None

    def test_degraded_health(self):
        """Test degraded health with error."""
        health = ServiceHealth(
            name="test-service",
            state=ServiceState.DEGRADED,
            last_check=datetime.now(),
            response_time_ms=500.0,
            error_message="Slow response"
        )

        assert health.state == ServiceState.DEGRADED
        assert health.response_time_ms == 500.0
        assert health.error_message == "Slow response"


@pytest.mark.integration
class TestOrchestrationIntegration:
    """Integration tests for orchestration patterns."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_2pc(self):
        """Test using circuit breaker with two-phase commit."""
        cb = CircuitBreaker("service_a", failure_threshold=2)
        tpc = TwoPhaseCommit(["service_a", "service_b"])

        # Prepare operations that respect circuit breaker
        async def prepare_a():
            if not cb.is_closed():
                raise Exception("Circuit open")
            return True

        async def prepare_b():
            return True

        # First attempt should succeed
        prepare_ops = {"service_a": prepare_a, "service_b": prepare_b}
        result = await tpc.prepare(prepare_ops)
        assert result == True

        # Trip the circuit breaker
        cb.record_failure()
        cb.record_failure()

        # Second attempt should fail due to circuit breaker
        result = await tpc.prepare(prepare_ops)
        assert result == False

    @pytest.mark.asyncio
    async def test_saga_with_compensation(self):
        """Test saga with real compensation logic."""
        saga = SagaOrchestrator()

        # Track state
        state = {"value": 0}

        async def increment():
            state["value"] += 1

        async def decrement():
            state["value"] -= 1

        async def double_increment():
            state["value"] += 2

        async def half_decrement():
            state["value"] -= 1

        # Execute successful saga
        await saga.execute_step("inc1", increment, decrement)
        await saga.execute_step("inc2", double_increment, half_decrement)

        assert state["value"] == 3

        # Now test failure
        state["value"] = 0

        async def failing_step():
            state["value"] += 1
            raise Exception("Failed")

        await saga.execute_step("inc1", increment, decrement)
        await saga.execute_step("fail", failing_step, decrement)

        # Should have compensated
        assert state["value"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
