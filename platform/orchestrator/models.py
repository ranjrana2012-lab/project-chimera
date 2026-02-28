"""Models for test scheduling."""
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ScheduledRunStatus(str, Enum):
    """Status of a scheduled test run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledRun(BaseModel):
    """A scheduled test run."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commit_sha: str
    branch: str
    test_filter: Optional[List[str]] = None
    full_suite: bool = True
    status: ScheduledRunStatus = ScheduledRunStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Worker allocation
    unit_test_workers: int = 16
    integration_workers: int = 8
    property_workers: int = 4
    e2e_workers: int = 2

    # Results
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: Optional[int] = None
