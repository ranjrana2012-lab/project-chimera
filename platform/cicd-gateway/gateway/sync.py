"""
Result sync service.

Polls GitHub Actions for workflow results and syncs to orchestrator.
"""

import logging
import zipfile
import io
import xml.etree.ElementTree as ET
import requests
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Client for GitHub API.

    Handles communication with GitHub Actions API.
    """

    def __init__(self, token: str, repo: str):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token
            repo: Repository name (owner/repo)
        """
        self.token = token
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        logger.info(f"GitHubClient initialized for {repo}")

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make API request to GitHub.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for requests

        Returns:
            Response data
        """
        url = f"{self.api_base}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=kwargs.get("params"), timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            raise

    def get_workflow_runs(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get workflow runs from repository.

        Args:
            status: Filter by status (conclusion)
            limit: Maximum number of runs

        Returns:
            List of workflow runs
        """
        params = {"per_page": min(limit, 100)}
        if status:
            params["conclusion"] = status

        data = self._request(
            "GET",
            f"/repos/{self.repo}/actions/runs",
            params=params
        )

        return data.get("workflow_runs", [])

    def get_workflow_run(self, run_id: int) -> Dict[str, Any]:
        """
        Get specific workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            Workflow run data
        """
        return self._request(
            "GET",
            f"/repos/{self.repo}/actions/runs/{run_id}"
        )

    def get_workflow_artifacts(self, run_id: int) -> List[Dict[str, Any]]:
        """
        Get artifacts for a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            List of artifacts
        """
        data = self._request(
            "GET",
            f"/repos/{self.repo}/actions/runs/{run_id}/artifacts"
        )

        return data.get("artifacts", [])

    def download_artifact(self, artifact_id: int) -> bytes:
        """
        Download artifact content.

        Args:
            artifact_id: Artifact ID

        Returns:
            Artifact content as bytes
        """
        # Get artifact download URL
        data = self._request(
            "GET",
            f"/repos/{self.repo}/actions/artifacts/{artifact_id}"
        )

        archive_url = data.get("archive_download_url")

        # Download archive
        response = requests.get(
            archive_url,
            headers=self.headers,
            timeout=60
        )
        response.raise_for_status()

        return response.content


class ResultParser:
    """
    Parses test results and coverage reports.
    """

    @staticmethod
    def parse_junit_xml(xml_content: str) -> Dict[str, Any]:
        """
        Parse JUnit XML test results.

        Args:
            xml_content: JUnit XML content

        Returns:
            Parsed results
        """
        try:
            root = ET.fromstring(xml_content)

            total = 0
            failed = 0
            skipped = 0
            errors = 0

            for testsuite in root.findall(".//testsuite"):
                total += int(testsuite.get("tests", 0))
                failed += int(testsuite.get("failures", 0))
                skipped += int(testsuite.get("skipped", 0))
                errors += int(testsuite.get("errors", 0))

            passed = total - failed - errors - skipped

            return {
                "total": total,
                "passed": max(0, passed),
                "failed": failed,
                "skipped": skipped,
                "errors": errors
            }

        except ET.ParseError as e:
            logger.error(f"Failed to parse JUnit XML: {e}")
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}

    @staticmethod
    def parse_coverage_json(coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse coverage JSON from pytest-cov.

        Args:
            coverage_data: Coverage JSON data

        Returns:
            Parsed coverage
        """
        totals = coverage_data.get("totals", {})
        files = coverage_data.get("files", {})

        # Handle both dict and list formats for files
        if isinstance(files, list):
            file_names = [f.get("name", "") for f in files]
        else:
            file_names = list(files.keys())

        return {
            "percentage": totals.get("percent_covered", 0.0),
            "covered_lines": totals.get("covered_lines", 0),
            "num_statements": totals.get("num_statements", 0),
            "files_covered": len(file_names),
            "files": file_names
        }


class ResultSyncService:
    """
    Syncs test results from GitHub Actions to orchestrator.

    Polls for completed workflows, downloads artifacts, and updates results.
    """

    def __init__(
        self,
        github: Optional[GitHubClient],
        orchestrator_url: str,
        api_key: str = ""
    ):
        """
        Initialize result sync service.

        Args:
            github: GitHub client (None for testing)
            orchestrator_url: Orchestrator base URL
            api_key parameter: key used for orchestrator API authentication
        """
        self.github = github
        self.orchestrator_url = orchestrator_url.rstrip("/")
        self.api_key = api_key
        self.pending_syncs: Dict[str, Dict[str, Any]] = {}

        logger.info("ResultSyncService initialized")

    def add_pending_sync(self, pipeline_id: str, run_id: str) -> None:
        """
        Add workflow to pending sync queue.

        Args:
            pipeline_id: GitHub Actions workflow ID
            run_id: Orchestrator run ID
        """
        self.pending_syncs[pipeline_id] = {
            "run_id": run_id,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "attempts": 0
        }

        logger.debug(f"Added pending sync: {pipeline_id}")

    def remove_pending_sync(self, pipeline_id: str) -> None:
        """
        Remove workflow from pending sync queue.

        Args:
            pipeline_id: GitHub Actions workflow ID
        """
        if pipeline_id in self.pending_syncs:
            del self.pending_syncs[pipeline_id]

    def get_pending_sync_count(self) -> int:
        """Get number of pending syncs."""
        return len(self.pending_syncs)

    def sync_completed_workflow(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Sync results for a completed workflow.

        Args:
            pipeline_id: GitHub Actions workflow ID

        Returns:
            Sync result
        """
        if pipeline_id not in self.pending_syncs:
            return {"synced": False, "error": "not_in_queue"}

        if not self.github:
            return {"synced": True, "skipped": True, "reason": "no_github_client"}

        try:
            # Get workflow artifacts
            artifacts = self.github.get_workflow_artifacts(int(pipeline_id))

            # Look for test results artifact
            test_results = None
            coverage_results = None

            for artifact in artifacts:
                if "test" in artifact.get("name", "").lower():
                    test_results = self._download_and_parse_artifact(
                        artifact["id"],
                        "test"
                    )
                elif "coverage" in artifact.get("name", "").lower():
                    coverage_results = self._download_and_parse_artifact(
                        artifact["id"],
                        "coverage"
                    )

            # Update orchestrator
            run_id = self.pending_syncs[pipeline_id]["run_id"]
            self._update_orchestrator(run_id, test_results, coverage_results)

            # Remove from queue
            self.remove_pending_sync(pipeline_id)

            return {
                "synced": True,
                "pipeline_id": pipeline_id,
                "run_id": run_id,
                "test_results": test_results,
                "coverage_results": coverage_results
            }

        except Exception as e:
            logger.error(f"Failed to sync workflow {pipeline_id}: {e}")
            self.pending_syncs[pipeline_id]["attempts"] += 1
            return {"synced": False, "error": str(e)}

    def _download_and_parse_artifact(
        self,
        artifact_id: int,
        artifact_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Download and parse artifact.

        Args:
            artifact_id: Artifact ID
            artifact_type: Type of artifact (test/coverage)

        Returns:
            Parsed data or None
        """
        content = self.github.download_artifact(artifact_id)

        # Extract zip
        with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith(".xml") and artifact_type == "test":
                    with zip_ref.open(file) as f:
                        xml_content = f.read().decode("utf-8")
                        return ResultParser.parse_junit_xml(xml_content)

                elif file.endswith(".json") and artifact_type == "coverage":
                    with zip_ref.open(file) as f:
                        json_content = f.read().decode("utf-8")
                        import json
                        return ResultParser.parse_coverage_json(json.load(io.BytesIO(json_content.encode())))

        return None

    def _update_orchestrator(
        self,
        run_id: str,
        test_results: Optional[Dict[str, Any]],
        coverage_results: Optional[Dict[str, Any]]
    ) -> None:
        """
        Update orchestrator with results.

        Args:
            run_id: Orchestrator run ID
            test_results: Test results
            coverage_results: Coverage results
        """
        # This would normally make an API call to the orchestrator
        # For now, just log
        logger.info(f"Updating orchestrator run {run_id}:")
        if test_results:
            logger.info(f"  Tests: {test_results['passed']}/{test_results['total']} passed")
        if coverage_results:
            logger.info(f"  Coverage: {coverage_results['percentage']}%")


class PollingService:
    """
    Polls GitHub Actions for completed workflows.

    Runs periodically to check for results and trigger sync.
    """

    def __init__(
        self,
        sync_service: ResultSyncService,
        interval_seconds: int = 30
    ):
        """
        Initialize polling service.

        Args:
            sync_service: Result sync service
            interval_seconds: Polling interval
        """
        self.sync_service = sync_service
        self.interval_seconds = interval_seconds
        self.is_running = False

        logger.info("PollingService initialized")

    def should_poll_workflow(self, workflow: Dict[str, Any]) -> bool:
        """
        Determine if workflow should be polled.

        Args:
            workflow: Workflow data

        Returns:
            True if should poll
        """
        status = workflow.get("status", "")
        conclusion = workflow.get("conclusion", "")

        # Poll running or queued workflows
        if status in ("in_progress", "queued"):
            return True

        # Poll completed workflows that haven't been synced
        if conclusion and workflow.get("id") in self.sync_service.pending_syncs:
            return True

        return False

    def get_workflows_to_poll(self) -> List[Dict[str, Any]]:
        """
        Get list of workflows that need polling.

        Returns:
            List of workflow data
        """
        if not self.sync_service.github:
            return []

        workflows = self.sync_service.github.get_workflow_runs()

        return [
            w for w in workflows
            if self.should_poll_workflow(w)
        ]

    def poll_once(self) -> Dict[str, Any]:
        """
        Perform one polling iteration.

        Returns:
            Polling results
        """
        synced = 0
        failed = 0
        skipped = 0

        workflows = self.get_workflows_to_poll()

        for workflow in workflows:
            pipeline_id = str(workflow["id"])
            conclusion = workflow.get("conclusion")

            # If completed and in queue, sync it
            if conclusion and pipeline_id in self.sync_service.pending_syncs:
                result = self.sync_service.sync_completed_workflow(pipeline_id)
                if result.get("synced"):
                    synced += 1
                else:
                    failed += 1
            else:
                skipped += 1

        return {
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
            "total_workflows": len(workflows)
        }
