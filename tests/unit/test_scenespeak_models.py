"""Unit tests for SceneSpeak base models."""
import pytest
from datetime import datetime
from services.scenespeak.src.models.request import GenerationRequest
from services.scenespeak.src.models.response import GenerationResponse


class TestGenerationRequest:
    """Test cases for GenerationRequest model."""

    def test_valid_request(self):
        """Test creating a valid request with minimal fields."""
        request = GenerationRequest(
            context="A sunny garden",
            character="Alice"
        )
        assert request.context == "A sunny garden"
        assert request.character == "Alice"
        assert request.sentiment == 0.0
        assert request.max_tokens == 256
        assert request.temperature == 0.8
        assert request.top_p == 0.95
        assert request.use_cache is True

    def test_sentiment_validation(self):
        """Test that sentiment values outside [-1.0, 1.0] raise ValueError."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="test",
                character="Bob",
                sentiment=2.0  # Too high
            )

    def test_sentiment_negative_boundary(self):
        """Test that negative sentiment below -1.0 raises ValueError."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="test",
                character="Bob",
                sentiment=-1.5  # Too low
            )

    def test_sentiment_boundary_values(self):
        """Test that boundary sentiment values are accepted."""
        request_high = GenerationRequest(
            context="test",
            character="Bob",
            sentiment=1.0
        )
        assert request_high.sentiment == 1.0

        request_low = GenerationRequest(
            context="test",
            character="Bob",
            sentiment=-1.0
        )
        assert request_low.sentiment == -1.0

    def test_context_min_length_validation(self):
        """Test that empty context raises ValueError."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="",
                character="Alice"
            )

    def test_context_max_length_validation(self):
        """Test that context exceeding max length raises ValueError."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="a" * 1001,  # Exceeds 1000 character limit
                character="Alice"
            )

    def test_max_tokens_validation(self):
        """Test max_tokens boundary validation."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="test",
                character="Bob",
                max_tokens=0  # Too low
            )

    def test_max_tokens_upper_bound(self):
        """Test max_tokens upper bound validation."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="test",
                character="Bob",
                max_tokens=1025  # Exceeds 1024
            )

    def test_temperature_validation(self):
        """Test temperature boundary validation."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="test",
                character="Bob",
                temperature=2.1  # Exceeds 2.0
            )

    def test_top_p_validation(self):
        """Test top_p boundary validation."""
        with pytest.raises(ValueError):
            GenerationRequest(
                context="test",
                character="Bob",
                top_p=1.1  # Exceeds 1.0
            )

    def test_optional_fields(self):
        """Test request with all optional fields specified."""
        request = GenerationRequest(
            context="A moonlit beach",
            character="Claire",
            sentiment=0.5,
            max_tokens=512,
            temperature=1.0,
            top_p=0.9,
            use_cache=False
        )
        assert request.max_tokens == 512
        assert request.temperature == 1.0
        assert request.top_p == 0.9
        assert request.use_cache is False


class TestGenerationResponse:
    """Test cases for GenerationResponse model."""

    def test_valid_response(self):
        """Test creating a valid response."""
        response = GenerationResponse(
            request_id="req-123",
            dialogue="Hello, my dear friend!",
            character="Alice",
            sentiment_used=0.5,
            tokens=10,
            confidence=0.95,
            from_cache=False,
            generation_time_ms=150.5,
            model_version="scenespeak-v0.1.0",
            timestamp=datetime.now()
        )
        assert response.request_id == "req-123"
        assert response.dialogue == "Hello, my dear friend!"
        assert response.character == "Alice"
        assert response.sentiment_used == 0.5
        assert response.tokens == 10
        assert response.confidence == 0.95
        assert response.from_cache is False
        assert response.generation_time_ms == 150.5
        assert response.model_version == "scenespeak-v0.1.0"

    def test_response_from_cache(self):
        """Test response indicating cached result."""
        response = GenerationResponse(
            request_id="req-456",
            dialogue="Cached dialogue",
            character="Bob",
            sentiment_used=-0.3,
            tokens=8,
            confidence=1.0,
            from_cache=True,
            generation_time_ms=5.0,
            model_version="scenespeak-v0.1.0",
            timestamp=datetime.now()
        )
        assert response.from_cache is True
        assert response.generation_time_ms < 10.0  # Should be very fast

    def test_response_with_zero_confidence(self):
        """Test response with minimal confidence."""
        response = GenerationResponse(
            request_id="req-789",
            dialogue="Uncertain response",
            character="Charlie",
            sentiment_used=0.0,
            tokens=5,
            confidence=0.0,
            from_cache=False,
            generation_time_ms=200.0,
            model_version="scenespeak-v0.1.0",
            timestamp=datetime.now()
        )
        assert response.confidence == 0.0
