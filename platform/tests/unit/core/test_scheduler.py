"""Comprehensive unit tests for TestScheduler module."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.scheduler import TestScheduler
from orchestrator.models import ScheduledRun, ScheduledRunStatus
from orchestrator.discovery import TestSpec


class TestScheduler:
    """Test suite for TestScheduler class."""

    def test_scheduler_initialization(self):
        """Test TestScheduler initializes with discovery instance."""
        scheduler = TestScheduler()
        assert scheduler.discovery is not None
        assert hasattr(scheduler, 'discovery')

    @pytest.mark.asyncio
    async def test_schedule_run_creates_scheduled_run(self):
        """Test schedule_run creates a ScheduledRun object."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [
                TestSpec(
                    test_id="tests/test.py::test_a",
                    file_path="tests/test.py",
                    test_function="test_a"
                )
            ]

            run = await scheduler.schedule_run(
                commit_sha="abc123",
                branch="main"
            )

            assert isinstance(run, ScheduledRun)
            assert run.commit_sha == "abc123"
            assert run.branch == "main"

    @pytest.mark.asyncio
    async def test_schedule_run_default_values(self):
        """Test schedule_run uses default values."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [
                TestSpec(
                    test_id="tests/test.py::test_a",
                    file_path="tests/test.py",
                    test_function="test_a"
                )
            ]

            run = await scheduler.schedule_run(
                commit_sha="abc123",
                branch="main"
            )

            assert run.full_suite is True
            assert run.status == ScheduledRunStatus.PENDING
            assert run.test_filter is None

    @pytest.mark.asyncio
    async def test_schedule_run_with_test_filter(self):
        """Test schedule_run with test filter."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [
                TestSpec(
                    test_id="tests/test.py::test_a",
                    file_path="tests/test.py",
                    test_function="test_a"
                ),
                TestSpec(
                    test_id="tests/test.py::test_b",
                    file_path="tests/test.py",
                    test_function="test_b"
                )
            ]

            run = await scheduler.schedule_run(
                commit_sha="abc123",
                branch="main",
                test_filter=["tests/test.py::test_a"]
            )

            assert run.test_filter == ["tests/test.py::test_a"]

    @pytest.mark.asyncio
    async def test_schedule_run_filters_tests(self):
        """Test schedule_run filters tests based on test_filter."""
        scheduler = TestScheduler()

        mock_tests = [
            TestSpec(
                test_id="tests/test.py::test_a",
                file_path="tests/test.py",
                test_function="test_a"
            ),
            TestSpec(
                test_id="tests/test.py::test_b",
                file_path="tests/test.py",
                test_function="test_b"
            ),
            TestSpec(
                test_id="tests/test.py::test_c",
                file_path="tests/test.py",
                test_function="test_c"
            )
        ]

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = mock_tests

            run = await scheduler.schedule_run(
                commit_sha="abc123",
                branch="main",
                test_filter=["tests/test.py::test_a", "tests/test.py::test_c"]
            )

            assert run.total_tests == 2

    @pytest.mark.asyncio
    async def test_schedule_run_full_suite_false(self):
        """Test schedule_run with full_suite=False."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [
                TestSpec(
                    test_id="tests/test.py::test_a",
                    file_path="tests/test.py",
                    test_function="test_a"
                )
            ]

            run = await scheduler.schedule_run(
                commit_sha="abc123",
                branch="main",
                full_suite=False
            )

            assert run.full_suite is False

    @pytest.mark.asyncio
    async def test_schedule_run_empty_test_list(self):
        """Test schedule_run with no tests discovered."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []

            run = await scheduler.schedule_run(
                commit_sha="abc123",
                branch="main"
            )

            assert run.total_tests == 0

    @pytest.mark.asyncio
    async def test_schedule_run_with_various_branches(self):
        """Test schedule_run with different branch names."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []

            run_main = await scheduler.schedule_run("abc123", "main")
            run_dev = await scheduler.schedule_run("def456", "develop")
            run_feature = await scheduler.schedule_run("ghi789", "feature/new-stuff")

            assert run_main.branch == "main"
            assert run_dev.branch == "develop"
            assert run_feature.branch == "feature/new-stuff"

    @pytest.mark.asyncio
    async def test_schedule_run_with_various_commit_shas(self):
        """Test schedule_run with different commit SHA formats."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []

            run_short = await scheduler.schedule_run("abc123", "main")
            run_full = await scheduler.schedule_run("a1b2c3d4e5f6g7h8i9j0", "main")
            run_with_tag = await scheduler.schedule_run("v1.2.3", "main")

            assert run_short.commit_sha == "abc123"
            assert run_full.commit_sha == "a1b2c3d4e5f6g7h8i9j0"
            assert run_with_tag.commit_sha == "v1.2.3"

    @pytest.mark.asyncio
    async def test_select_tests_for_commit_with_git_diff(self):
        """Test select_tests_for_commit uses git diff."""
        scheduler = TestScheduler()

        mock_output = b"services/auth/main.py\n"
        mock_output += b"services/auth/test_auth.py\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(mock_output, b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            with patch.object(scheduler, '_get_tests_for_file', new_callable=AsyncMock) as mock_get_tests:
                mock_get_tests.return_value = []

                tests = await scheduler.select_tests_for_commit(
                    commit_sha="abc123",
                    base_branch="main"
                )

                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0]
                assert "git" in call_args
                assert "diff" in call_args

    @pytest.mark.asyncio
    async def test_select_tests_for_commit_removes_duplicates(self):
        """Test select_tests_for_commit removes duplicate tests."""
        scheduler = TestScheduler()

        mock_tests = [
            TestSpec(
                test_id="tests/test.py::test_a",
                file_path="tests/test.py",
                test_function="test_a"
            )
        ]

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"file.py\n", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            with patch.object(scheduler, '_get_tests_for_file', new_callable=AsyncMock) as mock_get_tests:
                # Return same test twice to test deduplication
                mock_get_tests.return_value = mock_tests

                tests = await scheduler.select_tests_for_commit("abc123")

                # Should only have unique tests
                test_ids = [t.test_id for t in tests]
                assert len(test_ids) == len(set(test_ids))

    @pytest.mark.asyncio
    async def test_select_tests_for_commit_with_custom_base_branch(self):
        """Test select_tests_for_commit with custom base branch."""
        scheduler = TestScheduler()

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            with patch.object(scheduler, '_get_tests_for_file', new_callable=AsyncMock) as mock_get_tests:
                mock_get_tests.return_value = []

                await scheduler.select_tests_for_commit(
                    commit_sha="abc123",
                    base_branch="develop"
                )

                call_args = mock_subprocess.call_args[0]
                assert "develop" in call_args

    @pytest.mark.asyncio
    async def test_get_tests_for_file_uses_pytest_collect(self):
        """Test _get_tests_for_file uses pytest --collect-only."""
        scheduler = TestScheduler()

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            await scheduler._get_tests_for_file("services/auth/main.py")

            call_args = mock_subprocess.call_args[0]
            assert "pytest" in call_args
            assert "--collect-only" in call_args
            assert "-q" in call_args

    @pytest.mark.asyncio
    async def test_get_tests_for_file_parses_output(self):
        """Test _get_tests_for_file parses pytest output."""
        scheduler = TestScheduler()

        mock_output = b"services/auth/test_auth.py::test_login\n"
        mock_output += b"services/auth/test_auth.py::TestClass::test_logout\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(mock_output, b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            # Mock the discovery parser
            with patch.object(scheduler.discovery, '_parse_pytest_line') as mock_parse:
                mock_parse.return_value = TestSpec(
                    test_id="test",
                    file_path="test.py",
                    test_function="test"
                )

                tests = await scheduler._get_tests_for_file("services/auth/main.py")

                # Parser should be called for non-empty lines
                assert mock_parse.call_count > 0

    @pytest.mark.asyncio
    async def test_get_tests_for_file_handles_empty_output(self):
        """Test _get_tests_for_file handles empty pytest output."""
        scheduler = TestScheduler()

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            tests = await scheduler._get_tests_for_file("nonexistent.py")

            assert tests == []

    @pytest.mark.asyncio
    async def test_select_tests_for_commit_handles_no_changes(self):
        """Test select_tests_for_commit handles commit with no file changes."""
        scheduler = TestScheduler()

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            with patch.object(scheduler, '_get_tests_for_file', new_callable=AsyncMock) as mock_get_tests:
                mock_get_tests.return_value = []

                tests = await scheduler.select_tests_for_commit("abc123")

                assert tests == []

    @pytest.mark.asyncio
    async def test_select_tests_for_commit_handles_multiple_files(self):
        """Test select_tests_for_commit with multiple changed files."""
        scheduler = TestScheduler()

        changed_files = "services/auth/main.py\nservices/api/routes.py\ndocs/api.md\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(changed_files.encode(), b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            with patch.object(scheduler, '_get_tests_for_file', new_callable=AsyncMock) as mock_get_tests:
                mock_get_tests.return_value = []

                tests = await scheduler.select_tests_for_commit("abc123")

                # Should call _get_tests_for_file for each changed file
                assert mock_get_tests.call_count == 3

    @pytest.mark.asyncio
    async def test_schedule_run_id_generation(self):
        """Test schedule_run generates unique IDs."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []

            run1 = await scheduler.schedule_run("abc123", "main")
            run2 = await scheduler.schedule_run("def456", "main")

            assert run1.id != run2.id

    @pytest.mark.asyncio
    async def test_schedule_run_created_at_timestamp(self):
        """Test schedule_run sets created_at timestamp."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []

            import datetime
            before = datetime.datetime.utcnow()
            run = await scheduler.schedule_run("abc123", "main")
            after = datetime.datetime.utcnow()

            assert run.created_at is not None
            assert before <= run.created_at <= after

    @pytest.mark.asyncio
    async def test_schedule_run_default_worker_allocation(self):
        """Test schedule_run has default worker allocation."""
        scheduler = TestScheduler()

        with patch.object(scheduler.discovery, 'discover_tests', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []

            run = await scheduler.schedule_run("abc123", "main")

            assert run.unit_test_workers == 16
            assert run.integration_workers == 8
            assert run.property_workers == 4
            assert run.e2e_workers == 2


class TestScheduledRunStatus:
    """Test suite for ScheduledRunStatus enum."""

    def test_status_enum_values(self):
        """Test ScheduledRunStatus has all required status values."""
        assert ScheduledRunStatus.PENDING == "pending"
        assert ScheduledRunStatus.RUNNING == "running"
        assert ScheduledRunStatus.COMPLETED == "completed"
        assert ScheduledRunStatus.FAILED == "failed"
        assert ScheduledRunStatus.CANCELLED == "cancelled"

    def test_status_enum_comparison(self):
        """Test ScheduledRunStatus enum comparison works."""
        status1 = ScheduledRunStatus.PENDING
        status2 = ScheduledRunStatus.PENDING
        status3 = ScheduledRunStatus.RUNNING

        assert status1 == status2
        assert status1 != status3

    def test_status_enum_string_value(self):
        """Test ScheduledRunStatus enum values are strings."""
        assert isinstance(ScheduledRunStatus.PENDING, str)
        assert isinstance(ScheduledRunStatus.RUNNING, str)


class TestScheduledRun:
    """Test suite for ScheduledRun model."""

    def test_scheduled_run_creation(self):
        """Test ScheduledRun creation with required fields."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            total_tests=100
        )

        assert run.commit_sha == "abc123"
        assert run.branch == "main"
        assert run.total_tests == 100

    def test_scheduled_run_default_status(self):
        """Test ScheduledRun has PENDING as default status."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.status == ScheduledRunStatus.PENDING

    def test_scheduled_run_with_all_fields(self):
        """Test ScheduledRun with all fields populated."""
        from datetime import datetime

        now = datetime.utcnow()
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main",
            test_filter=["test_a", "test_b"],
            full_suite=False,
            status=ScheduledRunStatus.RUNNING,
            total_tests=50,
            passed=40,
            failed=5,
            skipped=5,
            duration_seconds=120
        )

        assert run.test_filter == ["test_a", "test_b"]
        assert run.full_suite is False
        assert run.status == ScheduledRunStatus.RUNNING
        assert run.passed == 40
        assert run.failed == 5
        assert run.skipped == 5

    def test_scheduled_run_custom_worker_allocation(self):
        """Test ScheduledRun with custom worker allocation."""
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

    def test_scheduled_run_id_is_uuid(self):
        """Test ScheduledRun generates UUID for id."""
        import uuid

        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        # Should be able to parse as UUID
        try:
            uuid.UUID(run.id)
            assert True
        except ValueError:
            assert False, "ID is not a valid UUID"

    def test_scheduled_run_results_initialization(self):
        """Test ScheduledRun initializes results counters to zero."""
        run = ScheduledRun(
            commit_sha="abc123",
            branch="main"
        )

        assert run.total_tests == 0
        assert run.passed == 0
        assert run.failed == 0
        assert run.skipped == 0
