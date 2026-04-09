"""
Unit tests for InferenceEngine non-async methods.

These tests focus on covering the non-async parts of the inference engine.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from inference import InferenceEngine, get_inference_engine
from models import ModelName


class TestInferenceEngineNonAsync:
    """Tests for non-async methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('inference.get_settings') as mock:
            settings = Mock()
            settings.device = "cpu"
            settings.normalize_db = -1.0
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def mock_model_pool(self):
        """Mock model pool for testing."""
        with patch('inference.get_model_pool') as mock:
            pool = Mock()
            pool.device = Mock()
            pool.estimate_vram_mb = Mock(return_value=4096)
            mock.return_value = pool
            yield pool

    def test_estimate_vram_required_musicgen_5s(self, mock_settings, mock_model_pool):
        """Test VRAM estimation for MusicGen at 5 seconds."""
        engine = InferenceEngine()
        vram = engine.estimate_vram_required(ModelName.MUSICGEN, 5.0)
        assert vram == 4096

    def test_estimate_vram_required_musicgen_10s(self, mock_settings, mock_model_pool):
        """Test VRAM estimation for MusicGen at 10 seconds."""
        engine = InferenceEngine()
        vram = engine.estimate_vram_required(ModelName.MUSICGEN, 10.0)
        assert vram > 4096
        assert vram <= 4096 * 2.0

    def test_estimate_vram_required_musicgen_1s(self, mock_settings, mock_model_pool):
        """Test VRAM estimation for MusicGen at 1 second (minimum)."""
        engine = InferenceEngine()
        vram = engine.estimate_vram_required(ModelName.MUSICGEN, 1.0)
        assert vram > 0
        assert vram < 4096

    def test_estimate_vram_required_acestep(self, mock_settings, mock_model_pool):
        """Test VRAM estimation for ACEStep."""
        engine = InferenceEngine()
        vram = engine.estimate_vram_required(ModelName.ACESTEP, 5.0)
        assert vram > 0

    def test_estimate_vram_duration_scaling(self, mock_settings, mock_model_pool):
        """Test that VRAM estimate scales appropriately with duration."""
        engine = InferenceEngine()

        vram_5 = engine.estimate_vram_required(ModelName.MUSICGEN, 5.0)
        vram_10 = engine.estimate_vram_required(ModelName.MUSICGEN, 10.0)
        vram_20 = engine.estimate_vram_required(ModelName.MUSICGEN, 20.0)

        # VRAM should increase with duration
        assert vram_10 > vram_5
        assert vram_20 >= vram_10

        # But should be capped at 2x base
        assert vram_20 <= 4096 * 2.0

    def test_estimate_vram_uses_model_pool_estimate(self, mock_settings, mock_model_pool):
        """Test that estimate_vram_required uses model_pool.estimate_vram_mb."""
        engine = InferenceEngine()

        # Call with different models to verify it uses the pool
        vram_musicgen = engine.estimate_vram_required(ModelName.MUSICGEN, 5.0)
        vram_acestep = engine.estimate_vram_required(ModelName.ACESTEP, 5.0)

        # Should have called estimate_vram_mb for each model
        assert mock_model_pool.estimate_vram_mb.called

    def test_get_inference_engine_singleton(self):
        """Test get_inference_engine returns singleton."""
        engine1 = get_inference_engine()
        engine2 = get_inference_engine()
        assert engine1 is engine2

    def test_inference_engine_initialization(self, mock_settings, mock_model_pool):
        """Test inference engine initializes correctly."""
        engine = InferenceEngine()
        assert engine.settings is not None
        assert engine.model_pool is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
