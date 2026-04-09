# tests/test_whisper.py
"""Tests for Whisper service"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from whisper_service import WhisperService, _MockWhisperModel


@pytest.fixture
def service():
    """Create WhisperService instance"""
    service = WhisperService(model_size="base")
    return service


def test_service_initialization():
    """Test WhisperService initializes with correct model size"""
    service = WhisperService(model_size="base")
    assert service.model_size == "base"
    assert service.model is not None


def test_service_initialization_custom_size():
    """Test WhisperService initializes with custom model size"""
    service = WhisperService(model_size="small")
    assert service.model_size == "small"
    assert service.model is not None


def test_service_initialization_with_device():
    """Test WhisperService initializes with custom device"""
    service = WhisperService(model_size="tiny", device="cpu")
    assert service.device == "cpu"
    assert service.model is not None


def test_transcribe_success(service):
    """Test successful transcription"""
    result = service.transcribe("/fake/audio.wav")

    # Check that we get a result with expected structure
    assert "text" in result
    assert "language" in result
    assert "segments" in result
    assert isinstance(result["text"], str)
    assert isinstance(result["language"], str)


def test_transcribe_with_language(service):
    """Test transcription with explicit language"""
    result = service.transcribe("/fake/audio.wav", language="fr")

    assert result["language"] == "fr"
    assert "text" in result


def test_detect_language(service):
    """Test language detection"""
    language = service.detect_language("/fake/audio.wav")

    assert isinstance(language, str)
    assert len(language) == 2  # Language codes are 2 letters


def test_model_loaded_check(service):
    """Test that model is loaded correctly"""
    assert service.is_loaded() is True
    assert service.model is not None


def test_mock_whisper_model():
    """Test the mock Whisper model directly"""
    mock_model = _MockWhisperModel()
    result = mock_model.transcribe("/fake/audio.wav")

    assert "text" in result
    assert "language" in result
    assert "MOCK" in result["text"]


def test_mock_language_detection():
    """Test the mock language detection"""
    mock_model = _MockWhisperModel()
    language = mock_model.detect_language("/fake/audio.wav")

    assert language == "en"
