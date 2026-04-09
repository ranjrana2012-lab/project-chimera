"""
Service Orchestration Package

Project Chimera Phase 2 - Service Coordination

This package provides orchestration patterns and service clients
for coordinating multiple Phase 2 services.
"""

from .patterns import (
    CircuitBreaker,
    TwoPhaseCommit,
    SagaOrchestrator,
    AdaptiveOrchestrator,
    SentimentLevel,
    ServiceState,
    ServiceHealth,
    OrchestrationResult
)

from .clients import (
    DMXClient,
    AudioClient,
    BSLClient,
    ShowOrchestrator
)

__all__ = [
    # Patterns
    "CircuitBreaker",
    "TwoPhaseCommit",
    "SagaOrchestrator",
    "AdaptiveOrchestrator",
    "SentimentLevel",
    "ServiceState",
    "ServiceHealth",
    "OrchestrationResult",
    # Clients
    "DMXClient",
    "AudioClient",
    "BSLClient",
    "ShowOrchestrator"
]
