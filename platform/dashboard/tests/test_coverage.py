"""
Unit tests for coverage metrics display component.

Tests coverage tracking, aggregation, and visualization.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

# Add dashboard to path
dashboard_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(dashboard_path))


class TestCoverageRecord:
    """Test CoverageRecord dataclass."""

    def test_coverage_record_creation(self):
        """Test creating coverage record."""
        from components.coverage import CoverageRecord
        record = CoverageRecord(
            service_name="test-service",
            total_lines=1000,
            covered_lines=850,
            percentage=85.0
        )
        assert record.service_name == "test-service"
        assert record.total_lines == 1000
        assert record.covered_lines == 850
        assert record.percentage == 85.0

    def test_coverage_record_uncovered_lines(self):
        """Test uncovered lines calculation."""
        from components.coverage import CoverageRecord
        record = CoverageRecord(
            service_name="test-service",
            total_lines=1000,
            covered_lines=850,
            percentage=85.0
        )
        assert record.uncovered_lines == 150

    def test_coverage_record_is_healthy(self):
        """Test health check for coverage."""
        from components.coverage import CoverageRecord

        # Healthy coverage
        record1 = CoverageRecord("svc1", 1000, 850, 85.0)
        assert record1.is_healthy(threshold=80.0) is True

        # Unhealthy coverage
        record2 = CoverageRecord("svc2", 1000, 750, 75.0)
        assert record2.is_healthy(threshold=80.0) is False

    def test_coverage_record_to_dict(self):
        """Test converting to dict."""
        from components.coverage import CoverageRecord
        record = CoverageRecord(
            service_name="test-service",
            total_lines=1000,
            covered_lines=850,
            percentage=85.0
        )
        data = record.to_dict()
        assert data["service_name"] == "test-service"
        assert data["percentage"] == 85.0
        assert "uncovered_lines" in data


class TestFileCoverage:
    """Test FileCoverage dataclass."""

    def test_file_coverage_creation(self):
        """Test creating file coverage."""
        from components.coverage import FileCoverage
        file_cov = FileCoverage(
            file_path="src/test.py",
            total_lines=100,
            covered_lines=80,
            percentage=80.0
        )
        assert file_cov.file_path == "src/test.py"
        assert file_cov.total_lines == 100

    def test_file_coverage_missing_threshold(self):
        """Test missing threshold check."""
        from components.coverage import FileCoverage

        # Above threshold
        file1 = FileCoverage("test1.py", 100, 85, 85.0)
        assert file1.is_missing(threshold=80.0) is False

        # Below threshold
        file2 = FileCoverage("test2.py", 100, 75, 75.0)
        assert file2.is_missing(threshold=80.0) is True


class TestCoverageSnapshot:
    """Test CoverageSnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating coverage snapshot."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        record = CoverageRecord("svc1", 1000, 850, 85.0)
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=[record]
        )
        assert len(snapshot.records) == 1
        assert snapshot.total_lines == 1000
        assert snapshot.covered_lines == 850

    def test_snapshot_aggregation(self):
        """Test snapshot aggregation."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        records = [
            CoverageRecord("svc1", 1000, 850, 85.0),
            CoverageRecord("svc2", 500, 400, 80.0)
        ]
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=records
        )
        assert snapshot.total_lines == 1500
        assert snapshot.covered_lines == 1250
        assert abs(snapshot.overall_percentage - 83.33) < 0.1


class TestCoverageTracker:
    """Test CoverageTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create coverage tracker."""
        from components.coverage import CoverageTracker
        return CoverageTracker()

    def test_tracker_init(self, tracker):
        """Test tracker initialization."""
        assert len(tracker.snapshots) == 0

    def test_add_snapshot(self, tracker):
        """Test adding coverage snapshot."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        record = CoverageRecord("svc1", 1000, 850, 85.0)
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=[record]
        )
        tracker.add_snapshot(snapshot)
        assert len(tracker.snapshots) == 1

    def test_get_latest_snapshot(self, tracker):
        """Test getting latest snapshot."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        snapshot1 = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=[CoverageRecord("svc1", 1000, 850, 85.0)]
        )
        snapshot2 = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=[CoverageRecord("svc1", 1000, 900, 90.0)]
        )

        tracker.add_snapshot(snapshot1)
        tracker.add_snapshot(snapshot2)

        latest = tracker.get_latest_snapshot()
        assert latest.overall_percentage == 90.0

    def test_get_coverage_trend(self, tracker):
        """Test getting coverage trend."""
        from components.coverage import CoverageSnapshot, CoverageRecord
        from datetime import timedelta

        # Add snapshots with different coverage
        for i in range(5):
            record = CoverageRecord("svc1", 1000, 800 + i * 10, 80.0 + i)
            snapshot = CoverageSnapshot(
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                records=[record]
            )
            tracker.add_snapshot(snapshot)

        trend = tracker.get_coverage_trend(limit=5)
        assert len(trend) == 5
        # Should be ordered oldest to newest
        assert trend[0]["percentage"] == 80.0
        assert trend[-1]["percentage"] == 84.0

    def test_get_service_coverage(self, tracker):
        """Test getting coverage by service."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        records = [
            CoverageRecord("svc1", 1000, 850, 85.0),
            CoverageRecord("svc2", 500, 400, 80.0)
        ]
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=records
        )
        tracker.add_snapshot(snapshot)

        svc1_cov = tracker.get_service_coverage("svc1")
        assert svc1_cov is not None
        assert svc1_cov.percentage == 85.0

        svc3_cov = tracker.get_service_coverage("svc3")
        assert svc3_cov is None

    def test_get_low_coverage_services(self, tracker):
        """Test getting low coverage services."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        records = [
            CoverageRecord("svc1", 1000, 850, 85.0),
            CoverageRecord("svc2", 500, 300, 60.0),
            CoverageRecord("svc3", 200, 100, 50.0)
        ]
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=records
        )
        tracker.add_snapshot(snapshot)

        low_cov = tracker.get_low_coverage_services(threshold=70.0)
        assert len(low_cov) == 2
        service_names = [c.service_name for c in low_cov]
        assert "svc2" in service_names
        assert "svc3" in service_names

    def test_get_coverage_change(self, tracker):
        """Test getting coverage change over time."""
        from components.coverage import CoverageSnapshot, CoverageRecord
        from datetime import timedelta

        snapshot1 = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            records=[CoverageRecord("svc1", 1000, 800, 80.0)]
        )
        snapshot2 = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=[CoverageRecord("svc1", 1000, 850, 85.0)]
        )

        tracker.add_snapshot(snapshot1)
        tracker.add_snapshot(snapshot2)

        change = tracker.get_coverage_change("svc1")
        assert change["current"] == 85.0
        assert change["previous"] == 80.0
        assert change["change"] == 5.0
        assert change["improved"] is True


class TestCoverageDisplay:
    """Test CoverageDisplay class."""

    @pytest.fixture
    def display(self):
        """Create coverage display."""
        from components.coverage import CoverageDisplay
        return CoverageDisplay()

    def test_get_summary(self, display):
        """Test getting coverage summary."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        records = [
            CoverageRecord("svc1", 1000, 850, 85.0),
            CoverageRecord("svc2", 500, 400, 80.0)
        ]
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=records
        )
        display.tracker.add_snapshot(snapshot)

        summary = display.get_summary()
        assert summary["overall_percentage"] == 83.33
        assert summary["total_lines"] == 1500
        assert summary["covered_lines"] == 1250

    def test_get_service_breakdown(self, display):
        """Test getting service breakdown."""
        from components.coverage import CoverageSnapshot, CoverageRecord

        records = [
            CoverageRecord("svc1", 1000, 850, 85.0),
            CoverageRecord("svc2", 500, 400, 80.0)
        ]
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=records
        )
        display.tracker.add_snapshot(snapshot)

        breakdown = display.get_service_breakdown()
        assert len(breakdown) == 2
        assert breakdown[0]["service_name"] == "svc1"

    def test_get_missing_files(self, display):
        """Test getting missing files below threshold."""
        from components.coverage import CoverageSnapshot, CoverageRecord, FileCoverage

        # Add snapshot with file coverage
        record = CoverageRecord("svc1", 1000, 850, 85.0)
        record.missing_files = [
            FileCoverage("src/low1.py", 100, 70, 70.0),
            FileCoverage("src/low2.py", 50, 30, 60.0)
        ]
        snapshot = CoverageSnapshot(
            timestamp=datetime.now(timezone.utc),
            records=[record]
        )
        display.tracker.add_snapshot(snapshot)

        missing = display.get_missing_files(threshold=80.0)
        assert len(missing) == 2
