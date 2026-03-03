"""
Storage modules for Test Orchestrator.
"""

from .history import (
    TestHistoryStorage,
    TestRunRecord,
    TestResultRecord,
    CoverageRecord
)

__all__ = [
    "TestHistoryStorage",
    "TestRunRecord",
    "TestResultRecord",
    "CoverageRecord"
]
