"""Tests for Translation Agent models."""

import pytest
from translation_agent.models import (
    TranslationRequest,
    TranslationResponse,
    SupportedLanguagesResponse,
    TranslationStatus,
)


class TestTranslationRequest:
    """Tests for TranslationRequest model."""

    def test_valid_request(self):
        """Test creating valid translation request."""
        request = TranslationRequest(
            text="Hello world",
            source_language="en",
            target_language="es",
        )
        assert request.text == "Hello world"
        assert request.source_language == "en"
        assert request.target_language == "es"

    def test_empty_text_raises_error(self):
        """Test empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            TranslationRequest(
                text="",
                source_language="en",
                target_language="es",
            )

    def test_whitespace_only_text_raises_error(self):
        """Test whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            TranslationRequest(
                text="   ",
                source_language="en",
                target_language="es",
            )

    def test_missing_source_language_raises_error(self):
        """Test missing source language raises ValueError."""
        with pytest.raises(ValueError, match="Source language is required"):
            TranslationRequest(
                text="Hello",
                source_language="",
                target_language="es",
            )

    def test_missing_target_language_raises_error(self):
        """Test missing target language raises ValueError."""
        with pytest.raises(ValueError, match="Target language is required"):
            TranslationRequest(
                text="Hello",
                source_language="en",
                target_language="",
            )

    def test_same_languages_raises_error(self):
        """Test same source and target language raises ValueError."""
        with pytest.raises(ValueError, match="must be different"):
            TranslationRequest(
                text="Hello",
                source_language="en",
                target_language="en",
            )


class TestTranslationResponse:
    """Tests for TranslationResponse model."""

    def test_successful_response(self):
        """Test successful translation response."""
        response = TranslationResponse(
            translated_text="Hola mundo",
            source_language="en",
            target_language="es",
            status=TranslationStatus.COMPLETED,
            confidence=0.95,
            cached=False,
        )
        assert response.translated_text == "Hola mundo"
        assert response.status == TranslationStatus.COMPLETED
        assert response.confidence == 0.95
        assert response.cached is False

    def test_failed_response(self):
        """Test failed translation response."""
        response = TranslationResponse(
            translated_text="Hello",
            source_language="en",
            target_language="es",
            status=TranslationStatus.FAILED,
            error="Service unavailable",
        )
        assert response.status == TranslationStatus.FAILED
        assert response.error == "Service unavailable"

    def test_to_dict(self):
        """Test converting response to dictionary."""
        response = TranslationResponse(
            translated_text="Hola mundo",
            source_language="en",
            target_language="es",
            status=TranslationStatus.COMPLETED,
            confidence=0.95,
        )
        result = response.to_dict()
        assert result == {
            "translated_text": "Hola mundo",
            "source_language": "en",
            "target_language": "es",
            "status": "completed",
            "confidence": 0.95,
            "cached": False,
            "error": None,
        }


class TestSupportedLanguagesResponse:
    """Tests for SupportedLanguagesResponse model."""

    def test_from_language_codes(self):
        """Test creating response from language codes."""
        codes = ["en", "es", "fr", "bsl"]
        response = SupportedLanguagesResponse.from_list(codes)

        assert len(response.languages) == 4
        assert response.languages[0] == {"code": "en", "name": "English"}
        assert response.languages[1] == {"code": "es", "name": "Spanish"}
        assert response.languages[3] == {"code": "bsl", "name": "British Sign Language"}

    def test_unknown_language_code(self):
        """Test handling unknown language code."""
        codes = ["xx"]
        response = SupportedLanguagesResponse.from_list(codes)

        assert len(response.languages) == 1
        assert response.languages[0] == {"code": "xx", "name": "XX"}
