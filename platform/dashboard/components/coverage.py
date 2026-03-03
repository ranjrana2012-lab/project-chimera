"""
Coverage metrics display component for dashboard.

Tracks code coverage across services and files.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class FileCoverage:
    """
    Coverage data for a single file.

    Attributes:
        file_path: Path to the file
        total_lines: Total number of lines
        covered_lines: Number of covered lines
        percentage: Coverage percentage
    """
    file_path: str
    total_lines: int
    covered_lines: int
    percentage: float

    @property
    def uncovered_lines(self) -> int:
        """Get number of uncovered lines."""
        return self.total_lines - self.covered_lines

    def is_missing(self, threshold: float = 80.0) -> bool:
        """Check if coverage is below threshold."""
        return self.percentage < threshold


@dataclass
class CoverageRecord:
    """
    Coverage data for a single service.

    Attributes:
        service_name: Name of the service
        total_lines: Total number of lines
        covered_lines: Number of covered lines
        percentage: Coverage percentage
        missing_files: List of files below threshold
    """
    service_name: str
    total_lines: int
    covered_lines: int
    percentage: float
    missing_files: List[FileCoverage] = field(default_factory=list)

    @property
    def uncovered_lines(self) -> int:
        """Get number of uncovered lines."""
        return self.total_lines - self.covered_lines

    @property
    def missing_files_count(self) -> int:
        """Get number of files below threshold."""
        return len(self.missing_files)

    def is_healthy(self, threshold: float = 80.0) -> bool:
        """Check if coverage meets threshold."""
        return self.percentage >= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service_name": self.service_name,
            "total_lines": self.total_lines,
            "covered_lines": self.covered_lines,
            "uncovered_lines": self.uncovered_lines,
            "percentage": self.percentage,
            "missing_files_count": self.missing_files_count,
            "is_healthy": self.is_healthy(),
            "missing_files": [f.file_path for f in self.missing_files]
        }


@dataclass
class CoverageSnapshot:
    """
    Coverage snapshot at a point in time.

    Contains coverage records for all services at a specific timestamp.
    """
    timestamp: datetime
    records: List[CoverageRecord] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        """Get total lines across all services."""
        return sum(r.total_lines for r in self.records)

    @property
    def covered_lines(self) -> int:
        """Get covered lines across all services."""
        return sum(r.covered_lines for r in self.records)

    @property
    def overall_percentage(self) -> float:
        """Get overall coverage percentage."""
        if self.total_lines == 0:
            return 0.0
        return (self.covered_lines / self.total_lines) * 100


class CoverageTracker:
    """
    Tracks coverage metrics over time.

    Stores coverage snapshots and provides trend analysis.
    """

    def __init__(self, max_snapshots: int = 100):
        """
        Initialize coverage tracker.

        Args:
            max_snapshots: Maximum snapshots to keep
        """
        self.max_snapshots = max_snapshots
        self.snapshots: List[CoverageSnapshot] = []
        self._service_history: Dict[str, List[float]] = {}

        logger.info("CoverageTracker initialized")

    def add_snapshot(self, snapshot: CoverageSnapshot) -> None:
        """
        Add a coverage snapshot.

        Args:
            snapshot: Coverage snapshot to add
        """
        self.snapshots.append(snapshot)

        # Update service history
        for record in snapshot.records:
            if record.service_name not in self._service_history:
                self._service_history[record.service_name] = []
            self._service_history[record.service_name].append(record.percentage)

        # Prune old snapshots
        if len(self.snapshots) > self.max_snapshots:
            old = self.snapshots.pop(0)
            # Also update history
            if len(self.snapshots) == 0:
                self._service_history.clear()

        logger.debug(f"Added coverage snapshot: {snapshot.overall_percentage:.1f}%")

    def get_latest_snapshot(self) -> Optional[CoverageSnapshot]:
        """
        Get the most recent snapshot.

        Returns:
            Latest snapshot or None
        """
        return self.snapshots[-1] if self.snapshots else None

    def get_coverage_trend(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get coverage trend data.

        Args:
            limit: Maximum number of data points

        Returns:
            List of trend data points
        """
        snapshots = self.snapshots[-limit:]

        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "percentage": s.overall_percentage,
                "total_lines": s.total_lines,
                "covered_lines": s.covered_lines
            }
            for s in snapshots
        ]

    def get_service_coverage(self, service_name: str) -> Optional[CoverageRecord]:
        """
        Get coverage for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            Coverage record or None
        """
        latest = self.get_latest_snapshot()
        if latest is None:
            return None

        for record in latest.records:
            if record.service_name == service_name:
                return record

        return None

    def get_low_coverage_services(self, threshold: float = 80.0) -> List[CoverageRecord]:
        """
        Get services with coverage below threshold.

        Args:
            threshold: Coverage threshold percentage

        Returns:
            List of coverage records below threshold
        """
        latest = self.get_latest_snapshot()
        if latest is None:
            return []

        return [r for r in latest.records if r.percentage < threshold]

    def get_coverage_change(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get coverage change for a service between snapshots.

        Args:
            service_name: Name of the service

        Returns:
            Change data or None
        """
        if len(self.snapshots) < 2:
            return None

        # Find latest and previous records
        latest_record = None
        previous_record = None

        for record in self.snapshots[-1].records:
            if record.service_name == service_name:
                latest_record = record
                break

        for record in self.snapshots[-2].records:
            if record.service_name == service_name:
                previous_record = record
                break

        if latest_record is None or previous_record is None:
            return None

        change = latest_record.percentage - previous_record.percentage

        return {
            "service_name": service_name,
            "current": latest_record.percentage,
            "previous": previous_record.percentage,
            "change": change,
            "improved": change > 0,
            "regressed": change < 0
        }

    def get_average_coverage(self, service_name: Optional[str] = None) -> float:
        """
        Get average coverage over time.

        Args:
            service_name: Specific service or None for overall

        Returns:
            Average coverage percentage
        """
        if service_name:
            history = self._service_history.get(service_name, [])
            if not history:
                return 0.0
            return sum(history) / len(history)

        # Overall average
        if not self.snapshots:
            return 0.0

        total = sum(s.overall_percentage for s in self.snapshots)
        return total / len(self.snapshots)


class CoverageDisplay:
    """
    Formats coverage data for dashboard display.

    Provides summary statistics, charts, and breakdowns.
    """

    def __init__(self, tracker: Optional[CoverageTracker] = None):
        """
        Initialize coverage display.

        Args:
            tracker: Coverage tracker to use
        """
        self.tracker = tracker or CoverageTracker()
        logger.info("CoverageDisplay initialized")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get overall coverage summary.

        Returns:
            Summary dictionary
        """
        latest = self.tracker.get_latest_snapshot()

        if latest is None:
            return {
                "overall_percentage": 0.0,
                "total_lines": 0,
                "covered_lines": 0,
                "uncovered_lines": 0,
                "service_count": 0,
                "timestamp": None
            }

        return {
            "overall_percentage": round(latest.overall_percentage, 2),
            "total_lines": latest.total_lines,
            "covered_lines": latest.covered_lines,
            "uncovered_lines": latest.total_lines - latest.covered_lines,
            "service_count": len(latest.records),
            "timestamp": latest.timestamp.isoformat()
        }

    def get_service_breakdown(self) -> List[Dict[str, Any]]:
        """
        Get coverage breakdown by service.

        Returns:
            List of service coverage data
        """
        latest = self.tracker.get_latest_snapshot()
        if latest is None:
            return []

        return [record.to_dict() for record in latest.records]

    def get_missing_files(self, threshold: float = 80.0) -> List[Dict[str, Any]]:
        """
        Get files below coverage threshold.

        Args:
            threshold: Coverage threshold

        Returns:
            List of missing file data
        """
        latest = self.tracker.get_latest_snapshot()
        if latest is None:
            return []

        missing = []
        for record in latest.records:
            for file_cov in record.missing_files:
                if file_cov.percentage < threshold:
                    missing.append({
                        "service": record.service_name,
                        "file_path": file_cov.file_path,
                        "percentage": file_cov.percentage,
                        "covered_lines": file_cov.covered_lines,
                        "total_lines": file_cov.total_lines
                    })

        return missing

    def get_trend_chart_data(self, limit: int = 30) -> Dict[str, Any]:
        """
        Get chart data for coverage trends.

        Args:
            limit: Number of data points

        Returns:
            Chart data
        """
        trend = self.tracker.get_coverage_trend(limit=limit)

        return {
            "labels": [t["timestamp"][-19:-14] for t in trend],  # Extract HH:MM
            "datasets": [
                {
                    "label": "Overall Coverage",
                    "data": [t["percentage"] for t in trend],
                    "borderColor": "rgb(54, 162, 235)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)"
                }
            ],
            "average": self.tracker.get_average_coverage()
        }

    def get_services_by_health(self, threshold: float = 80.0) -> Dict[str, List[str]]:
        """
        Categorize services by coverage health.

        Args:
            threshold: Coverage threshold

        Returns:
            Dictionary with 'healthy' and 'unhealthy' service lists
        """
        latest = self.tracker.get_latest_snapshot()
        if latest is None:
            return {"healthy": [], "unhealthy": []}

        healthy = []
        unhealthy = []

        for record in latest.records:
            if record.is_healthy(threshold):
                healthy.append(record.service_name)
            else:
                unhealthy.append(record.service_name)

        return {"healthy": healthy, "unhealthy": unhealthy}
