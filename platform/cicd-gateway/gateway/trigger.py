"""
Pipeline trigger service.

Handles triggering test runs via orchestrator and tracking mappings.
"""

import logging
import uuid
import requests
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# Service path mapping (same as in webhook.py)
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

ALL_SERVICES = [
    "scenespeak-agent",
    "captioning-agent",
    "bsl-agent",
    "sentiment-agent",
    "lighting-service",
    "safety-filter",
    "openclaw-orchestrator",
    "operator-console"
]


@dataclass
class PipelineTrigger:
    """
    Represents a pipeline trigger request.

    Attributes:
        pipeline_id: GitHub Actions workflow run ID
        branch: Git branch
        commit: Git commit SHA
        services: List of services to test
        triggered_at: When trigger was created
    """
    pipeline_id: str
    branch: str
    commit: str
    services: List[str]
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "branch": self.branch,
            "commit": self.commit,
            "services": self.services,
            "triggered_at": self.triggered_at.isoformat()
        }


@dataclass
class TriggerResult:
    """
    Result of a pipeline trigger.

    Attributes:
        pipeline_id: Pipeline identifier
        run_id: Orchestrator run ID (None if failed)
        status: Trigger status (triggered, failed, error)
        error: Error message if failed
        triggered_at: When trigger was attempted
    """
    pipeline_id: str
    run_id: Optional[str]
    status: str
    error: Optional[str] = None
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_success(self) -> bool:
        """Check if trigger was successful."""
        return self.status == "triggered" and self.run_id is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "run_id": self.run_id,
            "status": self.status,
            "error": self.error,
            "is_success": self.is_success(),
            "triggered_at": self.triggered_at.isoformat()
        }


class PipelineTriggerService:
    """
    Service for triggering test pipelines.

    Handles communication with the test orchestrator and
    tracks pipeline-to-run mappings.
    """

    def __init__(self, orchestrator_url: str, api_key: str):
        """
        Initialize trigger service.

        Args:
            orchestrator_url: Base URL for orchestrator API
            api_key: API key for orchestrator authentication
        """
        self.orchestrator_url = orchestrator_url.rstrip("/")
        self.api_key = api_key
        self.mappings: Dict[str, Dict[str, Any]] = {}

        logger.info(f"PipelineTriggerService initialized (orchestrator: {orchestrator_url})")

    def _orchestrator_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to orchestrator.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for requests

        Returns:
            Response data
        """
        url = f"{self.orchestrator_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=kwargs.get("params"), timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=kwargs.get("json"), timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=kwargs.get("json"), timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Orchestrator request failed: {e}")
            raise

    def create_trigger(
        self,
        event,
        services: Optional[List[str]] = None
    ) -> PipelineTrigger:
        """
        Create a pipeline trigger from webhook event.

        Args:
            event: Webhook event
            services: List of services (default: all)

        Returns:
            Pipeline trigger
        """
        # Generate pipeline ID from GitHub event
        if event.pipeline_id:
            pipeline_id = event.pipeline_id
        else:
            pipeline_id = str(uuid.uuid4())

        # Use provided services or detect from changed files
        if services is None:
            if event.changed_files:
                services = get_services_from_files(event.changed_files)
            else:
                services = ALL_SERVICES

        return PipelineTrigger(
            pipeline_id=pipeline_id,
            branch=event.branch or "main",
            commit=event.commit or "",
            services=services
        )

    def trigger_orchestrator(self, trigger: PipelineTrigger) -> TriggerResult:
        """
        Trigger test run in orchestrator.

        Args:
            trigger: Pipeline trigger

        Returns:
            Trigger result
        """
        try:
            response = self._orchestrator_request(
                "POST",
                "/api/v1/run-tests",
                json={
                    "services": trigger.services,
                    "branch": trigger.branch,
                    "commit": trigger.commit
                }
            )

            run_id = response.get("run_id")

            # Save mapping
            self.save_mapping(
                trigger.pipeline_id,
                run_id,
                trigger.branch,
                trigger.commit,
                status="triggered"
            )

            return TriggerResult(
                pipeline_id=trigger.pipeline_id,
                run_id=run_id,
                status="triggered"
            )

        except Exception as e:
            logger.error(f"Failed to trigger orchestrator: {e}")
            return TriggerResult(
                pipeline_id=trigger.pipeline_id,
                run_id=None,
                status="error",
                error=str(e)
            )

    def save_mapping(
        self,
        pipeline_id: str,
        run_id: str,
        branch: str,
        commit: str,
        status: str = "triggered"
    ) -> None:
        """
        Save pipeline-to-run mapping.

        Args:
            pipeline_id: Pipeline identifier
            run_id: Orchestrator run ID
            branch: Git branch
            commit: Git commit SHA
            status: Mapping status
        """
        self.mappings[pipeline_id] = {
            "run_id": run_id,
            "branch": branch,
            "commit": commit,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        logger.debug(f"Saved mapping: {pipeline_id} -> {run_id}")

    def get_mapping(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pipeline mapping.

        Args:
            pipeline_id: Pipeline identifier

        Returns:
            Mapping data or None
        """
        return self.mappings.get(pipeline_id)

    def get_run_id_for_pipeline(self, pipeline_id: str) -> Optional[str]:
        """
        Get orchestrator run ID for pipeline.

        Args:
            pipeline_id: Pipeline identifier

        Returns:
            Run ID or None
        """
        mapping = self.get_mapping(pipeline_id)
        return mapping["run_id"] if mapping else None

    def update_pipeline_status(self, pipeline_id: str, status: str) -> bool:
        """
        Update pipeline status.

        Args:
            pipeline_id: Pipeline identifier
            status: New status

        Returns:
            True if updated
        """
        if pipeline_id in self.mappings:
            self.mappings[pipeline_id]["status"] = status
            self.mappings[pipeline_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            logger.debug(f"Updated pipeline status: {pipeline_id} -> {status}")
            return True
        return False

    def get_pending_mappings(self) -> List[Dict[str, Any]]:
        """
        Get pending pipeline mappings.

        Returns:
            List of mappings with pending status
        """
        pending_statuses = ("triggered", "running")

        return [
            {**mapping, "pipeline_id": pid}
            for pid, mapping in self.mappings.items()
            if mapping.get("status") in pending_statuses
        ]

    def trigger_from_event(
        self,
        event,
        services: Optional[List[str]] = None
    ) -> TriggerResult:
        """
        Trigger test run from webhook event.

        Args:
            event: Webhook event
            services: List of services (optional)

        Returns:
            Trigger result
        """
        trigger = self.create_trigger(event, services)
        return self.trigger_orchestrator(trigger)


def get_services_from_files(changed_files: List[str]) -> List[str]:
    """
    Determine which services are affected by changed files.

    Args:
        changed_files: List of changed file paths

    Returns:
        List of affected service names
    """
    if not changed_files:
        return ALL_SERVICES.copy()

    services = set()

    for file_path in changed_files:
        for path_prefix, service in SERVICE_PATH_MAPPING.items():
            if file_path.startswith(path_prefix):
                services.add(service)
                break

    return list(services) if services else []
