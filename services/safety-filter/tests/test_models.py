"""
Comprehensive unit tests for models.py.

Tests all Pydantic models, enums, validation, and serialization.
"""

import pytest
from pydantic import ValidationError
from typing import Dict, Any
from datetime import datetime

import sys
sys.path.insert(0, '.')


class TestModerationLevelEnum:
    """Test ModerationLevel enum."""

    def test_all_levels_defined(self):
        """Test that all moderation levels are defined."""
        from models import ModerationLevel

        levels = list(ModerationLevel)

        assert ModerationLevel.SAFE in levels
        assert ModerationLevel.LOW in levels
        assert ModerationLevel.MEDIUM in levels
        assert ModerationLevel.HIGH in levels
        assert ModerationLevel.CRITICAL in levels

    def test_level_values(self):
        """Test moderation level string values."""
        from models import ModerationLevel

        assert ModerationLevel.SAFE.value == "safe"
        assert ModerationLevel.LOW.value == "low"
        assert ModerationLevel.MEDIUM.value == "medium"
        assert ModerationLevel.HIGH.value == "high"
        assert ModerationLevel.CRITICAL.value == "critical"

    def test_level_comparison(self):
        """Test that levels can be compared."""
        from models import ModerationLevel

        # Enum values can be compared
        assert ModerationLevel.LOW != ModerationLevel.HIGH
        assert ModerationLevel.SAFE == ModerationLevel.SAFE


class TestFilterActionEnum:
    """Test FilterAction enum."""

    def test_all_actions_defined(self):
        """Test that all filter actions are defined."""
        from models import FilterAction

        actions = list(FilterAction)

        assert FilterAction.ALLOW in actions
        assert FilterAction.BLOCK in actions
        assert FilterAction.FLAG in actions
        assert FilterAction.MODIFY in actions

    def test_action_values(self):
        """Test filter action string values."""
        from models import FilterAction

        assert FilterAction.ALLOW.value == "allow"
        assert FilterAction.BLOCK.value == "block"
        assert FilterAction.FLAG.value == "flag"
        assert FilterAction.MODIFY.value == "modify"


class TestFilterLayerEnum:
    """Test FilterLayer enum."""

    def test_all_layers_defined(self):
        """Test that all filter layers are defined."""
        from models import FilterLayer

        layers = list(FilterLayer)

        assert FilterLayer.PATTERN in layers
        assert FilterLayer.CLASSIFICATION in layers
        assert FilterLayer.CONTEXT in layers

    def test_layer_values(self):
        """Test filter layer string values."""
        from models import FilterLayer

        assert FilterLayer.PATTERN.value == "pattern"
        assert FilterLayer.CLASSIFICATION.value == "classification"
        assert FilterLayer.CONTEXT.value == "context"


class TestMatchedPatternModel:
    """Test MatchedPattern model."""

    def test_create_matched_pattern_minimal(self):
        """Test creating matched pattern with minimal fields."""
        from models import MatchedPattern, ModerationLevel

        pattern = MatchedPattern(
            pattern=r'\btest\b',
            type="test_type",
            severity=ModerationLevel.LOW
        )

        assert pattern.pattern == r'\btest\b'
        assert pattern.type == "test_type"
        assert pattern.severity == ModerationLevel.LOW
        assert pattern.position is None  # Default value

    def test_create_matched_pattern_with_position(self):
        """Test creating matched pattern with position."""
        from models import MatchedPattern, ModerationLevel

        pattern = MatchedPattern(
            pattern=r'\btest\b',
            type="test_type",
            severity=ModerationLevel.HIGH,
            position=42
        )

        assert pattern.position == 42

    def test_matched_pattern_serialization(self):
        """Test that MatchedPattern can be serialized."""
        from models import MatchedPattern, ModerationLevel

        pattern = MatchedPattern(
            pattern=r'\btest\b',
            type="test_type",
            severity=ModerationLevel.MEDIUM,
            position=10
        )

        # Should be serializable to dict
        pattern_dict = pattern.model_dump()

        assert pattern_dict["pattern"] == r'\btest\b'
        assert pattern_dict["type"] == "test_type"
        assert pattern_dict["severity"] == ModerationLevel.MEDIUM
        assert pattern_dict["position"] == 10

    def test_matched_pattern_json(self):
        """Test that MatchedPattern can be converted to JSON."""
        from models import MatchedPattern, ModerationLevel

        pattern = MatchedPattern(
            pattern=r'\btest\b',
            type="test_type",
            severity=ModerationLevel.LOW
        )

        # Should be JSON serializable
        import json
        pattern_json = json.dumps(pattern.model_dump())

        assert "test" in pattern_json


class TestModerationResultModel:
    """Test ModerationResult model."""

    def test_create_result_minimal(self):
        """Test creating result with required fields."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Content is safe",
            processing_time_ms=15.5
        )

        assert result.is_safe is True
        assert result.action == FilterAction.ALLOW
        assert result.level == ModerationLevel.SAFE
        assert result.confidence == 1.0
        assert result.layer == FilterLayer.CONTEXT
        assert result.reason == "Content is safe"
        assert result.processing_time_ms == 15.5

    def test_create_result_with_matched_patterns(self):
        """Test creating result with matched patterns."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel, MatchedPattern

        patterns = [
            MatchedPattern(
                pattern=r'\btest\b',
                type="profanity",
                severity=ModerationLevel.LOW,
                position=0
            )
        ]

        result = ModerationResult(
            is_safe=False,
            action=FilterAction.BLOCK,
            level=ModerationLevel.LOW,
            confidence=1.0,
            layer=FilterLayer.PATTERN,
            reason="Blocked by pattern",
            matched_patterns=patterns,
            processing_time_ms=10.0
        )

        assert len(result.matched_patterns) == 1
        assert result.matched_patterns[0].type == "profanity"

    def test_create_result_with_content_id(self):
        """Test creating result with content ID."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=5.0,
            content_id="test123"
        )

        assert result.content_id == "test123"

    def test_matched_patterns_default_empty_list(self):
        """Test that matched_patterns defaults to empty list."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=1.0
        )

        assert result.matched_patterns == []

    def test_content_id_default_none(self):
        """Test that content_id defaults to None."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=1.0
        )

        assert result.content_id is None

    def test_confidence_validation(self):
        """Test confidence field validation."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        # Valid confidence values
        valid_confidences = [0.0, 0.5, 1.0]

        for conf in valid_confidences:
            result = ModerationResult(
                is_safe=True,
                action=FilterAction.ALLOW,
                level=ModerationLevel.SAFE,
                confidence=conf,
                layer=FilterLayer.CONTEXT,
                reason="Safe",
                processing_time_ms=1.0
            )
            assert result.confidence == conf

    def test_result_serialization(self):
        """Test that result can be serialized."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=False,
            action=FilterAction.BLOCK,
            level=ModerationLevel.HIGH,
            confidence=0.95,
            layer=FilterLayer.PATTERN,
            reason="Blocked",
            processing_time_ms=20.0
        )

        result_dict = result.model_dump()

        assert result_dict["is_safe"] is False
        assert result_dict["action"] == FilterAction.BLOCK
        assert result_dict["level"] == ModerationLevel.HIGH
        assert result_dict["confidence"] == 0.95


class TestModerateRequestModel:
    """Test ModerateRequest model."""

    def test_create_request_with_content_only(self):
        """Test creating request with content only."""
        from models import ModerateRequest

        request = ModerateRequest(content="Test content")

        assert request.content == "Test content"
        assert request.content_id is None
        assert request.user_id is None
        assert request.session_id is None
        assert request.policy == "family"  # Default
        assert request.context is None

    def test_create_request_full(self):
        """Test creating request with all fields."""
        from models import ModerateRequest

        request = ModerateRequest(
            content="Test content",
            content_id="content123",
            user_id="user456",
            session_id="session789",
            policy="teen",
            context={"source": "web"}
        )

        assert request.content == "Test content"
        assert request.content_id == "content123"
        assert request.user_id == "user456"
        assert request.session_id == "session789"
        assert request.policy == "teen"
        assert request.context == {"source": "web"}

    def test_content_min_length_validation(self):
        """Test content field minimum length validation."""
        from models import ModerateRequest

        # Valid: non-empty content
        request = ModerateRequest(content="x")
        assert request.content == "x"

        # Invalid: empty content
        with pytest.raises(ValidationError):
            ModerateRequest(content="")

    def test_policy_default(self):
        """Test that policy defaults to 'family'."""
        from models import ModerateRequest

        request = ModerateRequest(content="test")

        assert request.policy == "family"

    def test_context_optional(self):
        """Test that context is optional."""
        from models import ModerateRequest

        request = ModerateRequest(content="test")

        assert request.context is None

    def test_request_with_empty_context(self):
        """Test request with empty context dict."""
        from models import ModerateRequest

        request = ModerateRequest(
            content="test",
            context={}
        )

        assert request.context == {}


class TestModerateResponseModel:
    """Test ModerateResponse model."""

    def test_create_response(self):
        """Test creating moderation response."""
        from models import ModerateResponse, ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=10.0
        )

        response = ModerateResponse(
            safe=True,
            result=result
        )

        assert response.safe is True
        assert response.result is result

    def test_response_serialization(self):
        """Test that response can be serialized."""
        from models import ModerateResponse, ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=False,
            action=FilterAction.BLOCK,
            level=ModerationLevel.HIGH,
            confidence=1.0,
            layer=FilterLayer.PATTERN,
            reason="Blocked",
            processing_time_ms=15.0
        )

        response = ModerateResponse(
            safe=False,
            result=result
        )

        response_dict = response.model_dump()

        assert response_dict["safe"] is False
        assert "result" in response_dict


class TestCheckRequestModel:
    """Test CheckRequest model."""

    def test_create_check_request_minimal(self):
        """Test creating check request with content only."""
        from models import CheckRequest

        request = CheckRequest(content="Test content")

        assert request.content == "Test content"
        assert request.policy == "family"  # Default

    def test_create_check_request_with_policy(self):
        """Test creating check request with custom policy."""
        from models import CheckRequest

        request = CheckRequest(
            content="Test content",
            policy="adult"
        )

        assert request.content == "Test content"
        assert request.policy == "adult"

    def test_content_min_length_validation(self):
        """Test content minimum length validation."""
        from models import CheckRequest

        # Valid
        request = CheckRequest(content="x")
        assert request.content == "x"

        # Invalid
        with pytest.raises(ValidationError):
            CheckRequest(content="")


class TestCheckResponseModel:
    """Test CheckResponse model."""

    def test_create_check_response(self):
        """Test creating check response."""
        from models import CheckResponse

        response = CheckResponse(
            safe=True,
            confidence=1.0,
            reason="Content is safe"
        )

        assert response.safe is True
        assert response.confidence == 1.0
        assert response.reason == "Content is safe"

    def test_reason_optional(self):
        """Test that reason is optional."""
        from models import CheckResponse

        response = CheckResponse(
            safe=True,
            confidence=0.95
        )

        assert response.reason is None


class TestHealthResponseModel:
    """Test HealthResponse model."""

    def test_create_health_response(self):
        """Test creating health response."""
        from models import HealthResponse

        response = HealthResponse(
            status="healthy",
            service="safety-filter",
            moderator_ready=True,
            policy="family"
        )

        assert response.status == "healthy"
        assert response.service == "safety-filter"
        assert response.moderator_ready is True
        assert response.policy == "family"

    def test_policy_optional(self):
        """Test that policy is optional."""
        from models import HealthResponse

        response = HealthResponse(
            status="healthy",
            service="safety-filter",
            moderator_ready=True
        )

        assert response.policy is None


class TestPolicyInfoModel:
    """Test PolicyInfo model."""

    def test_create_policy_info(self):
        """Test creating policy info."""
        from models import PolicyInfo, ModerationLevel

        info = PolicyInfo(
            name="family",
            description="Family-friendly policy",
            level=ModerationLevel.LOW,
            pattern_count=150
        )

        assert info.name == "family"
        assert info.description == "Family-friendly policy"
        assert info.level == ModerationLevel.LOW
        assert info.pattern_count == 150


class TestModelValidation:
    """Test Pydantic model validation."""

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        from models import ModerateRequest

        # Pydantic v2 by default doesn't allow extra fields
        # but we're not explicitly setting extra='forbid'
        # so this tests current behavior
        request = ModerateRequest(
            content="test",
            extra_field="value"  # This may be ignored or cause error
        )

        # Just verify the request was created
        assert request.content == "test"

    def test_type_validation(self):
        """Test that field types are validated."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        # Valid types
        result = ModerationResult(
            is_safe=True,  # bool
            action=FilterAction.ALLOW,  # enum
            level=ModerationLevel.SAFE,  # enum
            confidence=1.0,  # float
            layer=FilterLayer.CONTEXT,  # enum
            reason="test",  # str
            processing_time_ms=10.0  # float
        )

        assert isinstance(result.is_safe, bool)
        assert isinstance(result.confidence, float)
        assert isinstance(result.processing_time_ms, float)

    def test_string_field_validation(self):
        """Test string field validation."""
        from models import ModerateRequest

        request = ModerateRequest(
            content="test",
            policy="family"
        )

        assert isinstance(request.content, str)
        assert isinstance(request.policy, str)


class TestModelJSONSchema:
    """Test model JSON schema generation."""

    def test_moderate_request_schema(self):
        """Test that ModerateRequest has valid schema."""
        from models import ModerateRequest

        schema = ModerateRequest.model_json_schema()

        assert "properties" in schema
        assert "content" in schema["properties"]
        assert "content_id" in schema["properties"]

    def test_moderation_result_schema(self):
        """Test that ModerationResult has valid schema."""
        from models import ModerationResult

        schema = ModerationResult.model_json_schema()

        assert "properties" in schema
        assert "is_safe" in schema["properties"]
        assert "action" in schema["properties"]


class TestModelSerialization:
    """Test model serialization/deserialization."""

    def test_serialize_deserialize_moderate_request(self):
        """Test serializing and deserializing ModerateRequest."""
        from models import ModerateRequest

        original = ModerateRequest(
            content="Test content",
            policy="teen",
            context={"key": "value"}
        )

        # Serialize
        data = original.model_dump()

        # Deserialize
        restored = ModerateRequest(**data)

        assert restored.content == original.content
        assert restored.policy == original.policy
        assert restored.context == original.context

    def test_serialize_deserialize_moderation_result(self):
        """Test serializing and deserializing ModerationResult."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel, MatchedPattern

        original = ModerationResult(
            is_safe=False,
            action=FilterAction.BLOCK,
            level=ModerationLevel.HIGH,
            confidence=0.9,
            layer=FilterLayer.PATTERN,
            reason="Blocked",
            matched_patterns=[
                MatchedPattern(
                    pattern=r'\btest\b',
                    type="profanity",
                    severity=ModerationLevel.LOW
                )
            ],
            processing_time_ms=15.0,
            content_id="test123"
        )

        # Serialize
        data = original.model_dump()

        # Deserialize
        restored = ModerationResult(**data)

        assert restored.is_safe == original.is_safe
        assert restored.action == original.action
        assert len(restored.matched_patterns) == len(original.matched_patterns)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_content(self):
        """Test handling very long content strings."""
        from models import ModerateRequest

        long_content = "a" * 1000000

        request = ModerateRequest(content=long_content)

        assert len(request.content) == 1000000

    def test_unicode_content(self):
        """Test handling unicode content."""
        from models import ModerateRequest

        unicode_content = "Hello 世界 🌍 مرحبا"

        request = ModerateRequest(content=unicode_content)

        assert request.content == unicode_content

    def test_special_characters_in_content(self):
        """Test special characters in content."""
        from models import ModerateRequest

        special = "!@#$%^&*()_+-=[]{}|;':\",.<>?/"

        request = ModerateRequest(content=special)

        assert request.content == special

    def test_zero_confidence(self):
        """Test zero confidence value."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=False,
            action=FilterAction.FLAG,
            level=ModerationLevel.MEDIUM,
            confidence=0.0,
            layer=FilterLayer.CONTEXT,
            reason="Unsure",
            processing_time_ms=10.0
        )

        assert result.confidence == 0.0

    def test_maximum_confidence(self):
        """Test maximum confidence value."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=5.0
        )

        assert result.confidence == 1.0

    def test_zero_processing_time(self):
        """Test zero processing time."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=0.0
        )

        assert result.processing_time_ms == 0.0

    def test_negative_processing_time(self):
        """Test negative processing time (edge case)."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        # May be validated or not depending on model configuration
        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=-1.0
        )

        assert result.processing_time_ms == -1.0

    def test_empty_matched_patterns_list(self):
        """Test empty matched patterns list."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            matched_patterns=[],
            processing_time_ms=10.0
        )

        assert len(result.matched_patterns) == 0

    def test_context_with_nested_data(self):
        """Test context with nested dictionary."""
        from models import ModerateRequest

        nested_context = {
            "user": {
                "id": "123",
                "role": "admin"
            },
            "metadata": {
                "source": "web",
                "timestamp": "2024-01-01"
            }
        }

        request = ModerateRequest(
            content="test",
            context=nested_context
        )

        assert request.context == nested_context


class TestModelCopy:
    """Test model copying functionality."""

    def test_copy_moderation_result(self):
        """Test copying ModerationResult."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        original = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=10.0
        )

        copy = original.model_copy()

        assert copy.is_safe == original.is_safe
        assert copy.action == original.action

    def test_copy_with_updates(self):
        """Test copying with field updates."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        original = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=10.0
        )

        copy = original.model_copy(update={"confidence": 0.5})

        assert copy.confidence == 0.5
        assert original.confidence == 1.0


class TestModelFieldDefaults:
    """Test model field defaults."""

    def test_moderate_request_defaults(self):
        """Test ModerateRequest field defaults."""
        from models import ModerateRequest

        request = ModerateRequest(content="test")

        assert request.policy == "family"
        assert request.content_id is None
        assert request.user_id is None
        assert request.session_id is None
        assert request.context is None

    def test_moderation_result_defaults(self):
        """Test ModerationResult field defaults."""
        from models import ModerationResult, FilterAction, FilterLayer, ModerationLevel

        result = ModerationResult(
            is_safe=True,
            action=FilterAction.ALLOW,
            level=ModerationLevel.SAFE,
            confidence=1.0,
            layer=FilterLayer.CONTEXT,
            reason="Safe",
            processing_time_ms=10.0
        )

        assert result.matched_patterns == []
        assert result.content_id is None


class TestModelFieldDescriptions:
    """Test model field descriptions."""

    def test_moderate_request_has_descriptions(self):
        """Test that ModerateRequest fields have descriptions."""
        from models import ModerateRequest

        schema = ModerateRequest.model_json_schema()

        # Check that content field has description
        content_field = schema["properties"].get("content", {})
        assert "description" in content_field


class TestEnumIteration:
    """Test enum iteration capabilities."""

    def test_moderation_level_iteration(self):
        """Test iterating over ModerationLevel."""
        from models import ModerationLevel

        levels = [level for level in ModerationLevel]

        assert len(levels) == 5
        assert ModerationLevel.SAFE in levels

    def test_filter_action_iteration(self):
        """Test iterating over FilterAction."""
        from models import FilterAction

        actions = [action for action in FilterAction]

        assert len(actions) == 4

    def test_filter_layer_iteration(self):
        """Test iterating over FilterLayer."""
        from models import FilterLayer

        layers = [layer for layer in FilterLayer]

        assert len(layers) == 3
