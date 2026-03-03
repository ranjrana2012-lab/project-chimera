"""
Unit tests for Scene Validator.
"""

import pytest
from datetime import datetime

import sys
sys.path.insert(0, '.')

from core.scene_manager import (
    SceneManager,
    SceneConfig,
    SceneState
)
from validation.scene_validator import (
    SceneValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    validate_scene_config,
    validate_scene_file
)


class TestValidationIssue:
    """Test ValidationIssue dataclass."""

    def test_create_error(self):
        """Create error issue."""
        issue = ValidationIssue(
            ValidationSeverity.ERROR,
            "TEST_ERROR",
            "Test error message",
            "/path/to/field",
            "Fix this"
        )

        assert issue.severity == ValidationSeverity.ERROR
        assert issue.code == "TEST_ERROR"
        assert issue.message == "Test error message"
        assert issue.path == "/path/to/field"
        assert issue.suggestion == "Fix this"

    def test_repr(self):
        """String representation."""
        issue = ValidationIssue(
            ValidationSeverity.WARNING,
            "WARN_001",
            "Warning message"
        )

        assert "warning" in repr(issue)
        assert "WARN_001" in repr(issue)


class TestValidationResult:
    """Test ValidationResult."""

    def test_valid_result(self):
        """Create valid result."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert len(result.issues) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error(self):
        """Add error to result."""
        result = ValidationResult(is_valid=True)

        result.add_error("ERR_001", "Error message", "/path", "Fix")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "ERR_001"

    def test_add_warning(self):
        """Add warning to result."""
        result = ValidationResult(is_valid=True)

        result.add_warning("WARN_001", "Warning message")

        assert result.is_valid is True  # Warnings don't invalidate
        assert len(result.warnings) == 1

    def test_add_info(self):
        """Add info to result."""
        result = ValidationResult(is_valid=True)

        result.add_info("INFO_001", "Info message")

        assert len(result.info) == 1

    def test_mixed_issues(self):
        """Result with mixed issues."""
        result = ValidationResult(is_valid=True)

        result.add_error("ERR_001", "Error")
        result.add_warning("WARN_001", "Warning")
        result.add_info("INFO_001", "Info")

        assert len(result.issues) == 3
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.info) == 1

    def test_repr(self):
        """String representation."""
        result = ValidationResult(is_valid=True)
        result.add_warning("WARN_001", "Warning")

        assert "valid=True" in repr(result)
        assert "warnings=1" in repr(result)


class TestSceneValidatorInit:
    """Test SceneValidator initialization."""

    def test_init(self):
        """Initialize validator."""
        validator = SceneValidator()

        assert validator._valid_scene_types == {
            "monologue", "dialogue", "interactive",
            "transition", "finale", "intermission"
        }
        assert validator._valid_safety_policies == {
            "family", "teen", "adult", "unrestricted"
        }


class TestBasicFieldValidation:
    """Test basic field validation."""

    @pytest.fixture
    def validator(self):
        return SceneValidator()

    @pytest.fixture
    def valid_config(self):
        """Create a valid scene config."""
        config = SceneConfig(
            scene_id="test",
            name="Test Scene",
            scene_type="dialogue",
            version="1.0.0"
        )
        # Add required agents config
        config.config = {
            "scene_id": "test",
            "name": "Test Scene",
            "scene_type": "dialogue",
            "version": "1.0.0",
            "agents": {
                "scenespeak": {"enabled": True},
                "sentiment": {"enabled": True},
                "captioning": {"enabled": True}
            }
        }
        return config

    def test_valid_config_passes(self, validator, valid_config):
        """Valid config passes validation."""
        result = validator.validate_scene_config(valid_config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_scene_id(self, validator, valid_config):
        """Missing scene_id causes error."""
        valid_config.scene_id = ""

        result = validator.validate_scene_config(valid_config)

        assert result.is_valid is False
        # Check for MISSING_SCENE_ID code
        assert any("MISSING_SCENE_ID" == e.code for e in result.errors)

    def test_missing_name(self, validator, valid_config):
        """Missing name causes error."""
        valid_config.name = ""

        result = validator.validate_scene_config(valid_config)

        assert result.is_valid is False
        # Check for MISSING_NAME code
        assert any("MISSING_NAME" == e.code for e in result.errors)

    def test_missing_version_warning(self, validator):
        """Missing version causes warning."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version=None
        )
        config.config = {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "dialogue",
            "agents": {
                "scenespeak": {"enabled": True},
                "sentiment": {"enabled": True},
                "captioning": {"enabled": True}
            }
        }

        result = validator.validate_scene_config(config)

        # Should have warning but still be valid
        assert len(result.warnings) > 0


class TestSceneTypeValidation:
    """Test scene type validation."""

    @pytest.fixture
    def validator(self):
        return SceneValidator()

    @pytest.fixture
    def base_config(self):
        """Create base config with required agents."""
        return {
            "scene_id": "test",
            "name": "Test",
            "version": "1.0.0",
            "agents": {
                "scenespeak": {"enabled": True},
                "sentiment": {"enabled": True},
                "captioning": {"enabled": True}
            }
        }

    def test_valid_scene_types(self, validator, base_config):
        """All valid scene types pass."""
        valid_types = ["monologue", "dialogue", "interactive",
                      "transition", "finale", "intermission"]

        for scene_type in valid_types:
            config_data = base_config.copy()
            config_data["scene_type"] = scene_type
            config_data["scene_id"] = f"test-{scene_type}"

            config = SceneConfig.from_dict(config_data)

            result = validator.validate_scene_config(config)

            # Should not have scene_type errors
            type_errors = [e for e in result.errors if "scene_type" in e.path]
            assert len(type_errors) == 0

    def test_invalid_scene_type(self, validator, base_config):
        """Invalid scene type causes error."""
        base_config["scene_type"] = "invalid_type"
        config = SceneConfig.from_dict(base_config)

        result = validator.validate_scene_config(config)

        assert result.is_valid is False
        assert any("scene_type" in e.path for e in result.errors)


class TestTimingValidation:
    """Test timing constraint validation."""

    @pytest.fixture
    def validator(self):
        return SceneValidator()

    @pytest.fixture
    def base_config(self):
        """Create base config with required agents."""
        return {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "dialogue",
            "version": "1.0.0",
            "agents": {
                "scenespeak": {"enabled": True},
                "sentiment": {"enabled": True},
                "captioning": {"enabled": True}
            }
        }

    def test_short_min_duration_warning(self, validator, base_config):
        """Very short min duration causes warning."""
        base_config["timing"] = {"min_duration": 5}
        config = SceneConfig.from_dict(base_config)

        result = validator.validate_scene_config(config)

        assert len(result.warnings) > 0
        assert any("min_duration" in w.path for w in result.warnings)

    def test_long_max_duration_warning(self, validator, base_config):
        """Very long max duration causes warning."""
        base_config["timing"] = {"max_duration": 10000}
        config = SceneConfig.from_dict(base_config)

        result = validator.validate_scene_config(config)

        assert len(result.warnings) > 0
        assert any("max_duration" in w.path for w in result.warnings)

    def test_invalid_duration_range(self, validator, base_config):
        """Min > max duration causes error."""
        base_config["timing"] = {
            "min_duration": 300,
            "max_duration": 60
        }
        config = SceneConfig.from_dict(base_config)

        result = validator.validate_scene_config(config)

        assert result.is_valid is False
        # Check for INVALID_DURATION_RANGE code
        assert any("INVALID_DURATION_RANGE" == e.code for e in result.errors)


class TestAgentValidation:
    """Test agent configuration validation."""

    @pytest.fixture
    def validator(self):
        return SceneValidator()

    def test_missing_required_agent(self, validator):
        """Missing required agent causes error."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["agents"] = {
            "scenespeak": {"enabled": True}
            # Missing sentiment, captioning
        }

        result = validator.validate_scene_config(config)

        assert result.is_valid is False
        assert any("sentiment" in e.message or "captioning" in e.message
                  for e in result.errors)

    def test_invalid_agent_config_type(self, validator):
        """Invalid agent config type causes error."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["agents"] = {
            "scenespeak": "not_a_dict"
        }

        result = validator.validate_scene_config(config)

        assert result.is_valid is False

    def test_invalid_timeout(self, validator):
        """Invalid timeout causes error."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["agents"] = {
            "scenespeak": {"enabled": True, "timeout": -1}
        }

        result = validator.validate_scene_config(config)

        assert any("timeout" in e.path for e in result.errors)

    def test_long_timeout_warning(self, validator):
        """Long timeout causes warning."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["agents"] = {
            "scenespeak": {"enabled": True, "timeout": 500}
        }

        result = validator.validate_scene_config(config)

        assert any("timeout" in w.path for w in result.warnings)

    def test_invalid_temperature(self, validator):
        """Invalid temperature causes error."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["agents"] = {
            "scenespeak": {"enabled": True, "temperature": 3.0}
        }

        result = validator.validate_scene_config(config)

        assert any("temperature" in e.path for e in result.errors)


class TestSafetyValidation:
    """Test safety settings validation."""

    @pytest.fixture
    def validator(self):
        return SceneValidator()

    @pytest.fixture
    def base_config(self):
        """Create base config with required agents."""
        return {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "dialogue",
            "version": "1.0.0",
            "agents": {
                "scenespeak": {"enabled": True},
                "sentiment": {"enabled": True},
                "captioning": {"enabled": True}
            }
        }

    def test_invalid_safety_policy(self, validator, base_config):
        """Invalid safety policy causes error."""
        base_config["safety"] = {
            "content_policy": "invalid_policy"
        }
        config = SceneConfig.from_dict(base_config)

        result = validator.validate_scene_config(config)

        # Check for INVALID_SAFETY_POLICY code
        assert any("INVALID_SAFETY_POLICY" == e.code for e in result.errors)

    def test_safety_disabled_for_family(self, validator, base_config):
        """Moderation disabled for family scene causes error."""
        base_config["safety"] = {
            "content_policy": "family",
            "moderate_generated_content": False
        }
        config = SceneConfig.from_dict(base_config)

        result = validator.validate_scene_config(config)

        # Check for SAFETY_DISABLED_FOR_FAMILY code
        assert any("SAFETY_DISABLED_FOR_FAMILY" == e.code for e in result.errors)


class TestTransitionValidation:
    """Test transition validation."""

    @pytest.fixture
    def validator(self):
        return SceneValidator()

    @pytest.fixture
    def manager(self):
        """Create test manager."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config = {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "dialogue",
            "version": "1.0.0",
            "agents": {
                "scenespeak": {"enabled": True},
                "sentiment": {"enabled": True},
                "captioning": {"enabled": True}
            }
        }
        return SceneManager(config)

    def test_valid_transition(self, validator, manager):
        """Valid transition passes."""
        manager.initialize()  # LOADING state

        result = validator.validate_transition(manager, SceneState.ACTIVE)

        assert result.is_valid is True

    def test_invalid_transition(self, validator, manager):
        """Invalid transition fails."""
        result = validator.validate_transition(manager, SceneState.COMPLETED)

        assert result.is_valid is False
        # Check for INVALID_TRANSITION code
        assert any("INVALID_TRANSITION" == e.code for e in result.errors)

    def test_activate_from_wrong_state(self, validator, manager):
        """Cannot activate from IDLE."""
        result = validator.validate_transition(manager, SceneState.ACTIVE)

        assert result.is_valid is False
        # Check for INVALID_TRANSITION code (wrong state triggers invalid transition)
        assert any("INVALID_TRANSITION" == e.code for e in result.errors)

    def test_transition_from_completed(self, validator, manager):
        """Cannot transition from COMPLETED."""
        # Force to completed
        manager._state = SceneState.COMPLETED

        result = validator.validate_transition(manager, SceneState.ACTIVE)

        assert result.is_valid is False


class TestResourceValidation:
    """Test resource requirement validation."""

    @pytest.fixture
    def validator(self):
        return SceneValidator()

    def test_invalid_cpu_format(self, validator):
        """Invalid CPU limit format causes error."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["resources"] = {
            "cpu_limit": "invalid"
        }

        result = validator.validate_scene_config(config)

        assert any("cpu_limit" in e.path for e in result.errors)

    def test_invalid_memory_format(self, validator):
        """Invalid memory limit format causes error."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["resources"] = {
            "memory_limit": "invalid"
        }

        result = validator.validate_scene_config(config)

        assert any("memory_limit" in e.path for e in result.errors)

    def test_invalid_priority(self, validator):
        """Invalid priority causes error."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config["resources"] = {
            "priority": 150
        }

        result = validator.validate_scene_config(config)

        assert any("priority" in e.path for e in result.errors)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_validate_scene_config(self):
        """Convenience function validates config."""
        config = SceneConfig(
            scene_id="test",
            name="Test",
            scene_type="dialogue",
            version="1.0.0"
        )
        config.config = {
            "scene_id": "test",
            "name": "Test",
            "scene_type": "dialogue",
            "version": "1.0.0",
            "agents": {
                "scenespeak": {"enabled": True},
                "sentiment": {"enabled": True},
                "captioning": {"enabled": True}
            }
        }

        result = validate_scene_config(config)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    def test_validate_scene_file_not_found(self):
        """Non-existent file returns error."""
        result = validate_scene_file("/nonexistent/file.json")

        assert result.is_valid is False
        # Check for FILE_NOT_FOUND code
        assert any("FILE_NOT_FOUND" == e.code for e in result.errors)
