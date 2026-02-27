"""Unit tests for Safety Filter request and response models."""

import pytest
from datetime import datetime
from services.safety_filter.src.models.request import (
    SafetyCheckRequest,
    SafetyCheckOptions,
    StrictnessLevel,
    ContentCategory,
    PolicyRule,
    PolicyUpdateRequest,
    SafetyBatchRequest
)
from services.safety_filter.src.models.response import (
    SafetyCheckResponse,
    SafetyDecision,
    CategoryScore,
    FlaggedContent,
    SafetyDetails,
    PolicyResponse,
    HealthCheckResponse
)
from pydantic import ValidationError


@pytest.mark.unit
class TestSafetyCheckOptions:
    """Test cases for SafetyCheckOptions model."""

    def test_default_options(self):
        """Test creating options with defaults."""
        options = SafetyCheckOptions()
        assert options.strictness == StrictnessLevel.MODERATE
        assert options.include_details is True
        assert options.include_flagged_content is False

    def test_custom_options(self):
        """Test creating options with custom values."""
        options = SafetyCheckOptions(
            strictness=StrictnessLevel.STRICT,
            include_details=False,
            include_flagged_content=True,
            context="chat"
        )
        assert options.strictness == StrictnessLevel.STRICT
        assert options.include_details is False
        assert options.include_flagged_content is True
        assert options.context == "chat"

    def test_categories_filter(self):
        """Test filtering by specific categories."""
        options = SafetyCheckOptions(
            categories=[ContentCategory.PROFANITY, ContentCategory.VIOLENCE]
        )
        assert len(options.categories) == 2
        assert ContentCategory.PROFANITY in options.categories


@pytest.mark.unit
class TestSafetyCheckRequest:
    """Test cases for SafetyCheckRequest model."""

    def test_minimal_request(self):
        """Test creating minimal valid request."""
        request = SafetyCheckRequest(content="Test content")
        assert request.content == "Test content"
        assert request.options is not None

    def test_full_request(self):
        """Test creating request with all fields."""
        request = SafetyCheckRequest(
            content="Full test content here",
            options=SafetyCheckOptions(strictness=StrictnessLevel.STRICT),
            request_id="req-123",
            user_id="user-456",
            source="api"
        )
        assert request.content == "Full test content here"
        assert request.request_id == "req-123"
        assert request.user_id == "user-456"
        assert request.source == "api"

    def test_content_validation(self):
        """Test content length validation."""
        # Valid content
        request = SafetyCheckRequest(content="x" * 100)
        assert request.content == "x" * 100

        # Invalid: too short
        with pytest.raises(ValidationError):
            SafetyCheckRequest(content="")

        # Invalid: too long (max 10000)
        with pytest.raises(ValidationError):
            SafetyCheckRequest(content="x" * 10001)

    def test_request_with_options(self):
        """Test request with custom options."""
        options = SafetyCheckOptions(
            categories=[ContentCategory.HATE_SPEECH],
            strictness=StrictnessLevel.PERMISSIVE
        )
        request = SafetyCheckRequest(
            content="Test content",
            options=options
        )
        assert request.options.strictness == StrictnessLevel.PERMISSIVE


@pytest.mark.unit
class TestPolicyRule:
    """Test cases for PolicyRule model."""

    def test_create_rule(self):
        """Test creating a policy rule."""
        rule = PolicyRule(
            name="block_profanity",
            category=ContentCategory.PROFANITY,
            action="block",
            threshold=0.8
        )
        assert rule.name == "block_profanity"
        assert rule.category == ContentCategory.PROFANITY
        assert rule.action == "block"
        assert rule.threshold == 0.8
        assert rule.enabled is True

    def test_rule_with_conditions(self):
        """Test creating rule with conditions."""
        rule = PolicyRule(
            name="conditional_rule",
            category=ContentCategory.VIOLENCE,
            action="flag",
            threshold=0.7,
            conditions={"min_severity": "high"}
        )
        assert rule.conditions == {"min_severity": "high"}

    def test_threshold_validation(self):
        """Test threshold range validation."""
        # Valid thresholds
        PolicyRule(name="test", category="profanity", action="block", threshold=0.0)
        PolicyRule(name="test", category="profanity", action="block", threshold=1.0)

        # Invalid thresholds
        with pytest.raises(ValidationError):
            PolicyRule(name="test", category="profanity", action="block", threshold=-0.1)
        with pytest.raises(ValidationError):
            PolicyRule(name="test", category="profanity", action="block", threshold=1.1)


@pytest.mark.unit
class TestPolicyUpdateRequest:
    """Test cases for PolicyUpdateRequest model."""

    def test_update_request(self):
        """Test creating policy update request."""
        request = PolicyUpdateRequest(
            rules=[
                {
                    "name": "rule1",
                    "category": "profanity",
                    "action": "block",
                    "threshold": 0.8
                }
            ],
            default_action="flag",
            version="v1.0.0"
        )
        assert len(request.rules) == 1
        assert request.default_action == "flag"
        assert request.version == "v1.0.0"


@pytest.mark.unit
class TestSafetyBatchRequest:
    """Test cases for SafetyBatchRequest model."""

    def test_batch_request(self):
        """Test creating batch request."""
        request = SafetyBatchRequest(
            contents=["Content 1", "Content 2", "Content 3"]
        )
        assert len(request.contents) == 3

    def test_batch_validation(self):
        """Test batch size validation."""
        # Valid: 1 item
        SafetyBatchRequest(contents=["Single"])

        # Valid: 100 items
        SafetyBatchRequest(contents=["x"] * 100)

        # Invalid: 0 items
        with pytest.raises(ValidationError):
            SafetyBatchRequest(contents=[])

        # Invalid: 101 items
        with pytest.raises(ValidationError):
            SafetyBatchRequest(contents=["x"] * 101)


@pytest.mark.unit
class TestCategoryScore:
    """Test cases for CategoryScore model."""

    def test_category_score(self):
        """Test creating category score."""
        score = CategoryScore(
            category="profanity",
            score=0.85,
            flagged=True,
            matched_terms=["damn", "hell"]
        )
        assert score.category == "profanity"
        assert score.score == 0.85
        assert score.flagged is True
        assert len(score.matched_terms) == 2

    def test_score_validation(self):
        """Test score range validation."""
        # Valid scores
        CategoryScore(category="test", score=0.0, flagged=False)
        CategoryScore(category="test", score=1.0, flagged=False)

        # Invalid scores
        with pytest.raises(ValidationError):
            CategoryScore(category="test", score=-0.1, flagged=False)
        with pytest.raises(ValidationError):
            CategoryScore(category="test", score=1.1, flagged=False)


@pytest.mark.unit
class TestFlaggedContent:
    """Test cases for FlaggedContent model."""

    def test_flagged_content(self):
        """Test creating flagged content."""
        flagged = FlaggedContent(
            category="profanity",
            text="damn it",
            start_pos=10,
            end_pos=17,
            reason="Contains profanity",
            severity="medium"
        )
        assert flagged.category == "profanity"
        assert flagged.text == "damn it"
        assert flagged.start_pos == 10
        assert flagged.end_pos == 17


@pytest.mark.unit
class TestSafetyCheckResponse:
    """Test cases for SafetyCheckResponse model."""

    def test_response_creation(self):
        """Test creating safety check response."""
        response = SafetyCheckResponse(
            request_id="req-123",
            decision=SafetyDecision.FLAG,
            safe=False,
            confidence=0.85,
            explanation="Content flagged for profanity",
            model_version="v0.1.0",
            processing_time_ms=45.2
        )
        assert response.request_id == "req-123"
        assert response.decision == SafetyDecision.FLAG
        assert response.safe is False
        assert response.confidence == 0.85

    def test_response_with_details(self):
        """Test response with detailed analysis."""
        details = SafetyDetails(
            word_filter_results={"matches": []},
            ml_filter_results={"prediction": "safe"},
            category_scores=[
                CategoryScore(
                    category="profanity",
                    score=0.1,
                    flagged=False,
                    matched_terms=[]
                )
            ],
            overall_confidence=0.95,
            applied_rules=[]
        )
        response = SafetyCheckResponse(
            request_id="req-456",
            decision=SafetyDecision.ALLOW,
            safe=True,
            confidence=0.95,
            details=details,
            explanation="Content is safe",
            model_version="v0.1.0",
            processing_time_ms=25.0
        )
        assert response.details is not None
        assert len(response.details.category_scores) == 1

    def test_confidence_validation(self):
        """Test confidence range validation."""
        # Valid confidence
        SafetyCheckResponse(
            request_id="test",
            decision=SafetyDecision.ALLOW,
            safe=True,
            confidence=0.0,
            explanation="test",
            model_version="v1",
            processing_time_ms=10
        )
        SafetyCheckResponse(
            request_id="test",
            decision=SafetyDecision.ALLOW,
            safe=True,
            confidence=1.0,
            explanation="test",
            model_version="v1",
            processing_time_ms=10
        )

        # Invalid confidence
        with pytest.raises(ValidationError):
            SafetyCheckResponse(
                request_id="test",
                decision=SafetyDecision.ALLOW,
                safe=True,
                confidence=1.5,
                explanation="test",
                model_version="v1",
                processing_time_ms=10
            )


@pytest.mark.unit
class TestSafetyDecision:
    """Test cases for SafetyDecision enum."""

    def test_decision_values(self):
        """Test decision enum values."""
        assert SafetyDecision.ALLOW == "allow"
        assert SafetyDecision.BLOCK == "block"
        assert SafetyDecision.FLAG == "flag"
        assert SafetyDecision.WARN == "warn"


@pytest.mark.unit
class TestHealthCheckResponse:
    """Test cases for HealthCheckResponse model."""

    def test_health_response(self):
        """Test creating health check response."""
        response = HealthCheckResponse(
            status="healthy",
            version="0.1.0",
            uptime_seconds=3600.5,
            model_loaded=True,
            word_list_loaded=True,
            kafka_connected=True
        )
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.uptime_seconds == 3600.5
        assert response.model_loaded is True
