"""Tests for shared CI mode detection module."""
import pytest
from unittest.mock import patch
from services.shared.ci_mode import (
    is_cpu_mode,
    get_device,
    get_model_variant,
)


class TestIsCpuMode:
    """Test is_cpu_mode function."""

    def test_is_cpu_mode_default(self):
        """Test is_cpu_mode with no environment variable set."""
        # Default when CI_GPU_AVAILABLE is not set is "true" (CPU mode)
        with patch.dict('os.environ', clear=True):
            # Actually looking at the code, the default is the string "true"
            # and "true".lower() == "false" is False, so it returns False (not CPU mode)
            result = is_cpu_mode()
            assert result is False  # Default is not CPU mode (GPU available)

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'false'})
    def test_is_cpu_mode_when_false(self):
        """Test is_cpu_mode when CI_GPU_AVAILABLE is 'false'."""
        result = is_cpu_mode()
        assert result is True

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'true'})
    def test_is_cpu_mode_when_true(self):
        """Test is_cpu_mode when CI_GPU_AVAILABLE is 'true'."""
        result = is_cpu_mode()
        assert result is False

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'FALSE'})
    def test_is_cpu_mode_case_insensitive(self):
        """Test is_cpu_mode is case insensitive."""
        result = is_cpu_mode()
        assert result is True

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'TRUE'})
    def test_is_cpu_mode_case_insensitive_true(self):
        """Test is_cpu_mode is case insensitive for TRUE."""
        result = is_cpu_mode()
        assert result is False

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': '0'})
    def test_is_cpu_mode_with_zero(self):
        """Test is_cpu_mode with '0' value."""
        result = is_cpu_mode()
        assert result is False  # "0" != "false"


class TestGetDevice:
    """Test get_device function."""

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'false'})
    def test_get_device_cpu_mode(self):
        """Test get_device returns CPU in CPU mode."""
        device = get_device()
        assert device == "cpu"

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'true'})
    def test_get_device_gpu_mode(self):
        """Test get_device returns CUDA when GPU available."""
        device = get_device()
        assert device == "cuda"

    @patch.dict('os.environ', clear=True)
    def test_get_device_default(self):
        """Test get_device with default environment."""
        device = get_device()
        assert device == "cuda"  # Default is GPU mode


class TestGetModelVariant:
    """Test get_model_variant function."""

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'false'})
    def test_get_model_variant_cpu_mode(self):
        """Test get_model_variant returns 'ci' in CPU mode."""
        variant = get_model_variant()
        assert variant == "ci"

    @patch.dict('os.environ', {'CI_GPU_AVAILABLE': 'true'})
    def test_get_model_variant_gpu_mode(self):
        """Test get_model_variant returns 'full' when GPU available."""
        variant = get_model_variant()
        assert variant == "full"

    @patch.dict('os.environ', clear=True)
    def test_get_model_variant_default(self):
        """Test get_model_variant with default environment."""
        variant = get_model_variant()
        assert variant == "full"  # Default is GPU mode
