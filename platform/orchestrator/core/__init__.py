"""
Core modules for Test Orchestrator.
"""

from .discovery import (
    TestDiscovery,
    TestCatalog,
    TestInfo,
    ServiceTests
)

from .executor import (
    ParallelExecutor,
    ExecutionConfig,
    TestExecutionResult,
    ServiceExecutionResult,
    ExecutorState
)

__all__ = [
    "TestDiscovery",
    "TestCatalog",
    "TestInfo",
    "ServiceTests",
    "ParallelExecutor",
    "ExecutionConfig",
    "TestExecutionResult",
    "ServiceExecutionResult",
    "ExecutorState"
]
