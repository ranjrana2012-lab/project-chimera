"""
Test Result Aggregator - OpenClaw Test Orchestrator

Aggregates and analyzes test results from multiple runs.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json

from .executor import ServiceExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class AggregatedResult:
    """
    Result of aggregating test runs.

    Attributes:
        run_id: Unique run identifier
        total_tests: Total tests across all services
        passed: Total passed tests
        failed: Total failed tests
        skipped: Total skipped tests
        duration_seconds: Execution duration (max of all services)
        by_service: Results per service
        success_rate: Percentage of passed tests
        timestamp: Aggregation timestamp
    """
    run_id: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    by_service: Dict[str, ServiceExecutionResult]
    success_rate: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
            "success_rate": round(self.success_rate, 2),
            "by_service": {
                svc: result.to_dict()
                for svc, result in self.by_service.items()
            },
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TestTrend:
    """
    Trend analysis for a single metric.

    Attributes:
        initial: Initial value
        final: Final value
        delta: Change (final - initial)
        trend: Direction (improving, declining, stable)
    """
    initial: float
    final: float
    delta: float
    trend: str  # "improving", "declining", "stable"

    @classmethod
    def from_values(cls, initial: float, final: float) -> "TestTrend":
        """Create trend from two values."""
        delta = final - initial

        # Determine trend direction
        if abs(delta) < 5.0:  # Within 5% = stable
            trend = "stable"
        elif delta > 0:
            trend = "improving"
        else:
            trend = "declining"

        return cls(
            initial=round(initial, 2),
            final=round(final, 2),
            delta=round(delta, 2),
            trend=trend
        )


@dataclass
class ServiceTrend:
    """
    Trend analysis for a service.

    Attributes:
        service: Service name
        initial_pass_rate: Initial pass rate
        final_pass_rate: Final pass rate
        trend: Trend direction
        flaky_tests: List of potentially flaky test names
    """
    service: str
    initial_pass_rate: float
    final_pass_rate: float
    trend: str
    flaky_tests: List[str] = field(default_factory=list)


@dataclass
class TrendAnalysis:
    """
    Trend analysis across multiple runs.

    Attributes:
        run_count: Number of runs analyzed
        overall_trend: Overall trend direction
        service_trends: Trends per service
        timestamp: Analysis timestamp
    """
    run_count: int
    overall_trend: str
    service_trends: Dict[str, ServiceTrend]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResultAggregator:
    """
    Aggregates test results from multiple runs.

    Provides trend analysis and comparison capabilities.
    """

    def __init__(self):
        """Initialize result aggregator."""
        logger.info("ResultAggregator initialized")

    def aggregate_run(
        self,
        run_id: str,
        results: Dict[str, ServiceExecutionResult]
    ) -> AggregatedResult:
        """
        Aggregate results from a single test run.

        Args:
            run_id: Run identifier
            results: Service execution results

        Returns:
            AggregatedResult
        """
        total_tests = sum(r.total_tests for r in results.values())
        passed = sum(r.passed for r in results.values())
        failed = sum(r.failed for r in results.values())
        skipped = sum(r.skipped for r in results.values())

        # Duration is max of all services (parallel execution)
        duration = max((r.duration_seconds for r in results.values()), default=0.0)

        success_rate = self.calculate_success_rate(total_tests, passed, skipped)

        return AggregatedResult(
            run_id=run_id,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
            by_service=results,
            success_rate=success_rate
        )

    def aggregate_multiple_runs(
        self,
        runs: List[Dict[str, ServiceExecutionResult]]
    ) -> List[AggregatedResult]:
        """
        Aggregate multiple test runs.

        Args:
            runs: List of run result dictionaries

        Returns:
            List of AggregatedResult
        """
        aggregated = []

        for i, run in enumerate(runs):
            run_id = run.get("run_id", f"run-{i}")
            # Extract results from run dict
            results = {k: v for k, v in run.items() if isinstance(v, ServiceExecutionResult)}

            aggregated.append(self.aggregate_run(run_id, results))

        return aggregated

    def calculate_success_rate(
        self,
        total: int,
        passed: int,
        skipped: int
    ) -> float:
        """
        Calculate success rate (pass percentage).

        Args:
            total: Total tests
            passed: Passed tests
            skipped: Skipped tests

        Returns:
            Success rate percentage
        """
        if total == 0:
            return 100.0

        # Exclude skipped from denominator
        executed = total - skipped
        if executed == 0:
            return 100.0

        return (passed / executed) * 100.0

    def analyze_trends(
        self,
        history: List[AggregatedResult]
    ) -> TrendAnalysis:
        """
        Analyze trends across multiple runs.

        Args:
            history: List of aggregated results

        Returns:
            TrendAnalysis
        """
        if len(history) < 2:
            # Need at least 2 runs for trend analysis
            return TrendAnalysis(
                run_count=len(history),
                overall_trend="unknown",
                service_trends={}
            )

        # Calculate overall pass rate trend
        initial_rate = history[0].success_rate
        final_rate = history[-1].success_rate

        overall_trend = TestTrend.from_values(initial_rate, final_rate)

        # Analyze per-service trends
        service_trends = {}

        # Get all services across all runs
        all_services = set()
        for agg in history:
            all_services.update(agg.by_service.keys())

        for service in all_services:
            # Get initial and final pass rates for this service
            rates = []

            for agg in history:
                if service in agg.by_service:
                    svc_result = agg.by_service[service]
                    if svc_result.total_tests > 0:
                        rate = (svc_result.passed / svc_result.total_tests) * 100
                        rates.append(rate)

            if len(rates) >= 2:
                svc_trend = TestTrend.from_values(rates[0], rates[-1])
                service_trends[service] = ServiceTrend(
                    service=service,
                    initial_pass_rate=rates[0],
                    final_pass_rate=rates[-1],
                    trend=svc_trend.trend
                )

        return TrendAnalysis(
            run_count=len(history),
            overall_trend=overall_trend.trend,
            service_trends=service_trends
        )

    def compare_runs(
        self,
        run1: AggregatedResult,
        run2: AggregatedResult
    ) -> Dict[str, Any]:
        """
        Compare two test runs.

        Args:
            run1: First run (baseline)
            run2: Second run (comparison)

        Returns:
            Comparison dictionary
        """
        pass_rate_delta = run2.success_rate - run1.success_rate

        if abs(pass_rate_delta) < 5.0:
            improvement = "same"
        elif pass_rate_delta > 0:
            improvement = "better"
        else:
            improvement = "worse"

        return {
            "run1_id": run1.run_id,
            "run2_id": run2.run_id,
            "pass_rate_delta": round(pass_rate_delta, 2),
            "improvement": improvement,
            "test_count_delta": run2.total_tests - run1.total_tests,
            "duration_delta": run2.duration_seconds - run1.duration_seconds
        }

    def detect_flakiness(
        self,
        history: List[AggregatedResult],
        threshold: int = 2
    ) -> Dict[str, int]:
        """
        Detect potentially flaky services.

        A service is considered flaky if it fails in some runs
        but passes in others.

        Args:
            history: List of aggregated results
            threshold: Minimum occurrences to flag as flaky

        Returns:
            Dictionary of service name to flakiness count
        """
        flaky_counts = {}

        # Get all services
        all_services = set()
        for agg in history:
            all_services.update(agg.by_service.keys())

        for service in all_services:
            fail_count = 0
            total_count = 0

            for agg in history:
                if service in agg.by_service:
                    total_count += 1
                    if not agg.by_service[service].success:
                        fail_count += 1

            # Service is flaky if it failed some but not all times
            if 0 < fail_count < total_count and fail_count >= threshold:
                flaky_counts[service] = fail_count

        return flaky_counts

    def get_summary_metrics(
        self,
        history: List[AggregatedResult]
    ) -> Dict[str, Any]:
        """
        Get summary metrics across all runs.

        Args:
            history: List of aggregated results

        Returns:
            Summary metrics dictionary
        """
        if not history:
            return {
                "total_runs": 0,
                "avg_pass_rate": 0.0,
                "best_run": None,
                "worst_run": None
            }

        pass_rates = [r.success_rate for r in history]
        avg_pass_rate = sum(pass_rates) / len(pass_rates)

        best_run = max(history, key=lambda r: r.success_rate)
        worst_run = min(history, key=lambda r: r.success_rate)

        return {
            "total_runs": len(history),
            "avg_pass_rate": round(avg_pass_rate, 2),
            "best_run": {
                "run_id": best_run.run_id,
                "pass_rate": best_run.success_rate
            },
            "worst_run": {
                "run_id": worst_run.run_id,
                "pass_rate": worst_run.success_rate
            },
            "total_tests": sum(r.total_tests for r in history),
            "total_passed": sum(r.passed for r in history),
            "total_failed": sum(r.failed for r in history)
        }
