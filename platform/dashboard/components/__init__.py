"""
Dashboard components for monitoring and visualization.
"""

from .health import (
    ServiceHealth,
    HealthConfig,
    ServiceDefinition,
    HealthMonitor,
    HealthAggregator,
    get_default_services
)

from .results import (
    TestRun,
    ServiceTestResults,
    TrendData,
    ResultsTracker,
    ResultsDisplay
)

from .coverage import (
    FileCoverage,
    CoverageRecord,
    CoverageSnapshot,
    CoverageTracker,
    CoverageDisplay
)

__all__ = [
    "ServiceHealth",
    "HealthConfig",
    "ServiceDefinition",
    "HealthMonitor",
    "HealthAggregator",
    "get_default_services",
    "TestRun",
    "ServiceTestResults",
    "TrendData",
    "ResultsTracker",
    "ResultsDisplay",
    "FileCoverage",
    "CoverageRecord",
    "CoverageSnapshot",
    "CoverageTracker",
    "CoverageDisplay"
]
