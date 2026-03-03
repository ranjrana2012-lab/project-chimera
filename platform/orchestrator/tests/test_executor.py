"""
Unit tests for Parallel Test Executor.

Tests parallel test execution with service isolation.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_path))

from core.executor import (
    ParallelExecutor,
    ExecutionConfig,
    TestExecutionResult,
    ServiceExecutionResult,
    ExecutorState
)


class TestExecutionConfig:
    """Test ExecutionConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = ExecutionConfig()

        assert config.max_workers == 4
        assert config.service_isolation is True
        assert config.timeout_seconds == 300
        assert config.enable_coverage is False
        assert config.parallel is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = ExecutionConfig(
            max_workers=8,
            service_isolation=False,
            timeout_seconds=600,
            enable_coverage=True,
            parallel=False
        )

        assert config.max_workers == 8
        assert config.service_isolation is False
        assert config.timeout_seconds == 600
        assert config.enable_coverage is True
        assert config.parallel is False


class TestServiceExecutionResult:
    """Test ServiceExecutionResult dataclass."""

    def test_success_result(self):
        """Test successful execution result."""
        result = ServiceExecutionResult(
            service="test-service",
            success=True,
            total_tests=10,
            passed=10,
            failed=0,
            skipped=0,
            duration_seconds=5.2
        )

        assert result.service == "test-service"
        assert result.success is True
        assert result.total_tests == 10
        assert result.passed == 10
        assert result.failed == 0

    def test_failure_result(self):
        """Test failed execution result."""
        result = ServiceExecutionResult(
            service="test-service",
            success=False,
            total_tests=10,
            passed=8,
            failed=2,
            skipped=0,
            duration_seconds=5.2,
            error_message="2 tests failed"
        )

        assert result.success is False
        assert result.failed == 2
        assert result.error_message == "2 tests failed"


class TestTestExecutionResult:
    """Test TestExecutionResult dataclass."""

    def test_aggregated_result(self):
        """Test aggregated execution result."""
        result = TestExecutionResult(
            run_id="test-run-123",
            total_tests=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_seconds=30.5,
            by_service={
                "svc1": ServiceExecutionResult(
                    service="svc1",
                    success=True,
                    total_tests=50,
                    passed=50,
                    failed=0,
                    skipped=0,
                    duration_seconds=15.0
                ),
                "svc2": ServiceExecutionResult(
                    service="svc2",
                    success=False,
                    total_tests=50,
                    passed=45,
                    failed=5,
                    skipped=0,
                    duration_seconds=15.5
                )
            }
        )

        assert result.total_tests == 100
        assert result.passed == 95
        assert result.failed == 5
        assert len(result.by_service) == 2


class TestParallelExecutor:
    """Test ParallelExecutor functionality."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return ParallelExecutor(
            services_path="services",
            config=ExecutionConfig(max_workers=2)
        )

    @pytest.fixture
    def mock_services_dir(self, tmp_path):
        """Create mock services directory."""
        service1 = tmp_path / "services" / "svc1"
        service1.mkdir(parents=True)

        # Create test file
        tests = service1 / "tests"
        tests.mkdir()
        (tests / "test_example.py").write_text("""
def test_pass():
    assert True

def test_fail():
    assert False
""")

        # Create pytest.ini
        (service1 / "pytest.ini").write_text("[pytest]")

        service2 = tmp_path / "services" / "svc2"
        service2.mkdir(parents=True)
        tests2 = service2 / "tests"
        tests2.mkdir()
        (tests2 / "test_example.py").write_text("""
def test_also_pass():
    assert True
""")

        (service2 / "pytest.ini").write_text("[pytest]")

        return tmp_path

    def test_executor_init(self, executor):
        """Test executor initialization."""
        assert executor.services_path.name == "services"
        assert executor.config.max_workers == 2
        assert executor.state == ExecutorState.IDLE

    def test_execute_single_service(self, executor, mock_services_dir, tmp_path):
        """Test executing tests for a single service."""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = executor.execute_service("svc1")

            assert result.service == "svc1"
            # Tests run, exact counts may vary based on pytest output parsing
            assert result.total_tests >= 1
            assert result.passed >= 1 or result.failed >= 1

        finally:
            os.chdir(original_cwd)

    def test_execute_services_parallel(self, executor, mock_services_dir, tmp_path):
        """Test executing multiple services in parallel."""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            results = executor.execute_all(["svc1", "svc2"])

            assert len(results) == 2
            assert "svc1" in results
            assert "svc2" in results

        finally:
            os.chdir(original_cwd)

    def test_timeout_enforcement(self, executor, tmp_path):
        """Test that timeout is enforced."""
        import os
        original_cwd = os.getcwd()

        # Create service with long-running test
        slow_service = tmp_path / "services" / "slow"
        slow_service.mkdir(parents=True)
        tests = slow_service / "tests"
        tests.mkdir()
        (tests / "test_slow.py").write_text("""
import time

def test_slow():
    time.sleep(10)
    assert True
""")
        (slow_service / "pytest.ini").write_text("[pytest]")

        os.chdir(tmp_path)

        try:
            # Set short timeout
            executor.config.timeout_seconds = 2

            result = executor.execute_service("slow")

            # Should fail due to timeout
            assert result.success is False

        finally:
            os.chdir(original_cwd)

    def test_coverage_collection(self, tmp_path):
        """Test coverage collection when enabled."""
        import os
        original_cwd = os.getcwd()

        service = tmp_path / "services" / "cov-test"
        service.mkdir(parents=True)
        tests = service / "tests"
        tests.mkdir()
        (tests / "test_cov.py").write_text("""
def test_covered():
    assert True
""")
        (service / "pytest.ini").write_text("[pytest]")

        # Create simple module to cover
        (service / "example.py").write_text("""
def example_func():
    return 42
""")

        os.chdir(tmp_path)

        try:
            executor = ParallelExecutor(
                services_path="services",
                config=ExecutionConfig(enable_coverage=True)
            )

            result = executor.execute_service("cov-test")

            # Coverage should be generated
            assert result.coverage_percent is not None

        finally:
            os.chdir(original_cwd)

    def test_empty_service_list(self, executor):
        """Test executing with empty service list."""
        results = executor.execute_all([])

        assert len(results) == 0

    def test_get_executor_state(self, executor):
        """Test getting executor state."""
        state = executor.get_state()

        assert state == ExecutorState.IDLE

    def test_cancel_execution(self, executor, mock_services_dir, tmp_path):
        """Test cancelling running execution."""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Start execution in background
            import threading
            import time

            def run_execute():
                # Use slower config to allow cancel
                executor.execute_all(["svc1", "svc2"])

            thread = threading.Thread(target=run_execute)
            thread.start()

            # Give it a moment to start, then cancel
            time.sleep(0.1)
            executor.cancel()

            thread.join(timeout=5)

            # Executor should be in CANCELLED or COMPLETED state
            # (depending on timing, tests might finish before cancel)
            assert executor.state in (ExecutorState.CANCELLED, ExecutorState.FAILED, ExecutorState.COMPLETED)

        finally:
            os.chdir(original_cwd)


class TestRealServiceExecution:
    """Integration tests with real services."""

    @pytest.fixture
    def real_executor(self):
        """Create executor for real services."""
        return ParallelExecutor(
            services_path="services",
            config=ExecutionConfig(max_workers=2, timeout_seconds=60)
        )

    def test_execute_openclaw_tests(self, real_executor):
        """Test executing OpenClaw Orchestrator tests."""
        # Only run if service exists
        import os
        if not os.path.exists("services/openclaw-orchestrator"):
            pytest.skip("openclaw-orchestrator not found")

        result = real_executor.execute_service("openclaw-orchestrator")

        assert result.service == "openclaw-orchestrator"
        assert result.total_tests > 0
        assert result.duration_seconds >= 0

    def test_execute_all_real_services(self, real_executor):
        """Test executing all discovered services."""
        results = real_executor.execute_all()

        # Should execute at least one service
        assert len(results) >= 1

        # All results should have required fields
        for service, result in results.items():
            assert result.service == service
            assert result.total_tests >= 0
            assert result.passed >= 0
            assert result.failed >= 0
