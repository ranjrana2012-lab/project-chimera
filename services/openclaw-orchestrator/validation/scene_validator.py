"""
Scene Validator - OpenClaw Orchestrator

Pre-transition validation for scene configurations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.scene_manager import (
    SceneManager,
    SceneState,
    SceneConfig,
    SceneValidationError as SceneManagerError
)


logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity of validation issues."""
    ERROR = "error"       # Must be fixed before proceeding
    WARNING = "warning"   # Should be reviewed but can proceed
    INFO = "info"         # Informational only


@dataclass
class ValidationIssue:
    """
    A validation issue found during scene validation.

    Attributes:
        severity: Issue severity (error, warning, info)
        code: Unique error code
        message: Human-readable message
        path: JSON path to problematic field
        suggestion: Suggested fix (if applicable)
    """
    severity: ValidationSeverity
    code: str
    message: str
    path: str = ""
    suggestion: Optional[str] = None

    def __repr__(self) -> str:
        return f"ValidationIssue({self.severity.value}: {self.code} - {self.message})"


@dataclass
class ValidationResult:
    """
    Result of scene validation.

    Attributes:
        is_valid: True if no errors found
        issues: List of all validation issues
        errors: Error-level issues only
        warnings: Warning-level issues only
    """
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def info(self) -> List[ValidationIssue]:
        """Get info-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.INFO]

    def add_error(
        self,
        code: str,
        message: str,
        path: str = "",
        suggestion: str = None
    ) -> None:
        """Add an error issue."""
        self.issues.append(ValidationIssue(
            ValidationSeverity.ERROR, code, message, path, suggestion
        ))
        self.is_valid = False

    def add_warning(
        self,
        code: str,
        message: str,
        path: str = "",
        suggestion: str = None
    ) -> None:
        """Add a warning issue."""
        self.issues.append(ValidationIssue(
            ValidationSeverity.WARNING, code, message, path, suggestion
        ))

    def add_info(
        self,
        code: str,
        message: str,
        path: str = ""
    ) -> None:
        """Add an info issue."""
        self.issues.append(ValidationIssue(
            ValidationSeverity.INFO, code, message, path
        ))

    def __repr__(self) -> str:
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        return f"ValidationResult(valid={self.is_valid}, errors={error_count}, warnings={warning_count})"


class SceneValidator:
    """
    Validates scene configurations before transitions.

    Features:
        - Schema validation
        - Agent configuration validation
        - Timing constraint validation
        - Transition prerequisite validation
        - Resource availability checking

    Usage:
        validator = SceneValidator()
        result = validator.validate_scene_config(config)
        if not result.is_valid:
            for error in result.errors:
                print(f"Error: {error.message}")
    """

    def __init__(self):
        """Initialize scene validator."""
        self._valid_scene_types = {
            "monologue", "dialogue", "interactive",
            "transition", "finale", "intermission"
        }
        self._valid_safety_policies = {
            "family", "teen", "adult", "unrestricted"
        }

    def validate_scene_config(self, config: SceneConfig) -> ValidationResult:
        """
        Validate a scene configuration.

        Args:
            config: SceneConfig to validate

        Returns:
            ValidationResult with all issues
        """
        result = ValidationResult(is_valid=True)

        # Basic fields
        self._validate_basic_fields(config, result)

        # Scene type
        self._validate_scene_type(config, result)

        # Timing constraints
        self._validate_timing(config, result)

        # Agent configurations
        self._validate_agents(config, result)

        # Safety settings
        self._validate_safety(config, result)

        # Accessibility settings
        self._validate_accessibility(config, result)

        # Resource requirements
        self._validate_resources(config, result)

        return result

    def validate_transition(
        self,
        manager: SceneManager,
        target_state: SceneState
    ) -> ValidationResult:
        """
        Validate that a state transition is allowed.

        Args:
            manager: SceneManager making the transition
            target_state: Desired target state

        Returns:
            ValidationResult with any issues
        """
        result = ValidationResult(is_valid=True)

        # Check if transition is valid
        if not manager.can_transition_to(target_state):
            result.add_error(
                "INVALID_TRANSITION",
                f"Cannot transition from {manager.state.value} to {target_state.value}",
                suggestion=f"Valid transitions from {manager.state.value}: " +
                          f"{[s.value for s in VALID_TRANSITIONS.get(manager.state, [])]}"
            )
            return result

        # State-specific validations
        if target_state == SceneState.ACTIVE:
            self._validate_activate(manager, result)
        elif target_state == SceneState.TRANSITION:
            self._validate_begin_transition(manager, result)
        elif target_state == SceneState.COMPLETED:
            self._validate_complete(manager, result)

        return result

    def _validate_basic_fields(
        self,
        config: SceneConfig,
        result: ValidationResult
    ) -> None:
        """Validate basic required fields."""
        if not config.scene_id or not config.scene_id.strip():
            result.add_error(
                "MISSING_SCENE_ID",
                "Scene ID is required",
                path="scene_id",
                suggestion="Provide a unique scene identifier"
            )

        if not config.name or not config.name.strip():
            result.add_error(
                "MISSING_NAME",
                "Scene name is required",
                path="name",
                suggestion="Provide a human-readable scene name"
            )

        if not config.version:
            result.add_warning(
                "MISSING_VERSION",
                "Scene version not specified",
                path="version",
                suggestion="Consider adding a version number"
            )

    def _validate_scene_type(
        self,
        config: SceneConfig,
        result: ValidationResult
    ) -> None:
        """Validate scene type."""
        if not config.scene_type:
            result.add_error(
                "MISSING_SCENE_TYPE",
                "Scene type is required",
                path="scene_type",
                suggestion=f"Valid types: {', '.join(sorted(self._valid_scene_types))}"
            )
            return

        if config.scene_type not in self._valid_scene_types:
            result.add_error(
                "INVALID_SCENE_TYPE",
                f"Invalid scene type: {config.scene_type}",
                path="scene_type",
                suggestion=f"Valid types: {', '.join(sorted(self._valid_scene_types))}"
            )

    def _validate_timing(
        self,
        config: SceneConfig,
        result: ValidationResult
    ) -> None:
        """Validate timing constraints."""
        timing = config.config.get("timing", {})

        min_duration = timing.get("min_duration")
        max_duration = timing.get("max_duration")

        if min_duration is not None and min_duration < 10:
            result.add_warning(
                "SHORT_MIN_DURATION",
                f"Minimum duration ({min_duration}s) is very short",
                path="timing.min_duration",
                suggestion="Consider a longer minimum duration for better user experience"
            )

        if max_duration is not None and max_duration > 7200:
            result.add_warning(
                "LONG_MAX_DURATION",
                f"Maximum duration ({max_duration}s) exceeds 2 hours",
                path="timing.max_duration",
                suggestion="Consider breaking into multiple scenes"
            )

        if min_duration and max_duration and min_duration > max_duration:
            result.add_error(
                "INVALID_DURATION_RANGE",
                f"Min duration ({min_duration}s) > max duration ({max_duration}s)",
                path="timing",
                suggestion="Ensure min_duration <= max_duration"
            )

        # Warn if auto_transition is on with very short duration
        auto_transition = timing.get("auto_transition", False)
        if auto_transition and max_duration and max_duration < 60:
            result.add_warning(
                "QUICK_AUTO_TRANSITION",
                "Auto-transition enabled with short max duration",
                path="timing.auto_transition",
                suggestion="Consider increasing max_duration or disabling auto-transition"
            )

    def _validate_agents(
        self,
        config: SceneConfig,
        result: ValidationResult
    ) -> None:
        """Validate agent configurations."""
        agents = config.config.get("agents", {})

        # Check required agents
        required_agents = ["scenespeak", "sentiment", "captioning"]
        for agent in required_agents:
            if agent not in agents:
                result.add_error(
                    "MISSING_AGENT",
                    f"Required agent '{agent}' not configured",
                    path=f"agents.{agent}",
                    suggestion=f"Add configuration for {agent} agent"
                )

        # Validate individual agent configs
        for agent_name, agent_config in agents.items():
            if not isinstance(agent_config, dict):
                result.add_error(
                    "INVALID_AGENT_CONFIG",
                    f"Agent '{agent_name}' configuration must be an object",
                    path=f"agents.{agent_name}"
                )
                continue

            # Check if enabled
            enabled = agent_config.get("enabled", True)
            if not enabled:
                result.add_info(
                    "AGENT_DISABLED",
                    f"Agent '{agent_name}' is disabled",
                    path=f"agents.{agent_name}.enabled"
                )

            # Validate timeout
            timeout = agent_config.get("timeout")
            if timeout is not None:
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    result.add_error(
                        "INVALID_TIMEOUT",
                        f"Invalid timeout for agent '{agent_name}': {timeout}",
                        path=f"agents.{agent_name}.timeout",
                        suggestion="Timeout must be a positive number (seconds)"
                    )
                elif timeout > 300:
                    result.add_warning(
                        "LONG_TIMEOUT",
                        f"Agent '{agent_name}' timeout ({timeout}s) is very long",
                        path=f"agents.{agent_name}.timeout",
                        suggestion="Consider reducing timeout for faster failure detection"
                    )

            # Validate temperature for ML agents
            if agent_name in ["scenespeak", "sentiment"]:
                temperature = agent_config.get("temperature")
                if temperature is not None:
                    if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2):
                        result.add_error(
                            "INVALID_TEMPERATURE",
                            f"Invalid temperature for agent '{agent_name}': {temperature}",
                            path=f"agents.{agent_name}.temperature",
                            suggestion="Temperature must be between 0 and 2"
                        )

    def _validate_safety(
        self,
        config: SceneConfig,
        result: ValidationResult
    ) -> None:
        """Validate safety settings."""
        safety = config.config.get("safety", {})

        policy = safety.get("content_policy")
        if policy:
            if policy not in self._valid_safety_policies:
                result.add_error(
                    "INVALID_SAFETY_POLICY",
                    f"Invalid safety policy: {policy}",
                    path="safety.content_policy",
                    suggestion=f"Valid policies: {', '.join(sorted(self._valid_safety_policies))}"
                )

        # Warn if moderation is disabled
        moderate_generated = safety.get("moderate_generated_content", True)
        moderate_audience = safety.get("moderate_audience_input", True)

        if not moderate_generated and policy == "family":
            result.add_error(
                "SAFETY_DISABLED_FOR_FAMILY",
                "Content moderation disabled for family-friendly scene",
                path="safety.moderate_generated_content",
                suggestion="Enable moderation for family policy"
            )

        if not moderate_audience:
            result.add_warning(
                "AUDIENCE_MODERATION_DISABLED",
                "Audience input moderation disabled",
                path="safety.moderate_audience_input",
                suggestion="Enable moderation to filter inappropriate user input"
            )

    def _validate_accessibility(
        self,
        config: SceneConfig,
        result: ValidationResult
    ) -> None:
        """Validate accessibility settings."""
        accessibility = config.config.get("accessibility", {})

        # Check if captioning or BSL is enabled for family scenes
        captioning = accessibility.get("captioning", {}).get("enabled", True)
        bsl = accessibility.get("bsl", {}).get("enabled", True)

        safety_policy = config.config.get("safety", {}).get("content_policy", "family")
        if safety_policy == "family" and not captioning and not bsl:
            result.add_warning(
                "NO_ACCESSIBILITY",
                "Family scene has no accessibility features enabled",
                path="accessibility",
                suggestion="Enable captioning or BSL for accessibility compliance"
            )

    def _validate_resources(
        self,
        config: SceneConfig,
        result: ValidationResult
    ) -> None:
        """Validate resource requirements."""
        resources = config.config.get("resources", {})

        cpu_limit = resources.get("cpu_limit")
        if cpu_limit:
            # Parse CPU limit (e.g., "500m", "2")
            if not self._is_valid_cpu_limit(cpu_limit):
                result.add_error(
                    "INVALID_CPU_LIMIT",
                    f"Invalid CPU limit format: {cpu_limit}",
                    path="resources.cpu_limit",
                    suggestion="Use format like '500m' (milli-cpu) or '2' (cores)"
                )

        memory_limit = resources.get("memory_limit")
        if memory_limit:
            if not self._is_valid_memory_limit(memory_limit):
                result.add_error(
                    "INVALID_MEMORY_LIMIT",
                    f"Invalid memory limit format: {memory_limit}",
                    path="resources.memory_limit",
                    suggestion="Use format like '512Mi' or '2Gi'"
                )

        priority = resources.get("priority")
        if priority is not None:
            if not isinstance(priority, int) or not (0 <= priority <= 100):
                result.add_error(
                    "INVALID_PRIORITY",
                    f"Invalid priority: {priority}",
                    path="resources.priority",
                    suggestion="Priority must be an integer between 0 and 100"
                )

    def _validate_activate(
        self,
        manager: SceneManager,
        result: ValidationResult
    ) -> None:
        """Validate prerequisites for activating scene."""
        # Check if scene is in LOADING state
        if manager.state != SceneState.LOADING:
            result.add_error(
                "INVALID_STATE_FOR_ACTIVATE",
                f"Scene must be in LOADING state to activate, currently {manager.state.value}",
                suggestion="Complete scene loading before activation"
            )

    def _validate_begin_transition(
        self,
        manager: SceneManager,
        result: ValidationResult
    ) -> None:
        """Validate prerequisites for beginning transition."""
        # Check if scene is active or paused
        if not manager.is_active:
            result.add_error(
                "INVALID_STATE_FOR_TRANSITION",
                f"Scene must be active to begin transition, currently {manager.state.value}",
                suggestion="Activate scene before beginning transition"
            )

    def _validate_complete(
        self,
        manager: SceneManager,
        result: ValidationResult
    ) -> None:
        """Validate prerequisites for completing scene."""
        # Check if scene has been active
        if manager.state == SceneState.IDLE:
            result.add_warning(
                "COMPLATING_NEVER_ACTIVATED",
                "Scene is being completed without ever being activated",
                suggestion="Activate scene before completing, or use error state if setup failed"
            )

    def _is_valid_cpu_limit(self, limit: str) -> bool:
        """Check if CPU limit format is valid."""
        if isinstance(limit, (int, float)):
            return limit > 0

        if not isinstance(limit, str):
            return False

        # Format: "500m" or "2"
        if limit.endswith("m"):
            try:
                return 0 < int(limit[:-1]) <= 4000  # Max 4 cores
            except ValueError:
                return False
        else:
            try:
                return 0 < float(limit) <= 64  # Max 64 cores
            except ValueError:
                return False

    def _is_valid_memory_limit(self, limit: str) -> bool:
        """Check if memory limit format is valid."""
        if not isinstance(limit, str):
            return False

        # Format: "512Mi" or "2Gi"
        if limit.endswith("Mi"):
            try:
                return 0 < int(limit[:-2])
            except ValueError:
                return False
        elif limit.endswith("Gi"):
            try:
                return 0 < int(limit[:-2])
            except ValueError:
                return False
        return False


# Valid transitions for validation
VALID_TRANSITIONS = {
    SceneState.IDLE: [SceneState.LOADING],
    SceneState.LOADING: [SceneState.ACTIVE, SceneState.ERROR],
    SceneState.ACTIVE: [SceneState.PAUSED, SceneState.TRANSITION,
                        SceneState.COMPLETED, SceneState.ERROR],
    SceneState.PAUSED: [SceneState.ACTIVE, SceneState.COMPLETED,
                        SceneState.ERROR],
    SceneState.TRANSITION: [SceneState.ACTIVE, SceneState.COMPLETED,
                           SceneState.ERROR],
    SceneState.ERROR: [SceneState.LOADING, SceneState.COMPLETED],
    SceneState.COMPLETED: [],
}


# Convenience functions

def validate_scene_config(config: SceneConfig) -> ValidationResult:
    """
    Validate a scene configuration.

    Args:
        config: SceneConfig to validate

    Returns:
        ValidationResult with any issues
    """
    validator = SceneValidator()
    return validator.validate_scene_config(config)


def validate_scene_file(filepath: str) -> ValidationResult:
    """
    Validate a scene configuration file.

    Args:
        filepath: Path to scene configuration JSON

    Returns:
        ValidationResult with any issues
    """
    import json
    from pathlib import Path

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        config = SceneConfig.from_dict(data)
        return validate_scene_config(config)
    except FileNotFoundError:
        result = ValidationResult(is_valid=False)
        result.add_error("FILE_NOT_FOUND", f"Scene file not found: {filepath}")
        return result
    except json.JSONDecodeError as e:
        result = ValidationResult(is_valid=False)
        result.add_error("INVALID_JSON", f"Invalid JSON in scene file: {e}")
        return result
