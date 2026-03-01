import pytest
from unittest.mock import Mock, patch

from music_generation.models import ModelPoolManager, ModelInfo
from music_generation.errors import InsufficientVRAMError


@pytest.mark.asyncio
async def test_load_model():
    manager = ModelPoolManager(vram_limit_mb=8192)

    with patch.object(manager, "_load_model_from_disk", return_value=Mock()):
        await manager.load_model("musicgen")

    assert "musicgen" in manager.loaded_models
    assert manager.get_model_info("musicgen") is not None


@pytest.mark.asyncio
async def test_load_model_insufficient_vram():
    manager = ModelPoolManager(vram_limit_mb=100)

    with patch.object(manager, "_load_model_from_disk", return_value=Mock()):
        manager.model_requirements = {"musicgen": 2048}  # 2GB required
        with pytest.raises(InsufficientVRAMError):
            await manager.load_model("musicgen")


@pytest.mark.asyncio
async def test_estimate_vram_usage():
    manager = ModelPoolManager()
    manager.model_requirements = {"musicgen": 2048, "acestep": 4096}

    await manager.load_model("musicgen")
    usage = manager.estimate_vram_usage()

    assert usage["musicgen"] == 2048
