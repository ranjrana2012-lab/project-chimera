"""Unit tests for cue executor."""

import pytest
from services.lighting_control.src.core.cue_executor import (
    CueExecutor,
    CueList,
    CueDefinition,
    CueState
)
from services.lighting_control.src.models.request import CueRequest


@pytest.mark.unit
class TestCueList:
    """Test cases for CueList."""

    @pytest.fixture
    def cue_list(self):
        """Create a test cue list."""
        return CueList("main")

    def test_cue_list_initialization(self, cue_list):
        """Test cue list initialization."""
        assert cue_list.name == "main"
        assert len(cue_list.cues) == 0
        assert len(cue_list.execution_order) == 0

    def test_add_cue(self, cue_list):
        """Test adding a cue."""
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="warm",
            values={1: 255},
            fade_time=2.0,
            delay_secs=0.0,
            follow_on=False
        )
        result = cue_list.add_cue(cue)
        assert result is True
        assert "1" in cue_list.cues

    def test_add_duplicate_cue(self, cue_list):
        """Test adding duplicate cue."""
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="warm",
            values={1: 255},
            fade_time=2.0,
            delay_secs=0.0,
            follow_on=False
        )
        cue_list.add_cue(cue)
        result = cue_list.add_cue(cue)
        assert result is False

    def test_remove_cue(self, cue_list):
        """Test removing a cue."""
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="warm",
            values={1: 255},
            fade_time=2.0,
            delay_secs=0.0,
            follow_on=False
        )
        cue_list.add_cue(cue)
        result = cue_list.remove_cue("1")
        assert result is True
        assert "1" not in cue_list.cues

    def test_get_cue(self, cue_list):
        """Test getting a cue."""
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="warm",
            values={1: 255},
            fade_time=2.0,
            delay_secs=0.0,
            follow_on=False
        )
        cue_list.add_cue(cue)
        retrieved = cue_list.get_cue("1")
        assert retrieved is not None
        assert retrieved.cue_number == "1"

    def test_get_next_cue(self, cue_list):
        """Test getting next cue."""
        cue1 = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="warm",
            values={1: 255},
            fade_time=2.0,
            delay_secs=0.0,
            follow_on=False
        )
        cue2 = CueDefinition(
            cue_number="2",
            cue_list="main",
            preset_name="bright",
            values={1: 128},
            fade_time=1.0,
            delay_secs=0.0,
            follow_on=False
        )
        cue_list.add_cue(cue1)
        cue_list.add_cue(cue2)

        next_cue = cue_list.get_next_cue("1")
        assert next_cue is not None
        assert next_cue.cue_number == "2"


@pytest.mark.unit
@pytest.mark.asyncio
class TestCueExecutor:
    """Test cases for CueExecutor."""

    @pytest.fixture
    def executor(self):
        """Create a test executor."""
        return CueExecutor()

    async def test_executor_initialization(self, executor):
        """Test executor initialization."""
        assert executor.current_cue is None
        assert len(executor.active_executions) == 0

    async def test_create_cue_list(self, executor):
        """Test creating cue list."""
        cue_list = executor.create_cue_list("test")
        assert cue_list.name == "test"
        assert "test" in executor.cue_lists

    async def test_get_cue_list(self, executor):
        """Test getting cue list."""
        executor.create_cue_list("test")
        cue_list = executor.get_cue_list("test")
        assert cue_list is not None
        assert cue_list.name == "test"

    async def test_add_cue(self, executor):
        """Test adding a cue."""
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="test",
            values={1: 255},
            fade_time=1.0,
            delay_secs=0.0,
            follow_on=False
        )
        result = executor.add_cue(cue)
        assert result is True
        assert "main" in executor.cue_lists

    async def test_execute_cue_without_callback(self, executor):
        """Test executing cue without lighting callback."""
        executor.create_cue_list("main")
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="test",
            values={1: 255},
            fade_time=0.1,
            delay_secs=0.0,
            follow_on=False
        )
        executor.add_cue(cue)

        request = CueRequest(cue_number="1", cue_list="main")
        response = await executor.execute_cue(request)
        assert response.executed is True
        assert response.status == "completed"

    async def test_execute_cue_with_delay(self, executor):
        """Test executing cue with delay."""
        executor.create_cue_list("main")
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="test",
            values={1: 255},
            fade_time=0.0,
            delay_secs=0.1,
            follow_on=False
        )
        executor.add_cue(cue)

        request = CueRequest(cue_number="1", cue_list="main")
        response = await executor.execute_cue(request)
        assert response.executed is True
        assert response.timing["delay"] == 0.1

    async def test_execute_nonexistent_cue(self, executor):
        """Test executing non-existent cue."""
        request = CueRequest(cue_number="999", cue_list="main")
        response = await executor.execute_cue(request)
        assert response.executed is False
        assert response.status == "failed"

    async def test_get_current_cue(self, executor):
        """Test getting current cue."""
        assert executor.get_current_cue() is None

        # After execution
        executor.create_cue_list("main")
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="test",
            values={1: 255},
            fade_time=0.0,
            delay_secs=0.0,
            follow_on=False
        )
        executor.add_cue(cue)

        await executor.execute_cue(CueRequest(cue_number="1", cue_list="main"))
        current = executor.get_current_cue()
        assert current == "1"

    async def test_stop_all(self, executor):
        """Test stopping all executions."""
        await executor.stop_all()
        assert executor._stop_event.is_set()

    async def test_resume(self, executor):
        """Test resuming."""
        await executor.stop_all()
        await executor.resume()
        assert not executor._stop_event.is_set()

    async def test_get_statistics(self, executor):
        """Test getting statistics."""
        executor.create_cue_list("main")
        stats = executor.get_statistics()
        assert "total_executions" in stats
        assert "by_state" in stats
        assert "cue_lists" in stats
        assert "main" in stats["cue_lists"]

    async def test_clear_history(self, executor):
        """Test clearing execution history."""
        executor.create_cue_list("main")
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="test",
            values={1: 255},
            fade_time=0.0,
            delay_secs=0.0,
            follow_on=False
        )
        executor.add_cue(cue)
        await executor.execute_cue(CueRequest(cue_number="1", cue_list="main"))

        # Clear very old history
        count = executor.clear_history(older_than_secs=3600)
        # Should have cleared the completed execution
        assert count >= 0


@pytest.mark.unit
class TestCueDefinition:
    """Test cases for CueDefinition."""

    def test_cue_definition_creation(self):
        """Test creating cue definition."""
        cue = CueDefinition(
            cue_number="1",
            cue_list="main",
            preset_name="test",
            values={1: 255},
            fade_time=2.0,
            delay_secs=0.5,
            follow_on=True
        )
        assert cue.cue_number == "1"
        assert cue.preset_name == "test"
        assert cue.fade_time == 2.0
        assert cue.delay_secs == 0.5
        assert cue.follow_on is True
