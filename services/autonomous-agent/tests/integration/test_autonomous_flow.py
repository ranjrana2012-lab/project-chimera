"""Integration tests for autonomous flow."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from ralph_engine import RalphEngine, Task as RalphTask
from gsd_orchestrator import GSDOrchestrator
from flow_next import FlowNextManager


@pytest.fixture
def temp_state_dir():
    """Create temporary state directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_full_autonomous_flow(temp_state_dir):
    """Test full autonomous flow: GSD → Ralph → Flow-Next."""
    # Setup
    orchestrator = GSDOrchestrator()
    flow_manager = FlowNextManager(state_dir=temp_state_dir)
    ralph = RalphEngine(max_retries=3, state_file=str(temp_state_dir / "STATE.md"))

    # Test Discuss phase
    user_request = "Create a simple REST API"
    requirements = orchestrator.discuss_phase(user_request)

    assert requirements.goal == user_request

    # Test Plan phase
    plan = orchestrator.plan_phase(requirements)

    assert len(plan.tasks) > 0
    assert plan.tasks[0].id == "1"

    # Write requirements and plan to state directory
    orchestrator.write_requirements(requirements, str(temp_state_dir / "REQUIREMENTS.md"))
    orchestrator.write_plan(plan, str(temp_state_dir / "PLAN.md"))

    # Verify REQUIREMENTS.md was created
    req_file = temp_state_dir / "REQUIREMENTS.md"
    assert req_file.exists()
    assert "Create a simple REST API" in req_file.read_text()

    # Verify PLAN.md was created
    plan_file = temp_state_dir / "PLAN.md"
    assert plan_file.exists()

    # Test Flow-Next fresh session
    session = flow_manager.create_fresh_session()
    assert session.history == []

    # Test Ralph execution
    ralph_task = RalphTask(
        id="test-task-1",
        requirements=["Implement REST API"]
    )

    result = await ralph.execute_until_promise(ralph_task)

    assert result.success is True


@pytest.mark.asyncio
async def test_ralph_mode_retry_behavior(temp_state_dir):
    """Test Ralph Mode retry behavior."""
    ralph = RalphEngine(max_retries=3, state_file=str(temp_state_dir / "STATE.md"))

    # Create a task that will fail
    class FailingTask:
        id = "failing-task"
        requirements = ["fail"]

    # Mock execute to always fail
    async def failing_execute(task, context):
        from ralph_engine import Result
        return Result(success=False, error="Simulated failure")

    original_execute = ralph.execute_task
    ralph.execute_task = failing_execute

    # Should fail after 3 retries
    with pytest.raises(Exception):  # BackstopExceededError
        await ralph.execute_until_promise(FailingTask())

    # Restore original
    ralph.execute_task = original_execute


@pytest.mark.asyncio
async def test_flow_next_amnesia(temp_state_dir):
    """Test that Flow-Next provides fresh sessions (no history)."""
    flow_manager = FlowNextManager(state_dir=temp_state_dir)

    # Create first session
    session1 = flow_manager.create_fresh_session()
    session1.history.append("old context")
    session1.history.append("more old context")

    # Save and reset
    flow_manager.save_and_reset(session1)

    # Create new session - should be fresh
    session2 = flow_manager.create_fresh_session()

    assert session2.history == []
    assert len(session1.history) == 2  # Original unchanged
