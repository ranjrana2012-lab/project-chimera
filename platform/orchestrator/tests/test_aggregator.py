"""
Unit tests for Test Result Aggregator.

Tests aggregation of test results from multiple runs.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_path))

from core.aggregator import (
    ResultAggregator,
    AggregatedResult,
    TrendAnalysis,
    TestTrend,
    ServiceTrend
)


class TestServiceExecutionResult:
    """Test ServiceExecutionResult dataclass."""

    def test_create_result(self):
        """Test creating a service result."""
        from core.executor import ServiceExecutionResult

        result = ServiceExecutionResult(
            service="test-service",
            success=True,
            total_tests=10,
            passed=10,
            failed=0,
            skipped=0,
            duration_seconds=5.0
        )

        assert result.service == "test-service"
        assert result.success is True
        assert result.total_tests == 10


class TestAggregatedResult:
    """Test AggregatedResult dataclass."""

    def test_create_aggregated(self):
        """Test creating aggregated result."""
        from core.executor import ServiceExecutionResult, TestExecutionResult

        service_results = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            )
        }

        aggregated = AggregatedResult(
            run_id="test-run",
            total_tests=10,
            passed=10,
            failed=0,
            skipped=0,
            duration_seconds=5.0,
            by_service=service_results,
            success_rate=100.0
        )

        assert aggregated.run_id == "test-run"
        assert aggregated.success_rate == 100.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        from core.executor import ServiceExecutionResult

        service_results = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=8,
                failed=2,
                skipped=0,
                duration_seconds=5.0
            )
        }

        aggregated = AggregatedResult(
            run_id="test-run",
            total_tests=10,
            passed=8,
            failed=2,
            skipped=0,
            duration_seconds=5.0,
            by_service=service_results,
            success_rate=80.0
        )

        assert aggregated.success_rate == 80.0


class TestResultAggregator:
    """Test ResultAggregator functionality."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return ResultAggregator()

    @pytest.fixture
    def sample_results(self):
        """Create sample execution results."""
        from core.executor import ServiceExecutionResult

        return {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            ),
            "svc2": ServiceExecutionResult(
                service="svc2",
                success=False,
                total_tests=20,
                passed=18,
                failed=2,
                skipped=0,
                duration_seconds=10.0
            )
        }

    def test_aggregator_init(self, aggregator):
        """Test aggregator initialization."""
        assert aggregator is not None

    def test_aggregate_single_run(self, aggregator, sample_results):
        """Test aggregating a single test run."""
        aggregated = aggregator.aggregate_run("run-123", sample_results)

        assert aggregated.run_id == "run-123"
        assert aggregated.total_tests == 30  # 10 + 20
        assert aggregated.passed == 28  # 10 + 18
        assert aggregated.failed == 2
        assert abs(aggregated.success_rate - 93.33) < 0.01  # 28/30 * 100

    def test_aggregate_multiple_runs(self, aggregator):
        """Test aggregating multiple test runs."""
        from core.executor import ServiceExecutionResult

        run1 = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            )
        }

        run2 = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=9,
                failed=1,
                skipped=0,
                duration_seconds=5.5
            )
        }

        # Aggregate both runs
        agg1 = aggregator.aggregate_run("run-1", run1)
        agg2 = aggregator.aggregate_run("run-2", run2)

        assert agg1.passed == 10
        assert agg2.passed == 9

    def test_aggregate_empty_results(self, aggregator):
        """Test aggregating empty results."""
        aggregated = aggregator.aggregate_run("empty-run", {})

        assert aggregated.run_id == "empty-run"
        assert aggregated.total_tests == 0
        assert aggregated.passed == 0
        assert aggregated.failed == 0

    def test_calculate_success_rate(self, aggregator):
        """Test success rate calculation."""
        rate = aggregator.calculate_success_rate(100, 95, 0)

        assert rate == 95.0

    def test_calculate_success_rate_with_skips(self, aggregator):
        """Test success rate calculation with skipped tests."""
        # Skipped tests shouldn't affect success rate
        rate = aggregator.calculate_success_rate(100, 90, 5)

        # 90 passed out of 95 executed = 94.74%
        assert abs(rate - 94.74) < 0.1


class TestTrendAnalysis:
    """Test trend analysis functionality."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return ResultAggregator()

    @pytest.fixture
    def sample_history(self, aggregator):
        """Create sample execution history."""
        from core.executor import ServiceExecutionResult

        # Create 3 runs with improving trends
        history = []

        for i in range(3):
            results = {
                "svc1": ServiceExecutionResult(
                    service="svc1",
                    success=(i > 0),  # First fails, others pass
                    total_tests=10,
                    passed=8 + i,  # 8, 9, 10
                    failed=2 - i,
                    skipped=0,
                    duration_seconds=5.0
                )
            }

            aggregated = aggregator.aggregate_run(f"run-{i}", results)
            history.append(aggregated)

        return history

    def test_analyze_trends(self, aggregator, sample_history):
        """Test trend analysis."""
        trends = aggregator.analyze_trends(sample_history)

        assert trends is not None
        assert trends.run_count == 3
        assert trends.overall_trend == "improving"  # Tests getting better

    def test_service_trends(self, aggregator, sample_history):
        """Test per-service trend analysis."""
        trends = aggregator.analyze_trends(sample_history)

        assert "svc1" in trends.service_trends
        svc1_trend = trends.service_trends["svc1"]

        assert svc1_trend.service == "svc1"
        assert svc1_trend.initial_pass_rate == 80.0  # 8/10
        assert svc1_trend.final_pass_rate == 100.0  # 10/10

    def test_trend_comparison(self, aggregator):
        """Test comparing two trends."""
        from core.executor import ServiceExecutionResult

        # Improving trend
        results1 = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=5,
                failed=5,
                skipped=0,
                duration_seconds=5.0
            )
        }

        results2 = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            )
        }

        agg1 = aggregator.aggregate_run("run-1", results1)
        agg2 = aggregator.aggregate_run("run-2", results2)

        comparison = aggregator.compare_runs(agg1, agg2)

        assert comparison["improvement"] == "better"
        assert comparison["pass_rate_delta"] == 50.0  # 100 - 50


class TestAggregationOutput:
    """Test aggregation output formats."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return ResultAggregator()

    def test_to_dict(self, aggregator):
        """Test converting aggregated result to dict."""
        from core.executor import ServiceExecutionResult

        results = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            )
        }

        aggregated = aggregator.aggregate_run("run-1", results)
        data = aggregated.to_dict()

        assert "run_id" in data
        assert "total_tests" in data
        assert "success_rate" in data
        assert data["run_id"] == "run-1"

    def test_to_json(self, aggregator):
        """Test JSON serialization."""
        import json

        from core.executor import ServiceExecutionResult

        results = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            )
        }

        aggregated = aggregator.aggregate_run("run-1", results)
        json_str = aggregated.to_json()

        # Verify valid JSON
        parsed = json.loads(json_str)
        assert parsed["run_id"] == "run-1"


class TestMetricCalculation:
    """Test metric calculations."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return ResultAggregator()

    def test_average_duration(self, aggregator):
        """Test average duration calculation."""
        from core.executor import ServiceExecutionResult

        results = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            ),
            "svc2": ServiceExecutionResult(
                service="svc2",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=15.0
            )
        }

        aggregated = aggregator.aggregate_run("run-1", results)

        # Average duration should be 10 (max of parallel runs)
        # or sum (20) if sequential. The implementation returns max.
        assert aggregated.duration_seconds == 15.0  # max(5, 15)

    def test_flakiness_detection(self, aggregator):
        """Test flaky test detection."""
        # Run same tests twice with different results
        from core.executor import ServiceExecutionResult

        results1 = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=True,
                total_tests=10,
                passed=10,
                failed=0,
                skipped=0,
                duration_seconds=5.0
            )
        }

        results2 = {
            "svc1": ServiceExecutionResult(
                service="svc1",
                success=False,  # Failed in second run
                total_tests=10,
                passed=9,
                failed=1,
                skipped=0,
                duration_seconds=5.0
            )
        }

        agg1 = aggregator.aggregate_run("run-1", results1)
        agg2 = aggregator.aggregate_run("run-2", results2)

        # Check for flakiness with threshold=1
        flaky = aggregator.detect_flakiness([agg1, agg2], threshold=1)

        assert len(flaky) > 0
        assert "svc1" in flaky
