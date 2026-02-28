"""Test scheduler module."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from orchestrator.scheduler import TestScheduler
from orchestrator.models import ScheduledRun, ScheduledRunStatus


@pytest.mark.asyncio
async def test_schedule_run_creates_run_object():
    """Test scheduling a run creates a ScheduledRun object."""
    scheduler = TestScheduler()

    run = await scheduler.schedule_run(
        commit_sha="abc123",
        branch="main"
    )

    assert isinstance(run, ScheduledRun)
    assert run.commit_sha == "abc123"
    assert run.branch == "main"
    assert run.status == ScheduledRunStatus.PENDING
    assert run.total_tests > 0


def test_scheduled_run_status_enum():
    """Test ScheduledRunStatus enum has all required values."""
    assert ScheduledRunStatus.PENDING == "pending"
    assert ScheduledRunStatus.RUNNING == "running"
    assert ScheduledRunStatus.COMPLETED == "completed"
    assert ScheduledRunStatus.FAILED == "failed"
    assert ScheduledRunStatus.CANCELLED == "cancelled"


def test_scheduled_run_model():
    """Test ScheduledRun model validation."""
    run = ScheduledRun(
        commit_sha="abc123",
        branch="main",
        total_tests=100,
        unit_test_workers=16,
        integration_workers=8,
        property_workers=4,
        e2e_workers=2
    )

    assert run.commit_sha == "abc123"
    assert run.branch == "main"
    assert run.total_tests == 100
    assert run.unit_test_workers == 16
    assert run.status == ScheduledRunStatus.PENDING
