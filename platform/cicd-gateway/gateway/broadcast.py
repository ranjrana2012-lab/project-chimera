"""
Status broadcast service.

Broadcasts CI/CD status updates via WebSocket to dashboard.
"""

import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """WebSocket event types."""
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    TEST_PROGRESS = "test_progress"
    COVERAGE_UPDATE = "coverage_update"


@dataclass
class BroadcastMessage:
    """
    WebSocket broadcast message.

    Attributes:
        type: Message type
        data: Message payload
        timestamp: When message was created
    """
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class StatusBroadcastService:
    """
    Broadcasts CI/CD status updates to connected clients.

    Sends WebSocket messages to dashboard for real-time updates.
    """

    def __init__(self, ws_url: str):
        """
        Initialize broadcast service.

        Args:
            ws_url: WebSocket URL for dashboard
        """
        self.ws_url = ws_url
        self._clients: List = []  # Would be actual WebSocket connections

        logger.info(f"StatusBroadcastService initialized (ws: {ws_url})")

    def _send_to_ws(self, message: BroadcastMessage) -> bool:
        """
        Send message to WebSocket clients.

        Args:
            message: Message to broadcast

        Returns:
            True if sent successfully
        """
        # In production, this would broadcast to actual WebSocket clients
        # For now, just log the message
        logger.info(f"Broadcasting: {message.type}")
        return True

    def broadcast_pipeline_started(
        self,
        pipeline_id: str,
        run_id: str,
        branch: str
    ) -> bool:
        """
        Broadcast pipeline started event.

        Args:
            pipeline_id: GitHub Actions workflow ID
            run_id: Orchestrator run ID
            branch: Git branch

        Returns:
            True if broadcast successfully
        """
        message = BroadcastMessage(
            type=EventType.PIPELINE_STARTED.value,
            data={
                "pipeline_id": pipeline_id,
                "run_id": run_id,
                "branch": branch,
                "status": "running"
            }
        )

        return self._send_to_ws(message)

    def broadcast_pipeline_completed(
        self,
        pipeline_id: str,
        run_id: str,
        status: str,
        total_tests: int,
        passed: int,
        failed: int,
        duration_seconds: float = 0.0
    ) -> bool:
        """
        Broadcast pipeline completed event.

        Args:
            pipeline_id: GitHub Actions workflow ID
            run_id: Orchestrator run ID
            status: Completion status (success, failure, etc)
            total_tests: Total number of tests
            passed: Number of passing tests
            failed: Number of failing tests
            duration_seconds: Test duration

        Returns:
            True if broadcast successfully
        """
        message = BroadcastMessage(
            type=EventType.PIPELINE_COMPLETED.value,
            data={
                "pipeline_id": pipeline_id,
                "run_id": run_id,
                "status": status,
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "duration_seconds": duration_seconds,
                "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0
            }
        )

        return self._send_to_ws(message)

    def broadcast_pipeline_failed(
        self,
        pipeline_id: str,
        run_id: str,
        error: str
    ) -> bool:
        """
        Broadcast pipeline failed event.

        Args:
            pipeline_id: GitHub Actions workflow ID
            run_id: Orchestrator run ID
            error: Error message

        Returns:
            True if broadcast successfully
        """
        message = BroadcastMessage(
            type=EventType.PIPELINE_FAILED.value,
            data={
                "pipeline_id": pipeline_id,
                "run_id": run_id,
                "error": error
            }
        )

        return self._send_to_ws(message)

    def broadcast_test_progress(
        self,
        run_id: str,
        service: str,
        passed: int,
        failed: int,
        total: int
    ) -> bool:
        """
        Broadcast test progress update.

        Args:
            run_id: Orchestrator run ID
            service: Service being tested
            passed: Number of passing tests
            failed: Number of failing tests
            total: Total number of tests

        Returns:
            True if broadcast successfully
        """
        message = BroadcastMessage(
            type=EventType.TEST_PROGRESS.value,
            data={
                "run_id": run_id,
                "service": service,
                "passed": passed,
                "failed": failed,
                "total": total,
                "progress": (passed + failed) / total * 100 if total > 0 else 0
            }
        )

        return self._send_to_ws(message)

    def broadcast_coverage_update(
        self,
        run_id: str,
        service: str,
        percentage: float
    ) -> bool:
        """
        Broadcast coverage update.

        Args:
            run_id: Orchestrator run ID
            service: Service name
            percentage: Coverage percentage

        Returns:
            True if broadcast successfully
        """
        message = BroadcastMessage(
            type=EventType.COVERAGE_UPDATE.value,
            data={
                "run_id": run_id,
                "service": service,
                "percentage": percentage
            }
        )

        return self._send_to_ws(message)

    def broadcast_status_summary(self, summary: Dict[str, Any]) -> bool:
        """
        Broadcast overall CI/CD status summary.

        Args:
            summary: Status summary data

        Returns:
            True if broadcast successfully
        """
        message = BroadcastMessage(
            type="status_summary",
            data=summary
        )

        return self._send_to_ws(message)
