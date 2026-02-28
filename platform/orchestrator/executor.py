"""Parallel test execution with worker pools."""
import asyncio
import uuid
from typing import AsyncGenerator, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from orchestrator.models import ScheduledRun, ScheduledRunStatus
from orchestrator.discovery import TestSpec


class TestResult(BaseModel):
    """Result from a single test execution."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    status: str  # "passed", "failed", "skipped", "error", "timeout"
    duration_ms: int
    output: str = ""
    error_message: str = ""
    started_at: datetime
    completed_at: datetime


class ParallelExecutor:
    """Execute tests in parallel across worker pools."""

    def __init__(self, max_workers: int = 16):
        self.max_workers = max_workers
        self.semaphores: Dict[str, asyncio.Semaphore] = {
            "database": asyncio.Semaphore(5),
            "kafka": asyncio.Semaphore(3),
            "external_api": asyncio.Semaphore(10)
        }

    async def execute_tests(
        self,
        run: ScheduledRun
    ) -> AsyncGenerator[TestResult, None]:
        """Execute tests in parallel, yielding results as they complete."""

        # Update run status
        run.status = ScheduledRunStatus.RUNNING
        run.started_at = datetime.utcnow()

        # Discover tests
        from orchestrator.discovery import TestDiscovery
        discovery = TestDiscovery()
        tests = await discovery.discover_tests("tests/")

        # Create tasks for all tests
        tasks = []
        for test_spec in tests[:5]:  # Limit to 5 for testing
            task = self._create_test_task(run.id, test_spec)
            tasks.append(task)

        # Execute tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Yield results
        for result in results:
            if isinstance(result, Exception):
                yield TestResult(
                    test_id="unknown",
                    status="error",
                    duration_ms=0,
                    error_message=str(result),
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
            else:
                yield result

        # Update run status
        run.completed_at = datetime.utcnow()
        run.status = ScheduledRunStatus.COMPLETED

    async def _create_test_task(self, run_id: str, test_spec: TestSpec) -> TestResult:
        """Create and execute a single test task."""
        started_at = datetime.utcnow()

        try:
            # Execute the test
            proc = await asyncio.create_subprocess_exec(
                "pytest",
                test_spec.file_path,
                "-v",
                "--tb=short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=30.0
            )

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Parse result
            if proc.returncode == 0:
                status = "passed"
            else:
                status = "failed"

            result = TestResult(
                test_id=test_spec.test_id,
                status=status,
                duration_ms=duration_ms,
                output=stdout.decode(),
                error_message=stderr.decode() if status == "failed" else "",
                started_at=started_at,
                completed_at=completed_at
            )

            return result

        except asyncio.TimeoutError:
            return TestResult(
                test_id=test_spec.test_id,
                status="timeout",
                duration_ms=30000,
                error_message="Test timed out after 30 seconds",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
