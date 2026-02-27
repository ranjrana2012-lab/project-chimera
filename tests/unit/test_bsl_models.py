"""Unit tests for BSL Text2Gloss Agent."""

import pytest
from datetime import datetime
from services.bsl_text2gloss_agent.src.models.request import (
    TranslationRequest,
    BatchTranslationRequest
)
from services.bsl_text2gloss_agent.src.models.response import (
    TranslationResponse,
    SignBreakdown,
    BatchTranslationResponse
)
from services.bsl_text2gloss_agent.src.core.gloss_formatter import GlossFormatter, GlossFormat


class TestTranslationRequest:
    """Test cases for TranslationRequest model."""

    def test_valid_request_minimal(self):
        """Test creating a valid request with minimal fields."""
        request = TranslationRequest(text="Hello, how are you?")
        assert request.text == "Hello, how are you?"
        assert request.source_lang == "en"
        assert request.gloss_format == "hamnosys"
        assert request.include_breakdown is True
        assert request.normalize is True

    def test_valid_request_all_fields(self):
        """Test creating a valid request with all fields."""
        request = TranslationRequest(
            text="The weather is beautiful.",
            source_lang="en",
            gloss_format="simplified",
            include_breakdown=False,
            normalize=False
        )
        assert request.text == "The weather is beautiful."
        assert request.gloss_format == "simplified"
        assert request.include_breakdown is False
        assert request.normalize is False

    def test_text_min_length_validation(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError):
            TranslationRequest(text="")

    def test_text_max_length_validation(self):
        """Test that text exceeding max length raises ValueError."""
        with pytest.raises(ValueError):
            TranslationRequest(text="a" * 5001)

    def test_valid_gloss_formats(self):
        """Test various valid gloss formats."""
        formats = ["hamnosys", "stokoe", "simplified"]
        for fmt in formats:
            request = TranslationRequest(
                text="Hello",
                gloss_format=fmt
            )
            assert request.gloss_format == fmt


class TestBatchTranslationRequest:
    """Test cases for BatchTranslationRequest model."""

    def test_valid_batch_request(self):
        """Test creating a valid batch request."""
        request = BatchTranslationRequest(
            texts=["Hello", "How are you?", "Goodbye"]
        )
        assert len(request.texts) == 3
        assert request.source_lang == "en"
        assert request.gloss_format == "hamnosys"

    def test_batch_min_length_validation(self):
        """Test that empty texts list raises ValueError."""
        with pytest.raises(ValueError):
            BatchTranslationRequest(texts=[])

    def test_batch_max_length_validation(self):
        """Test that texts list exceeding max size raises ValueError."""
        with pytest.raises(ValueError):
            BatchTranslationRequest(texts=["test"] * 101)

    def test_batch_with_all_options(self):
        """Test batch request with all options specified."""
        request = BatchTranslationRequest(
            texts=["Hello", "Goodbye"],
            source_lang="en",
            gloss_format="simplified",
            include_breakdown=True,
            normalize=True
        )
        assert request.include_breakdown is True
        assert request.normalize is True


class TestSignBreakdown:
    """Test cases for SignBreakdown model."""

    def test_valid_breakdown(self):
        """Test creating a valid sign breakdown."""
        breakdown = SignBreakdown(
            gloss="HELLO",
            english_source="Hello",
            handshape="open hand",
            location="forehead",
            movement="away from body",
            non_manual="friendly expression",
            confidence=0.92
        )
        assert breakdown.gloss == "HELLO"
        assert breakdown.english_source == "Hello"
        assert breakdown.handshape == "open hand"
        assert breakdown.location == "forehead"
        assert breakdown.movement == "away from body"
        assert breakdown.non_manual == "friendly expression"
        assert breakdown.confidence == 0.92

    def test_breakdown_minimal(self):
        """Test breakdown with only required fields."""
        breakdown = SignBreakdown(
            gloss="YOU",
            english_source="you",
            confidence=0.95
        )
        assert breakdown.gloss == "YOU"
        assert breakdown.handshape is None
        assert breakdown.location is None

    def test_confidence_boundary_values(self):
        """Test confidence boundary validation."""
        breakdown_min = SignBreakdown(
            gloss="TEST",
            english_source="test",
            confidence=0.0
        )
        assert breakdown_min.confidence == 0.0

        breakdown_max = SignBreakdown(
            gloss="TEST",
            english_source="test",
            confidence=1.0
        )
        assert breakdown_max.confidence == 1.0

    def test_confidence_validation(self):
        """Test that confidence outside [0.0, 1.0] raises ValueError."""
        with pytest.raises(ValueError):
            SignBreakdown(
                gloss="TEST",
                english_source="test",
                confidence=1.5
            )

        with pytest.raises(ValueError):
            SignBreakdown(
                gloss="TEST",
                english_source="test",
                confidence=-0.1
            )


class TestTranslationResponse:
    """Test cases for TranslationResponse model."""

    def test_valid_response(self):
        """Test creating a valid translation response."""
        response = TranslationResponse(
            request_id="req-bsl-123456",
            gloss_text="HELLO HOW YOU",
            source_text="Hello, how are you?",
            breakdown=[
                SignBreakdown(
                    gloss="HELLO",
                    english_source="Hello",
                    confidence=0.92
                )
            ],
            notations={"simplified": "HELLO HOW YOU"},
            language="bsl",
            gloss_format="hamnosys",
            confidence=0.91,
            translation_time_ms=156.8,
            model_version="opus-mt-en-ROMANCE-bsl-v0.1.0"
        )
        assert response.request_id == "req-bsl-123456"
        assert response.gloss_text == "HELLO HOW YOU"
        assert response.source_text == "Hello, how are you?"
        assert len(response.breakdown) == 1
        assert response.language == "bsl"
        assert response.confidence == 0.91
        assert response.translation_time_ms == 156.8

    def test_response_with_empty_breakdown(self):
        """Test response with empty breakdown."""
        response = TranslationResponse(
            request_id="req-bsl-789",
            gloss_text="HELLO",
            source_text="Hello",
            breakdown=[],
            notations={},
            language="bsl",
            gloss_format="simplified",
            confidence=0.85,
            translation_time_ms=100.0,
            model_version="test-v0.1.0"
        )
        assert len(response.breakdown) == 0
        assert len(response.notations) == 0


class TestBatchTranslationResponse:
    """Test cases for BatchTranslationResponse model."""

    def test_valid_batch_response(self):
        """Test creating a valid batch response."""
        response = BatchTranslationResponse(
            request_id="req-bsl-batch-789",
            translations=[],
            total_count=3,
            successful_count=3,
            failed_count=0,
            total_time_ms=456.2
        )
        assert response.request_id == "req-bsl-batch-789"
        assert response.total_count == 3
        assert response.successful_count == 3
        assert response.failed_count == 0
        assert response.total_time_ms == 456.2


class TestGlossFormatter:
    """Test cases for GlossFormatter."""

    def test_format_simplified(self):
        """Test simplified gloss formatting."""
        formatter = GlossFormatter(default_format=GlossFormat.SIMPLIFIED)
        result = formatter.format_gloss("hello how are you")
        assert result == "HELLO HOW ARE YOU"

    def test_format_with_case_normalization(self):
        """Test that formatter normalizes to uppercase."""
        formatter = GlossFormatter(default_format=GlossFormat.SIMPLIFIED)
        result = formatter.format_gloss("HeLLo HoW aRe YoU")
        assert result == "HELLO HOW ARE YOU"

    def test_format_with_whitespace_normalization(self):
        """Test that formatter normalizes whitespace."""
        formatter = GlossFormatter(default_format=GlossFormat.SIMPLIFIED)
        result = formatter.format_gloss("hello   how    are   you")
        assert result == "HELLO HOW ARE YOU"

    def test_create_breakdown(self):
        """Test breakdown creation."""
        formatter = GlossFormatter()
        breakdown = formatter.create_breakdown(
            "HELLO HOW YOU",
            "hello how you",
            confidence=0.90
        )
        assert len(breakdown) == 3
        assert breakdown[0]["gloss"] == "HELLO"
        assert breakdown[0]["english_source"] == "hello"
        assert breakdown[0]["confidence"] == 0.90

    def test_normalize_text(self):
        """Test text normalization."""
        formatter = GlossFormatter()
        result = formatter.normalize_text("Hello,  how  are  you?")
        assert result == "hello, how are you?"

    def test_normalize_contractions(self):
        """Test contraction expansion."""
        formatter = GlossFormatter()
        result = formatter.normalize_text("don't won't can't")
        assert result == "do not will not cannot"

    def test_add_non_manual_markers(self):
        """Test adding non-manual markers."""
        formatter = GlossFormatter()
        result = formatter.add_non_manual_markers(
            "HELLO",
            ["question"]
        )
        assert "?brows" in result or "?face" in result


class TestGlossFormat:
    """Test cases for GlossFormat enum."""

    def test_gloss_format_values(self):
        """Test that all format values are accessible."""
        assert GlossFormat.HAMNOSYS.value == "hamnosys"
        assert GlossFormat.STOKOE.value == "stokoe"
        assert GlossFormat.SIMPLIFIED.value == "simplified"
        assert GlossFormat.SIGNWRITING.value == "signwriting"

    def test_gloss_format_from_string(self):
        """Test creating GlossFormat from string."""
        fmt = GlossFormat("hamnosys")
        assert fmt == GlossFormat.HAMNOSYS

        fmt = GlossFormat("simplified")
        assert fmt == GlossFormat.SIMPLIFIED
