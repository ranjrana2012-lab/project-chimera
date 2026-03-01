import pytest

from music_orchestration.errors import (
    MusicServiceError,
    ModelNotFoundError,
    InsufficientVRAMError,
    GenerationTimeoutError,
    InvalidPromptError,
    ApprovalRequiredError,
)


def test_model_not_found_error():
    error = ModelNotFoundError("musicgen")
    assert "musicgen" in str(error)
    assert error.model_name == "musicgen"


def test_insufficient_vram_error():
    error = InsufficientVRAMError(required_mb=4096, available_mb=2048)
    assert "4096" in str(error)
    assert "2048" in str(error)
    assert error.required_mb == 4096


def test_invalid_prompt_error():
    error = InvalidPromptError("blocked content")
    assert "blocked content" in str(error)


def test_approval_required_error():
    error = ApprovalRequiredError("abc-123")
    assert "abc-123" in str(error)
