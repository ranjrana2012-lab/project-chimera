"""
Scene State Manager - OpenClaw Orchestrator

Implements the scene state machine for Project Chimera.
Manages scene lifecycle, state transitions, and validation.
"""

import threading
import logging
from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
import json


logger = logging.getLogger(__name__)


class SceneState(Enum):
    """
    Scene states as defined in the state machine.

    States:
        IDLE: Scene created but not loaded
        LOADING: Scene resources are being loaded
        ACTIVE: Scene is live and processing
        PAUSED: Scene is temporarily suspended
        TRANSITION: Scene is transitioning to another
        COMPLETED: Scene has finished successfully
        ERROR: Scene encountered an error
    """
    IDLE = "idle"
    LOADING = "loading"
    ACTIVE = "active"
    PAUSED = "paused"
    TRANSITION = "transition"
    COMPLETED = "completed"
    ERROR = "error"

    def __str__(self) -> str:
        return self.value

    # Terminal states (cannot transition from)
    @property
    def is_terminal(self) -> bool:
        return self in (SceneState.COMPLETED,)

    # Active states (scene is running)
    @property
    def is_active(self) -> bool:
        return self in (SceneState.ACTIVE, SceneState.PAUSED, SceneState.TRANSITION)

    # Transitional states (moving to/from active)
    @property
    def is_transitional(self) -> bool:
        return self in (SceneState.LOADING, SceneState.TRANSITION, SceneState.ERROR)


class SceneStateError(Exception):
    """Base exception for scene state errors."""
    pass


class InvalidTransitionError(SceneStateError):
    """Raised when an invalid state transition is attempted."""
    def __init__(self, current_state: SceneState, target_state: SceneState):
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            f"Invalid transition: {current_state.value} -> {target_state.value}"
        )


class SceneValidationError(SceneStateError):
    """Raised when scene validation fails."""
    pass


@dataclass
class SceneConfig:
    """
    Scene configuration.

    Attributes:
        scene_id: Unique scene identifier
        name: Human-readable scene name
        scene_type: Type of scene (monologue, dialogue, etc.)
        version: Configuration version
        config: Full configuration dictionary
    """
    scene_id: str
    name: str
    scene_type: str
    version: str
    config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneConfig":
        """Create SceneConfig from dictionary.

        Raises:
            SceneValidationError: If required fields are missing
        """
        required_fields = ["scene_id", "name", "scene_type", "version"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise SceneValidationError(
                f"Missing required fields: {', '.join(missing)}"
            )

        return cls(
            scene_id=data["scene_id"],
            name=data["name"],
            scene_type=data["scene_type"],
            version=data["version"],
            config=data
        )

    @classmethod
    def from_file(cls, filepath: Path) -> "SceneConfig":
        """Load SceneConfig from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class StateTransition:
    """
    Record of a state transition.

    Attributes:
        from_state: Previous state
        to_state: New state
        timestamp: When the transition occurred
        trigger: What caused the transition
        metadata: Additional transition data
    """
    from_state: SceneState
    to_state: SceneState
    timestamp: datetime
    trigger: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# Valid state transitions as defined in state machine
VALID_TRANSITIONS: Dict[SceneState, List[SceneState]] = {
    SceneState.IDLE: [SceneState.LOADING],
    SceneState.LOADING: [SceneState.ACTIVE, SceneState.ERROR],
    SceneState.ACTIVE: [SceneState.PAUSED, SceneState.TRANSITION,
                        SceneState.COMPLETED, SceneState.ERROR],
    SceneState.PAUSED: [SceneState.ACTIVE, SceneState.COMPLETED,
                        SceneState.ERROR],
    SceneState.TRANSITION: [SceneState.ACTIVE, SceneState.COMPLETED,
                           SceneState.ERROR],
    SceneState.ERROR: [SceneState.LOADING, SceneState.COMPLETED],
    SceneState.COMPLETED: [],  # Terminal state
}


class SceneManager:
    """
    Manages scene state and transitions.

    Features:
        - Thread-safe state management
        - State validation
        - Transition callbacks
        - State history tracking
        - Error recovery support

    Usage:
        manager = SceneManager(config)
        manager.initialize()
        manager.activate()
        manager.pause()
        manager.resume()
        manager.complete()
    """

    def __init__(self, config: SceneConfig):
        """
        Initialize scene manager.

        Args:
            config: Scene configuration
        """
        self._config = config
        self._state = SceneState.IDLE
        self._state_lock = threading.RLock()
        self._transition_history: List[StateTransition] = []
        self._state_callbacks: Dict[SceneState, List[Callable]] = {
            state: [] for state in SceneState
        }
        self._transition_callbacks: List[Callable] = []

        # State-specific data
        self._state_data: Dict[str, Any] = {
            "created_at": datetime.now(timezone.utc),
            "activated_at": None,
            "paused_at": None,
            "error": None,
            "retry_count": 0,
        }

        logger.info(
            f"SceneManager initialized for scene {config.scene_id} "
            f"({config.name}) in IDLE state"
        )

    @property
    def config(self) -> SceneConfig:
        """Get scene configuration."""
        return self._config

    @property
    def state(self) -> SceneState:
        """Get current state (thread-safe)."""
        with self._state_lock:
            return self._state

    @property
    def scene_id(self) -> str:
        """Get scene ID."""
        return self._config.scene_id

    @property
    def is_active(self) -> bool:
        """Check if scene is in an active state."""
        return self.state.is_active

    @property
    def is_terminal(self) -> bool:
        """Check if scene is in a terminal state."""
        return self.state.is_terminal

    def get_state_data(self, key: str, default: Any = None) -> Any:
        """
        Get state-specific data.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            State data value
        """
        return self._state_data.get(key, default)

    def set_state_data(self, key: str, value: Any) -> None:
        """
        Set state-specific data.

        Args:
            key: Data key
            value: Data value
        """
        self._state_data[key] = value

    def register_callback(self, state: SceneState, callback: Callable) -> None:
        """
        Register a callback for when a state is entered.

        Args:
            state: State to watch
            callback: Callback function(scene_manager)
        """
        with self._state_lock:
            self._state_callbacks[state].append(callback)

    def register_transition_callback(self, callback: Callable) -> None:
        """
        Register a callback for any state transition.

        Args:
            callback: Callback function(transition)
        """
        with self._state_lock:
            self._transition_callbacks.append(callback)

    def can_transition_to(self, target_state: SceneState) -> bool:
        """
        Check if transition to target state is valid.

        Args:
            target_state: Desired target state

        Returns:
            True if transition is valid
        """
        with self._state_lock:
            return target_state in VALID_TRANSITIONS.get(self._state, [])

    def _validate_transition(self, target_state: SceneState) -> None:
        """
        Validate state transition.

        Args:
            target_state: Desired target state

        Raises:
            InvalidTransitionError: If transition is invalid
        """
        if not self.can_transition_to(target_state):
            raise InvalidTransitionError(self._state, target_state)

    def _transition_to(self, target_state: SceneState,
                      trigger: str, metadata: Dict[str, Any] = None) -> None:
        """
        Perform state transition (internal method).

        Args:
            target_state: Target state
            trigger: What triggered the transition
            metadata: Additional transition data
        """
        with self._state_lock:
            from_state = self._state

            # Record transition
            transition = StateTransition(
                from_state=from_state,
                to_state=target_state,
                timestamp=datetime.now(timezone.utc),
                trigger=trigger,
                metadata=metadata or {}
            )
            self._transition_history.append(transition)

            # Update state
            logger.info(
                f"Scene {self.scene_id}: {from_state.value} -> {target_state.value} "
                f"(trigger: {trigger})"
            )
            self._state = target_state

            # Update state data
            if target_state == SceneState.ACTIVE:
                self._state_data["activated_at"] = datetime.now(timezone.utc)
            elif target_state == SceneState.PAUSED:
                self._state_data["paused_at"] = datetime.now(timezone.utc)

            # Call transition callbacks
            for callback in self._transition_callbacks:
                try:
                    callback(transition)
                except Exception as e:
                    logger.error(f"Transition callback error: {e}")

            # Call state entry callbacks
            for callback in self._state_callbacks[target_state]:
                try:
                    callback(self)
                except Exception as e:
                    logger.error(f"State callback error: {e}")

    # --- State transition methods ---

    def initialize(self) -> None:
        """
        Initialize scene (IDLE -> LOADING).

        Raises:
            InvalidTransitionError: If current state is not IDLE
            SceneValidationError: If configuration is invalid
        """
        self._validate_transition(SceneState.LOADING)

        # Validate configuration
        self._validate_config()

        # Transition to LOADING
        self._transition_to(SceneState.LOADING, "initialize")

    def activate(self) -> None:
        """
        Activate scene (LOADING -> ACTIVE).

        Raises:
            InvalidTransitionError: If current state is not LOADING
        """
        self._validate_transition(SceneState.ACTIVE)
        self._transition_to(SceneState.ACTIVE, "activate")

    def pause(self, reason: str = "") -> None:
        """
        Pause scene (ACTIVE -> PAUSED).

        Args:
            reason: Reason for pausing

        Raises:
            InvalidTransitionError: If current state is not ACTIVE
        """
        self._validate_transition(SceneState.PAUSED)
        self._transition_to(
            SceneState.PAUSED,
            "pause",
            metadata={"reason": reason}
        )

    def resume(self) -> None:
        """
        Resume scene (PAUSED -> ACTIVE).

        Raises:
            InvalidTransitionError: If current state is not PAUSED
        """
        self._validate_transition(SceneState.ACTIVE)
        self._transition_to(SceneState.ACTIVE, "resume")

    def begin_transition(self, target_scene_id: str,
                        transition_type: str = "cut") -> None:
        """
        Begin scene transition (ACTIVE -> TRANSITION).

        Args:
            target_scene_id: Destination scene
            transition_type: Type of transition (cut, fade, crossfade)

        Raises:
            InvalidTransitionError: If current state is not ACTIVE/PAUSED
        """
        # Can transition from ACTIVE or PAUSED
        if self._state not in (SceneState.ACTIVE, SceneState.PAUSED):
            raise InvalidTransitionError(self._state, SceneState.TRANSITION)

        self._transition_to(
            SceneState.TRANSITION,
            "begin_transition",
            metadata={
                "target_scene_id": target_scene_id,
                "transition_type": transition_type
            }
        )

    def complete(self, reason: str = "natural") -> None:
        """
        Complete scene (ACTIVE/PAUSED/ERROR -> COMPLETED).

        Args:
            reason: Reason for completion

        Raises:
            InvalidTransitionError: If current state cannot transition to COMPLETED
        """
        self._validate_transition(SceneState.COMPLETED)
        self._transition_to(
            SceneState.COMPLETED,
            "complete",
            metadata={"reason": reason}
        )

    def error(self, error_code: str, error_message: str,
             recoverable: bool = True) -> None:
        """
        Enter error state.

        Args:
            error_code: Error code (e.g., "E001")
            error_message: Human-readable error message
            recoverable: Whether error is recoverable

        Raises:
            InvalidTransitionError: If already in terminal state
        """
        # Can error from any state except COMPLETED
        if self._state == SceneState.COMPLETED:
            raise InvalidTransitionError(self._state, SceneState.ERROR)

        self._state_data["error"] = {
            "code": error_code,
            "message": error_message,
            "recoverable": recoverable,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self._transition_to(
            SceneState.ERROR,
            "error",
            metadata={
                "error_code": error_code,
                "recoverable": recoverable
            }
        )

    def recover(self) -> None:
        """
        Attempt recovery from error (ERROR -> LOADING).

        Raises:
            InvalidTransitionError: If not in ERROR state or not recoverable
        """
        self._validate_transition(SceneState.LOADING)

        error_info = self._state_data.get("error", {})
        if not error_info.get("recoverable", True):
            raise SceneStateError("Error is not recoverable")

        # Increment retry count
        self._state_data["retry_count"] += 1

        self._transition_to(SceneState.LOADING, "recover")

    def get_transition_history(self) -> List[StateTransition]:
        """
        Get state transition history.

        Returns:
            List of transitions in chronological order
        """
        with self._state_lock:
            return list(self._transition_history)

    def _validate_config(self) -> None:
        """
        Validate scene configuration.

        Raises:
            SceneValidationError: If configuration is invalid
        """
        required_fields = ["scene_id", "name", "version", "scene_type"]
        for field in required_fields:
            if not hasattr(self._config, field) or not getattr(self._config, field):
                raise SceneValidationError(
                    f"Missing required field: {field}"
                )

        # Validate scene type
        valid_types = ["monologue", "dialogue", "interactive",
                      "transition", "finale", "intermission"]
        if self._config.scene_type not in valid_types:
            raise SceneValidationError(
                f"Invalid scene_type: {self._config.scene_type}. "
                f"Must be one of {valid_types}"
            )

        logger.debug(f"Scene {self.scene_id} configuration validated")

    def __repr__(self) -> str:
        return (
            f"SceneManager(id={self.scene_id}, "
            f"name={self._config.name}, "
            f"state={self._state.value})"
        )


# Convenience functions

def create_scene_from_file(filepath: Path) -> SceneManager:
    """
    Create a scene manager from a configuration file.

    Args:
        filepath: Path to scene configuration JSON

    Returns:
        Initialized SceneManager in IDLE state

    Raises:
        SceneValidationError: If configuration is invalid
    """
    config = SceneConfig.from_file(filepath)
    return SceneManager(config)


def create_scene_from_dict(config_dict: Dict[str, Any]) -> SceneManager:
    """
    Create a scene manager from a configuration dictionary.

    Args:
        config_dict: Scene configuration dictionary

    Returns:
        Initialized SceneManager in IDLE state

    Raises:
        SceneValidationError: If configuration is invalid
    """
    config = SceneConfig.from_dict(config_dict)
    return SceneManager(config)
