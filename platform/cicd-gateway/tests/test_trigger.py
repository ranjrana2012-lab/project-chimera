"""
Unit tests for pipeline trigger service.

Tests triggering test runs via orchestrator and tracking mappings.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

# Add cicd-gateway to path
gateway_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(gateway_path))


class TestPipelineTrigger:
    """Test PipelineTrigger dataclass."""

    def test_trigger_creation(self):
        """Test creating pipeline trigger."""
        from gateway.trigger import PipelineTrigger

        trigger = PipelineTrigger(
            pipeline_id="4527",
            branch="main",
            commit="abc123",
            services=["scenespeak-agent", "captioning-agent"]
        )
        assert trigger.pipeline_id == "4527"
        assert trigger.branch == "main"
        assert trigger.services == ["scenespeak-agent", "captioning-agent"]

    def test_trigger_to_dict(self):
        """Test converting trigger to dict."""
        from gateway.trigger import PipelineTrigger

        trigger = PipelineTrigger(
            pipeline_id="4527",
            branch="main",
            commit="abc123",
            services=["svc1"]
        )

        data = trigger.to_dict()
        assert data["pipeline_id"] == "4527"
        assert data["branch"] == "main"


class TestTriggerResult:
    """Test TriggerResult dataclass."""

    def test_result_creation(self):
        """Test creating trigger result."""
        from gateway.trigger import TriggerResult

        result = TriggerResult(
            pipeline_id="4527",
            run_id="test-run-abc",
            status="triggered"
        )
        assert result.pipeline_id == "4527"
        assert result.run_id == "test-run-abc"

    def test_result_success(self):
        """Test success check."""
        from gateway.trigger import TriggerResult

        result1 = TriggerResult("4527", "test-run", "triggered")
        assert result1.is_success() is True

        result2 = TriggerResult("4527", None, "failed")
        assert result2.is_success() is False


class TestPipelineTriggerService:
    """Test PipelineTriggerService class."""

    @pytest.fixture
    def service(self):
        """Create pipeline trigger service."""
        from gateway.trigger import PipelineTriggerService
        return PipelineTriggerService(
            orchestrator_url="http://orchestrator:8000",
            api_key="test_key"
        )

    def test_service_init(self, service):
        """Test service initialization."""
        assert service.orchestrator_url == "http://orchestrator:8000"
        assert len(service.mappings) == 0

    def test_create_trigger(self, service):
        """Test creating a pipeline trigger."""
        from gateway.trigger import PipelineTrigger
        from gateway.webhook import WebhookEvent

        event = WebhookEvent(
            event_type="push",
            repository="test/repo",
            branch="main",
            commit="abc123"
        )

        trigger = service.create_trigger(event, services=["svc1"])
        assert trigger.pipeline_id is not None
        assert trigger.branch == "main"

    def test_trigger_orchestrator(self, service):
        """Test triggering orchestrator (mocked)."""
        from gateway.trigger import PipelineTrigger

        trigger = PipelineTrigger(
            pipeline_id="4527",
            branch="main",
            commit="abc123",
            services=["svc1"]
        )

        # Mock the HTTP request
        service._orchestrator_request = lambda method, endpoint, **kwargs: {
            "run_id": "test-run-abc",
            "status": "started"
        }

        result = service.trigger_orchestrator(trigger)
        assert result.is_success() is True
        assert result.run_id == "test-run-abc"

    def test_save_mapping(self, service):
        """Test saving pipeline mapping."""
        service.save_mapping("4527", "test-run-abc", "main", "abc123")
        assert "4527" in service.mappings
        assert service.mappings["4527"]["run_id"] == "test-run-abc"

    def test_get_mapping(self, service):
        """Test getting pipeline mapping."""
        service.save_mapping("4527", "test-run-abc", "main", "abc123")

        mapping = service.get_mapping("4527")
        assert mapping["run_id"] == "test-run-abc"
        assert mapping["branch"] == "main"

    def test_get_mapping_unknown(self, service):
        """Test getting unknown mapping."""
        mapping = service.get_mapping("unknown")
        assert mapping is None

    def test_get_run_id_for_pipeline(self, service):
        """Test getting run ID for pipeline."""
        service.save_mapping("4527", "test-run-abc", "main", "abc123")

        run_id = service.get_run_id_for_pipeline("4527")
        assert run_id == "test-run-abc"

    def test_update_pipeline_status(self, service):
        """Test updating pipeline status."""
        service.save_mapping("4527", "test-run-abc", "main", "abc123")

        service.update_pipeline_status("4527", "completed")
        assert service.mappings["4527"]["status"] == "completed"

    def test_get_pending_mappings(self, service):
        """Test getting pending mappings."""
        service.save_mapping("4527", "test-run-1", "main", "abc1", status="triggered")
        service.save_mapping("4528", "test-run-2", "main", "abc2", status="completed")

        pending = service.get_pending_mappings()
        assert len(pending) == 1
        assert pending[0]["pipeline_id"] == "4527"

    def test_trigger_from_event(self, service):
        """Test triggering from webhook event."""
        from gateway.trigger import PipelineTrigger
        from gateway.webhook import WebhookEvent

        event = WebhookEvent(
            event_type="push",
            repository="test/repo",
            branch="main",
            commit="abc123"
        )

        # Mock orchestrator request
        service._orchestrator_request = lambda method, endpoint, **kwargs: {
            "run_id": "test-run-abc",
            "status": "started"
        }

        result = service.trigger_from_event(event, services=["svc1"])
        assert result.is_success() is True
        assert result.run_id == "test-run-abc"


class TestServiceDetection:
    """Test service detection from changed files."""

    def test_get_services_from_files(self):
        """Test getting services from changed files."""
        from gateway.trigger import get_services_from_files

        files = [
            "platform/agents/scenespeak/main.py",
            "platform/agents/captioning/handlers.py",
            "tests/test_scenespeak.py"
        ]

        services = get_services_from_files(files)
        assert "scenespeak-agent" in services
        assert "captioning-agent" in services

    def test_get_services_no_files(self):
        """Test getting services with no files."""
        from gateway.trigger import get_services_from_files

        services = get_services_from_files([])
        # Should return all services
        assert len(services) == 8

    def test_get_services_unknown_files(self):
        """Test getting services with unknown file paths."""
        from gateway.trigger import get_services_from_files

        files = ["unknown/path/file.py"]
        services = get_services_from_files(files)
        # Unknown files don't match any service
        assert len(services) == 0
