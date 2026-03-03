"""
Webhook handler for GitHub Events.

Receives, validates, and processes GitHub webhook events.
"""

import hmac
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload: Raw request payload
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False

    hash_value = signature[7:]  # Remove "sha256=" prefix
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, hash_value)


@dataclass
class WebhookEvent:
    """
    Represents a GitHub webhook event.

    Attributes:
        event_type: Type of event (push, pull_request, workflow_run)
        action: Action that triggered the event
        repository: Full repository name (owner/repo)
        branch: Branch name
        commit: Commit SHA
        pipeline_id: GitHub Actions workflow run ID (for workflow_run events)
        status: Workflow status (for workflow_run events)
        pr_number: Pull request number (for PR events)
        changed_files: List of changed file paths
        raw_payload: Original webhook payload
    """
    event_type: str
    repository: str = ""
    action: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None
    pipeline_id: Optional[str] = None
    status: Optional[str] = None
    pr_number: Optional[int] = None
    changed_files: List[str] = field(default_factory=list)
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_github_payload(cls, event_type: str, payload: Dict[str, Any]) -> "WebhookEvent":
        """
        Create WebhookEvent from GitHub webhook payload.

        Args:
            event_type: GitHub event type
            payload: Webhook payload

        Returns:
            Parsed webhook event
        """
        event = cls(event_type=event_type, raw_payload=payload)

        if event_type == "push":
            event._parse_push_payload(payload)
        elif event_type == "pull_request":
            event._parse_pr_payload(payload)
        elif event_type == "workflow_run":
            event._parse_workflow_run_payload(payload)

        return event

    def _parse_push_payload(self, payload: Dict[str, Any]) -> None:
        """Parse push event payload."""
        self.action = "push"
        self.repository = payload.get("repository", {}).get("full_name", "")
        self.commit = payload.get("after", "")

        # Parse branch from ref (refs/heads/main)
        ref = payload.get("ref", "")
        if ref.startswith("refs/heads/"):
            self.branch = ref[11:]

    def _parse_pr_payload(self, payload: Dict[str, Any]) -> None:
        """Parse pull request event payload."""
        self.action = payload.get("action", "")
        self.repository = payload.get("repository", {}).get("full_name", "")

        pr = payload.get("pull_request", {})
        self.pr_number = pr.get("number")
        self.branch = pr.get("head", {}).get("ref", "")
        self.commit = pr.get("head", {}).get("sha", "")

    def _parse_workflow_run_payload(self, payload: Dict[str, Any]) -> None:
        """Parse workflow_run event payload."""
        self.action = payload.get("action", "")
        self.repository = payload.get("repository", {}).get("full_name", "")

        workflow_run = payload.get("workflow_run", {})
        self.pipeline_id = str(workflow_run.get("id", ""))
        self.status = workflow_run.get("conclusion", "")
        self.branch = workflow_run.get("head_branch", "")
        self.commit = workflow_run.get("head_sha", "")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "action": self.action,
            "repository": self.repository,
            "branch": self.branch,
            "commit": self.commit,
            "pipeline_id": self.pipeline_id,
            "status": self.status,
            "pr_number": self.pr_number,
            "received_at": self.received_at.isoformat()
        }


class WebhookHandler:
    """
    Handles GitHub webhook events.

    Validates signatures, parses events, and determines actions.
    """

    # Mapping of file paths to services
    SERVICE_PATH_MAPPING = {
        "platform/agents/scenespeak": "scenespeak-agent",
        "platform/agents/captioning": "captioning-agent",
        "platform/agents/bsl": "bsl-agent",
        "platform/agents/sentiment": "sentiment-agent",
        "platform/services/lighting": "lighting-service",
        "platform/services/safety": "safety-filter",
        "platform/orchestrator": "openclaw-orchestrator",
        "platform/console": "operator-console",
    }

    def __init__(self, secret: str, allowed_repos: Optional[List[str]] = None):
        """
        Initialize webhook handler.

        Args:
            secret: GitHub webhook secret
            allowed_repos: List of allowed repositories (default: allow all)
        """
        self.secret = secret
        self.allowed_repos = allowed_repos or []
        logger.info("WebhookHandler initialized")

    def validate_request(
        self,
        payload: bytes,
        signature: Optional[str],
        event_type: str
    ) -> Dict[str, Any]:
        """
        Validate webhook request.

        Args:
            payload: Raw request payload
            signature: X-Hub-Signature-256 header
            event_type: X-GitHub-Event header

        Returns:
            Validation result
        """
        # Check signature
        if not signature:
            return {
                "valid": False,
                "error": "missing_signature"
            }

        if not verify_github_signature(payload, signature, self.secret):
            logger.warning("Invalid webhook signature")
            return {
                "valid": False,
                "error": "invalid_signature"
            }

        # Check event type
        if event_type not in ("push", "pull_request", "workflow_run"):
            return {
                "valid": False,
                "error": f"unsupported_event_type: {event_type}"
            }

        return {"valid": True}

    def parse_event(self, event_type: str, payload: Dict[str, Any]) -> WebhookEvent:
        """
        Parse webhook event from payload.

        Args:
            event_type: GitHub event type
            payload: Webhook payload

        Returns:
            Parsed webhook event
        """
        event = WebhookEvent.from_github_payload(event_type, payload)

        # Validate repository
        if self.allowed_repos and event.repository not in self.allowed_repos:
            logger.warning(f"Repository not allowed: {event.repository}")
            raise ValueError(f"Repository not allowed: {event.repository}")

        return event

    def should_trigger_pipeline(self, event: WebhookEvent) -> bool:
        """
        Determine if event should trigger a test pipeline.

        Args:
            event: Webhook event

        Returns:
            True if pipeline should be triggered
        """
        # Push events trigger pipelines
        if event.event_type == "push":
            return True

        # PR events trigger pipelines
        if event.event_type == "pull_request" and event.action in ("opened", "synchronized", "reopened"):
            return True

        # Workflow run events don't trigger (they're results)
        if event.event_type == "workflow_run":
            return False

        return False

    def get_affected_services(self, event: WebhookEvent) -> List[str]:
        """
        Determine which services are affected by an event.

        Args:
            event: Webhook event

        Returns:
            List of affected service names
        """
        # For workflow_run events, we don't have changed files
        if event.event_type == "workflow_run":
            return []

        # For other events, we'd typically fetch changed files from GitHub API
        # For now, return empty - will be implemented with GitHub API integration
        if event.changed_files:
            services = set()
            for file_path in event.changed_files:
                for path_prefix, service in self.SERVICE_PATH_MAPPING.items():
                    if file_path.startswith(path_prefix):
                        services.add(service)
            return list(services)

        # Default to all services if we can't determine
        return [
            "scenespeak-agent",
            "captioning-agent",
            "bsl-agent",
            "sentiment-agent",
            "lighting-service",
            "safety-filter",
            "openclaw-orchestrator",
            "operator-console"
        ]


class WebhookLogger:
    """
    Logs webhook events for debugging and auditing.
    """

    def __init__(self, max_events: int = 1000):
        """
        Initialize webhook logger.

        Args:
            max_events: Maximum events to keep in memory
        """
        self.max_events = max_events
        self.events: List[Dict[str, Any]] = []

        logger.info("WebhookLogger initialized")

    def log_event(
        self,
        event: WebhookEvent,
        payload: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a webhook event.

        Args:
            event: Webhook event
            payload: Original payload

        Returns:
            Log entry ID
        """
        log_id = str(uuid.uuid4())

        log_entry = {
            "id": log_id,
            "event": event.to_dict(),
            "payload": payload or event.raw_payload,
            "logged_at": datetime.now(timezone.utc).isoformat()
        }

        self.events.append(log_entry)

        # Prune old events
        if len(self.events) > self.max_events:
            self.events.pop(0)

        logger.debug(f"Logged webhook event: {log_id}")
        return log_id

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent webhook events.

        Args:
            limit: Maximum number of events

        Returns:
            List of recent events
        """
        return self.events[-limit:][::-1]

    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """
        Get events filtered by type.

        Args:
            event_type: Event type to filter

        Returns:
            List of matching events
        """
        return [
            e for e in self.events
            if e["event"]["event_type"] == event_type
        ]

    def get_events_by_repo(self, repository: str) -> List[Dict[str, Any]]:
        """
        Get events filtered by repository.

        Args:
            repository: Repository name

        Returns:
            List of matching events
        """
        return [
            e for e in self.events
            if e["event"]["repository"] == repository
        ]
