"""Comprehensive unit tests for orchestrator models."""
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
import uuid

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.models import ScheduledRun, ScheduledRunStatus


class TestScheduledRunStatus:
    """Test suite for ScheduledRunStatus enum."""

    def test_status_enum_all_values(self):
        """Test all status enum values are correct."""
        assert ScheduledRunStatus.PENDING.value == "pending"
        assert ScheduledRunStatus.RUNNING.value == "running"
        assert ScheduledRunStatus.COMPLETED.value == "completed"
        assert ScheduledRunStatus.FAILED.value == "failed"
        assert ScheduledRunStatus.CANCELLED.value == "cancelled"

    def test_status_enum_is_string(self):
        """Test status enum values are strings."""
        assert isinstance(ScheduledRunStatus.PENDING, str)
        assert isinstance(ScheduledRunStatus.RUNNING, str)
        assert isinstance(ScheduledRunStatus.COMPLETED, str)

    def test_status_enum_iteration(self):
        """Test iterating over status enum values."""
        statuses = [s for s in ScheduledRunStatus]
        assert len(statuses) == 5
        assert ScheduledRunStatus.PENDING in statuses
        assert ScheduledRunStatus.CANCELLED in statuses

    def test_status_enum_equality(self):
        """Test status enum equality comparison."""
        assert ScheduledRunStatus.PENDING == "pending"
        assert ScheduledRunStatus.PENDING == ScheduledRunStatus.PENDING
        assert ScheduledRunStatus.PENDING != ScheduledRunStatus.RUNNING

    def test_status_enum_hashable(self):
        """Test status enum is hashable (can be used in sets/dicts)."""
        status_set = {ScheduledRunStatus.PENDING, ScheduledRunStatus.RUNNING}
        assert len(status_set) == 2
        assert ScheduledRunStatus.PENDING in status_set


class TestScheduledRun:
    """Test suite for ScheduledRun model."""

    def test_scheduled_run_minimal_creation(self):
        """Test ScheduledRun creation with minimal required fields."""
        run = ScheduledRun(
            commit_sha="abc123def456",
            branch="main"
        )

        assert run.commit_sha == "abc123def456"
        assert run.branch == "main"

    def test_scheduled_run_id_is_string(self):
        """Test ScheduledRun id is a string UUID."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert isinstance(run.id, str)
        # Should be valid UUID format
        uuid.UUID(run.id)  # Will raise if invalid

    def test_scheduled_run_id_unique_per_instance(self):
        """Test each ScheduledRun gets unique id."""
        run1 = ScheduledRun(commit_sha="abc", branch="main")
        run2 = ScheduledRun(commit_sha="def", branch="main")

        assert run1.id != run2.id

    def test_scheduled_run_default_status(self):
        """Test default status is PENDING."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.status == ScheduledRunStatus.PENDING

    def test_scheduled_run_custom_status(self):
        """Test setting custom status."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            status=ScheduledRunStatus.RUNNING
        )

        assert run.status == ScheduledRunStatus.RUNNING

    def test_scheduled_run_default_full_suite(self):
        """Test default full_suite is True."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.full_suite is True

    def test_scheduled_run_test_filter_none(self):
        """Test default test_filter is None."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.test_filter is None

    def test_scheduled_run_with_test_filter(self):
        """Test setting test_filter."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            test_filter=["tests/test_a.py", "tests/test_b.py"]
        )

        assert run.test_filter == ["tests/test_a.py", "tests/test_b.py"]
        assert len(run.test_filter) == 2

    def test_scheduled_run_default_worker_allocation(self):
        """Test default worker allocation."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.unit_test_workers == 16
        assert run.integration_workers == 8
        assert run.property_workers == 4
        assert run.e2e_workers == 2

    def test_scheduled_run_custom_worker_allocation(self):
        """Test custom worker allocation."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            unit_test_workers=32,
            integration_workers=16,
            property_workers=8,
            e2e_workers=4
        )

        assert run.unit_test_workers == 32
        assert run.integration_workers == 16
        assert run.property_workers == 8
        assert run.e2e_workers == 4

    def test_scheduled_run_default_results(self):
        """Test default result counters are zero."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.total_tests == 0
        assert run.passed == 0
        assert run.failed == 0
        assert run.skipped == 0

    def test_scheduled_run_with_results(self):
        """Test setting result counters."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            total_tests=100,
            passed=85,
            failed=10,
            skipped=5
        )

        assert run.total_tests == 100
        assert run.passed == 85
        assert run.failed == 10
        assert run.skipped == 5

    def test_scheduled_run_created_at_timestamp(self):
        """Test created_at is set automatically."""
        before = datetime.utcnow()
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )
        after = datetime.utcnow()

        assert run.created_at is not None
        assert before <= run.created_at <= after

    def test_scheduled_run_started_at_optional(self):
        """Test started_at is optional and defaults to None."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.started_at is None

    def test_scheduled_run_with_started_at(self):
        """Test setting started_at."""
        now = datetime.utcnow()
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            started_at=now
        )

        assert run.started_at == now

    def test_scheduled_run_completed_at_optional(self):
        """Test completed_at is optional and defaults to None."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.completed_at is None

    def test_scheduled_run_with_completed_at(self):
        """Test setting completed_at."""
        now = datetime.utcnow()
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            completed_at=now
        )

        assert run.completed_at == now

    def test_scheduled_run_duration_seconds_optional(self):
        """Test duration_seconds is optional and defaults to None."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.duration_seconds is None

    def test_scheduled_run_with_duration_seconds(self):
        """Test setting duration_seconds."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            duration_seconds=300
        )

        assert run.duration_seconds == 300

    def test_scheduled_run_branch_names(self):
        """Test various branch name formats."""
        branches = [
            "main",
            "master",
            "develop",
            "feature/new-feature",
            "bugfix/fix-123",
            "release/v1.0.0",
            "hotfix/critical-fix"
        ]

        for branch in branches:
            run = ScheduledRun(
                commit_sha="abc123",
                branch=branch
            )
            assert run.branch == branch

    def test_scheduled_run_commit_sha_formats(self):
        """Test various commit SHA formats."""
        shas = [
            "abc123",
            "abc123def456",
            "a1b2c3d4e5f6g7h8i9j0",
            "abcdef1234567890abcdef1234567890abcdef12"  # Full SHA
        ]

        for sha in shas:
            run = ScheduledRun(
                commit_sha=sha,
                branch="main"
            )
            assert run.commit_sha == sha

    def test_scheduled_run_complete_lifecycle(self):
        """Test complete lifecycle of a scheduled run."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        # Initial state
        assert run.status == ScheduledRunStatus.PENDING
        assert run.started_at is None
        assert run.completed_at is None

        # Start execution
        run.status = ScheduledRunStatus.RUNNING
        run.started_at = datetime.utcnow()
        assert run.status == ScheduledRunStatus.RUNNING

        # Complete with results
        run.status = ScheduledRunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        run.total_tests = 100
        run.passed = 95
        run.failed = 5
        run.duration_seconds = 120

        assert run.status == ScheduledRunStatus.COMPLETED
        assert run.started_at is not None
        assert run.completed_at is not None
        assert run.duration_seconds == 120

    def test_scheduled_run_failed_lifecycle(self):
        """Test lifecycle when run fails."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        run.status = ScheduledRunStatus.RUNNING
        run.started_at = datetime.utcnow()

        run.status = ScheduledRunStatus.FAILED
        run.completed_at = datetime.utcnow()

        assert run.status == ScheduledRunStatus.FAILED

    def test_scheduled_run_cancelled_lifecycle(self):
        """Test lifecycle when run is cancelled."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        run.status = ScheduledRunStatus.CANCELLED
        run.completed_at = datetime.utcnow()

        assert run.status == ScheduledRunStatus.CANCELLED

    def test_scheduled_run_serialization(self):
        """Test ScheduledRun can be serialized to dict."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            total_tests=50
        )

        run_dict = run.model_dump()

        assert run_dict["commit_sha"] == "abc123"
        assert run_dict["branch"] == "main"
        assert run_dict["total_tests"] == 50
        assert "id" in run_dict

    def test_scheduled_run_json_serialization(self):
        """Test ScheduledRun can be serialized to JSON."""
        import json

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        run_json = run.model_dump_json()

        assert "abc123" in run_json
        assert "main" in run_json

    def test_scheduled_run_with_zero_workers(self):
        """Test ScheduledRun with zero workers (edge case)."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            unit_test_workers=0,
            integration_workers=0,
            property_workers=0,
            e2e_workers=0
        )

        assert run.unit_test_workers == 0
        assert run.integration_workers == 0

    def test_scheduled_run_partial_results(self):
        """Test ScheduledRun with partial results."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            total_tests=100,
            passed=50,
            # failed and skipped left as default
        )

        assert run.total_tests == 100
        assert run.passed == 50
        assert run.failed == 0
        assert run.skipped == 0

    def test_scheduled_run_model_fields(self):
        """Test all expected fields are present."""
        run = ScheduledRun(
            commit_sha="abc",
            branch="main"
        )

        expected_fields = [
            "id", "commit_sha", "branch", "test_filter", "full_suite",
            "status", "created_at", "started_at", "completed_at",
            "unit_test_workers", "integration_workers", "property_workers",
            "e2e_workers", "total_tests", "passed", "failed", "skipped",
            "duration_seconds"
        ]

        for field in expected_fields:
            assert hasattr(run, field), f"Missing field: {field}"

    def test_scheduled_run_validation(self):
        """Test ScheduledRun validates input."""
        # Valid inputs should work
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            total_tests=100,
            passed=100,
            failed=0,
            skipped=0
        )

        assert run.total_tests == 100

    def test_scheduled_run_with_long_branch_name(self):
        """Test ScheduledRun with very long branch name."""
        long_branch = "feature/" + "a" * 200

        run = ScheduledRun(
            commit_sha="abc123",
            branch=long_branch
        )

        assert run.branch == long_branch

    def test_scheduled_run_copy(self):
        """Test ScheduledRun can be copied."""
        run1 = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        run2 = run1.model_copy()

        assert run2.id == run1.id
        assert run2.commit_sha == run1.commit_sha

    def test_scheduled_run_copy_with_updates(self):
        """Test ScheduledRun can be copied with updates."""
        run1 = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            status=ScheduledRunStatus.PENDING
        )

        run2 = run1.model_copy(update={"status": ScheduledRunStatus.RUNNING})

        assert run2.commit_sha == run1.commit_sha
        assert run2.status == ScheduledRunStatus.RUNNING
        assert run1.status == ScheduledRunStatus.PENDING
