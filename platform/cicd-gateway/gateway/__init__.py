"""
CI/CD Gateway package.

Integrates GitHub Actions with Project Chimera test platform.
"""

from .webhook import (
    verify_github_signature,
    WebhookEvent,
    WebhookHandler,
    WebhookLogger
)

from .trigger import (
    PipelineTrigger,
    TriggerResult,
    PipelineTriggerService,
    get_services_from_files
)

from .sync import (
    GitHubClient,
    ResultParser,
    ResultSyncService,
    PollingService
)

from .broadcast import (
    EventType,
    BroadcastMessage,
    StatusBroadcastService
)

__all__ = [
    "verify_github_signature",
    "WebhookEvent",
    "WebhookHandler",
    "WebhookLogger",
    "PipelineTrigger",
    "TriggerResult",
    "PipelineTriggerService",
    "get_services_from_files",
    "GitHubClient",
    "ResultParser",
    "ResultSyncService",
    "PollingService",
    "EventType",
    "BroadcastMessage",
    "StatusBroadcastService"
]
