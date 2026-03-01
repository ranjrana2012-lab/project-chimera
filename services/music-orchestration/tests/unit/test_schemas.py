import pytest
from pydantic import ValidationError

from music_orchestration.schemas import (
    MusicRequest,
    MusicResponse,
    GenerationProgress,
    UseCase,
)


def test_music_request_with_valid_data():
    request = MusicRequest(
        prompt="upbeat electronic background",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )
    assert request.prompt == "upbeat electronic background"
    assert request.use_case == UseCase.MARKETING
    assert request.duration_seconds == 30


def test_music_request_rejects_invalid_duration():
    with pytest.raises(ValidationError):
        MusicRequest(
            prompt="test",
            use_case=UseCase.MARKETING,
            duration_seconds=500  # Too long
        )


def test_music_request_accepts_optional_params():
    request = MusicRequest(
        prompt="dramatic orchestral",
        use_case=UseCase.SHOW,
        duration_seconds=180,
        genre="orchestral",
        mood="dramatic",
        tempo=120,
        key_signature="C minor"
    )
    assert request.genre == "orchestral"
    assert request.mood == "dramatic"
    assert request.tempo == 120


def test_music_response_serialization():
    response = MusicResponse(
        request_id="abc-123",
        music_id="def-456",
        status="completed",
        audio_url="https://minio/audio.mp3",
        duration_seconds=30,
        format="mp3",
        was_cache_hit=True
    )
    data = response.model_dump()
    assert data["request_id"] == "abc-123"
    assert data["was_cache_hit"] is True
