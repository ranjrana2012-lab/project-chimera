"""
Manual Transition Triggers - OpenClaw Orchestrator

Provides operator-initiated manual transitions via API and Console.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


# Valid transition types
VALID_TRANSITION_TYPES = {"cut", "fade", "crossfade"}


@dataclass
class ManualTransitionRequest:
    """
    Request for manual scene transition.

    Attributes:
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        transition_type: Type of transition (cut, fade, crossfade)
        reason: Reason for transition
        operator_id: ID of requesting operator
        metadata: Additional request metadata
    """
    source_scene_id: str
    target_scene_id: str
    transition_type: str
    reason: str
    operator_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TriggerState(Enum):
    """States of a trigger."""
    ENABLED = "enabled"
    APPROVED = "approved"
    DENIED = "denied"
    TRIGGERED = "triggered"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add warning message."""
        self.warnings.append(message)


class TransitionRequestValidator:
    """Validates manual transition requests."""

    def validate(self, request: ManualTransitionRequest) -> ValidationResult:
        """
        Validate transition request.

        Args:
            request: Request to validate

        Returns:
            ValidationResult with any errors found
        """
        result = ValidationResult(is_valid=True)

        # Check source scene ID
        if not request.source_scene_id or not request.source_scene_id.strip():
            result.add_error("source_scene_id is required")

        # Check target scene ID
        if not request.target_scene_id or not request.target_scene_id.strip():
            result.add_error("target_scene_id is required")

        # Check source and target are different
        if (request.source_scene_id and request.target_scene_id and
            request.source_scene_id == request.target_scene_id):
            result.add_error("source_scene_id and target_scene_id must be different")

        # Check transition type
        if request.transition_type not in VALID_TRANSITION_TYPES:
            result.add_error(
                f"transition_type must be one of: {', '.join(VALID_TRANSITION_TYPES)}"
            )

        # Check operator ID
        if not request.operator_id or not request.operator_id.strip():
            result.add_error("operator_id is required")

        # Check reason
        if not request.reason or not request.reason.strip():
            result.add_warning("No reason provided for transition")

        return result


@dataclass
class ManualTriggerConfig:
    """
    Configuration for a manual trigger.

    Attributes:
        trigger_id: Unique trigger identifier
        request: Original transition request
        priority: Trigger priority (manual triggers default to high)
        requires_approval: Whether trigger requires approval
    """
    trigger_id: str
    request: ManualTransitionRequest
    priority: int = 80  # Manual triggers have high priority by default
    requires_approval: bool = False


class ManualTrigger:
    """
    A manual transition trigger initiated by an operator.

    Requires approval before execution unless operator is authorized.
    """

    def __init__(self, config: ManualTriggerConfig):
        """
        Initialize manual trigger.

        Args:
            config: Trigger configuration
        """
        self._config = config
        self._state = TriggerState.ENABLED
        self._approved_by: Optional[str] = None
        self._approved_at: Optional[datetime] = None
        self._denied_by: Optional[str] = None
        self._denied_reason: Optional[str] = None
        self._triggered_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._cancelled_by: Optional[str] = None
        self._cancellation_reason: Optional[str] = None

        logger.info(
            f"Created manual trigger {config.trigger_id} "
            f"from {config.request.source_scene_id} to {config.request.target_scene_id} "
            f"by operator {config.request.operator_id}"
        )

    @property
    def trigger_id(self) -> str:
        """Get trigger ID."""
        return self._config.trigger_id

    @property
    def state(self) -> TriggerState:
        """Get current state."""
        return self._state

    @property
    def source_scene_id(self) -> str:
        """Get source scene ID."""
        return self._config.request.source_scene_id

    @property
    def target_scene_id(self) -> str:
        """Get target scene ID."""
        return self._config.request.target_scene_id

    @property
    def transition_type(self) -> str:
        """Get transition type."""
        return self._config.request.transition_type

    @property
    def priority(self) -> int:
        """Get trigger priority."""
        return self._config.priority

    @property
    def operator_id(self) -> str:
        """Get requesting operator ID."""
        return self._config.request.operator_id

    @property
    def approved_by(self) -> Optional[str]:
        """Get operator who approved."""
        return self._approved_by

    @property
    def approved_at(self) -> Optional[datetime]:
        """Get approval timestamp."""
        return self._approved_at

    @property
    def denied_by(self) -> Optional[str]:
        """Get operator who denied."""
        return self._denied_by

    @property
    def denial_reason(self) -> Optional[str]:
        """Get denial reason."""
        return self._denied_reason

    @property
    def triggered_at(self) -> Optional[datetime]:
        """Get triggered timestamp."""
        return self._triggered_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get completed timestamp."""
        return self._completed_at

    @property
    def cancellation_reason(self) -> Optional[str]:
        """Get cancellation reason."""
        return self._cancellation_reason

    def is_authorized(self, operator_id: str) -> bool:
        """
        Check if operator is authorized to execute this trigger.

        Args:
            operator_id: Operator ID to check

        Returns:
            True if operator is authorized
        """
        # Requesting operator is always authorized for their own request
        if operator_id == self._config.request.operator_id:
            return True

        # Otherwise requires approval
        return self._state == TriggerState.APPROVED

    def approve(self, approver_id: str) -> None:
        """
        Approve the trigger for execution.

        Args:
            approver_id: ID of approving operator

        Raises:
            RuntimeError: If trigger is not in appropriate state
        """
        if self._state != TriggerState.ENABLED:
            raise RuntimeError(f"Cannot approve trigger in state {self._state.value}")

        self._state = TriggerState.APPROVED
        self._approved_by = approver_id
        self._approved_at = datetime.now(timezone.utc)

        logger.info(
            f"Trigger {self._config.trigger_id} approved by {approver_id}"
        )

    def deny(self, denier_id: str, reason: str) -> None:
        """
        Deny the trigger.

        Args:
            denier_id: ID of denying operator
            reason: Reason for denial

        Raises:
            RuntimeError: If trigger is not in appropriate state
        """
        if self._state != TriggerState.ENABLED:
            raise RuntimeError(f"Cannot deny trigger in state {self._state.value}")

        self._state = TriggerState.DENIED
        self._denied_by = denier_id
        self._denied_reason = reason

        logger.info(
            f"Trigger {self._config.trigger_id} denied by {denier_id}: {reason}"
        )

    def fire(self) -> None:
        """
        Fire the trigger.

        Raises:
            RuntimeError: If trigger is not approved
        """
        if self._state != TriggerState.APPROVED:
            # Check if requesting operator is firing their own request
            if self._config.request.operator_id == self.operator_id:
                # Auto-approve own request
                self.approve(self.operator_id)
            else:
                raise RuntimeError(
                    f"Cannot fire trigger in state {self._state.value}. "
                    f"Must be approved first."
                )

        self._state = TriggerState.TRIGGERED
        self._triggered_at = datetime.now(timezone.utc)

        logger.info(f"Fired manual trigger {self._config.trigger_id}")

    def complete(self) -> None:
        """Mark trigger as complete."""
        if self._state != TriggerState.TRIGGERED:
            raise RuntimeError(f"Cannot complete trigger in state {self._state.value}")

        self._state = TriggerState.COMPLETE
        self._completed_at = datetime.now(timezone.utc)

        logger.info(f"Completed manual trigger {self._config.trigger_id}")

    def cancel(self, reason: str, cancelled_by: Optional[str] = None) -> None:
        """
        Cancel the trigger.

        Args:
            reason: Reason for cancellation
            cancelled_by: Optional operator who cancelled
        """
        self._state = TriggerState.CANCELLED
        self._cancellation_reason = reason
        self._cancelled_by = cancelled_by

        logger.info(
            f"Cancelled manual trigger {self._config.trigger_id}: {reason}"
        )

    def get_transition_data(self) -> Dict[str, Any]:
        """
        Get transition data for execution.

        Returns:
            Dictionary with transition information
        """
        return {
            "source_scene_id": self._config.request.source_scene_id,
            "target_scene_id": self._config.request.target_scene_id,
            "transition_type": self._config.request.transition_type,
            "operator_id": self._config.request.operator_id,
            "reason": self._config.request.reason,
            "metadata": self._config.request.metadata,
            "triggered_at": self._triggered_at.isoformat() if self._triggered_at else None
        }


class ManualTriggerRegistry:
    """
    Registry for manual transition triggers.

    Manages the lifecycle of manual transition requests.
    """

    def __init__(self):
        """Initialize registry."""
        self._triggers: Dict[str, ManualTrigger] = {}
        self._validator = TransitionRequestValidator()

        logger.info("ManualTriggerRegistry initialized")

    def create_transition_request(
        self,
        request: ManualTransitionRequest
    ) -> str:
        """
        Create a new transition request.

        Args:
            request: Transition request

        Returns:
            Created trigger ID

        Raises:
            ValueError: If request validation fails
        """
        # Validate request
        result = self._validator.validate(request)
        if not result.is_valid:
            errors = ", ".join(result.errors)
            raise ValueError(f"Invalid transition request: {errors}")

        # Create trigger
        trigger_id = f"mt-{uuid.uuid4().hex[:8]}"
        config = ManualTriggerConfig(
            trigger_id=trigger_id,
            request=request
        )

        trigger = ManualTrigger(config)
        self._triggers[trigger_id] = trigger

        logger.info(f"Created manual transition request {trigger_id}")

        return trigger_id

    def get_trigger(self, trigger_id: str) -> Optional[ManualTrigger]:
        """
        Get trigger by ID.

        Args:
            trigger_id: Trigger ID

        Returns:
            ManualTrigger or None if not found
        """
        return self._triggers.get(trigger_id)

    def approve_request(
        self,
        trigger_id: str,
        approver_id: str
    ) -> bool:
        """
        Approve a transition request.

        Args:
            trigger_id: Trigger ID
            approver_id: Approving operator ID

        Returns:
            True if approved
        """
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            return False

        try:
            trigger.approve(approver_id)
            return True
        except RuntimeError:
            return False

    def deny_request(
        self,
        trigger_id: str,
        denier_id: str,
        reason: str
    ) -> bool:
        """
        Deny a transition request.

        Args:
            trigger_id: Trigger ID
            denier_id: Denying operator ID
            reason: Reason for denial

        Returns:
            True if denied
        """
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            return False

        try:
            trigger.deny(denier_id, reason)
            return True
        except RuntimeError:
            return False

    def cancel_request(
        self,
        trigger_id: str,
        reason: str,
        cancelled_by: Optional[str] = None
    ) -> bool:
        """
        Cancel a transition request.

        Args:
            trigger_id: Trigger ID
            reason: Cancellation reason
            cancelled_by: Operator who cancelled

        Returns:
            True if cancelled
        """
        trigger = self.get_trigger(trigger_id)
        if not trigger:
            return False

        trigger.cancel(reason, cancelled_by)
        return True

    def get_pending_requests(self) -> List[ManualTrigger]:
        """
        Get all pending transition requests.

        Returns:
            List of triggers awaiting approval
        """
        return [
            trigger for trigger in self._triggers.values()
            if trigger.state == TriggerState.ENABLED
        ]

    def get_all_requests(self) -> List[ManualTrigger]:
        """
        Get all transition requests.

        Returns:
            List of all triggers
        """
        return list(self._triggers.values())

    def remove_trigger(self, trigger_id: str) -> bool:
        """
        Remove a trigger from registry.

        Args:
            trigger_id: Trigger ID

        Returns:
            True if removed
        """
        if trigger_id in self._triggers:
            del self._triggers[trigger_id]
            logger.info(f"Removed manual trigger {trigger_id}")
            return True
        return False


# Global registry instance
_global_registry: Optional[ManualTriggerRegistry] = None


def get_registry() -> ManualTriggerRegistry:
    """Get global manual trigger registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ManualTriggerRegistry()
    return _global_registry


# Convenience functions

def create_manual_transition_request(
    source_scene_id: str,
    target_scene_id: str,
    transition_type: str,
    operator_id: str,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a manual transition request.

    Args:
        source_scene_id: Scene to transition from
        target_scene_id: Scene to transition to
        transition_type: Type of transition (cut, fade, crossfade)
        operator_id: Requesting operator ID
        reason: Optional reason for transition
        metadata: Optional metadata

    Returns:
        Created trigger ID

    Raises:
        ValueError: If request validation fails
    """
    request = ManualTransitionRequest(
        source_scene_id=source_scene_id,
        target_scene_id=target_scene_id,
        transition_type=transition_type,
        reason=reason or "Manual transition",
        operator_id=operator_id,
        metadata=metadata or {}
    )

    registry = get_registry()
    return registry.create_transition_request(request)


def approve_transition(trigger_id: str, approver_id: str) -> bool:
    """
    Approve a transition request.

    Args:
        trigger_id: Trigger ID
        approver_id: Approving operator ID

    Returns:
        True if approved
    """
    registry = get_registry()
    return registry.approve_request(trigger_id, approver_id)


def deny_transition(trigger_id: str, denier_id: str, reason: str) -> bool:
    """
    Deny a transition request.

    Args:
        trigger_id: Trigger ID
        denier_id: Denying operator ID
        reason: Reason for denial

    Returns:
        True if denied
    """
    registry = get_registry()
    return registry.deny_request(trigger_id, denier_id, reason)
