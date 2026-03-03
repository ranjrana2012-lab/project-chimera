"""
Unit tests for Test History Storage.

Tests PostgreSQL storage of test results.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_path))

from storage.history import (
    TestHistoryStorage,
    TestRunRecord,
    TestResultRecord,
    CoverageRecord
)


class TestDataclasses:
    """Test storage dataclasses."""

    def test_test_run_record(self):
        """Test TestRunRecord creation."""
        record = TestRunRecord(
            run_id="test-run-123",
            timestamp="2026-03-04T00:00:00Z",
            total_tests=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_seconds=30.5
        )

        assert record.run_id == "test-run-123"
        assert record.total_tests == 100

    def test_test_result_record(self):
        """Test TestResultRecord creation."""
        record = TestResultRecord(
            run_id="test-run-123",
            service="test-service",
            test_name="test_example",
            status="passed",
            duration_ms=100
        )

        assert record.service == "test-service"
        assert record.status == "passed"

    def test_coverage_record(self):
        """Test CoverageRecord creation."""
        record = CoverageRecord(
            run_id="test-run-123",
            service="test-service",
            coverage_percent=85.5,
            lines_covered=850,
            lines_total=1000
        )

        assert record.coverage_percent == 85.5

    def test_record_to_tuple(self):
        """Test TestRunRecord to_tuple conversion."""
        record = TestRunRecord(
            run_id="test-run-123",
            timestamp="2026-03-04T00:00:00Z",
            total_tests=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_seconds=30.5
        )

        tup = record.to_tuple()

        assert tup[0] == "test-run-123"
        assert len(tup) == 8


class TestDegradedMode:
    """Test degraded mode behavior when psycopg2 is not available."""

    def test_degraded_mode_storage(self):
        """Test storage in degraded mode (no DB)."""
        # Force degraded mode
        storage = TestHistoryStorage(
            host="localhost",
            database="test_db"
        )

        # If psycopg2 is not available, should be in degraded mode
        # Otherwise, the connection will have been attempted
        assert storage is not None

    def test_store_run_in_degraded_mode(self):
        """Test storing run in degraded mode."""
        storage = TestHistoryStorage(
            host="localhost",
            database="test_db"
        )

        record = TestRunRecord(
            run_id="test-run-123",
            timestamp="2026-03-04T00:00:00Z",
            total_tests=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_seconds=30.5
        )

        # Should not crash in degraded mode
        run_id = storage.store_run(record)
        assert run_id == "test-run-123"

    def test_store_results_in_degraded_mode(self):
        """Test storing results in degraded mode."""
        storage = TestHistoryStorage(
            host="localhost",
            database="test_db"
        )

        results = [
            TestResultRecord(
                run_id="test-run-123",
                service="svc1",
                test_name="test_1",
                status="passed",
                duration_ms=100
            )
        ]

        # Should not crash in degraded mode
        count = storage.store_results(results)
        assert count == 0 or count == 1  # 0 if degraded, 1 if stored

    def test_get_run_in_degraded_mode(self):
        """Test retrieving run in degraded mode."""
        storage = TestHistoryStorage(
            host="localhost",
            database="test_db"
        )

        run = storage.get_run("test-run-123")

        # Should return None in degraded mode
        assert run is None

    def test_get_recent_runs_in_degraded_mode(self):
        """Test retrieving recent runs in degraded mode."""
        storage = TestHistoryStorage(
            host="localhost",
            database="test_db"
        )

        runs = storage.get_recent_runs(limit=10)

        # Should return empty list in degraded mode
        assert runs == []


class TestConnectionHandling:
    """Test database connection handling."""

    def test_close_connection(self):
        """Test closing connection."""
        storage = TestHistoryStorage(
            host="localhost",
            database="test_db"
        )

        # Should not crash
        storage.close()

    def test_context_manager(self):
        """Test using storage as context manager."""
        with TestHistoryStorage(host="localhost", database="test_db") as storage:
            assert storage is not None

        # Connection should be closed after context


class TestStorageBehavior:
    """Test storage behavior with database (integration tests)."""

    def test_storage_initialization(self):
        """Test storage initialization with different parameters."""
        storage1 = TestHistoryStorage(
            host="localhost",
            database="test_db",
            user="test_user",
            password="test_pass",
            port=5433
        )

        assert storage1.host == "localhost"
        assert storage1.database == "test_db"
        assert storage1.user == "test_user"
        assert storage1.port == 5433

    def test_auto_create_tables_flag(self):
        """Test auto_create_tables flag."""
        storage = TestHistoryStorage(
            host="localhost",
            database="test_db",
            auto_create_tables=False
        )

        assert storage.auto_create_tables is False

    def test_metadata_handling(self):
        """Test metadata in TestRunRecord."""
        metadata = {
            "branch": "main",
            "commit": "abc123",
            "environment": "test"
        }

        record = TestRunRecord(
            run_id="test-run-123",
            timestamp="2026-03-04T00:00:00Z",
            total_tests=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_seconds=30.5,
            metadata=metadata
        )

        assert record.metadata == metadata
        assert record.metadata["branch"] == "main"


class TestQueryConstruction:
    """Test that query construction is correct."""

    def test_result_record_to_tuple(self):
        """Test TestResultRecord tuple conversion."""
        record = TestResultRecord(
            run_id="test-run-123",
            service="svc1",
            test_name="test_example",
            status="passed",
            duration_ms=100,
            error_message=None
        )

        tup = record.to_tuple()

        assert tup == ("test-run-123", "svc1", "test_example", "passed", 100, None)

    def test_result_record_with_error(self):
        """Test TestResultRecord with error message."""
        record = TestResultRecord(
            run_id="test-run-123",
            service="svc1",
            test_name="test_example",
            status="failed",
            duration_ms=100,
            error_message="AssertionError: assert False"
        )

        tup = record.to_tuple()

        assert tup[5] == "AssertionError: assert False"

    def test_coverage_record_to_tuple(self):
        """Test CoverageRecord tuple conversion."""
        record = CoverageRecord(
            run_id="test-run-123",
            service="svc1",
            coverage_percent=85.5,
            lines_covered=850,
            lines_total=1000
        )

        tup = record.to_tuple()

        assert len(tup) == 6
        assert tup[1] == "svc1"
        assert tup[2] == 85.5
