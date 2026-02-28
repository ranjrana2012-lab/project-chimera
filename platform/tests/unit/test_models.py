"""Test database models."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from shared.models import (
    TestRun,
    TestResult,
    CoverageSnapshot,
    MutationResult,
    PerformanceMetric,
    DailySummary,
    QualityGateResult,
)


def test_test_run_model_attributes():
    """Test TestRun model has required attributes."""
    run = TestRun(
        commit_sha="abc123",
        branch="main",
        status="pending",
        total_tests=100,
        started_at=datetime.now(timezone.utc),
    )
    assert run.commit_sha == "abc123"
    assert run.branch == "main"
    assert run.status == "pending"
    assert run.total_tests == 100


def test_test_result_model_attributes():
    """Test TestResult model has required attributes."""
    result = TestResult(
        run_id=None,
        test_id="tests/example.py::test_example",
        status="passed",
        duration_ms=100,
    )
    assert result.test_id == "tests/example.py::test_example"
    assert result.status == "passed"
    assert result.duration_ms == 100


def test_coverage_snapshot_model_attributes():
    """Test CoverageSnapshot model has required attributes."""
    snapshot = CoverageSnapshot(
        run_id=None,
        service_name="auth-service",
        line_coverage=85.5,
        branch_coverage=75.0,
        lines_covered=855,
        lines_total=1000,
    )
    assert snapshot.service_name == "auth-service"
    assert snapshot.line_coverage == 85.5
    assert snapshot.lines_covered == 855


def test_mutation_result_model_attributes():
    """Test MutationResult model has required attributes."""
    mutation = MutationResult(
        run_id=None,
        service_name="auth-service",
        total_mutations=100,
        killed_mutations=85,
        survived_mutations=10,
        timeout_mutations=5,
        mutation_score=85.0,
    )
    assert mutation.service_name == "auth-service"
    assert mutation.total_mutations == 100
    assert mutation.mutation_score == 85.0


def test_performance_metric_model_attributes():
    """Test PerformanceMetric model has required attributes."""
    metric = PerformanceMetric(
        run_id=None,
        endpoint_name="/api/v1/users",
        requests_per_second=1000.5,
        avg_response_time_ms=50,
        p95_response_time_ms=100,
        p99_response_time_ms=200,
        error_rate=0.1,
    )
    assert metric.endpoint_name == "/api/v1/users"
    assert metric.requests_per_second == 1000.5
    assert metric.avg_response_time_ms == 50


def test_daily_summary_model_attributes():
    """Test DailySummary model has required attributes."""
    from datetime import date

    summary = DailySummary(
        date=date(2024, 1, 1),
        service_name="auth-service",
        total_runs=10,
        avg_coverage=85.5,
        avg_mutation_score=80.0,
        avg_duration_seconds=300,
    )
    assert summary.date == date(2024, 1, 1)
    assert summary.service_name == "auth-service"
    assert summary.total_runs == 10


def test_quality_gate_result_model_attributes():
    """Test QualityGateResult model has required attributes."""
    gate = QualityGateResult(
        run_id=None,
        gate_name="coverage_gate",
        status="passed",
        threshold=80.0,
        actual_value=85.5,
        message="Coverage threshold met",
    )
    assert gate.gate_name == "coverage_gate"
    assert gate.status == "passed"
    assert gate.threshold == 80.0


@pytest.mark.asyncio
@pytest.mark.skip(reason="Database not set up yet - will be tested in integration tests")
async def test_create_test_run(db_session: AsyncSession):
    """Test creating a test run."""
    run = TestRun(
        commit_sha="abc123",
        branch="main",
        status="pending",
        total_tests=100,
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    assert run.id is not None
    assert run.commit_sha == "abc123"


@pytest.mark.asyncio
@pytest.mark.skip(reason="Database not set up yet - will be tested in integration tests")
async def test_test_result_relationship(db_session: AsyncSession):
    """Test test results belong to run."""
    run = TestRun(
        commit_sha="abc123",
        branch="main",
        status="completed",
        total_tests=1,
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(run)
    await db_session.flush()

    result = TestResult(
        run_id=run.id,
        test_id="tests/example.py::test_example",
        status="passed",
        duration_ms=100,
    )
    db_session.add(result)
    await db_session.commit()

    assert result.run_id == run.id
