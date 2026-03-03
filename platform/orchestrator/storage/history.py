"""
Test History Storage - OpenClaw Test Orchestrator

Stores test results in PostgreSQL for trend analysis.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available - using degraded mode")


@dataclass
class TestRunRecord:
    """
    Record of a test run.

    Attributes:
        run_id: Unique run identifier
        timestamp: Run timestamp
        total_tests: Total tests executed
        passed: Number passed
        failed: Number failed
        skipped: Number skipped
        duration_seconds: Execution duration
        metadata: Additional metadata
    """
    run_id: str
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.run_id,
            self.timestamp,
            self.total_tests,
            self.passed,
            self.failed,
            self.skipped,
            self.duration_seconds,
            self.metadata
        )


@dataclass
class TestResultRecord:
    """
    Record of a single test result.

    Attributes:
        run_id: Associated run ID
        service: Service name
        test_name: Test function name
        status: Test status (passed, failed, skipped)
        duration_ms: Test duration in milliseconds
        error_message: Error message if failed
    """
    run_id: str
    service: str
    test_name: str
    status: str
    duration_ms: int
    error_message: Optional[str] = None

    def to_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.run_id,
            self.service,
            self.test_name,
            self.status,
            self.duration_ms,
            self.error_message
        )


@dataclass
class CoverageRecord:
    """
    Record of coverage data.

    Attributes:
        run_id: Associated run ID
        service: Service name
        coverage_percent: Coverage percentage
        lines_covered: Number of covered lines
        lines_total: Total lines
        timestamp: Record timestamp
    """
    run_id: str
    service: str
    coverage_percent: float
    lines_covered: int
    lines_total: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.run_id,
            self.service,
            self.coverage_percent,
            self.lines_covered,
            self.lines_total,
            self.timestamp
        )


class TestHistoryStorage:
    """
    Stores and retrieves test history from PostgreSQL.

    Provides persistence for test results, enabling trend analysis
    and historical reporting.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "test_history",
        user: str = "postgres",
        password: str = "",
        auto_create_tables: bool = True
    ):
        """
        Initialize test history storage.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            auto_create_tables: Automatically create tables if they don't exist
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.auto_create_tables = auto_create_tables

        self._conn = None
        self._degraded_mode = not PSYCOPG2_AVAILABLE

        if self._degraded_mode:
            logger.warning("Running in degraded mode - no database storage")
            return

        # Connect to database
        self._connect()

        if auto_create_tables:
            self._create_tables()

        logger.info(f"TestHistoryStorage initialized (database={database})")

    def _connect(self) -> None:
        """Establish database connection."""
        if self._degraded_mode:
            return

        try:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._degraded_mode = True

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if self._degraded_mode or self._conn is None:
            return

        try:
            with self._conn.cursor() as cursor:
                # Test runs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_runs (
                        run_id VARCHAR(255) PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        total_tests INTEGER NOT NULL,
                        passed INTEGER NOT NULL,
                        failed INTEGER NOT NULL,
                        skipped INTEGER NOT NULL,
                        duration_seconds FLOAT NOT NULL,
                        metadata JSONB
                    )
                """)

                # Test results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_results (
                        id SERIAL PRIMARY KEY,
                        run_id VARCHAR(255) NOT NULL REFERENCES test_runs(run_id) ON DELETE CASCADE,
                        service VARCHAR(100) NOT NULL,
                        test_name VARCHAR(255) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        duration_ms INTEGER NOT NULL,
                        error_message TEXT
                    )
                """)

                # Coverage history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS coverage_history (
                        id SERIAL PRIMARY KEY,
                        run_id VARCHAR(255) NOT NULL REFERENCES test_runs(run_id) ON DELETE CASCADE,
                        service VARCHAR(100) NOT NULL,
                        coverage_percent FLOAT NOT NULL,
                        lines_covered INTEGER NOT NULL,
                        lines_total INTEGER NOT NULL,
                        timestamp TIMESTAMP NOT NULL
                    )
                """)

                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_test_results_run_id
                    ON test_results(run_id)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_test_results_service
                    ON test_results(service)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_coverage_service
                    ON coverage_history(service)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_coverage_timestamp
                    ON coverage_history(timestamp DESC)
                """)

                self._conn.commit()
                logger.info("Database tables verified/created")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")

    def store_run(self, record: TestRunRecord) -> str:
        """
        Store a test run record.

        Args:
            record: Test run record

        Returns:
            Run ID
        """
        if self._degraded_mode:
            logger.debug(f"Degraded mode: would store run {record.run_id}")
            return record.run_id

        try:
            with self._conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO test_runs
                    (run_id, timestamp, total_tests, passed, failed, skipped, duration_seconds, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        timestamp = EXCLUDED.timestamp,
                        total_tests = EXCLUDED.total_tests,
                        passed = EXCLUDED.passed,
                        failed = EXCLUDED.failed,
                        skipped = EXCLUDED.skipped,
                        duration_seconds = EXCLUDED.duration_seconds,
                        metadata = EXCLUDED.metadata
                """, record.to_tuple())

            self._conn.commit()
            logger.info(f"Stored test run {record.run_id}")
            return record.run_id

        except Exception as e:
            logger.error(f"Failed to store run: {e}")
            self._conn.rollback()
            return record.run_id

    def store_results(self, results: List[TestResultRecord]) -> int:
        """
        Store test result records.

        Args:
            results: List of test result records

        Returns:
            Number of results stored
        """
        if self._degraded_mode:
            logger.debug(f"Degraded mode: would store {len(results)} results")
            return len(results)

        try:
            with self._conn.cursor() as cursor:
                cursor.executemany("""
                    INSERT INTO test_results
                    (run_id, service, test_name, status, duration_ms, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [r.to_tuple() for r in results])

            self._conn.commit()
            logger.info(f"Stored {len(results)} test results")
            return len(results)

        except Exception as e:
            logger.error(f"Failed to store results: {e}")
            self._conn.rollback()
            return 0

    def store_coverage(self, record: CoverageRecord) -> None:
        """
        Store coverage record.

        Args:
            record: Coverage record
        """
        if self._degraded_mode:
            logger.debug(f"Degraded mode: would store coverage for {record.service}")
            return

        try:
            with self._conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO coverage_history
                    (run_id, service, coverage_percent, lines_covered, lines_total, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, record.to_tuple())

            self._conn.commit()
            logger.info(f"Stored coverage for {record.service}")

        except Exception as e:
            logger.error(f"Failed to store coverage: {e}")
            self._conn.rollback()

    def get_run(self, run_id: str) -> Optional[TestRunRecord]:
        """
        Retrieve a test run by ID.

        Args:
            run_id: Run identifier

        Returns:
            TestRunRecord or None if not found
        """
        if self._degraded_mode:
            return None

        try:
            with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM test_runs WHERE run_id = %s
                """, (run_id,))

                row = cursor.fetchone()

                if row:
                    return TestRunRecord(
                        run_id=row["run_id"],
                        timestamp=row["timestamp"].isoformat(),
                        total_tests=row["total_tests"],
                        passed=row["passed"],
                        failed=row["failed"],
                        skipped=row["skipped"],
                        duration_seconds=row["duration_seconds"],
                        metadata=row.get("metadata", {})
                    )
                return None

        except Exception as e:
            logger.error(f"Failed to get run: {e}")
            return None

    def get_results_by_run(self, run_id: str) -> List[TestResultRecord]:
        """
        Retrieve all results for a run.

        Args:
            run_id: Run identifier

        Returns:
            List of TestResultRecord
        """
        if self._degraded_mode:
            return []

        try:
            with self._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT run_id, service, test_name, status, duration_ms, error_message
                    FROM test_results WHERE run_id = %s
                """, (run_id,))

                rows = cursor.fetchall()

                return [
                    TestResultRecord(
                        run_id=row[0],
                        service=row[1],
                        test_name=row[2],
                        status=row[3],
                        duration_ms=row[4],
                        error_message=row[5]
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get results: {e}")
            return []

    def get_recent_runs(self, limit: int = 10) -> List[TestRunRecord]:
        """
        Retrieve recent test runs.

        Args:
            limit: Maximum number of runs to retrieve

        Returns:
            List of TestRunRecord
        """
        if self._degraded_mode:
            return []

        try:
            with self._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT run_id, timestamp, total_tests, passed, failed, skipped, duration_seconds
                    FROM test_runs
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))

                rows = cursor.fetchall()

                return [
                    TestRunRecord(
                        run_id=row[0],
                        timestamp=row[1].isoformat(),
                        total_tests=row[2],
                        passed=row[3],
                        failed=row[4],
                        skipped=row[5],
                        duration_seconds=row[6]
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get recent runs: {e}")
            return []

    def get_coverage_history(
        self,
        service: str,
        limit: int = 10
    ) -> List[CoverageRecord]:
        """
        Retrieve coverage history for a service.

        Args:
            service: Service name
            limit: Maximum number of records

        Returns:
            List of CoverageRecord
        """
        if self._degraded_mode:
            return []

        try:
            with self._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT run_id, service, coverage_percent, lines_covered, lines_total, timestamp
                    FROM coverage_history
                    WHERE service = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (service, limit))

                rows = cursor.fetchall()

                return [
                    CoverageRecord(
                        run_id=row[0],
                        service=row[1],
                        coverage_percent=row[2],
                        lines_covered=row[3],
                        lines_total=row[4],
                        timestamp=row[5].isoformat()
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get coverage history: {e}")
            return []

    def delete_run(self, run_id: str) -> bool:
        """
        Delete a test run and all associated data.

        Args:
            run_id: Run identifier

        Returns:
            True if deleted, False otherwise
        """
        if self._degraded_mode:
            return False

        try:
            with self._conn.cursor() as cursor:
                cursor.execute("DELETE FROM test_runs WHERE run_id = %s", (run_id,))

            self._conn.commit()
            logger.info(f"Deleted test run {run_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete run: {e}")
            self._conn.rollback()
            return False

    def get_service_stats(self, service: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a service.

        Args:
            service: Service name

        Returns:
            Statistics dictionary
        """
        if self._degraded_mode:
            return None

        try:
            with self._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_runs,
                        COALESCE(SUM(passed), 0) as total_passed,
                        COALESCE(SUM(failed), 0) as total_failed,
                        AVG(duration_seconds) as avg_duration
                    FROM test_runs tr
                    JOIN test_results trr ON tr.run_id = trr.run_id
                    WHERE trr.service = %s
                """, (service,))

                row = cursor.fetchone()

                if row:
                    return {
                        "total_runs": row[0],
                        "total_passed": row[1],
                        "total_failed": row[2],
                        "avg_duration": row[3]
                    }
                return None

        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return None

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
