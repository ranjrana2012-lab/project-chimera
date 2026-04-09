#!/usr/bin/env python3
"""
Service Orchestration Patterns
Project Chimera Phase 2 - Service Coordination

This module provides orchestration patterns for coordinating
multiple Phase 2 services (DMX, Audio, BSL) in live performances.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentLevel(Enum):
    """Audience sentiment levels for adaptive responses."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class ServiceState(Enum):
    """Service states for orchestration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass
class ServiceHealth:
    """Health status of a service."""
    name: str
    state: ServiceState
    last_check: datetime
    response_time_ms: float
    error_message: Optional[str] = None


@dataclass
class OrchestrationResult:
    """Result of an orchestration operation."""
    success: bool
    services_involved: List[str]
    failed_services: List[str]
    duration_ms: float
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class CircuitBreaker:
    """
    Circuit Breaker Pattern for Service Resilience

    Prevents cascading failures by tripping open when a service
    fails repeatedly, allowing it time to recover.
    """

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_attempts: int = 3
    ):
        """
        Initialize circuit breaker.

        Args:
            service_name: Name of the service being protected
            failure_threshold: Failures before tripping open
            timeout_seconds: Seconds to wait before trying again
            half_open_attempts: Attempts in half-open state
        """
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_attempts = half_open_attempts

        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = "closed"  # closed, open, half_open
        self._half_open_success_count = 0

    def is_closed(self) -> bool:
        """Check if circuit is closed (allowing requests)."""
        if self._state == "open":
            # Check if timeout has elapsed
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    logger.info(f"Circuit breaker for {self.service_name} entering half-open state")
                    self._state = "half_open"
                    self._half_open_success_count = 0
                    return True
            return False
        return True

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == "half_open":
            self._half_open_success_count += 1
            if self._half_open_success_count >= self.half_open_attempts:
                logger.info(f"Circuit breaker for {self.service_name} closing")
                self._state = "closed"
                self._failure_count = 0
        elif self._state == "closed":
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._state == "half_open":
            logger.warning(f"Circuit breaker for {self.service_name} opening (half-open failed)")
            self._state = "open"
        elif self._failure_count >= self.failure_threshold:
            logger.warning(f"Circuit breaker for {self.service_name} opening (threshold reached)")
            self._state = "open"


class TwoPhaseCommit:
    """
    Two-Phase Commit Pattern for Distributed Transactions

    Ensures atomic operations across multiple services by using
    a prepare-commit-rollback protocol.
    """

    def __init__(self, participants: List[str]):
        """
        Initialize 2PC coordinator.

        Args:
            participants: List of service names involved
        """
        self.participants = participants
        self._prepared: Dict[str, bool] = {}
        self._committed: Dict[str, bool] = {}
        self._rolled_back: Dict[str, bool] = {}

    async def prepare(self, operations: Dict[str, Callable]) -> bool:
        """
        Phase 1: Prepare all participants.

        Args:
            operations: Dictionary of service -> prepare function

        Returns:
            True if all participants prepared successfully
        """
        logger.info(f"Starting prepare phase for {len(self.participants)} participants")

        for participant in self.participants:
            if participant not in operations:
                logger.error(f"No prepare operation for {participant}")
                return False

            try:
                logger.info(f"Preparing {participant}...")
                result = await operations[participant]()
                if result:
                    self._prepared[participant] = True
                    logger.info(f"{participant} prepared successfully")
                else:
                    logger.error(f"{participant} prepare failed")
                    return False
            except Exception as e:
                logger.error(f"{participant} prepare exception: {e}")
                return False

        return all(self._prepared.values())

    async def commit(self, operations: Dict[str, Callable]) -> OrchestrationResult:
        """
        Phase 2: Commit all participants.

        Args:
            operations: Dictionary of service -> commit function

        Returns:
            OrchestrationResult with commit status
        """
        start_time = datetime.now()
        failed_services = []

        logger.info("Starting commit phase")

        for participant in self.participants:
            if participant not in operations:
                failed_services.append(participant)
                continue

            try:
                logger.info(f"Committing {participant}...")
                await operations[participant]()
                self._committed[participant] = True
                logger.info(f"{participant} committed successfully")
            except Exception as e:
                logger.error(f"{participant} commit failed: {e}")
                failed_services.append(participant)

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return OrchestrationResult(
            success=len(failed_services) == 0,
            services_involved=self.participants,
            failed_services=failed_services,
            duration_ms=duration_ms,
            data={
                "committed": list(self._committed.keys()),
                "prepared": list(self._prepared.keys())
            }
        )

    async def rollback(self, operations: Dict[str, Callable]) -> OrchestrationResult:
        """
        Rollback all participants.

        Args:
            operations: Dictionary of service -> rollback function

        Returns:
            OrchestrationResult with rollback status
        """
        start_time = datetime.now()
        failed_services = []

        logger.warning("Starting rollback phase")

        for participant in self.participants:
            if participant not in operations:
                failed_services.append(participant)
                continue

            try:
                logger.info(f"Rolling back {participant}...")
                await operations[participant]()
                self._rolled_back[participant] = True
                logger.info(f"{participant} rolled back successfully")
            except Exception as e:
                logger.error(f"{participant} rollback failed: {e}")
                failed_services.append(participant)

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return OrchestrationResult(
            success=len(failed_services) == 0,
            services_involved=self.participants,
            failed_services=failed_services,
            duration_ms=duration_ms,
            data={
                "rolled_back": list(self._rolled_back.keys())
            }
        )


class SagaOrchestrator:
    """
    Saga Pattern for Distributed Transactions

    Executes a sequence of operations with compensating transactions
    to handle failures gracefully.
    """

    def __init__(self):
        """Initialize Saga orchestrator."""
        self._executed_steps: List[str] = []
        self._compensations: Dict[str, Callable] = {}

    async def execute_step(
        self,
        step_name: str,
        operation: Callable,
        compensation: Callable
    ) -> bool:
        """
        Execute a single step with compensation.

        Args:
            step_name: Name of the step
            operation: Function to execute
            compensation: Compensation function if step fails

        Returns:
            True if step succeeded
        """
        try:
            logger.info(f"Executing step: {step_name}")
            await operation()
            self._executed_steps.append(step_name)
            self._compensations[step_name] = compensation
            return True
        except Exception as e:
            logger.error(f"Step {step_name} failed: {e}")
            await self._compensate(step_name)
            return False

    async def _compensate(self, failed_step: str) -> None:
        """
        Compensate for failed step by running compensating transactions.

        Args:
            failed_step: Name of the step that failed
        """
        logger.warning(f"Compensating for failed step: {failed_step}")

        # Compensate in reverse order
        for step in reversed(self._executed_steps):
            if step == failed_step:
                break
            if step in self._compensations:
                try:
                    logger.info(f"Running compensation for: {step}")
                    await self._compensations[step]()
                    logger.info(f"Compensation for {step} completed")
                except Exception as e:
                    logger.error(f"Compensation for {step} failed: {e}")


class AdaptiveOrchestrator:
    """
    Adaptive Orchestration for Sentiment-Based Responses

    Coordinates services to deliver adaptive experiences based on
    audience sentiment analysis.
    """

    def __init__(
        self,
        dmx_client=None,
        audio_client=None,
        bsl_client=None
    ):
        """
        Initialize adaptive orchestrator.

        Args:
            dmx_client: DMX controller client
            audio_client: Audio controller client
            bsl_client: BSL avatar service client
        """
        self.dmx_client = dmx_client
        self.audio_client = audio_client
        self.bsl_client = bsl_client

        # Circuit breakers for each service
        self.circuit_breakers = {
            "dmx": CircuitBreaker("dmx-controller"),
            "audio": CircuitBreaker("audio-controller"),
            "bsl": CircuitBreaker("bsl-avatar-service")
        }

        # Sentiment-based scene mappings
        self.scene_mappings = {
            SentimentLevel.VERY_NEGATIVE: "somber_scene",
            SentimentLevel.NEGATIVE: "tense_scene",
            SentimentLevel.NEUTRAL: "neutral_scene",
            SentimentLevel.POSITIVE: "bright_scene",
            SentimentLevel.VERY_POSITIVE: "celebration_scene"
        }

        # Sentiment-based audio mappings
        self.audio_mappings = {
            SentimentLevel.VERY_NEGATIVE: {"volume": -30, "track": "ambient_dark"},
            SentimentLevel.NEGATIVE: {"volume": -20, "track": "tension_builder"},
            SentimentLevel.NEUTRAL: {"volume": -15, "track": "neutral_ambiance"},
            SentimentLevel.POSITIVE: {"volume": -10, "track": "uplifting_melody"},
            SentimentLevel.VERY_POSITIVE: {"volume": -8, "track": "celebration_fanfare"}
        }

    async def execute_adaptive_response(
        self,
        sentiment: SentimentLevel,
        dialogue_text: Optional[str] = None
    ) -> OrchestrationResult:
        """
        Execute adaptive response across all services.

        Args:
            sentiment: Current audience sentiment
            dialogue_text: Optional dialogue for BSL translation

        Returns:
            OrchestrationResult with execution status
        """
        start_time = datetime.now()
        services_involved = []
        failed_services = []

        logger.info(f"Executing adaptive response for sentiment: {sentiment.value}")

        # Phase 1: Lighting (DMX)
        if self.dmx_client and self.circuit_breakers["dmx"].is_closed():
            services_involved.append("dmx")
            try:
                scene = self.scene_mappings.get(sentiment, "neutral_scene")
                await self._execute_dmx_scene(scene)
                self.circuit_breakers["dmx"].record_success()
            except Exception as e:
                logger.error(f"DMX execution failed: {e}")
                self.circuit_breakers["dmx"].record_failure()
                failed_services.append("dmx")

        # Phase 2: Audio
        if self.audio_client and self.circuit_breakers["audio"].is_closed():
            services_involved.append("audio")
            try:
                audio_config = self.audio_mappings.get(sentiment, {"volume": -15})
                await self._execute_audio_response(audio_config)
                self.circuit_breakers["audio"].record_success()
            except Exception as e:
                logger.error(f"Audio execution failed: {e}")
                self.circuit_breakers["audio"].record_failure()
                failed_services.append("audio")

        # Phase 3: BSL Translation (if dialogue provided)
        if dialogue_text and self.bsl_client and self.circuit_breakers["bsl"].is_closed():
            services_involved.append("bsl")
            try:
                await self._execute_bsl_translation(dialogue_text)
                self.circuit_breakers["bsl"].record_success()
            except Exception as e:
                logger.error(f"BSL execution failed: {e}")
                self.circuit_breakers["bsl"].record_failure()
                failed_services.append("bsl")

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return OrchestrationResult(
            success=len(failed_services) == 0,
            services_involved=services_involved,
            failed_services=failed_services,
            duration_ms=duration_ms,
            data={
                "sentiment": sentiment.value,
                "scene": self.scene_mappings.get(sentiment),
                "dialogue_length": len(dialogue_text) if dialogue_text else 0
            }
        )

    async def _execute_dmx_scene(self, scene: str) -> None:
        """Execute DMX scene change."""
        logger.info(f"Executing DMX scene: {scene}")
        # In real implementation, call DMX client
        await asyncio.sleep(0.1)  # Simulate network call

    async def _execute_audio_response(self, config: Dict[str, Any]) -> None:
        """Execute audio response."""
        logger.info(f"Executing audio response: {config}")
        # In real implementation, call Audio client
        await asyncio.sleep(0.1)  # Simulate network call

    async def _execute_bsl_translation(self, text: str) -> None:
        """Execute BSL translation."""
        logger.info(f"Executing BSL translation for: {text[:50]}...")
        # In real implementation, call BSL client
        await asyncio.sleep(0.2)  # Simulate network call

    async def execute_emergency_stop(self) -> OrchestrationResult:
        """
        Execute emergency stop across all services.

        Returns:
            OrchestrationResult with emergency stop status
        """
        start_time = datetime.now()
        services_involved = []
        failed_services = []

        logger.warning("Executing emergency stop across all services")

        # Emergency stop DMX
        if self.dmx_client:
            services_involved.append("dmx")
            try:
                await self._emergency_stop_dmx()
            except Exception as e:
                logger.error(f"DMX emergency stop failed: {e}")
                failed_services.append("dmx")

        # Emergency mute Audio
        if self.audio_client:
            services_involved.append("audio")
            try:
                await self._emergency_mute_audio()
            except Exception as e:
                logger.error(f"Audio emergency mute failed: {e}")
                failed_services.append("audio")

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return OrchestrationResult(
            success=len(failed_services) == 0,
            services_involved=services_involved,
            failed_services=failed_services,
            duration_ms=duration_ms,
            data={"operation": "emergency_stop"}
        )

    async def _emergency_stop_dmx(self) -> None:
        """Execute DMX emergency stop."""
        logger.warning("Executing DMX emergency stop")
        # In real implementation, call DMX client
        await asyncio.sleep(0.05)

    async def _emergency_mute_audio(self) -> None:
        """Execute Audio emergency mute."""
        logger.warning("Executing Audio emergency mute")
        # In real implementation, call Audio client
        await asyncio.sleep(0.05)


# Example usage
async def main():
    """Example usage of orchestration patterns."""

    # Circuit Breaker example
    print("=== Circuit Breaker Example ===")
    cb = CircuitBreaker("test-service", failure_threshold=3)

    for i in range(5):
        if cb.is_closed():
            print(f"Attempt {i+1}: Circuit closed - making request")
            # Simulate failures
            if i < 3:
                cb.record_failure()
                print(f"  -> Recorded failure (count: {cb._failure_count})")
            else:
                cb.record_success()
                print(f"  -> Recorded success")
        else:
            print(f"Attempt {i+1}: Circuit open - request blocked")

    # Two-Phase Commit example
    print("\n=== Two-Phase Commit Example ===")

    async def mock_prepare_dmx():
        print("  Preparing DMX...")
        await asyncio.sleep(0.1)
        return True

    async def mock_prepare_audio():
        print("  Preparing Audio...")
        await asyncio.sleep(0.1)
        return True

    async def mock_commit_dmx():
        print("  Committing DMX...")
        await asyncio.sleep(0.1)

    async def mock_commit_audio():
        print("  Committing Audio...")
        await asyncio.sleep(0.1)

    tpc = TwoPhaseCommit(["dmx", "audio"])
    prepare_ops = {
        "dmx": mock_prepare_dmx,
        "audio": mock_prepare_audio
    }
    commit_ops = {
        "dmx": mock_commit_dmx,
        "audio": mock_commit_audio
    }

    if await tpc.prepare(prepare_ops):
        result = await tpc.commit(commit_ops)
        print(f"  Commit result: {result.success}")

    # Adaptive Orchestrator example
    print("\n=== Adaptive Orchestrator Example ===")

    orchestrator = AdaptiveOrchestrator()

    result = await orchestrator.execute_adaptive_response(
        sentiment=SentimentLevel.POSITIVE,
        dialogue_text="Thank you for your wonderful performance!"
    )
    print(f"  Adaptive response: {result.success}")
    print(f"  Services involved: {result.services_involved}")
    print(f"  Duration: {result.duration_ms:.1f}ms")


if __name__ == "__main__":
    asyncio.run(main())
