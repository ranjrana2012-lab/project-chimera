"""
Unit tests for CI/CD status display component.

Tests pipeline tracking, status display, and workflow history.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add dashboard to path
dashboard_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(dashboard_path))


class TestPipelineStatus:
    """Test PipelineStatus enum."""

    def test_status_values(self):
        """Test status values."""
        from components.cicd import PipelineStatus

        assert PipelineStatus.SUCCESS.value == "success"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.PENDING.value == "pending"
        assert PipelineStatus.RUNNING.value == "running"

    def test_from_string(self):
        """Test creating status from string."""
        from components.cicd import PipelineStatus

        assert PipelineStatus.from_string("success") == PipelineStatus.SUCCESS
        assert PipelineStatus.from_string("failed") == PipelineStatus.FAILED
        assert PipelineStatus.from_string("pending") == PipelineStatus.PENDING
        assert PipelineStatus.from_string("running") == PipelineStatus.RUNNING


class TestPipelineRun:
    """Test PipelineRun dataclass."""

    def test_pipeline_run_creation(self):
        """Test creating a pipeline run."""
        from components.cicd import PipelineRun, PipelineStatus

        run = PipelineRun(
            pipeline_id="4527",
            branch="main",
            status=PipelineStatus.SUCCESS,
            commit="8d3e2f1",
            duration_seconds=323.0
        )
        assert run.pipeline_id == "4527"
        assert run.branch == "main"
        assert run.status == PipelineStatus.SUCCESS

    def test_is_completed(self):
        """Test completion check."""
        from components.cicd import PipelineRun, PipelineStatus

        # Success is completed
        run1 = PipelineRun(
            pipeline_id="1",
            branch="main",
            status=PipelineStatus.SUCCESS,
            commit="abc"
        )
        assert run1.is_completed() is True

        # Failed is completed
        run2 = PipelineRun(
            pipeline_id="2",
            branch="main",
            status=PipelineStatus.FAILED,
            commit="def"
        )
        assert run2.is_completed() is True

        # Running is not completed
        run3 = PipelineRun(
            pipeline_id="3",
            branch="main",
            status=PipelineStatus.RUNNING,
            commit="ghi"
        )
        assert run3.is_completed() is False

    def test_duration_formatted(self):
        """Test duration formatting."""
        from components.cicd import PipelineRun

        run = PipelineRun(
            pipeline_id="1",
            branch="main",
            duration_seconds=323.0
        )
        assert run.duration_formatted == "5m 23s"

    def test_to_dict(self):
        """Test converting to dict."""
        from components.cicd import PipelineRun, PipelineStatus

        run = PipelineRun(
            pipeline_id="4527",
            branch="main",
            status=PipelineStatus.SUCCESS,
            commit="8d3e2f1"
        )
        data = run.to_dict()
        assert data["pipeline_id"] == "4527"
        assert data["status"] == "success"


class TestCICDTracker:
    """Test CICDTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create CI/CD tracker."""
        from components.cicd import CICDTracker
        return CICDTracker()

    def test_tracker_init(self, tracker):
        """Test tracker initialization."""
        assert len(tracker.runs) == 0

    def test_add_run(self, tracker):
        """Test adding a pipeline run."""
        from components.cicd import PipelineRun, PipelineStatus

        run = PipelineRun(
            pipeline_id="4527",
            branch="main",
            status=PipelineStatus.SUCCESS,
            commit="8d3e2f1"
        )
        tracker.add_run(run)
        assert len(tracker.runs) == 1

    def test_get_latest_runs(self, tracker):
        """Test getting latest runs."""
        from components.cicd import PipelineRun, PipelineStatus

        # Add 5 runs
        for i in range(5):
            run = PipelineRun(
                pipeline_id=f"{4527 + i}",
                branch="main",
                status=PipelineStatus.SUCCESS,
                commit=f"commit{i}"
            )
            tracker.add_run(run)

        latest = tracker.get_latest_runs(limit=3)
        assert len(latest) == 3
        # Most recent first
        assert latest[0].pipeline_id == "4531"

    def test_get_runs_by_status(self, tracker):
        """Test filtering runs by status."""
        from components.cicd import PipelineRun, PipelineStatus

        tracker.add_run(PipelineRun("1", "main", PipelineStatus.SUCCESS, "a"))
        tracker.add_run(PipelineRun("2", "main", PipelineStatus.FAILED, "b"))
        tracker.add_run(PipelineRun("3", "main", PipelineStatus.SUCCESS, "c"))

        successful = tracker.get_runs_by_status(PipelineStatus.SUCCESS)
        failed = tracker.get_runs_by_status(PipelineStatus.FAILED)

        assert len(successful) == 2
        assert len(failed) == 1

    def test_get_success_rate(self, tracker):
        """Test getting success rate."""
        from components.cicd import PipelineRun, PipelineStatus

        # 3 success, 1 failed, 1 pending
        tracker.add_run(PipelineRun("1", "main", PipelineStatus.SUCCESS, "a"))
        tracker.add_run(PipelineRun("2", "main", PipelineStatus.SUCCESS, "b"))
        tracker.add_run(PipelineRun("3", "main", PipelineStatus.FAILED, "c"))
        tracker.add_run(PipelineRun("4", "main", PipelineStatus.SUCCESS, "d"))
        tracker.add_run(PipelineRun("5", "main", PipelineStatus.PENDING, "e"))

        # Success rate = success / (success + failed)
        rate = tracker.get_success_rate()
        assert abs(rate - 75.0) < 0.1  # 3/4 = 75%

    def test_get_average_duration(self, tracker):
        """Test getting average duration."""
        from components.cicd import PipelineRun, PipelineStatus

        run1 = PipelineRun("1", "main", PipelineStatus.SUCCESS, "a", duration_seconds=300.0)
        run2 = PipelineRun("2", "main", PipelineStatus.SUCCESS, "b", duration_seconds=400.0)
        run3 = PipelineRun("3", "main", PipelineStatus.SUCCESS, "c", duration_seconds=200.0)

        tracker.add_run(run1)
        tracker.add_run(run2)
        tracker.add_run(run3)

        avg = tracker.get_average_duration()
        assert abs(avg - 300.0) < 0.1  # (300 + 400 + 200) / 3


class TestCICDDisplay:
    """Test CICDDisplay class."""

    @pytest.fixture
    def display(self):
        """Create CI/CD display."""
        from components.cicd import CICDDisplay
        return CICDDisplay()

    def test_get_summary(self, display):
        """Test getting summary."""
        from components.cicd import PipelineRun, PipelineStatus

        display.tracker.add_run(PipelineRun("1", "main", PipelineStatus.SUCCESS, "a", 300.0))
        display.tracker.add_run(PipelineRun("2", "main", PipelineStatus.FAILED, "b", 200.0))
        display.tracker.add_run(PipelineRun("3", "main", PipelineStatus.RUNNING, "c"))

        summary = display.get_summary()
        assert "total_runs" in summary
        assert "success_count" in summary
        assert "failed_count" in summary
        assert "running_count" in summary
        assert summary["total_runs"] == 3

    def test_get_pipeline_table(self, display):
        """Test getting pipeline table data."""
        from components.cicd import PipelineRun, PipelineStatus

        display.tracker.add_run(PipelineRun("4527", "main", PipelineStatus.SUCCESS, "8d3e2f1", duration_seconds=323.0))
        display.tracker.add_run(PipelineRun("4526", "main", PipelineStatus.FAILED, "1a9b5c3", duration_seconds=252.0))

        table = display.get_pipeline_table()
        assert len(table) == 2
        # Most recent insertion first (4526 was added last)
        assert table[0]["pipeline_id"] == "4526"
        assert table[0]["status"] == "failed"

    def test_get_branch_summary(self, display):
        """Test getting branch summary."""
        from components.cicd import PipelineRun, PipelineStatus

        display.tracker.add_run(PipelineRun("1", "main", PipelineStatus.SUCCESS, "a"))
        display.tracker.add_run(PipelineRun("2", "main", PipelineStatus.SUCCESS, "b"))
        display.tracker.add_run(PipelineRun("3", "feature", PipelineStatus.RUNNING, "c"))

        summary = display.get_branch_summary()
        assert summary["main"]["total"] == 2
        assert summary["main"]["success"] == 2
        assert summary["feature"]["total"] == 1
