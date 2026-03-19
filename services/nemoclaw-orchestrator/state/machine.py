# services/nemoclaw-orchestrator/state/machine.py
"""Show state machine with Redis persistence for managing show lifecycles."""
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import asyncio


class ShowState(str, Enum):
    """States in the show lifecycle.

    Uses str enum for JSON serialization compatibility.
    """
    IDLE = "IDLE"
    PRELUDE = "PRELUDE"
    ACTIVE = "ACTIVE"
    POSTLUDE = "POSTLUDE"
    CLEANUP = "CLEANUP"


# Valid state transitions
TRANSITIONS: Dict[ShowState, list[ShowState]] = {
    ShowState.IDLE: [ShowState.PRELUDE],
    ShowState.PRELUDE: [ShowState.ACTIVE, ShowState.CLEANUP],
    ShowState.ACTIVE: [ShowState.POSTLUDE, ShowState.CLEANUP],
    ShowState.POSTLUDE: [ShowState.CLEANUP],
    ShowState.CLEANUP: [ShowState.IDLE],
}


class ShowStateMachine:
    """State machine for managing show states with Redis persistence.

    The state machine manages the lifecycle of a show through the following states:
    IDLE → PRELUDE → ACTIVE → POSTLUDE → CLEANUP → IDLE

    State transitions are validated against the TRANSITIONS dict and can be
    optionally persisted to a RedisStateStore for recovery.
    """

    def __init__(
        self,
        show_id: str,
        state_store: Optional["RedisStateStore"] = None,
    ):
        """Initialize the state machine.

        Args:
            show_id: Unique identifier for the show
            state_store: Optional RedisStateStore for persistence
        """
        self.show_id = show_id
        self.state_store = state_store
        self.current_state = ShowState.IDLE
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def _validate_transition(self, new_state: ShowState) -> None:
        """Validate that a state transition is allowed.

        Args:
            new_state: The target state

        Raises:
            ValueError: If the transition is not valid
        """
        allowed_states = TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed_states:
            raise ValueError(
                f"Cannot transition from {self.current_state.value} to {new_state.value}"
            )

    def _persist_state(self) -> None:
        """Persist current state to RedisStateStore if available."""
        if self.state_store:
            # Try to create a task if there's a running loop
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.state_store.save_state(self.show_id, self.to_dict()))
            except RuntimeError:
                # No running event loop - this is fine for tests
                # In production, this will be called from an async context
                pass

    def transition_to(self, new_state: ShowState) -> None:
        """Transition to a new state.

        Args:
            new_state: The target state

        Raises:
            ValueError: If the transition is not valid
        """
        self._validate_transition(new_state)
        self.current_state = new_state
        self.updated_at = datetime.now(timezone.utc)
        self._persist_state()

    def start(self) -> None:
        """Start the show by transitioning to PRELUDE state.

        Raises:
            ValueError: If not in IDLE state
        """
        if self.current_state != ShowState.IDLE:
            raise ValueError(
                f"Cannot start show from {self.current_state.value}, must be IDLE"
            )
        self.transition_to(ShowState.PRELUDE)

    def end(self) -> None:
        """End the show by transitioning to CLEANUP then IDLE.

        This method handles the complete shutdown sequence from any
        active state (PRELUDE, ACTIVE, POSTLUDE) to CLEANUP and finally IDLE.

        Raises:
            ValueError: If already in IDLE or CLEANUP state
        """
        if self.current_state in (ShowState.IDLE, ShowState.CLEANUP):
            raise ValueError(
                f"Cannot end show from {self.current_state.value}"
            )

        # Transition to CLEANUP
        self.transition_to(ShowState.CLEANUP)

        # Then transition to IDLE
        self.transition_to(ShowState.IDLE)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state machine to dictionary for serialization.

        Returns:
            Dictionary containing show_id, state, and timestamps
        """
        return {
            "show_id": self.show_id,
            "state": self.current_state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShowStateMachine":
        """Create a ShowStateMachine from a dictionary.

        Args:
            data: Dictionary containing show_id, state, and timestamps

        Returns:
            ShowStateMachine instance
        """
        machine = cls(show_id=data["show_id"])
        machine.current_state = ShowState(data["state"])
        machine.created_at = datetime.fromisoformat(data["created_at"])
        machine.updated_at = datetime.fromisoformat(data["updated_at"])
        return machine

    def get_state(self) -> Dict[str, Any]:
        """Get the current state as a dictionary.

        Returns:
            Dictionary containing current state information
        """
        return self.to_dict()

    def is_running(self) -> bool:
        """Check if the show is currently running.

        Returns:
            True if in ACTIVE state, False otherwise
        """
        return self.current_state == ShowState.ACTIVE

    def is_paused(self) -> bool:
        """Check if the show is paused.

        Returns:
            True if in PRELUDE or POSTLUDE state, False otherwise
        """
        return self.current_state in (ShowState.PRELUDE, ShowState.POSTLUDE)

    def is_ended(self) -> bool:
        """Check if the show has ended.

        Returns:
            True if in IDLE state, False otherwise
        """
        return self.current_state == ShowState.IDLE

