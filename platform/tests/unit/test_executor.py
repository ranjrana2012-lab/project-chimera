"""Test parallel executor."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from orchestrator.executor import ParallelExecutor, TestResult
from orchestrator.scheduler import TestScheduler
from orchestrator.models import ScheduledRun, ScheduledRunStatus

@pytest.mark.asyncio
async def test_executor_initializes_with_semaphores():
    """Test executor creates semaphores for resource management."""
    executor = ParallelExecutor()

    assert "database" in executor.semaphores
    assert "kafka" in executor.semaphores
    assert "external_api" in executor.semaphores

def test_test_result_model():
    """Test TestResult model validation."""
    from datetime import datetime

    result = TestResult(
        test_id="tests/example.py::test_func",
        status="passed",
        duration_ms=100,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )

    assert result.test_id == "tests/example.py::test_func"
    assert result.status == "passed"
    assert result.duration_ms == 100
    assert result.result_id is not None
