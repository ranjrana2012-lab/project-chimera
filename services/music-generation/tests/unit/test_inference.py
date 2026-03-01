import pytest
from unittest.mock import Mock, AsyncMock

from music_generation.inference import InferenceEngine
from music_generation.models import ModelPoolManager
from music_generation.schemas import GenerationParams


@pytest.mark.asyncio
async def test_generate_music():
    model_pool = ModelPoolManager()
    engine = InferenceEngine(model_pool)

    result = await engine.generate(
        model_name="musicgen",
        prompt="upbeat electronic",
        params=GenerationParams(duration_seconds=30)
    )

    assert result.duration_seconds == 30
    assert result.format == "wav"


@pytest.mark.asyncio
async def test_generate_with_cancel():
    model_pool = ModelPoolManager()
    engine = InferenceEngine(model_pool)

    request_id = await engine.start_generation("musicgen", "test", GenerationParams(duration_seconds=30))
    result = await engine.cancel_generation(request_id)

    assert result is True
