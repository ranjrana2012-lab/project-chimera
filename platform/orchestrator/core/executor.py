"""
Parallel Test Executor - OpenClaw Test Orchestrator

Executes tests in parallel with service isolation.
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid

logger = logging.getLogger(__name__)


class ExecutorState(Enum):
    """Executor state machine."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionConfig:
    """
    Configuration for test execution.

    Attributes:
        max_workers: Maximum parallel workers
        service_isolation: Enable service isolation
        timeout_seconds: Per-service timeout
        enable_coverage: Enable coverage collection
        parallel: Enable parallel execution
        pytest_args: Additional pytest arguments
    """
    max_workers: int = 4
    service_isolation: bool = True
    timeout_seconds: int = 300  # 5 minutes
    enable_coverage: bool = False
    parallel: bool = True
    pytest_args: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_workers": self.max_workers,
            "service_isolation": self.service_isolation,
            "timeout_seconds": self.timeout_seconds,
            "enable_coverage": self.enable_coverage,
            "parallel": self.parallel,
            "pytest_args": self.pytest_args
        }


@dataclass
class ServiceExecutionResult:
    """
    Result of test execution for a single service.

    Attributes:
        service: Service name
        success: Whether all tests passed
        total_tests: Total number of tests
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        duration_seconds: Execution duration
        error_message: Error message if failed
        coverage_percent: Coverage percentage (if enabled)
        output: Test output
    """
    service: str
    success: bool
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    error_message: Optional[str] = None
    coverage_percent: Optional[float] = None
    output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service": self.service,
            "success": self.success,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "coverage_percent": self.coverage_percent
        }


@dataclass
class TestExecutionResult:
    """
    Result of full test execution.

    Attributes:
        run_id: Unique run identifier
        total_tests: Total tests across all services
        passed: Total passed tests
        failed: Total failed tests
        skipped: Total skipped tests
        duration_seconds: Total duration
        by_service: Results per service
        timestamp: Execution timestamp
    """
    run_id: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    by_service: Dict[str, ServiceExecutionResult]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
            "by_service": {
                svc: result.to_dict()
                for svc, result in self.by_service.items()
            },
            "timestamp": self.timestamp
        }


class ParallelExecutor:
    """
    Executes tests in parallel with service isolation.

    Uses subprocess isolation for each service to ensure
    test independence and prevent state leakage.
    """

    def __init__(
        self,
        services_path: str = "services",
        config: Optional[ExecutionConfig] = None
    ):
        """
        Initialize parallel executor.

        Args:
            services_path: Path to services directory
            config: Execution configuration
        """
        self.services_path = Path(services_path)
        self.config = config or ExecutionConfig()
        self.state = ExecutorState.IDLE
        self._cancel_event = threading.Event()

        logger.info(
            f"ParallelExecutor initialized (max_workers={self.config.max_workers})"
        )

    def execute_service(
        self,
        service: str,
        test_pattern: Optional[str] = None
    ) -> ServiceExecutionResult:
        """
        Execute tests for a single service.

        Args:
            service: Service name
            test_pattern: Optional test pattern (e.g., "test_scene_*")

        Returns:
            ServiceExecutionResult
        """
        service_path = self.services_path / service

        if not service_path.exists():
            return ServiceExecutionResult(
                service=service,
                success=False,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_seconds=0.0,
                error_message=f"Service path does not exist: {service_path}"
            )

        start_time = time.time()

        try:
            # Build pytest command
            cmd = self._build_pytest_command(service_path, test_pattern)

            logger.debug(f"Executing: {' '.join(cmd)}")

            # Run tests in subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=service_path
            )

            duration = time.time() - start_time

            # Parse output
            parsed = self._parse_pytest_output(result.stdout, result.stderr)

            # Check for coverage
            coverage = self._parse_coverage(service_path) if self.config.enable_coverage else None

            return ServiceExecutionResult(
                service=service,
                success=(result.returncode == 0),
                total_tests=parsed.get("total", 0),
                passed=parsed.get("passed", 0),
                failed=parsed.get("failed", 0),
                skipped=parsed.get("skipped", 0),
                duration_seconds=duration,
                error_message=parsed.get("error"),
                coverage_percent=coverage,
                output=result.stdout
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ServiceExecutionResult(
                service=service,
                success=False,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_seconds=duration,
                error_message=f"Test execution timed out after {self.config.timeout_seconds}s"
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error executing tests for {service}: {e}")
            return ServiceExecutionResult(
                service=service,
                success=False,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_seconds=duration,
                error_message=str(e)
            )

    def execute_all(
        self,
        services: Optional[List[str]] = None,
        test_pattern: Optional[str] = None
    ) -> Dict[str, ServiceExecutionResult]:
        """
        Execute tests for all specified services.

        Args:
            services: List of services to test. If None, discovers all.
            test_pattern: Optional test pattern filter

        Returns:
            Dictionary of service name to ServiceExecutionResult
        """
        if services is None:
            # Discover services with tests
            services = [
                d.name for d in self.services_path.iterdir()
                if d.is_dir() and (d / "tests").exists()
                and not d.name.startswith(".")
            ]

        if not services:
            logger.warning("No services to execute")
            return {}

        self.state = ExecutorState.RUNNING
        results = {}
        start_time = time.time()

        try:
            if self.config.parallel and len(services) > 1:
                results = self._execute_parallel(services, test_pattern)
            else:
                results = self._execute_sequential(services, test_pattern)

            duration = time.time() - start_time

            # Update state based on results
            all_passed = all(r.success for r in results.values())
            self.state = ExecutorState.COMPLETED if all_passed else ExecutorState.FAILED

        except Exception as e:
            logger.error(f"Error during test execution: {e}")
            self.state = ExecutorState.FAILED

        return results

    def _execute_parallel(
        self,
        services: List[str],
        test_pattern: Optional[str]
    ) -> Dict[str, ServiceExecutionResult]:
        """Execute services in parallel using thread pool."""
        import concurrent.futures

        results = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_workers
        ) as executor:
            # Submit all jobs
            future_to_service = {
                executor.submit(self.execute_service, service, test_pattern): service
                for service in services
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_service):
                if self._cancel_event.is_set():
                    # Cancel remaining futures
                    for f in future_to_service:
                        f.cancel()
                    break

                service = future_to_service[future]
                try:
                    results[service] = future.result()
                except Exception as e:
                    logger.error(f"Service {service} raised exception: {e}")
                    results[service] = ServiceExecutionResult(
                        service=service,
                        success=False,
                        total_tests=0,
                        passed=0,
                        failed=0,
                        skipped=0,
                        duration_seconds=0.0,
                        error_message=str(e)
                    )

        return results

    def _execute_sequential(
        self,
        services: List[str],
        test_pattern: Optional[str]
    ) -> Dict[str, ServiceExecutionResult]:
        """Execute services sequentially."""
        results = {}

        for service in services:
            if self._cancel_event.is_set():
                break

            results[service] = self.execute_service(service, test_pattern)

        return results

    def _build_pytest_command(
        self,
        service_path: Path,
        test_pattern: Optional[str]
    ) -> List[str]:
        """Build pytest command for service."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests",
            "-v",
            "--tb=short",
            "--no-header"
        ]

        if test_pattern:
            cmd.extend(["-k", test_pattern])

        if self.config.enable_coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=term-missing",
                "--cov-report=json"
            ])

        cmd.extend(self.config.pytest_args)

        return cmd

    def _parse_pytest_output(
        self,
        stdout: str,
        stderr: str
    ) -> Dict[str, Any]:
        """Parse pytest output to extract test counts."""
        result = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": None
        }

        # Parse stderr for pytest summary (usually at end)
        output = stdout + stderr

        # Look for summary line like "5 passed, 2 failed in 3.5s"
        import re

        # Match patterns like:
        # - "5 passed"
        # - "5 passed, 2 failed"
        # - "5 passed, 2 failed, 1 skipped"
        # - "1 failed, 1 passed" (different order)
        # Also match "= X failed, Y passed" format

        # Try multiple patterns
        patterns = [
            r"(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?",  # passed, failed, skipped
            r"(\d+) failed(?:, (\d+) passed)?(?:, (\d+) skipped)?",  # failed, passed, skipped
            r"(\d+) passed in",  # just passed count
        ]

        for line in output.split("\n"):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    groups = match.groups()
                    if "passed" in pattern:
                        result["passed"] = int(groups[0])
                        if groups[1]:
                            if "failed" in pattern:
                                result["failed"] = int(groups[1])
                            if groups[2] and "skipped" in pattern:
                                result["skipped"] = int(groups[2])
                    elif "failed" in pattern:
                        result["failed"] = int(groups[0])
                        if groups[1]:
                            result["passed"] = int(groups[1])
                        if groups[2]:
                            result["skipped"] = int(groups[2])

                    # Also try to find the "collected" line for total
                    collected_match = re.search(r"collected (\d+) items?", output)
                    if collected_match:
                        result["total"] = int(collected_match.group(1))
                    else:
                        result["total"] = (
                            result["passed"] + result["failed"] + result["skipped"]
                        )
                    break
            if result["total"] > 0:
                break

        # Look for error messages
        if "ERROR" in output or "FAILED" in stderr:
            result["error"] = "Tests failed - see output for details"

        return result

    def _parse_coverage(self, service_path: Path) -> Optional[float]:
        """Parse coverage.json file."""
        coverage_file = service_path / "coverage.json"

        if not coverage_file.exists():
            return None

        try:
            with open(coverage_file) as f:
                data = json.load(f)

            totals = data.get("totals", {})
            percent_covered = totals.get("percent_covered")

            if percent_covered is not None:
                return round(percent_covered, 2)

        except Exception as e:
            logger.warning(f"Failed to parse coverage: {e}")

        return None

    def cancel(self) -> None:
        """Cancel running execution."""
        logger.info("Cancelling test execution")
        self._cancel_event.set()
        self.state = ExecutorState.CANCELLED

    def get_state(self) -> ExecutorState:
        """Get current executor state."""
        return self.state

    def reset(self) -> None:
        """Reset executor to idle state."""
        self.state = ExecutorState.IDLE
        self._cancel_event.clear()
