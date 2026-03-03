"""
Unit tests for result sync service.

Tests polling GitHub Actions for results and syncing to orchestrator.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

# Add cicd-gateway to path
gateway_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(gateway_path))


class TestGitHubClient:
    """Test GitHub client."""

    @pytest.fixture
    def client(self):
        """Create GitHub client."""
        from gateway.sync import GitHubClient
        return GitHubClient(token="test_token", repo="test/repo")

    def test_client_init(self, client):
        """Test client initialization."""
        assert client.token == "test_token"
        assert client.repo == "test/repo"

    def test_get_workflow_runs(self, client):
        """Test getting workflow runs."""
        # Mock requests.get
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflow_runs": [
                {"id": 4527, "status": "completed", "conclusion": "success"},
                {"id": 4528, "status": "in_progress", "conclusion": None}
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        with mock.patch("requests.get", return_value=mock_response):
            runs = client.get_workflow_runs()

        assert len(runs) == 2
        assert runs[0]["id"] == 4527

    def test_get_workflow_artifacts(self, client):
        """Test getting workflow artifacts."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "artifacts": [
                {"id": 1, "name": "test-results", "archive_download_url": "http://example.com/test.zip"}
            ]
        }
        mock_response.raise_for_status = mock.Mock()

        with mock.patch("requests.get", return_value=mock_response):
            artifacts = client.get_workflow_artifacts(4527)

        assert len(artifacts) == 1
        assert artifacts[0]["name"] == "test-results"


class TestResultParser:
    """Test result parsing."""

    def test_parse_junit_xml(self):
        """Test parsing JUnit XML."""
        from gateway.sync import ResultParser

        xml = """<?xml version="1.0"?>
        <testsuites>
            <testsuite name="test_suite" tests="10" failures="1" errors="0" skipped="0">
                <testcase name="test1" classname="TestClass"/>
                <testcase name="test2" classname="TestClass">
                    <failure message="Test failed"/>
                </testcase>
            </testsuite>
        </testsuites>"""

        results = ResultParser.parse_junit_xml(xml)
        assert results["total"] == 10
        assert results["passed"] == 9
        assert results["failed"] == 1

    def test_parse_coverage_json(self):
        """Test parsing coverage JSON."""
        from gateway.sync import ResultParser

        coverage_data = {
            "totals": {
                "percent_covered": 85.5
            },
            "files": [
                {"name": "test.py", "summary": {"percent_covered": 80.0}}
            ]
        }

        results = ResultParser.parse_coverage_json(coverage_data)
        assert results["percentage"] == 85.5
        assert results["files_covered"] == 1


class TestResultSyncService:
    """Test result sync service."""

    @pytest.fixture
    def service(self):
        """Create result sync service."""
        from gateway.sync import ResultSyncService, GitHubClient

        github = GitHubClient(token="test_token", repo="test/repo")
        return ResultSyncService(github=github, orchestrator_url="http://orchestrator:8000")

    def test_service_init(self, service):
        """Test service initialization."""
        assert service.github is not None
        assert len(service.pending_syncs) == 0

    def test_add_pending_sync(self, service):
        """Test adding pending sync."""
        service.add_pending_sync("4527", "test-run-abc")
        assert "4527" in service.pending_syncs
        assert service.pending_syncs["4527"]["run_id"] == "test-run-abc"

    def test_remove_pending_sync(self, service):
        """Test removing pending sync."""
        service.add_pending_sync("4527", "test-run-abc")
        service.remove_pending_sync("4527")
        assert "4527" not in service.pending_syncs

    def test_sync_completed_workflow(self, service):
        """Test syncing completed workflow."""
        import unittest.mock as mock

        # Add to pending sync queue
        service.add_pending_sync("4527", "test-run-abc")

        # Mock GitHub API
        mock_artifacts = mock.Mock()
        mock_artifacts.return_value = [
            {"id": 1, "name": "test-results", "archive_download_url": "http://example.com/test.zip"}
        ]

        # Mock artifact download (empty zip for test)
        mock_download = mock.Mock()
        mock_download.return_value = b""  # Empty bytes

        # Mock orchestrator update
        mock_update = mock.Mock()
        mock_update.return_value = {"status": "ok"}

        service.github.get_workflow_artifacts = mock_artifacts
        service._download_and_parse_artifact = mock_download
        service._update_orchestrator = mock_update

        result = service.sync_completed_workflow("4527")

        # Should succeed even with no test data
        assert result["synced"] is True

    def test_get_pending_sync_count(self, service):
        """Test getting pending sync count."""
        service.add_pending_sync("4527", "run1")
        service.add_pending_sync("4528", "run2")

        assert service.get_pending_sync_count() == 2


class TestPollingService:
    """Test polling service."""

    @pytest.fixture
    def polling(self):
        """Create polling service."""
        from gateway.sync import PollingService, ResultSyncService
        sync = ResultSyncService(github=None, orchestrator_url="http://test")
        return PollingService(sync_service=sync, interval_seconds=30)

    def test_polling_init(self, polling):
        """Test polling initialization."""
        assert polling.interval_seconds == 30
        assert polling.is_running is False

    def test_should_poll_workflow(self, polling):
        """Test determining if workflow should be polled."""
        # Running workflow should be polled
        assert polling.should_poll_workflow({"status": "in_progress"}) is True
        assert polling.should_poll_workflow({"status": "queued"}) is True

        # Completed workflow should not be polled
        assert polling.should_poll_workflow({"status": "completed"}) is False

    def test_get_workflows_to_poll(self, polling):
        """Test getting workflows that need polling."""
        import unittest.mock as mock

        # Mock get_workflow_runs
        mock_get = mock.Mock()
        mock_get.return_value = [
            {"id": 4527, "status": "in_progress"},
            {"id": 4528, "status": "completed"},
            {"id": 4529, "status": "queued"}
        ]

        polling.sync_service.github = mock.Mock()
        polling.sync_service.github.get_workflow_runs = mock_get

        workflows = polling.get_workflows_to_poll()
        assert len(workflows) == 2  # in_progress and queued
        assert 4527 in [w["id"] for w in workflows]
        assert 4529 in [w["id"] for w in workflows]
