"""
Test results display component for dashboard.

Tracks test runs, pass rates, trends, and service-level results.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TestRun:
    """
    Represents a single test run.

    Attributes:
        run_id: Unique run identifier
        timestamp: When the run started
        total_tests: Total number of tests
        passed: Number of passing tests
        failed: Number of failing tests
        skipped: Number of skipped tests
        duration_seconds: How long the run took
    """
    run_id: str
    timestamp: datetime
    total_tests: int
    passed: int
    failed: int
    skipped: int = 0
    duration_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def status(self) -> str:
        """Get run status based on pass rate."""
        rate = self.success_rate
        if rate >= 95:
            return "passed"
        elif rate >= 80:
            return "partial"
        else:
            return "failed"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "status": self.status
        }


@dataclass
class ServiceTestResults:
    """
    Test results for a single service.

    Attributes:
        service_name: Name of the service
        total_tests: Total number of tests
        passed: Number of passing tests
        failed: Number of failing tests
        skipped: Number of skipped tests
        duration_seconds: How long tests took
    """
    service_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int = 0
    duration_seconds: float = 0.0

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100


@dataclass
class TrendData:
    """
    Data point for trend charts.

    Attributes:
        run_id: Run identifier
        timestamp: When the run occurred
        pass_rate: Pass rate percentage
        total_tests: Total number of tests
    """
    run_id: str
    timestamp: datetime
    pass_rate: float
    total_tests: int


class ResultsTracker:
    """
    Tracks test results over time.

    Stores test runs, service-level results, and provides
    trend analysis and statistics.
    """

    def __init__(self, max_runs: int = 100):
        """
        Initialize results tracker.

        Args:
            max_runs: Maximum number of runs to keep in memory
        """
        self.max_runs = max_runs
        self.runs: Dict[str, TestRun] = {}
        self.service_results: Dict[str, List[ServiceTestResults]] = defaultdict(list)
        self._run_order: List[str] = []

        logger.info("ResultsTracker initialized")

    def add_run(self, run: TestRun) -> None:
        """
        Add a test run.

        Args:
            run: Test run to add
        """
        self.runs[run.run_id] = run
        self._run_order.append(run.run_id)

        # Prune old runs if needed
        if len(self._run_order) > self.max_runs:
            old_id = self._run_order.pop(0)
            if old_id in self.runs:
                del self.runs[old_id]
            if old_id in self.service_results:
                del self.service_results[old_id]

        logger.debug(f"Added test run: {run.run_id}")

    def add_service_results(self, run_id: str, results: ServiceTestResults) -> None:
        """
        Add service-level test results for a run.

        Args:
            run_id: Run identifier
            results: Service test results
        """
        self.service_results[run_id].append(results)
        logger.debug(f"Added service results for {results.service_name} in {run_id}")

    def get_run(self, run_id: str) -> Optional[TestRun]:
        """
        Get a specific test run.

        Args:
            run_id: Run identifier

        Returns:
            Test run or None if not found
        """
        return self.runs.get(run_id)

    def get_recent_runs(self, limit: int = 10) -> List[TestRun]:
        """
        Get recent test runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of test runs, most recent first
        """
        recent_ids = self._run_order[-limit:]
        return [self.runs[rid] for rid in reversed(recent_ids) if rid in self.runs]

    def get_trend_data(self, limit: int = 30) -> List[TrendData]:
        """
        Get trend data for charts.

        Args:
            limit: Maximum number of data points

        Returns:
            List of trend data, ordered by timestamp (oldest first)
        """
        runs = self.get_recent_runs(limit)
        # Reverse to get oldest first
        runs = list(reversed(runs))

        return [
            TrendData(
                run_id=run.run_id,
                timestamp=run.timestamp,
                pass_rate=run.success_rate,
                total_tests=run.total_tests
            )
            for run in runs
        ]

    def get_average_pass_rate(self, run_count: int = 30) -> float:
        """
        Calculate average pass rate over recent runs.

        Args:
            run_count: Number of recent runs to consider

        Returns:
            Average pass rate percentage
        """
        runs = self.get_recent_runs(limit=run_count)
        if not runs:
            return 0.0

        total = sum(run.success_rate for run in runs)
        return total / len(runs)

    def get_service_summary(self, run_id: str) -> List[ServiceTestResults]:
        """
        Get service-level results for a run.

        Args:
            run_id: Run identifier

        Returns:
            List of service test results
        """
        return self.service_results.get(run_id, [])

    def get_best_run(self, run_count: int = 30) -> Optional[TestRun]:
        """
        Get the best recent run by pass rate.

        Args:
            run_count: Number of recent runs to consider

        Returns:
            Best test run or None
        """
        runs = self.get_recent_runs(limit=run_count)
        if not runs:
            return None

        return max(runs, key=lambda r: r.success_rate)

    def get_worst_run(self, run_count: int = 30) -> Optional[TestRun]:
        """
        Get the worst recent run by pass rate.

        Args:
            run_count: Number of recent runs to consider

        Returns:
            Worst test run or None
        """
        runs = self.get_recent_runs(limit=run_count)
        if not runs:
            return None

        return min(runs, key=lambda r: r.success_rate)

    def compare_with_previous(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Compare a run with the previous run.

        Args:
            run_id: Run identifier

        Returns:
            Comparison data or None if no previous run exists
        """
        if run_id not in self._run_order:
            return None

        idx = self._run_order.index(run_id)
        if idx == 0:
            return None

        prev_id = self._run_order[idx - 1]
        if prev_id not in self.runs:
            return None

        current = self.runs[run_id]
        previous = self.runs[prev_id]

        change = current.success_rate - previous.success_rate

        return {
            "run_id": run_id,
            "previous_run_id": prev_id,
            "current_pass_rate": current.success_rate,
            "previous_pass_rate": previous.success_rate,
            "change": change,
            "improved": change > 0,
            "regressed": change < 0
        }


class ResultsDisplay:
    """
    Formats test results for dashboard display.

    Provides summary statistics, chart data, and tables
    for visualizing test results.
    """

    def __init__(self, tracker: Optional[ResultsTracker] = None):
        """
        Initialize results display.

        Args:
            tracker: Results tracker to use (creates new if None)
        """
        self.tracker = tracker or ResultsTracker()
        logger.info("ResultsDisplay initialized")

    def get_summary_data(self) -> Dict[str, Any]:
        """
        Get summary statistics for all runs.

        Returns:
            Summary dictionary with totals and rates
        """
        recent = self.tracker.get_recent_runs(limit=1)

        if not recent:
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "success_rate": 0.0,
                "last_run": None
            }

        latest = recent[0]

        return {
            "total_tests": latest.total_tests,
            "passed": latest.passed,
            "failed": latest.failed,
            "skipped": latest.skipped,
            "success_rate": latest.success_rate,
            "last_run": latest.run_id,
            "last_run_timestamp": latest.timestamp.isoformat()
        }

    def get_trend_chart_data(self, limit: int = 30) -> Dict[str, Any]:
        """
        Get chart data for pass rate trends.

        Args:
            limit: Number of data points

        Returns:
            Chart data with labels and datasets
        """
        trends = self.tracker.get_trend_data(limit=limit)

        return {
            "labels": [t.timestamp.strftime("%H:%M") for t in trends],
            "datasets": [
                {
                    "label": "Pass Rate",
                    "data": [t.pass_rate for t in trends],
                    "borderColor": "rgb(75, 192, 192)",
                    "backgroundColor": "rgba(75, 192, 192, 0.2)"
                }
            ],
            "average": self.tracker.get_average_pass_rate(limit)
        }

    def get_recent_runs_table(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent runs as table data.

        Args:
            limit: Maximum number of runs

        Returns:
            List of row dictionaries
        """
        runs = self.tracker.get_recent_runs(limit=limit)

        return [
            {
                "run_id": run.run_id,
                "status": run.status,
                "total_tests": run.total_tests,
                "passed": run.passed,
                "failed": run.failed,
                "duration_seconds": run.duration_seconds,
                "success_rate": run.success_rate,
                "timestamp": run.timestamp.isoformat(),
                "time_ago": self._format_time_ago(run.timestamp)
            }
            for run in runs
        ]

    def get_service_breakdown(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get service-level breakdown for a run.

        Args:
            run_id: Run identifier

        Returns:
            List of service result dictionaries
        """
        results = self.tracker.get_service_summary(run_id)

        return [
            {
                "service_name": r.service_name,
                "total_tests": r.total_tests,
                "passed": r.passed,
                "failed": r.failed,
                "pass_rate": r.pass_rate,
                "duration_seconds": r.duration_seconds
            }
            for r in results
        ]

    def get_comparison_data(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comparison data for a run vs previous.

        Args:
            run_id: Run identifier

        Returns:
            Comparison data or None
        """
        comparison = self.tracker.compare_with_previous(run_id)

        if comparison is None:
            return None

        comparison["change_formatted"] = f"+{comparison['change']:.1f}%" if comparison['improved'] else f"{comparison['change']:.1f}%"

        return comparison

    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as time ago."""
        delta = datetime.now(timezone.utc) - timestamp
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"
