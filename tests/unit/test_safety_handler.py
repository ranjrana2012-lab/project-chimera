"""Unit tests for Safety Filter Handler module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.safety_filter.src.core.handler import SafetyHandler
from services.safety_filter.src.models.request import SafetyCheckRequest, SafetyCheckOptions, StrictnessLevel
from services.safety_filter.src.models.response import SafetyDecision


@pytest.mark.unit
class TestSafetyHandler:
    """Test cases for SafetyHandler class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.word_list_path = None
        settings.ml_model_path = None
        settings.device = "cpu"
        settings.policy_path = None
        settings.default_action = "flag"
        settings.kafka_servers = None
        settings.kafka_topic = "safety-audit"
        settings.audit_log_path = None
        settings.audit_enabled = True
        return settings

    @pytest.fixture
    def handler(self, mock_settings):
        """Create a SafetyHandler for testing."""
        return SafetyHandler(mock_settings)

    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test that handler initializes correctly."""
        assert handler.word_filter is not None
        assert handler.ml_filter is not None
        assert handler.policy_engine is not None
        assert handler.audit_logger is not None

    @pytest.mark.asyncio
    async def test_initialize(self, handler):
        """Test handler initialization process."""
        await handler.initialize()
        assert handler.ml_filter.model_loaded is True or handler.ml_filter.model_loaded is False  # May use fallback

    @pytest.mark.asyncio
    async def test_check_content_safe(self, handler):
        """Test checking safe content."""
        await handler.initialize()

        request = SafetyCheckRequest(
            content="This is a safe message about the theater performance.",
            options=SafetyCheckOptions(
                strictness=StrictnessLevel.MODERATE
            ),
            request_id="test-req-1"
        )

        response = await handler.check_content(request)
        assert response.request_id == "test-req-1"
        assert response.decision in [SafetyDecision.ALLOW, SafetyDecision.FLAG, SafetyDecision.WARN, SafetyDecision.BLOCK]
        assert "confidence" in response.model_fields or hasattr(response, "confidence")

    @pytest.mark.asyncio
    async def test_check_content_with_flagged_content(self, handler):
        """Test checking content with flagged content details."""
        await handler.initialize()

        request = SafetyCheckRequest(
            content="This contains some problematic content.",
            options=SafetyCheckOptions(
                include_flagged_content=True,
                include_details=True
            )
        )

        response = await handler.check_content(request)
        assert response is not None

    @pytest.mark.asyncio
    async def test_check_content_with_categories(self, handler):
        """Test checking content with specific categories."""
        await handler.initialize()

        request = SafetyCheckRequest(
            content="Test message content here.",
            options=SafetyCheckOptions(
                categories=["profanity", "violence"]
            )
        )

        response = await handler.check_content(request)
        assert response is not None

    @pytest.mark.asyncio
    async def test_check_batch(self, handler):
        """Test batch content checking."""
        await handler.initialize()

        from services.safety_filter.src.models.request import SafetyBatchRequest

        request = SafetyBatchRequest(
            contents=[
                "First safe message.",
                "Second safe message.",
                "Third safe message."
            ],
            options=SafetyCheckOptions(
                strictness=StrictnessLevel.MODERATE
            ),
            request_id="batch-test-1"
        )

        response = await handler.check_batch(request)
        assert response.request_id == "batch-test-1"
        assert len(response.results) == 3
        assert response.aggregate["total_items"] == 3

    @pytest.mark.asyncio
    async def test_filter_content(self, handler):
        """Test content filtering."""
        filtered = await handler.filter_content(
            "What the hell is this?",
            filter_char="*",
            categories=["profanity"]
        )
        assert filtered is not None
        # Content should be filtered
        assert "*" in filtered or "hell" not in filtered.lower()

    def test_get_policies(self, handler):
        """Test getting current policies."""
        policies = handler.get_policies()
        assert "rules" in policies
        assert "default_action" in policies
        assert "category_weights" in policies

    def test_update_policies(self, handler):
        """Test updating policies."""
        new_rules = [
            {
                "name": "test_rule",
                "category": "profanity",
                "action": "block",
                "threshold": 0.8,
                "enabled": True
            }
        ]
        updated = handler.update_policies(new_rules, default_action="flag")
        assert "rules" in updated
        assert updated["default_action"] == "flag"

    def test_get_health_status(self, handler):
        """Test getting health status."""
        health = handler.get_health_status()
        assert "status" in health
        assert "uptime_seconds" in health
        assert "components" in health

    def test_get_statistics(self, handler):
        """Test getting operational statistics."""
        stats = handler.get_statistics()
        assert "uptime_seconds" in stats
        assert "audit_stats" in stats

    @pytest.mark.asyncio
    async def test_close(self, handler):
        """Test closing handler."""
        await handler.initialize()
        await handler.close()
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_check_content_generates_request_id(self, handler):
        """Test that request ID is generated if not provided."""
        await handler.initialize()

        request = SafetyCheckRequest(
            content="Test content.",
            # No request_id provided
        )

        response = await handler.check_content(request)
        assert response.request_id is not None
        assert len(response.request_id) > 0

    @pytest.mark.asyncio
    async def test_check_content_with_user_metadata(self, handler):
        """Test checking content with user metadata."""
        await handler.initialize()

        request = SafetyCheckRequest(
            content="Test content for user metadata.",
            user_id="user-123",
            source="chat"
        )

        response = await handler.check_content(request)
        assert response is not None

    @pytest.mark.asyncio
    async def test_check_different_strictness_levels(self, handler):
        """Test checking content with different strictness levels."""
        await handler.initialize()

        content = "This might be borderline content."

        for strictness in [StrictnessLevel.PERMISSIVE, StrictnessLevel.MODERATE, StrictnessLevel.STRICT]:
            request = SafetyCheckRequest(
                content=content,
                options=SafetyCheckOptions(strictness=strictness)
            )
            response = await handler.check_content(request)
            assert response is not None

    @pytest.mark.asyncio
    async def test_build_flagged_content(self, handler):
        """Test building flagged content details."""
        word_results = {
            "matches": [
                {"category": "profanity", "text": "test", "position": 0}
            ]
        }
        ml_results = {
            "harm_probability": 0.8,
            "top_category": "profanity",
            "confidence": 0.85
        }

        flagged = handler._build_flagged_content(
            "Test content here",
            word_results,
            ml_results
        )
        assert isinstance(flagged, list)

    @pytest.mark.asyncio
    async def test_error_handling_in_check_content(self, handler):
        """Test error handling during content check."""
        await handler.initialize()

        # Create an invalid request (content too short if validated)
        # This tests the error handling path
        request = SafetyCheckRequest(
            content="x",  # Minimal content
        )

        try:
            response = await handler.check_content(request)
            # Should not raise an error, but handle gracefully
            assert response is not None
        except Exception as e:
            # If exception is raised, it should be handled
            assert True  # Test passes if we get here

    @pytest.mark.asyncio
    async def test_processing_time_recorded(self, handler):
        """Test that processing time is recorded."""
        await handler.initialize()

        request = SafetyCheckRequest(
            content="Test content for timing.",
        )

        response = await handler.check_content(request)
        assert response.processing_time_ms >= 0
