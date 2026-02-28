"""Test scheduling and selection logic."""
import asyncio
from typing import List, Optional
from orchestrator.models import ScheduledRun, ScheduledRunStatus
from orchestrator.discovery import TestDiscovery, TestSpec


class TestScheduler:
    """Schedule test runs for optimal execution."""

    def __init__(self):
        self.discovery = TestDiscovery()

    async def schedule_run(
        self,
        commit_sha: str,
        branch: str,
        test_filter: Optional[List[str]] = None,
        full_suite: bool = True
    ) -> ScheduledRun:
        """Create a scheduled test run."""

        # Discover all tests
        all_tests = await self.discovery.discover_tests("tests/")

        # Filter tests if test_filter provided
        if test_filter:
            tests = [t for t in all_tests if t.test_id in test_filter]
        else:
            tests = all_tests

        # Create scheduled run
        run = ScheduledRun(
            commit_sha=commit_sha,
            branch=branch,
            test_filter=test_filter,
            full_suite=full_suite,
            total_tests=len(tests),
            status=ScheduledRunStatus.PENDING
        )

        return run

    async def select_tests_for_commit(
        self,
        commit_sha: str,
        base_branch: str = "main"
    ) -> List[TestSpec]:
        """Select tests affected by a commit's changes using git diff."""

        # Get changed files using git diff
        proc = await asyncio.create_subprocess_exec(
            "git",
            "diff",
            "--name-only",
            f"{base_branch}...{commit_sha}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await proc.communicate()
        changed_files = stdout.decode().strip().split("\n")
        changed_files = [f for f in changed_files if f]

        # Use pytest to find affected tests
        tests = []
        for file_path in changed_files:
            file_tests = await self._get_tests_for_file(file_path)
            tests.extend(file_tests)

        # Remove duplicates
        seen = set()
        unique_tests = []
        for test in tests:
            if test.test_id not in seen:
                seen.add(test.test_id)
                unique_tests.append(test)

        return unique_tests

    async def _get_tests_for_file(self, file_path: str) -> List[TestSpec]:
        """Get tests that import from or test a specific file."""
        # Use pytest --collect-only with file filter
        proc = await asyncio.create_subprocess_exec(
            "pytest",
            "--collect-only",
            "-q",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await proc.communicate()
        tests = []

        for line in stdout.decode().split("\n"):
            if "<Function" in line or "<Class" in line:
                test_spec = self.discovery._parse_pytest_line(line)
                if test_spec:
                    tests.append(test_spec)

        return tests
