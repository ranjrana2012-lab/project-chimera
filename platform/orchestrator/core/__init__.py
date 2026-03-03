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

from .aggregator import (
    ResultAggregator,
    AggregatedResult,
    TrendAnalysis,
    TestTrend,
    ServiceTrend
)

from .coverage import (
    CoverageCollector,
    CoverageReport,
    CoverageData,
    FileCoverage
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
    "ExecutorState",
    "ResultAggregator",
    "AggregatedResult",
    "TrendAnalysis",
    "TestTrend",
    "ServiceTrend",
    "CoverageCollector",
    "CoverageReport",
    "CoverageData",
    "FileCoverage"
]
