"""
Unit tests for webhook handler.

Tests GitHub webhook event reception, validation, and parsing.
"""

import pytest
import hmac
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# Add cicd-gateway to path
gateway_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(gateway_path))


class TestGitHubSignature:
    """Test GitHub signature verification."""

    def test_verify_signature_valid(self):
        """Test verifying valid signature."""
        from gateway.webhook import verify_github_signature

        payload = b'{"test": "data"}'
        secret = "example"

        # Generate valid signature
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        assert verify_github_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        """Test verifying invalid signature."""
        from gateway.webhook import verify_github_signature

        payload = b'{"test": "data"}'
        secret = "example"

        # Invalid signature
        signature = "sha256=invalid"

        assert verify_github_signature(payload, signature, secret) is False

    def test_verify_signature_wrong_secret(self):
        """Test verifying signature with wrong secret."""
        from gateway.webhook import verify_github_signature

        payload = b'{"test": "data"}'
        secret1 = "secret1"
        secret2 = "secret2"

        # Signature with secret1
        signature = "sha256=" + hmac.new(
            secret1.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Verify with secret2 should fail
        assert verify_github_signature(payload, signature, secret2) is False


class TestWebhookEvent:
    """Test WebhookEvent dataclass."""

    def test_event_creation(self):
        """Test creating webhook event."""
        from gateway.webhook import WebhookEvent

        event = WebhookEvent(
            event_type="workflow_run",
            action="completed",
            repository="test/repo",
            branch="main"
        )
        assert event.event_type == "workflow_run"
        assert event.action == "completed"

    def test_event_from_push_payload(self):
        """Test parsing push event payload."""
        from gateway.webhook import WebhookEvent

        payload = {
            "ref": "refs/heads/main",
            "repository": {
                "full_name": "test/repo"
            },
            "after": "abc123",
            "sender": {
                "login": "testuser"
            }
        }

        event = WebhookEvent.from_github_payload("push", payload)
        assert event.event_type == "push"
        assert event.branch == "main"
        assert event.commit == "abc123"

    def test_event_from_pr_payload(self):
        """Test parsing pull request event payload."""
        from gateway.webhook import WebhookEvent

        payload = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "head": {
                    "ref": "feature-branch",
                    "sha": "def456"
                },
                "base": {
                    "ref": "main"
                }
            },
            "repository": {
                "full_name": "test/repo"
            }
        }

        event = WebhookEvent.from_github_payload("pull_request", payload)
        assert event.event_type == "pull_request"
        assert event.action == "opened"
        assert event.branch == "feature-branch"
        assert event.pr_number == 123

    def test_event_from_workflow_run_payload(self):
        """Test parsing workflow run event payload."""
        from gateway.webhook import WebhookEvent

        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 4527,
                "name": "Tests",
                "status": "completed",
                "conclusion": "success",
                "head_branch": "main",
                "head_sha": "abc123",
                "html_url": "https://github.com/test/run"
            },
            "repository": {
                "full_name": "test/repo"
            }
        }

        event = WebhookEvent.from_github_payload("workflow_run", payload)
        assert event.event_type == "workflow_run"
        assert event.action == "completed"
        assert event.pipeline_id == "4527"
        assert event.status == "success"


class TestWebhookHandler:
    """Test WebhookHandler class."""

    @pytest.fixture
    def handler(self):
        """Create webhook handler."""
        from gateway.webhook import WebhookHandler
        return WebhookHandler(secret="test_secret")

    def test_handler_init(self, handler):
        """Test handler initialization."""
        assert handler.secret == "test_secret"

    def test_validate_request_valid(self, handler):
        """Test validating valid request."""
        payload = b'{"test": "data"}'
        signature = "sha256=" + hmac.new(
            b"test_secret",
            payload,
            hashlib.sha256
        ).hexdigest()

        result = handler.validate_request(payload, signature, "push")
        assert result["valid"] is True

    def test_validate_request_invalid_signature(self, handler):
        """Test validating request with invalid signature."""
        payload = b'{"test": "data"}'
        signature = "sha256=invalid"

        result = handler.validate_request(payload, signature, "push")
        assert result["valid"] is False
        assert "error" in result

    def test_validate_request_missing_headers(self, handler):
        """Test validating request with missing headers."""
        result = handler.validate_request(
            b'{"test": "data"}',
            None,
            "push"
        )
        assert result["valid"] is False

    def test_parse_event_push(self, handler):
        """Test parsing push event."""
        payload = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "test/repo"},
            "after": "abc123"
        }

        event = handler.parse_event("push", payload)
        assert event.event_type == "push"
        assert event.branch == "main"

    def test_should_trigger_pipeline(self, handler):
        """Test determining if event should trigger pipeline."""
        from gateway.webhook import WebhookEvent

        # Push to main should trigger
        event1 = WebhookEvent(
            event_type="push",
            repository="test/repo",
            branch="main",
            commit="abc123"
        )
        assert handler.should_trigger_pipeline(event1) is True

        # Push to feature branch should trigger
        event2 = WebhookEvent(
            event_type="push",
            repository="test/repo",
            branch="feature/test",
            commit="def456"
        )
        assert handler.should_trigger_pipeline(event2) is True

        # PR opened should trigger
        event3 = WebhookEvent(
            event_type="pull_request",
            action="opened",
            repository="test/repo",
            branch="feature/test"
        )
        assert handler.should_trigger_pipeline(event3) is True

        # Workflow completed should NOT trigger (it's a result)
        event4 = WebhookEvent(
            event_type="workflow_run",
            action="completed",
            repository="test/repo",
            status="success"
        )
        assert handler.should_trigger_pipeline(event4) is False

    def test_get_affected_services(self, handler):
        """Test determining affected services from event."""
        from gateway.webhook import WebhookEvent

        event = WebhookEvent(
            event_type="push",
            repository="test/repo",
            branch="main",
            commit="abc123",
            changed_files=[
                "platform/agents/scenespeak/main.py",
                "tests/test_scenespeak.py"
            ]
        )

        services = handler.get_affected_services(event)
        assert "scenespeak-agent" in services


class TestWebhookLogger:
    """Test WebhookLogger class."""

    @pytest.fixture
    def logger_instance(self):
        """Create webhook logger."""
        from gateway.webhook import WebhookLogger
        return WebhookLogger()

    def test_log_event(self, logger_instance):
        """Test logging webhook event."""
        from gateway.webhook import WebhookEvent

        event = WebhookEvent(
            event_type="push",
            repository="test/repo",
            branch="main",
            commit="abc123"
        )

        log_id = logger_instance.log_event(event, payload={"test": "data"})
        assert log_id is not None

    def test_get_recent_events(self, logger_instance):
        """Test getting recent events."""
        from gateway.webhook import WebhookEvent

        for i in range(5):
            event = WebhookEvent(
                event_type="push",
                repository="test/repo",
                branch=f"branch{i}",
                commit=f"commit{i}"
            )
            logger_instance.log_event(event)

        recent = logger_instance.get_recent_events(limit=3)
        assert len(recent) == 3
