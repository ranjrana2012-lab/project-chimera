"""
Agent Handoff Logic - OpenClaw Orchestrator

Handles agent state transfer between scenes during transitions.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

from core.scene_manager import SceneManager, SceneState

logger = logging.getLogger(__name__)


class HandoffState(Enum):
    """States of an agent handoff."""
    PENDING = "pending"
    CAPTURING = "capturing"
    VALIDATING = "validating"
    TRANSFERRING = "transferring"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentStateSnapshot:
    """
    Snapshot of an agent's state.

    Captures the complete state of an agent for transfer between scenes.
    """
    agent_id: str
    agent_type: str
    state_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    serialized_at: Optional[str] = None

    def __post_init__(self):
        """Set serialization timestamp."""
        if self.serialized_at is None:
            self.serialized_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert snapshot to dictionary.

        Returns:
            Dictionary representation of snapshot
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state_data": self.state_data,
            "metadata": self.metadata,
            "serialized_at": self.serialized_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentStateSnapshot":
        """
        Create snapshot from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            AgentStateSnapshot instance
        """
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            state_data=data["state_data"],
            metadata=data.get("metadata", {}),
            serialized_at=data.get("serialized_at")
        )


@dataclass
class SnapshotValidationResult:
    """Result of snapshot validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class HandoffResult:
    """
    Result of an agent handoff operation.

    Contains details about the handoff execution.
    """
    agent_id: str
    source_scene_id: str
    target_scene_id: str
    success: bool
    transferred_bytes: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class AgentHandoffConfig:
    """
    Configuration for an agent handoff.

    Attributes:
        agent_id: ID of agent to handoff
        source_scene_id: Scene transferring from
        target_scene_id: Scene transferring to
        timeout_seconds: Timeout for handoff operations
        retry_attempts: Number of retry attempts on failure
    """
    agent_id: str
    source_scene_id: str
    target_scene_id: str
    timeout_seconds: float = 5.0
    retry_attempts: int = 3


class AgentHandoff:
    """
    Handles handoff of an agent between scenes.

    Manages the complete lifecycle of state transfer including
    capture, validation, transfer, and verification.
    """

    def __init__(
        self,
        config: AgentHandoffConfig,
        source_scene: SceneManager,
        target_scene: SceneManager
    ):
        """
        Initialize agent handoff.

        Args:
            config: Handoff configuration
            source_scene: Source scene manager
            target_scene: Target scene manager
        """
        self._config = config
        self._source_scene = source_scene
        self._target_scene = target_scene
        self._handoff_id = f"hho-{uuid.uuid4().hex[:8]}"
        self._state = HandoffState.PENDING
        self._snapshot: Optional[AgentStateSnapshot] = None
        self._result: Optional[HandoffResult] = None
        self._created_at = datetime.now(timezone.utc)
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._max_retries = config.retry_attempts
        self._current_retry = 0

        logger.info(
            f"Created agent handoff {self._handoff_id} for agent {config.agent_id} "
            f"from {config.source_scene_id} to {config.target_scene_id}"
        )

    @property
    def handoff_id(self) -> str:
        """Get handoff ID."""
        return self._handoff_id

    @property
    def state(self) -> HandoffState:
        """Get current handoff state."""
        return self._state

    @property
    def agent_id(self) -> str:
        """Get agent ID."""
        return self._config.agent_id

    def _capture_snapshot(self) -> AgentStateSnapshot:
        """
        Capture agent state from source scene.

        Returns:
            AgentStateSnapshot

        Raises:
            RuntimeError: If snapshot capture fails
        """
        self._state = HandoffState.CAPTURING

        try:
            # Get agent state from source scene
            state_data = self._source_scene._state_data.get("agent_states", {}).get(
                self._config.agent_id, {}
            )

            # Create snapshot
            snapshot = AgentStateSnapshot(
                agent_id=self._config.agent_id,
                agent_type=self._infer_agent_type(self._config.agent_id),
                state_data=state_data,
                metadata={
                    "source_scene": self._config.source_scene_id,
                    "captured_at": datetime.now(timezone.utc).isoformat()
                }
            )

            logger.info(
                f"Captured snapshot for agent {self._config.agent_id} "
                f"({len(json.dumps(state_data))} bytes)"
            )

            self._snapshot = snapshot
            return snapshot

        except Exception as e:
            self._state = HandoffState.FAILED
            raise RuntimeError(f"Failed to capture snapshot: {e}")

    def _infer_agent_type(self, agent_id: str) -> str:
        """
        Infer agent type from agent ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent type string
        """
        # Simple inference based on agent ID patterns
        agent_type_map = {
            "scenespeak": "llm",
            "captioning": "translation",
            "sentiment": "ml",
            "bsl": "translation",
            "lighting": "controller",
            "safety": "filter"
        }
        return agent_type_map.get(agent_id.lower(), "unknown")

    def _validate_snapshot(self, snapshot: AgentStateSnapshot) -> SnapshotValidationResult:
        """
        Validate snapshot for transfer.

        Args:
            snapshot: Snapshot to validate

        Returns:
            SnapshotValidationResult
        """
        self._state = HandoffState.VALIDATING

        errors = []

        # Check agent ID matches
        if snapshot.agent_id != self._config.agent_id:
            errors.append(
                f"Agent ID mismatch: expected {self._config.agent_id}, "
                f"got {snapshot.agent_id}"
            )

        # Check required fields exist
        required_fields = ["context"]
        for field_name in required_fields:
            if field_name not in snapshot.state_data:
                errors.append(f"Missing required field: {field_name}")

        # Validate snapshot is not empty
        if not snapshot.state_data:
            errors.append("Snapshot state_data is empty")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"Snapshot validation passed for {snapshot.agent_id}")
        else:
            logger.warning(f"Snapshot validation failed: {errors}")

        return SnapshotValidationResult(is_valid=is_valid, errors=errors)

    def _transfer_state(self, snapshot: AgentStateSnapshot) -> bool:
        """
        Transfer snapshot to target scene.

        Args:
            snapshot: Snapshot to transfer

        Returns:
            True if transfer successful

        Raises:
            RuntimeError: If transfer fails
        """
        self._state = HandoffState.TRANSFERRING

        try:
            # Initialize agent_states dict if not exists
            if "agent_states" not in self._target_scene._state_data:
                self._target_scene._state_data["agent_states"] = {}

            # Transfer snapshot data to target scene
            self._target_scene._state_data["agent_states"][self._config.agent_id] = (
                snapshot.state_data.copy()
            )

            transferred_bytes = len(json.dumps(snapshot.state_data))

            logger.info(
                f"Transferred state for agent {self._config.agent_id} "
                f"to scene {self._config.target_scene_id} "
                f"({transferred_bytes} bytes)"
            )

            return True

        except Exception as e:
            raise RuntimeError(f"Failed to transfer state: {e}")

    def execute(self) -> HandoffResult:
        """
        Execute the handoff with retry logic.

        Returns:
            HandoffResult

        Raises:
            RuntimeError: If max retries exceeded
        """
        self._started_at = datetime.now(timezone.utc)

        try:
            while self._current_retry <= self._max_retries:
                try:
                    # Capture snapshot
                    snapshot = self._capture_snapshot()

                    # Validate snapshot
                    validation = self._validate_snapshot(snapshot)
                    if not validation.is_valid:
                        self._state = HandoffState.FAILED
                        return HandoffResult(
                            agent_id=self._config.agent_id,
                            source_scene_id=self._config.source_scene_id,
                            target_scene_id=self._config.target_scene_id,
                            success=False,
                            error=f"Validation failed: {validation.errors}"
                        )

                    # Transfer state
                    if self._transfer_state(snapshot):
                        self._state = HandoffState.COMPLETE
                        self._completed_at = datetime.now(timezone.utc)
                        duration = (self._completed_at - self._started_at).total_seconds()

                        result = HandoffResult(
                            agent_id=self._config.agent_id,
                            source_scene_id=self._config.source_scene_id,
                            target_scene_id=self._config.target_scene_id,
                            success=True,
                            transferred_bytes=len(json.dumps(snapshot.state_data)),
                            duration_seconds=duration
                        )

                        self._result = result
                        return result

                except Exception as e:
                    self._current_retry += 1

                    if self._current_retry > self._max_retries:
                        self._state = HandoffState.FAILED
                        self._completed_at = datetime.now(timezone.utc)

                        error_msg = f"Max retries ({self._max_retries}) exceeded: {str(e)}"
                        logger.error(f"Handoff {self._handoff_id} failed: {error_msg}")

                        return HandoffResult(
                            agent_id=self._config.agent_id,
                            source_scene_id=self._config.source_scene_id,
                            target_scene_id=self._config.target_scene_id,
                            success=False,
                            error=error_msg
                        )

                    # Exponential backoff
                    backoff = 2 ** (self._current_retry - 1)
                    logger.info(f"Retry {self._current_retry}/{self._max_retries} after {backoff}s")
                    time.sleep(backoff)

        except Exception as e:
            self._state = HandoffState.FAILED
            return HandoffResult(
                agent_id=self._config.agent_id,
                source_scene_id=self._config.source_scene_id,
                target_scene_id=self._config.target_scene_id,
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

        # Should not reach here
        return HandoffResult(
            agent_id=self._config.agent_id,
            source_scene_id=self._config.source_scene_id,
            target_scene_id=self._config.target_scene_id,
            success=False,
            error="Unknown error"
        )

    def cancel(self, reason: str) -> None:
        """
        Cancel the handoff.

        Args:
            reason: Cancellation reason
        """
        if self._state == HandoffState.COMPLETE:
            raise RuntimeError("Cannot cancel completed handoff")

        self._state = HandoffState.CANCELLED
        self._completed_at = datetime.now(timezone.utc)

        logger.info(f"Cancelled handoff {self._handoff_id}: {reason}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get handoff status.

        Returns:
            Status dictionary
        """
        return {
            "handoff_id": self._handoff_id,
            "agent_id": self._config.agent_id,
            "source_scene_id": self._config.source_scene_id,
            "target_scene_id": self._config.target_scene_id,
            "state": self._state.value,
            "created_at": self._created_at.isoformat(),
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "current_retry": self._current_retry,
            "max_retries": self._max_retries
        }


class AgentHandoffOrchestrator:
    """
    Orchestrates multiple agent handoffs.

    Manages concurrent handoffs between scenes with tracking and cleanup.
    """

    def __init__(self):
        """Initialize orchestrator."""
        self._handoffs: Dict[str, AgentHandoff] = {}
        self._active_handoffs: Dict[str, AgentHandoff] = {}
        self._completed_handoffs: List[HandoffResult] = []

        logger.info("AgentHandoffOrchestrator initialized")

    def create_handoff(
        self,
        agent_id: str,
        source_scene_id: str,
        target_scene_id: str,
        source_scene: SceneManager,
        target_scene: SceneManager,
        timeout_seconds: float = 5.0,
        retry_attempts: int = 3
    ) -> str:
        """
        Create a new handoff.

        Args:
            agent_id: Agent to handoff
            source_scene_id: Source scene ID
            target_scene_id: Target scene ID
            source_scene: Source scene manager
            target_scene: Target scene manager
            timeout_seconds: Operation timeout
            retry_attempts: Retry attempts on failure

        Returns:
            Handoff ID
        """
        config = AgentHandoffConfig(
            agent_id=agent_id,
            source_scene_id=source_scene_id,
            target_scene_id=target_scene_id,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts
        )

        handoff = AgentHandoff(config, source_scene, target_scene)
        self._handoffs[handoff.handoff_id] = handoff
        self._active_handoffs[handoff.handoff_id] = handoff

        logger.info(f"Created handoff {handoff.handoff_id} for agent {agent_id}")

        return handoff.handoff_id

    def execute_all(self) -> List[HandoffResult]:
        """
        Execute all active handoffs.

        Returns:
            List of handoff results
        """
        results = []
        handoff_ids = list(self._active_handoffs.keys())

        logger.info(f"Executing {len(handoff_ids)} handoffs")

        for handoff_id in handoff_ids:
            handoff = self._active_handoffs.get(handoff_id)
            if handoff:
                try:
                    result = handoff.execute()
                    results.append(result)
                    self._completed_handoffs.append(result)

                    # Remove from active
                    if handoff_id in self._active_handoffs:
                        del self._active_handoffs[handoff_id]

                except Exception as e:
                    logger.error(f"Error executing handoff {handoff_id}: {e}")
                    results.append(HandoffResult(
                        agent_id=handoff.agent_id,
                        source_scene_id=handoff._config.source_scene_id,
                        target_scene_id=handoff._config.target_scene_id,
                        success=False,
                        error=str(e)
                    ))

        return results

    def cancel_handoff(self, handoff_id: str, reason: str) -> bool:
        """
        Cancel a handoff.

        Args:
            handoff_id: Handoff to cancel
            reason: Cancellation reason

        Returns:
            True if cancelled
        """
        handoff = self._active_handoffs.get(handoff_id)
        if not handoff:
            return False

        try:
            handoff.cancel(reason)
            if handoff_id in self._active_handoffs:
                del self._active_handoffs[handoff_id]
            return True
        except Exception as e:
            logger.error(f"Error cancelling handoff {handoff_id}: {e}")
            return False

    def get_handoff_status(self, handoff_id: str) -> Optional[Dict[str, Any]]:
        """
        Get handoff status.

        Args:
            handoff_id: Handoff ID

        Returns:
            Status dict or None if not found
        """
        handoff = self._handoffs.get(handoff_id)
        if not handoff:
            return None
        return handoff.get_status()

    def cleanup_completed_handoffs(self, max_age_seconds: float = 3600) -> int:
        """
        Cleanup old completed handoffs.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of handoffs cleaned up
        """
        now = datetime.now(timezone.utc)
        cleaned = 0

        handoffs_to_remove = []

        for handoff_id, handoff in self._handoffs.items():
            if handoff.state != HandoffState.COMPLETE:
                continue

            if handoff._completed_at:
                age = (now - handoff._completed_at).total_seconds()
                if age > max_age_seconds:
                    handoffs_to_remove.append(handoff_id)

        for handoff_id in handoffs_to_remove:
            del self._handoffs[handoff_id]
            cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old handoffs")

        return cleaned

    def get_handoff_history(self) -> List[Dict[str, Any]]:
        """
        Get handoff history.

        Returns:
            List of completed handoff results
        """
        return [
            {
                "agent_id": r.agent_id,
                "source_scene_id": r.source_scene_id,
                "target_scene_id": r.target_scene_id,
                "success": r.success,
                "transferred_bytes": r.transferred_bytes,
                "duration_seconds": r.duration_seconds,
                "error": r.error
            }
            for r in self._completed_handoffs
        ]

    def get_active_handoffs(self) -> List[Dict[str, Any]]:
        """
        Get all active handoffs.

        Returns:
            List of active handoff statuses
        """
        return [
            handoff.get_status()
            for handoff in self._active_handoffs.values()
        ]
