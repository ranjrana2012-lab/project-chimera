"""
Unit tests for Manual Transition Triggers.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import json

import sys
sys.path.insert(0, '.')

from core.scene_manager import SceneManager, SceneConfig, SceneState
from transitions.manual_triggers import (
    ManualTriggerConfig,
    ManualTrigger,
    ManualTransitionRequest,
    TransitionRequestValidator,
    TriggerState
)


class TestManualTransitionRequest:
    """Test ManualTransitionRequest dataclass."""

    def test_create_request(self):
        """Create transition request."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Manual operator transition",
            operator_id="operator-001"
        )

        assert request.source_scene_id == "scene-001"
        assert request.target_scene_id == "scene-002"
        assert request.transition_type == "fade"
        assert request.reason == "Manual operator transition"
        assert request.operator_id == "operator-001"

    def test_create_request_with_metadata(self):
        """Create request with metadata."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="cut",
            reason="Emergency transition",
            operator_id="operator-002",
            metadata={"urgency": "high"}
        )

        assert request.metadata == {"urgency": "high"}


class TestTransitionRequestValidator:
    """Test TransitionRequestValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return TransitionRequestValidator()

    def test_validate_valid_request(self, validator):
        """Validate valid transition request."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Test",
            operator_id="operator-001"
        )

        result = validator.validate(request)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_source_scene(self, validator):
        """Missing source scene ID."""
        request = ManualTransitionRequest(
            source_scene_id="",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Test",
            operator_id="operator-001"
        )

        result = validator.validate(request)

        assert result.is_valid is False
        assert any("source_scene_id" in e.lower() for e in result.errors)

    def test_validate_missing_target_scene(self, validator):
        """Missing target scene ID."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="",
            transition_type="fade",
            reason="Test",
            operator_id="operator-001"
        )

        result = validator.validate(request)

        assert result.is_valid is False
        assert any("target_scene_id" in e.lower() for e in result.errors)

    def test_validate_invalid_transition_type(self, validator):
        """Invalid transition type."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="invalid_type",
            reason="Test",
            operator_id="operator-001"
        )

        result = validator.validate(request)

        assert result.is_valid is False
        assert any("transition_type" in e.lower() for e in result.errors)

    def test_validate_same_source_and_target(self, validator):
        """Source and target scene IDs cannot be the same."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-001",
            transition_type="fade",
            reason="Test",
            operator_id="operator-001"
        )

        result = validator.validate(request)

        assert result.is_valid is False
        assert any("different" in e.lower() for e in result.errors)

    def test_validate_missing_operator_id(self, validator):
        """Missing operator ID."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Test",
            operator_id=""
        )

        result = validator.validate(request)

        assert result.is_valid is False
        assert any("operator_id" in e.lower() for e in result.errors)


class TestManualTriggerConfig:
    """Test ManualTriggerConfig dataclass."""

    def test_create_config(self):
        """Create trigger configuration."""
        request = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Test",
            operator_id="operator-001"
        )

        config = ManualTriggerConfig(
            trigger_id="mt-001",
            request=request,
            priority=80
        )

        assert config.trigger_id == "mt-001"
        assert config.request.source_scene_id == "scene-001"
        assert config.priority == 80


class TestManualTrigger:
    """Test ManualTrigger class."""

    @pytest.fixture
    def transition_request(self):
        """Create test request."""
        return ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Manual operator transition",
            operator_id="operator-001"
        )

    @pytest.fixture
    def config(self, transition_request):
        """Create test config."""
        return ManualTriggerConfig(
            trigger_id="mt-001",
            request=transition_request,
            priority=80
        )

    def test_create_trigger(self, config):
        """Create manual trigger."""
        trigger = ManualTrigger(config)

        assert trigger.trigger_id == "mt-001"
        assert trigger.state == TriggerState.ENABLED
        assert trigger.source_scene_id == "scene-001"
        assert trigger.target_scene_id == "scene-002"

    def test_approve_trigger(self, config):
        """Approve a manual trigger."""
        trigger = ManualTrigger(config)
        trigger.approve("operator-002")

        assert trigger.state == TriggerState.APPROVED
        assert trigger.approved_by == "operator-002"
        assert trigger.approved_at is not None

    def test_deny_trigger(self, config):
        """Deny a manual trigger."""
        trigger = ManualTrigger(config)
        trigger.deny("operator-002", "Not approved")

        assert trigger.state == TriggerState.DENIED
        assert trigger.denied_by == "operator-002"
        assert trigger.denial_reason == "Not approved"

    def test_fire_approved_trigger(self, config):
        """Fire an approved trigger."""
        trigger = ManualTrigger(config)
        trigger.approve("operator-002")
        trigger.fire()

        assert trigger.state == TriggerState.TRIGGERED
        assert trigger.triggered_at is not None

    def test_cannot_fire_unapproved_trigger(self, config):
        """Requesting operator can fire their unapproved request (auto-approves)."""
        trigger = ManualTrigger(config)

        # Requesting operator can fire their own request
        # This auto-approves the request
        trigger.fire()

        assert trigger.state == TriggerState.TRIGGERED
        assert trigger.approved_by == "operator-001"  # Auto-approved by requesting operator

    def test_complete_trigger(self, config):
        """Complete a trigger."""
        trigger = ManualTrigger(config)
        trigger.approve("operator-002")
        trigger.fire()
        trigger.complete()

        assert trigger.state == TriggerState.COMPLETE
        assert trigger.completed_at is not None

    def test_cancel_trigger(self, config):
        """Cancel a trigger."""
        trigger = ManualTrigger(config)
        trigger.cancel("Cancelled by operator")

        assert trigger.state == TriggerState.CANCELLED
        assert trigger.cancellation_reason == "Cancelled by operator"

    def test_get_transition_data(self, config):
        """Get transition data for execution."""
        trigger = ManualTrigger(config)

        data = trigger.get_transition_data()

        assert data["source_scene_id"] == "scene-001"
        assert data["target_scene_id"] == "scene-002"
        assert data["transition_type"] == "fade"
        assert data["operator_id"] == "operator-001"

    def test_is_authorized_operator(self, config):
        """Check if operator is authorized."""
        trigger = ManualTrigger(config)

        # Requesting operator is authorized
        assert trigger.is_authorized("operator-001")

        # Different operator is not authorized (without approval)
        assert trigger.is_authorized("operator-002") is False


class TestManualTriggerRegistry:
    """Test ManualTriggerRegistry."""

    @pytest.fixture
    def registry(self):
        """Create trigger registry."""
        from transitions.manual_triggers import ManualTriggerRegistry
        return ManualTriggerRegistry()

    @pytest.fixture
    def transition_request(self):
        """Create test request."""
        return ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Test",
            operator_id="operator-001"
        )

    def test_create_transition_request(self, registry, transition_request):
        """Create and register transition request."""
        trigger_id = registry.create_transition_request(transition_request)

        assert trigger_id is not None
        assert trigger_id.startswith("mt-")

        trigger = registry.get_trigger(trigger_id)
        assert trigger is not None
        assert trigger.source_scene_id == "scene-001"

    def test_get_nonexistent_trigger(self, registry):
        """Get non-existent trigger returns None."""
        trigger = registry.get_trigger("nonexistent")
        assert trigger is None

    def test_approve_request(self, registry, transition_request):
        """Approve a transition request."""
        trigger_id = registry.create_transition_request(transition_request)

        approved = registry.approve_request(trigger_id, "operator-002")

        assert approved is True

        trigger = registry.get_trigger(trigger_id)
        assert trigger.state == TriggerState.APPROVED

    def test_deny_request(self, registry, transition_request):
        """Deny a transition request."""
        trigger_id = registry.create_transition_request(transition_request)

        denied = registry.deny_request(trigger_id, "operator-002", "Not approved")

        assert denied is True

        trigger = registry.get_trigger(trigger_id)
        assert trigger.state == TriggerState.DENIED

    def test_get_pending_requests(self, registry):
        """Get all pending requests."""
        request1 = ManualTransitionRequest(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type="fade",
            reason="Test",
            operator_id="operator-001"
        )

        request2 = ManualTransitionRequest(
            source_scene_id="scene-002",
            target_scene_id="scene-003",
            transition_type="cut",
            reason="Test",
            operator_id="operator-001"
        )

        registry.create_transition_request(request1)
        registry.create_transition_request(request2)

        pending = registry.get_pending_requests()

        assert len(pending) == 2

    def test_cancel_request(self, registry, transition_request):
        """Cancel a transition request."""
        trigger_id = registry.create_transition_request(transition_request)

        cancelled = registry.cancel_request(trigger_id, "Cancelled by operator")

        assert cancelled is True

        trigger = registry.get_trigger(trigger_id)
        assert trigger.state == TriggerState.CANCELLED
