"""Tests for Ralph Engine."""

import pytest
from ralph_engine import RalphEngine, BackstopExceededError


@pytest.fixture
def engine():
    """Create a RalphEngine instance for testing."""
    return RalphEngine(max_retries=3)


def test_ralph_engine_initialization(engine):
    """Test RalphEngine initializes with correct settings."""
    assert engine.max_retries == 3
    assert engine.retry_count == 0


def test_ralph_engine_backstop_not_hit_on_success(engine):
    """Test that engine doesn't hit backstop when task succeeds."""
    class MockTask:
        id = "test-task-1"
        requirements = ["requirement1"]

    class MockResult:
        success = True
        error = None
        data = {"message": "Success"}

    async def mock_execute(task, context):
        return MockResult()

    engine.execute_task = mock_execute

    result = engine.execute_until_promise_sync(MockTask())

    assert result.success is True
    assert engine.retry_count == 0


def test_ralph_engine_backstop_hit_after_max_retries(engine):
    """Test that engine raises BackstopExceededError after max retries."""
    class MockTask:
        id = "test-task-2"
        requirements = ["requirement1"]

    class MockResult:
        success = False
        error = "Test error"
        data = {}

    async def mock_execute(task, context):
        return MockResult()

    engine.execute_task = mock_execute

    with pytest.raises(BackstopExceededError) as exc_info:
        engine.execute_until_promise_sync(MockTask())

    assert "test-task-2" in str(exc_info.value)
    assert "3 retries" in str(exc_info.value)
    assert engine.retry_count == 3


# Synchronous wrapper for async testing
def execute_until_promise_sync(self, task):
    """Synchronous wrapper for testing."""
    import asyncio

    async def _execute():
        return await self.execute_until_promise(task)

    return asyncio.run(_execute())


# Monkey patch for testing
RalphEngine.execute_until_promise_sync = execute_until_promise_sync
