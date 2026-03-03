"""
Unit tests for test results display component.

Tests test results aggregation, trend analysis, and history.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add dashboard to path
dashboard_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(dashboard_path))


class TestTestRun:
    """Test TestRun dataclass."""

    def test_test_run_creation(self):
        """Test creating a test run."""
        from components.results import TestRun
        run = TestRun(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            total_tests=100,
            passed=95,
            failed=5,
            duration_seconds=60.0
        )
        assert run.run_id == "run-123"
        assert run.total_tests == 100
        assert run.passed == 95
        assert run.failed == 5

    def test_test_run_success_rate(self):
        """Test success rate calculation."""
        from components.results import TestRun
        run = TestRun(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            total_tests=100,
            passed=95,
            failed=5,
            duration_seconds=60.0
        )
        assert run.success_rate == 95.0

    def test_test_run_status_passed(self):
        """Test run status when passed."""
        from components.results import TestRun
        run = TestRun(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            total_tests=100,
            passed=95,
            failed=5,
            duration_seconds=60.0
        )
        assert run.status == "passed"

    def test_test_run_status_failed(self):
        """Test run status when failed."""
        from components.results import TestRun
        run = TestRun(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            total_tests=100,
            passed=50,
            failed=50,
            duration_seconds=60.0
        )
        assert run.status == "failed"

    def test_test_run_to_dict(self):
        """Test converting to dict."""
        from components.results import TestRun
        run = TestRun(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            total_tests=100,
            passed=95,
            failed=5,
            duration_seconds=60.0
        )
        data = run.to_dict()
        assert data["run_id"] == "run-123"
        assert data["total_tests"] == 100
        assert data["success_rate"] == 95.0


class TestServiceTestResults:
    """Test ServiceTestResults dataclass."""

    def test_service_results_creation(self):
        """Test creating service results."""
        from components.results import ServiceTestResults
        results = ServiceTestResults(
            service_name="test-service",
            total_tests=50,
            passed=45,
            failed=5,
            skipped=0,
            duration_seconds=30.0
        )
        assert results.service_name == "test-service"
        assert results.total_tests == 50
        assert results.passed == 45

    def test_service_results_pass_rate(self):
        """Test pass rate calculation."""
        from components.results import ServiceTestResults
        results = ServiceTestResults(
            service_name="test-service",
            total_tests=50,
            passed=45,
            failed=5,
            skipped=0,
            duration_seconds=30.0
        )
        assert results.pass_rate == 90.0


class TestTrendData:
    """Test TrendData dataclass."""

    def test_trend_data_creation(self):
        """Test creating trend data."""
        from components.results import TrendData
        trend = TrendData(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            pass_rate=95.0,
            total_tests=100
        )
        assert trend.run_id == "run-123"
        assert trend.pass_rate == 95.0


class TestResultsTracker:
    """Test ResultsTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create results tracker."""
        from components.results import ResultsTracker
        return ResultsTracker()

    def test_tracker_init(self, tracker):
        """Test tracker initialization."""
        assert len(tracker.runs) == 0
        assert len(tracker.service_results) == 0

    def test_add_run(self, tracker):
        """Test adding a test run."""
        from components.results import TestRun
        run = TestRun(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            total_tests=100,
            passed=95,
            failed=5,
            duration_seconds=60.0
        )
        tracker.add_run(run)
        assert len(tracker.runs) == 1
        assert "run-123" in tracker.runs

    def test_add_service_results(self, tracker):
        """Test adding service results."""
        from components.results import ServiceTestResults
        results = ServiceTestResults(
            service_name="test-service",
            total_tests=50,
            passed=45,
            failed=5,
            skipped=0,
            duration_seconds=30.0
        )
        tracker.add_service_results("run-123", results)
        assert "run-123" in tracker.service_results
        assert len(tracker.service_results["run-123"]) == 1

    def test_get_recent_runs(self, tracker):
        """Test getting recent runs."""
        from components.results import TestRun

        # Add 5 runs (run-0 added first, run-4 added last)
        for i in range(5):
            run = TestRun(
                run_id=f"run-{i}",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i),
                total_tests=100,
                passed=90 + i,
                failed=10 - i,
                duration_seconds=60.0
            )
            tracker.add_run(run)

        recent = tracker.get_recent_runs(limit=3)
        assert len(recent) == 3
        # Most recent INSERTIONS first (run-4 was added last)
        assert recent[0].run_id == "run-4"
        assert recent[1].run_id == "run-3"
        assert recent[2].run_id == "run-2"

    def test_get_trend_data(self, tracker):
        """Test getting trend data."""
        from components.results import TestRun

        # Add runs with varying pass rates
        for i in range(5):
            run = TestRun(
                run_id=f"run-{i}",
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                total_tests=100,
                passed=90 + i,
                failed=10 - i,
                duration_seconds=60.0
            )
            tracker.add_run(run)

        trends = tracker.get_trend_data(limit=30)
        assert len(trends) == 5
        # Should be ordered by timestamp ascending (oldest first)
        assert trends[0].pass_rate == 90.0
        assert trends[-1].pass_rate == 94.0

    def test_get_average_pass_rate(self, tracker):
        """Test getting average pass rate."""
        from components.results import TestRun

        runs = [
            TestRun("run-1", datetime.now(timezone.utc), 100, 90, 10, 60.0),
            TestRun("run-2", datetime.now(timezone.utc), 100, 95, 5, 60.0),
            TestRun("run-3", datetime.now(timezone.utc), 100, 85, 15, 60.0),
        ]
        for run in runs:
            tracker.add_run(run)

        avg = tracker.get_average_pass_rate()
        assert abs(avg - 90.0) < 0.01  # (90 + 95 + 85) / 3 = 90

    def test_get_service_summary(self, tracker):
        """Test getting service summary."""
        from components.results import ServiceTestResults

        results1 = ServiceTestResults("svc1", 50, 45, 5, 0, 30.0)
        results2 = ServiceTestResults("svc2", 100, 95, 5, 0, 60.0)

        tracker.add_service_results("run-123", results1)
        tracker.add_service_results("run-123", results2)

        summary = tracker.get_service_summary("run-123")
        assert len(summary) == 2
        assert summary[0].service_name == "svc1"
        assert summary[1].service_name == "svc2"

    def test_get_best_and_worst_runs(self, tracker):
        """Test getting best and worst runs."""
        from components.results import TestRun

        runs = [
            TestRun("run-1", datetime.now(timezone.utc), 100, 85, 15, 60.0),
            TestRun("run-2", datetime.now(timezone.utc), 100, 95, 5, 60.0),
            TestRun("run-3", datetime.now(timezone.utc), 100, 90, 10, 60.0),
        ]
        for run in runs:
            tracker.add_run(run)

        best = tracker.get_best_run()
        worst = tracker.get_worst_run()

        assert best.run_id == "run-2"
        assert worst.run_id == "run-1"


class TestResultsDisplay:
    """Test ResultsDisplay class."""

    @pytest.fixture
    def display(self):
        """Create results display."""
        from components.results import ResultsDisplay
        return ResultsDisplay()

    def test_display_init(self, display):
        """Test display initialization."""
        assert display.tracker is not None

    def test_get_summary_data(self, display):
        """Test getting summary data."""
        from components.results import TestRun

        run = TestRun(
            run_id="run-123",
            timestamp=datetime.now(timezone.utc),
            total_tests=100,
            passed=95,
            failed=5,
            duration_seconds=60.0
        )
        display.tracker.add_run(run)

        summary = display.get_summary_data()
        assert "total_tests" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "success_rate" in summary
        assert summary["total_tests"] == 100
        assert summary["passed"] == 95
        assert summary["failed"] == 5

    def test_get_trend_chart_data(self, display):
        """Test getting trend chart data."""
        from components.results import TestRun

        for i in range(5):
            run = TestRun(
                run_id=f"run-{i}",
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                total_tests=100,
                passed=90 + i,
                failed=10 - i,
                duration_seconds=60.0
            )
            display.tracker.add_run(run)

        chart_data = display.get_trend_chart_data()
        assert "labels" in chart_data
        assert "datasets" in chart_data
        assert len(chart_data["datasets"]) > 0

    def test_get_recent_runs_table(self, display):
        """Test getting recent runs table."""
        from components.results import TestRun

        for i in range(3):
            run = TestRun(
                run_id=f"run-{i}",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i),
                total_tests=100,
                passed=90 + i,
                failed=10 - i,
                duration_seconds=60.0
            )
            display.tracker.add_run(run)

        table = display.get_recent_runs_table()
        assert len(table) == 3
        assert "run_id" in table[0]
        assert "status" in table[0]
        assert "total_tests" in table[0]


class TestPassRateComparison:
    """Test pass rate comparison functionality."""

    def test_compare_with_previous(self):
        """Test comparing with previous run."""
        from components.results import ResultsTracker, TestRun

        tracker = ResultsTracker()
        run1 = TestRun("run-1", datetime.now(timezone.utc) - timedelta(minutes=10), 100, 90, 10, 60.0)
        run2 = TestRun("run-2", datetime.now(timezone.utc), 100, 95, 5, 60.0)

        tracker.add_run(run1)
        tracker.add_run(run2)

        comparison = tracker.compare_with_previous("run-2")
        assert comparison["current_pass_rate"] == 95.0
        assert comparison["previous_pass_rate"] == 90.0
        assert comparison["change"] == 5.0
        assert comparison["improved"] is True
