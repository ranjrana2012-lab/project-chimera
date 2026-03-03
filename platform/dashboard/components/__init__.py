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

from .alerts import (
    Alert,
    AlertSeverity,
    Incident,
    IncidentStatus,
    AlertManager
)

from .cicd import (
    PipelineStatus,
    PipelineRun,
    CICDTracker,
    CICDDisplay
)

from .responsive import (
    ScreenSize,
    ResponsiveConfig,
    ResponsiveAdapter,
    ViewportHelper
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
    "CoverageDisplay",
    "Alert",
    "AlertSeverity",
    "Incident",
    "IncidentStatus",
    "AlertManager",
    "PipelineStatus",
    "PipelineRun",
    "CICDTracker",
    "CICDDisplay",
    "ScreenSize",
    "ResponsiveConfig",
    "ResponsiveAdapter",
    "ViewportHelper"
]
