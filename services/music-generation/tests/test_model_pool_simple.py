"""
Simple unit tests for ModelPool.

These tests use proper mocking to avoid hanging.
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model_pool import ModelPool, get_model_pool
from models import ModelName


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('model_pool.get_settings') as mock:
        settings = Mock()
        settings.device = "cpu"
        settings.musicgen_model_path = "/models/musicgen"
        settings.acestep_model_path = "/models/acestep"
        settings.huggingface_cache_dir = "/models/cache"
        mock.return_value = settings
        yield mock


@pytest.fixture
def model_pool(mock_settings):
    """Create model pool for testing."""
    return ModelPool()


class TestModelPoolInitialization:
    """Tests for model pool initialization."""

    def test_model_pool_initializes(self, model_pool):
        """Test model pool initializes correctly."""
        assert model_pool is not None
        assert ModelName.MUSICGEN in model_pool.models
        assert ModelName.ACESTEP in model_pool.models

    def test_model_pool_singleton(self):
        """Test get_model_pool returns singleton."""
        pool1 = get_model_pool()
        pool2 = get_model_pool()
        assert pool1 is pool2


class TestModelPoolVRAMEstimation:
    """Tests for VRAM estimation."""

    def test_estimate_vram_musicgen(self, model_pool):
        """Test VRAM estimation for MusicGen."""
        vram = model_pool.estimate_vram_mb(ModelName.MUSICGEN)
        assert vram == 4096

    def test_estimate_vram_acestep(self, model_pool):
        """Test VRAM estimation for ACEStep."""
        vram = model_pool.estimate_vram_mb(ModelName.ACESTEP)
        assert vram > 0


class TestModelPoolUnloading:
    """Tests for model unloading."""

    @pytest.mark.asyncio
    async def test_unload_loaded_model(self, model_pool):
        """Test unloading a loaded model."""
        # Set up a loaded model
        model_pool.models[ModelName.MUSICGEN] = Mock()
        model_pool.processors[ModelName.MUSICGEN] = Mock()

        await model_pool.unload_model(ModelName.MUSICGEN)

        assert model_pool.models[ModelName.MUSICGEN] is None
        assert model_pool.processors[ModelName.MUSICGEN] is None

    @pytest.mark.asyncio
    async def test_unload_none_model(self, model_pool):
        """Test unloading a model that's already None."""
        model_pool.models[ModelName.MUSICGEN] = None
        model_pool.processors[ModelName.MUSICGEN] = None

        # Should not raise
        await model_pool.unload_model(ModelName.MUSICGEN)

        assert model_pool.models[ModelName.MUSICGEN] is None

    @pytest.mark.asyncio
    async def test_unload_clears_cuda_cache(self, model_pool):
        """Test unloading clears CUDA cache when available."""
        model_pool.models[ModelName.MUSICGEN] = Mock()
        model_pool.processors[ModelName.MUSICGEN] = Mock()

        with patch('torch.cuda.is_available') as mock_cuda:
            mock_cuda.return_value = True

            with patch('torch.cuda.empty_cache') as mock_empty_cache:
                await model_pool.unload_model(ModelName.MUSICGEN)

                mock_empty_cache.assert_called_once()


class TestModelPoolGetModel:
    """Tests for get_model method."""

    @pytest.mark.asyncio
    async def test_get_model_already_loaded(self, model_pool):
        """Test get_model returns already loaded model."""
        mock_model = Mock()
        mock_processor = Mock()
        model_pool.models[ModelName.MUSICGEN] = mock_model
        model_pool.processors[ModelName.MUSICGEN] = mock_processor

        model, processor = await model_pool.get_model(ModelName.MUSICGEN)

        assert model == mock_model
        assert processor == mock_processor


class TestModelPoolLoading:
    """Tests for model loading."""

    @pytest.mark.asyncio
    async def test_load_model_failure(self, model_pool):
        """Test model loading failure is handled."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            with patch('model_pool.MusicgenForConditionalGeneration') as mock_model_class:
                mock_model_class.from_pretrained.side_effect = Exception("Network error")

                with pytest.raises(Exception, match="Network error"):
                    await model_pool._load_model(ModelName.MUSICGEN)


class TestModelPoolSwitching:
    """Tests for model switching."""

    @pytest.mark.asyncio
    async def test_switch_model_unloads_old(self, model_pool):
        """Test switch_model unloads the old model."""
        model_pool.models[ModelName.MUSICGEN] = Mock()
        model_pool.processors[ModelName.MUSICGEN] = Mock()

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            with patch('model_pool.AutoModel') as mock_auto_model:
                mock_model = Mock()
                mock_model.to = Mock(return_value=mock_model)
                mock_model.eval = Mock()
                mock_auto_model.from_pretrained.return_value = mock_model

                await model_pool.switch_model(ModelName.MUSICGEN, ModelName.ACESTEP)

                assert model_pool.models[ModelName.MUSICGEN] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
