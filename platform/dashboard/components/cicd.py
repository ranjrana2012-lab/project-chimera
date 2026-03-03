"""
CI/CD status display component for dashboard.

Tracks pipeline runs, status, and provides CI/CD metrics.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Pipeline run status."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, value: str) -> "PipelineStatus":
        """Create status from string."""
        mapping = {
            "success": cls.SUCCESS,
            "failed": cls.FAILED,
            "pending": cls.PENDING,
            "running": cls.RUNNING,
            "cancelled": cls.CANCELLED
        }
        return mapping.get(value.lower(), cls.PENDING)


@dataclass
class PipelineRun:
    """
    Represents a CI/CD pipeline run.

    Attributes:
        pipeline_id: Pipeline run identifier
        branch: Git branch
        status: Run status
        commit: Git commit hash
        started_at: When the run started
        finished_at: When the run finished
        duration_seconds: How long the run took
    """
    pipeline_id: str
    branch: str = "main"
    status: PipelineStatus = PipelineStatus.PENDING
    commit: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        """Set started_at if not provided."""
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

    def is_completed(self) -> bool:
        """Check if run has completed."""
        return self.status in (PipelineStatus.SUCCESS, PipelineStatus.FAILED, PipelineStatus.CANCELLED)

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        minutes = int(self.duration_seconds // 60)
        seconds = int(self.duration_seconds % 60)
        return f"{minutes}m {seconds}s"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "branch": self.branch,
            "status": self.status.value,
            "commit": self.commit,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self.duration_formatted,
            "is_completed": self.is_completed()
        }


class CICDTracker:
    """
    Tracks CI/CD pipeline runs.

    Stores run history and provides statistics.
    """

    def __init__(self, max_runs: int = 100):
        """
        Initialize CI/CD tracker.

        Args:
            max_runs: Maximum runs to keep
        """
        self.max_runs = max_runs
        self.runs: List[PipelineRun] = []
        self._run_index: Dict[str, PipelineRun] = {}

        logger.info("CICDTracker initialized")

    def add_run(self, run: PipelineRun) -> None:
        """
        Add a pipeline run.

        Args:
            run: Pipeline run to add
        """
        self.runs.append(run)
        self._run_index[run.pipeline_id] = run

        # Prune old runs
        if len(self.runs) > self.max_runs:
            old = self.runs.pop(0)
            if old.pipeline_id in self._run_index and self._run_index[old.pipeline_id] == old:
                del self._run_index[old.pipeline_id]

        logger.debug(f"Added pipeline run: {run.pipeline_id}")

    def get_run(self, pipeline_id: str) -> Optional[PipelineRun]:
        """
        Get a specific pipeline run.

        Args:
            pipeline_id: Pipeline identifier

        Returns:
            Pipeline run or None
        """
        return self._run_index.get(pipeline_id)

    def get_latest_runs(self, limit: int = 10) -> List[PipelineRun]:
        """
        Get latest pipeline runs.

        Args:
            limit: Maximum number of runs

        Returns:
            List of pipeline runs, most recent first
        """
        return self.runs[-limit:][::-1]

    def get_runs_by_status(self, status: PipelineStatus) -> List[PipelineRun]:
        """
        Get runs filtered by status.

        Args:
            status: Status to filter by

        Returns:
            List of matching runs
        """
        return [r for r in self.runs if r.status == status]

    def get_runs_by_branch(self, branch: str) -> List[PipelineRun]:
        """
        Get runs for a specific branch.

        Args:
            branch: Branch name

        Returns:
            List of runs for the branch
        """
        return [r for r in self.runs if r.branch == branch]

    def get_success_rate(self, run_count: int = 20) -> float:
        """
        Calculate success rate over recent runs.

        Args:
            run_count: Number of recent runs to consider

        Returns:
            Success rate percentage
        """
        recent = self.runs[-run_count:]

        # Only count completed runs
        completed = [r for r in recent if r.is_completed()]
        if not completed:
            return 0.0

        successful = [r for r in completed if r.status == PipelineStatus.SUCCESS]
        return (len(successful) / len(completed)) * 100

    def get_average_duration(self, run_count: int = 20) -> float:
        """
        Calculate average duration over recent runs.

        Args:
            run_count: Number of recent runs to consider

        Returns:
            Average duration in seconds
        """
        recent = self.runs[-run_count:]

        # Only count completed runs with duration
        completed = [r for r in recent if r.is_completed() and r.duration_seconds > 0]
        if not completed:
            return 0.0

        total = sum(r.duration_seconds for r in completed)
        return total / len(completed)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Summary dictionary
        """
        total = len(self.runs)
        if total == 0:
            return {
                "total_runs": 0,
                "success_count": 0,
                "failed_count": 0,
                "running_count": 0,
                "pending_count": 0,
                "success_rate": 0.0
            }

        successful = len(self.get_runs_by_status(PipelineStatus.SUCCESS))
        failed = len(self.get_runs_by_status(PipelineStatus.FAILED))
        running = len(self.get_runs_by_status(PipelineStatus.RUNNING))
        pending = len(self.get_runs_by_status(PipelineStatus.PENDING))

        return {
            "total_runs": total,
            "success_count": successful,
            "failed_count": failed,
            "running_count": running,
            "pending_count": pending,
            "success_rate": self.get_success_rate()
        }


class CICDDisplay:
    """
    Formats CI/CD data for dashboard display.

    Provides summary statistics and tables for visualization.
    """

    def __init__(self, tracker: Optional[CICDTracker] = None):
        """
        Initialize CI/CD display.

        Args:
            tracker: CI/CD tracker to use
        """
        self.tracker = tracker or CICDTracker()
        logger.info("CICDDisplay initialized")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get CI/CD summary.

        Returns:
            Summary dictionary
        """
        summary = self.tracker.get_summary()
        summary["average_duration"] = self.tracker.get_average_duration()
        summary["average_duration_formatted"] = self._format_duration(summary["average_duration"])
        return summary

    def get_pipeline_table(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pipeline runs as table data.

        Args:
            limit: Maximum number of runs

        Returns:
            List of row dictionaries
        """
        runs = self.tracker.get_latest_runs(limit=limit)

        return [
            {
                **run.to_dict(),
                "status_icon": self._get_status_icon(run.status),
                "short_commit": run.commit[:7] if run.commit else "N/A"
            }
            for run in runs
        ]

    def get_branch_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary by branch.

        Returns:
            Dictionary mapping branch names to summaries
        """
        branches = set(r.branch for r in self.tracker.runs)

        result = {}
        for branch in branches:
            runs = self.tracker.get_runs_by_branch(branch)
            successful = len([r for r in runs if r.status == PipelineStatus.SUCCESS])
            failed = len([r for r in runs if r.status == PipelineStatus.FAILED])
            running = len([r for r in runs if r.status == PipelineStatus.RUNNING])

            result[branch] = {
                "total": len(runs),
                "success": successful,
                "failed": failed,
                "running": running,
                "success_rate": (successful / len(runs) * 100) if runs else 0
            }

        return result

    def get_status_distribution(self) -> Dict[str, int]:
        """
        Get distribution of run statuses.

        Returns:
            Dictionary mapping status names to counts
        """
        summary = self.tracker.get_summary()

        return {
            "success": summary["success_count"],
            "failed": summary["failed_count"],
            "running": summary["running_count"],
            "pending": summary["pending_count"]
        }

    def _format_duration(self, seconds: float) -> str:
        """Format duration as readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    def _get_status_icon(self, status: PipelineStatus) -> str:
        """Get icon for status."""
        icons = {
            PipelineStatus.SUCCESS: "✅",
            PipelineStatus.FAILED: "❌",
            PipelineStatus.RUNNING: "🔄",
            PipelineStatus.PENDING: "⏳",
            PipelineStatus.CANCELLED: "🚫"
        }
        return icons.get(status, "❓")
