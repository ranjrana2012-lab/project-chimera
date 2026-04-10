"""Data models for Translation Agent."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TranslationStatus(str, Enum):
    """Status of translation request."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class TranslationRequest:
    """Request for text translation."""

    text: str
    source_language: str
    target_language: str

    def __post_init__(self) -> None:
        """Validate translation request."""
        if not self.text or not self.text.strip():
            raise ValueError("Text cannot be empty")
        if not self.source_language:
            raise ValueError("Source language is required")
        if not self.target_language:
            raise ValueError("Target language is required")
        if self.source_language == self.target_language:
            raise ValueError("Source and target languages must be different")


@dataclass(frozen=True)
class TranslationResponse:
    """Response from translation service."""

    translated_text: str
    source_language: str
    target_language: str
    status: TranslationStatus
    confidence: float = 1.0
    cached: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "translated_text": self.translated_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "status": self.status.value,
            "confidence": self.confidence,
            "cached": self.cached,
            "error": self.error,
        }


@dataclass(frozen=True)
class SupportedLanguagesResponse:
    """Response listing supported languages."""

    languages: list[dict[str, str]]

    @classmethod
    def from_list(cls, language_codes: list[str]) -> "SupportedLanguagesResponse":
        """Create response from language code list."""
        language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "pl": "Polish",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "bsl": "British Sign Language",
        }

        languages = [
            {"code": code, "name": language_names.get(code, code.upper())}
            for code in language_codes
        ]
        return cls(languages=languages)
