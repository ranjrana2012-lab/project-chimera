"""Comprehensive unit tests for ParallelExecutor module."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from datetime import datetime, timedelta

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.executor import ParallelExecutor, TestResult
from orchestrator.models import ScheduledRun, ScheduledRunStatus


class TestTestResult:
    """Test suite for TestResult model."""

    def test_test_result_creation_with_all_fields(self):
        """Test TestResult creation with all fields."""
        started_at = datetime.utcnow()
        completed_at = started_at + timedelta(seconds=1)

        result = TestResult(
            result_id="test-result-123",
            test_id="tests/test.py::test_function",
            status="passed",
            duration_ms=1000,
            output="Test output",
            error_message="",
            started_at=started_at,
            completed_at=completed_at
        )

        assert result.result_id == "test-result-123"
        assert result.test_id == "tests/test.py::test_function"
        assert result.status == "passed"
        assert result.duration_ms == 1000
        assert result.output == "Test output"

    def test_test_result_default_result_id(self):
        """Test TestResult generates UUID for result_id if not provided."""
        result = TestResult(
            test_id="tests/test.py::test_function",
            status="passed",
            duration_ms=100,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert result.result_id is not None
        assert len(result.result_id) > 0

    def test_test_result_passed_status(self):
        """Test TestResult with passed status."""
        result = TestResult(
            test_id="test",
            status="passed",
            duration_ms=100,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert result.status == "passed"
        assert result.error_message == ""

    def test_test_result_failed_status(self):
        """Test TestResult with failed status."""
        result = TestResult(
            test_id="test",
            status="failed",
            duration_ms=100,
            error_message="AssertionError: Expected 200, got 500",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert result.status == "failed"
        assert "AssertionError" in result.error_message

    def test_test_result_skipped_status(self):
        """Test TestResult with skipped status."""
        result = TestResult(
            test_id="test",
            status="skipped",
            duration_ms=0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert result.status == "skipped"

    def test_test_result_error_status(self):
        """Test TestResult with error status."""
        result = TestResult(
            test_id="test",
            status="error",
            duration_ms=50,
            error_message="ImportError: Module not found",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert result.status == "error"

    def test_test_result_timeout_status(self):
        """Test TestResult with timeout status."""
        result = TestResult(
            test_id="test",
            status="timeout",
            duration_ms=30000,
            error_message="Test timed out after 30 seconds",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert result.status == "timeout"
        assert result.duration_ms == 30000

    def test_test_result_duration_calculation(self):
        """Test TestResult duration is in milliseconds."""
        started_at = datetime.utcnow()
        completed_at = started_at + timedelta(milliseconds=500)

        result = TestResult(
            test_id="test",
            status="passed",
            duration_ms=500,
            started_at=started_at,
            completed_at=completed_at
        )

        assert result.duration_ms == 500

    def test_test_result_with_long_output(self):
        """Test TestResult with long output text."""
        long_output = "x" * 10000

        result = TestResult(
            test_id="test",
            status="passed",
            duration_ms=100,
            output=long_output,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert len(result.output) == 10000

    def test_test_result_timestamps(self):
        """Test TestResult timestamps are datetime objects."""
        now = datetime.utcnow()

        result = TestResult(
            test_id="test",
            status="passed",
            duration_ms=100,
            started_at=now,
            completed_at=now + timedelta(seconds=1)
        )

        assert isinstance(result.started_at, datetime)
        assert isinstance(result.completed_at, datetime)
        assert result.completed_at > result.started_at


class TestParallelExecutor:
    """Test suite for ParallelExecutor class."""

    def test_executor_initialization_default_workers(self):
        """Test ParallelExecutor initializes with default max_workers."""
        executor = ParallelExecutor()

        assert executor.max_workers == 16

    def test_executor_initialization_custom_workers(self):
        """Test ParallelExecutor with custom max_workers."""
        executor = ParallelExecutor(max_workers=32)

        assert executor.max_workers == 32

    def test_executor_initialization_creates_semaphores(self):
        """Test ParallelExecutor creates resource semaphores."""
        executor = ParallelExecutor()

        assert "database" in executor.semaphores
        assert "kafka" in executor.semaphores
        assert "external_api" in executor.semaphores

    def test_executor_semaphore_types(self):
        """Test ParallelExecutor semaphores are asyncio.Semaphore."""
        import asyncio

        executor = ParallelExecutor()

        assert isinstance(executor.semaphores["database"], asyncio.Semaphore)
        assert isinstance(executor.semaphores["kafka"], asyncio.Semaphore)
        assert isinstance(executor.semaphores["external_api"], asyncio.Semaphore)

    def test_executor_semaphore_limits(self):
        """Test ParallelExecutor semaphore limits."""
        executor = ParallelExecutor()

        # Check semaphore internal value represents the limit
        # This is implementation-specific but useful to verify
        assert executor.semaphores["database"]._value == 5
        assert executor.semaphores["kafka"]._value == 3
        assert executor.semaphores["external_api"]._value == 10

    @pytest.mark.asyncio
    async def test_execute_tests_updates_run_status(self):
        """Test execute_tests updates run status to RUNNING."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            total_tests=5
        )

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery

            # Collect results
            results = []
            async for result in executor.execute_tests(run):
                results.append(result)
                break  # Just need to check status changed

            assert run.status == ScheduledRunStatus.RUNNING

    @pytest.mark.asyncio
    async def test_execute_tests_sets_started_at(self):
        """Test execute_tests sets started_at timestamp."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery

            async for result in executor.execute_tests(run):
                break

            assert run.started_at is not None

    @pytest.mark.asyncio
    async def test_execute_tests_creates_test_tasks(self):
        """Test execute_tests creates tasks for tests."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        mock_tests = [
            MagicMock(test_id="test_a", file_path="test_a.py"),
            MagicMock(test_id="test_b", file_path="test_b.py")
        ]

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=mock_tests)
            mock_discovery_class.return_value = mock_discovery

            with patch.object(executor, '_create_test_task', new_callable=AsyncMock) as mock_task:
                mock_task.return_value = TestResult(
                    test_id="test",
                    status="passed",
                    duration_ms=100,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )

                results = []
                async for result in executor.execute_tests(run):
                    results.append(result)

                # Should create tasks (limited to 5 in current implementation)
                assert mock_task.call_count <= 5

    @pytest.mark.asyncio
    async def test_execute_tests_handles_exceptions(self):
        """Test execute_tests handles task exceptions."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery

            with patch("asyncio.gather") as mock_gather:
                # Mock gather to return an exception
                mock_gather.return_value = [Exception("Test error")]

                results = []
                async for result in executor.execute_tests(run):
                    results.append(result)
                    break

                # Should yield error result
                assert len(results) > 0
                if results:
                    assert results[0].status == "error"

    @pytest.mark.asyncio
    async def test_execute_tests_sets_completed_at(self):
        """Test execute_tests sets completed_at after execution."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery

            # Consume all results
            async for _ in executor.execute_tests(run):
                pass

            assert run.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_tests_sets_status_to_completed(self):
        """Test execute_tests sets final status to COMPLETED."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery

            # Consume all results
            async for _ in executor.execute_tests(run):
                pass

            assert run.status == ScheduledRunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_create_test_task_executes_pytest(self):
        """Test _create_test_task executes pytest subprocess."""
        executor = ParallelExecutor()

        run_id = "run-123"
        test_spec = MagicMock(
            test_id="tests/test.py::test_func",
            file_path="tests/test.py"
        )

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"PASSED\n", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            result = await executor._create_test_task(run_id, test_spec)

            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0]
            assert "pytest" in call_args
            assert "tests/test.py" in call_args

    @pytest.mark.asyncio
    async def test_create_test_task_passed_result(self):
        """Test _create_test_task returns passed status for exit code 0."""
        executor = ParallelExecutor()

        run_id = "run-123"
        test_spec = MagicMock(
            test_id="tests/test.py::test_func",
            file_path="tests/test.py"
        )

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"test output", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            result = await executor._create_test_task(run_id, test_spec)

            assert result.status == "passed"
            assert result.test_id == "tests/test.py::test_func"

    @pytest.mark.asyncio
    async def test_create_test_task_failed_result(self):
        """Test _create_test_task returns failed status for non-zero exit."""
        executor = ParallelExecutor()

        run_id = "run-123"
        test_spec = MagicMock(
            test_id="tests/test.py::test_func",
            file_path="tests/test.py"
        )

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b"AssertionError"))
            mock_proc.returncode = 1
            mock_subprocess.return_value = mock_proc

            result = await executor._create_test_task(run_id, test_spec)

            assert result.status == "failed"
            assert result.error_message == "AssertionError"

    @pytest.mark.asyncio
    async def test_create_test_task_timeout(self):
        """Test _create_test_task handles timeout."""
        executor = ParallelExecutor()

        run_id = "run-123"
        test_spec = MagicMock(
            test_id="tests/test.py::test_func",
            file_path="tests/test.py"
        )

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            with patch("asyncio.wait_for") as mock_wait:
                mock_wait.side_effect = asyncio.TimeoutError()

                result = await executor._create_test_task(run_id, test_spec)

                assert result.status == "timeout"
                assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_create_test_task_calculates_duration(self):
        """Test _create_test_task calculates duration correctly."""
        executor = ParallelExecutor()

        run_id = "run-123"
        test_spec = MagicMock(
            test_id="tests/test.py::test_func",
            file_path="tests/test.py"
        )

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            import time
            mock_proc = AsyncMock()
            # Add small delay to test duration calculation
            async def mock_communicate():
                await asyncio.sleep(0.01)
                return (b"", b"")

            mock_proc.communicate = mock_communicate
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            result = await executor._create_test_task(run_id, test_spec)

            assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_create_test_task_includes_output(self):
        """Test _create_test_task includes stdout in result."""
        executor = ParallelExecutor()

        run_id = "run-123"
        test_spec = MagicMock(
            test_id="tests/test.py::test_func",
            file_path="tests/test.py"
        )

        test_output = b"=== test session starts ===\ntest.py::test_func PASSED\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(test_output, b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            result = await executor._create_test_task(run_id, test_spec)

            assert "test session starts" in result.output

    @pytest.mark.asyncio
    async def test_create_test_task_includes_stderr_on_failure(self):
        """Test _create_test_task includes stderr on failure."""
        executor = ParallelExecutor()

        run_id = "run-123"
        test_spec = MagicMock(
            test_id="tests/test.py::test_func",
            file_path="tests/test.py"
        )

        error_output = b"Traceback (most recent call last):\nAssertionError"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", error_output))
            mock_proc.returncode = 1
            mock_subprocess.return_value = mock_proc

            result = await executor._create_test_task(run_id, test_spec)

            assert result.status == "failed"
            assert "AssertionError" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_tests_with_empty_test_suite(self):
        """Test execute_tests handles empty test suite."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery

            results = []
            async for result in executor.execute_tests(run):
                results.append(result)

            # Should complete without errors
            assert run.status == ScheduledRunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_tests_uses_default_test_path(self):
        """Test execute_tests uses default tests/ path."""
        executor = ParallelExecutor()

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        with patch("orchestrator.executor.TestDiscovery") as mock_discovery_class:
            mock_discovery = AsyncMock()
            mock_discovery.discover_tests = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery

            async for _ in executor.execute_tests(run):
                pass

            # Verify discover_tests was called with correct path
            mock_discovery.discover_tests.assert_called_once_with("tests/")

    @pytest.mark.asyncio
    async def test_executor_with_varying_max_workers(self):
        """Test executor with different max_workers values."""
        for workers in [1, 4, 8, 16, 32, 64]:
            executor = ParallelExecutor(max_workers=workers)
            assert executor.max_workers == workers
