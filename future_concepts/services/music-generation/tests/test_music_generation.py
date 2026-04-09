"""
Unit tests for Music Generation Service.

Tests verify that the music generation service can:
- Process audio through AudioProcessor
- Manage model pool with ModelPool
- Validate generation requests
- Generate music with InferenceEngine
"""

import pytest
import sys
import os
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio import AudioProcessor
from model_pool import ModelPool, get_model_pool
from models import ModelName, GenerationRequest, GenerationResponse
from inference import InferenceEngine


class TestAudioProcessor:
    """Tests for AudioProcessor audio processing functionality."""

    def test_audio_processor_initializes(self):
        """Test that AudioProcessor can be initialized."""
        processor = AudioProcessor()
        assert processor is not None
        assert processor.settings is not None

    def test_normalize_audio(self):
        """Test audio normalization to target dB level."""
        processor = AudioProcessor()

        # Create test audio with low amplitude
        audio = np.random.randn(44100).astype(np.float32) * 0.01

        normalized = processor.normalize(audio, target_db=-1.0)

        assert normalized is not None
        assert normalized.shape == audio.shape
        # Check that audio is normalized (closer to target level)
        rms = np.sqrt(np.mean(normalized ** 2))
        assert rms > 0.01  # Should be louder after normalization

    def test_normalize_empty_audio(self):
        """Test normalization handles empty audio."""
        processor = AudioProcessor()
        audio = np.array([]).astype(np.float32)

        normalized = processor.normalize(audio)

        assert normalized.size == 0

    def test_normalize_zero_audio(self):
        """Test normalization handles all-zero audio."""
        processor = AudioProcessor()
        audio = np.zeros(44100).astype(np.float32)

        normalized = processor.normalize(audio)

        assert np.array_equal(normalized, audio)

    def test_trim_silence_from_audio(self):
        """Test silence trimming from audio."""
        processor = AudioProcessor()

        # Create audio with silence at start and end
        sample_rate = 44100
        silence = np.zeros(10000).astype(np.float32)
        signal = np.random.randn(44100).astype(np.float32) * 0.5
        audio = np.concatenate([silence, signal, silence])

        trimmed = processor.trim_silence(audio, sample_rate)

        assert trimmed is not None
        # Trimmed audio should be shorter than original
        assert len(trimmed) < len(audio)
        # Should contain most of the signal
        assert len(trimmed) > 40000

    def test_trim_silence_all_silent(self):
        """Test trimming handles all-silent audio."""
        processor = AudioProcessor()

        audio = np.zeros(44100).astype(np.float32)
        trimmed = processor.trim_silence(audio, 44100)

        # Should return as-is or empty
        assert len(trimmed) <= len(audio)

    def test_to_wav_conversion(self):
        """Test conversion to WAV format."""
        processor = AudioProcessor()

        # Create test audio
        audio = np.random.randn(44100).astype(np.float32) * 0.5
        sample_rate = 44100

        wav_bytes, metadata = processor.to_wav(audio, sample_rate)

        assert wav_bytes is not None
        assert len(wav_bytes) > 0
        assert metadata is not None
        assert metadata["format"] == "wav"
        assert metadata["sample_rate"] == sample_rate
        assert "duration_seconds" in metadata
        assert "channels" in metadata

    def test_process_full_pipeline(self):
        """Test full audio processing pipeline."""
        processor = AudioProcessor()

        # Create test audio
        audio = np.random.randn(44100).astype(np.float32) * 0.3
        sample_rate = 44100

        wav_bytes, metadata = processor.process(
            audio,
            sample_rate,
            normalize=True,
            trim=True
        )

        assert wav_bytes is not None
        assert len(wav_bytes) > 0
        assert metadata["format"] == "wav"


class TestModelPool:
    """Tests for ModelPool model management."""

    def test_model_pool_initializes(self):
        """Test that ModelPool can be initialized."""
        pool = ModelPool()
        assert pool is not None
        assert ModelName.MUSICGEN in pool.models
        assert ModelName.ACESTEP in pool.models

    def test_get_model_pool_singleton(self):
        """Test that get_model_pool returns singleton instance."""
        pool1 = get_model_pool()
        pool2 = get_model_pool()
        assert pool1 is pool2

    def test_estimate_vram_musicgen(self):
        """Test VRAM estimation for MusicGen model."""
        pool = ModelPool()
        vram = pool.estimate_vram_mb(ModelName.MUSICGEN)
        assert vram > 0
        assert vram == 4096  # Expected for musicgen-small

    def test_estimate_vram_acestep(self):
        """Test VRAM estimation for ACEStep model."""
        pool = ModelPool()
        vram = pool.estimate_vram_mb(ModelName.ACESTEP)
        assert vram > 0
        assert vram == 2048  # Expected for ACEStep

    @pytest.mark.asyncio
    async def test_unload_model(self):
        """Test model unloading."""
        pool = ModelPool()

        # Set a model as "loaded" (mock)
        pool.models[ModelName.MUSICGEN] = Mock()
        pool.processors[ModelName.MUSICGEN] = Mock()

        await pool.unload_model(ModelName.MUSICGEN)

        assert pool.models[ModelName.MUSICGEN] is None
        assert pool.processors[ModelName.MUSICGEN] is None


class TestGenerationRequest:
    """Tests for GenerationRequest validation."""

    def test_valid_request(self):
        """Test creation of valid generation request."""
        request = GenerationRequest(
            prompt="Generate upbeat electronic music",
            model=ModelName.MUSICGEN,
            duration=5.0,
            sample_rate=44100
        )

        assert request.prompt == "Generate upbeat electronic music"
        assert request.model == ModelName.MUSICGEN
        assert request.duration == 5.0
        assert request.sample_rate == 44100

    def test_default_values(self):
        """Test default values for generation request."""
        request = GenerationRequest(
            prompt="Test music"
        )

        assert request.model == ModelName.MUSICGEN
        assert request.duration == 5.0
        assert request.sample_rate == 44100

    def test_prompt_validation_empty(self):
        """Test that empty prompt is rejected."""
        with pytest.raises(ValueError):
            GenerationRequest(prompt="")

    def test_prompt_validation_whitespace(self):
        """Test that whitespace-only prompt is rejected."""
        with pytest.raises(ValueError):
            GenerationRequest(prompt="   ")

    def test_prompt_validation_stripped(self):
        """Test that prompt is stripped of whitespace."""
        request = GenerationRequest(prompt="  Test music  ")
        assert request.prompt == "Test music"

    def test_duration_validation_minimum(self):
        """Test that duration below minimum is rejected."""
        with pytest.raises(ValueError):
            GenerationRequest(
                prompt="Test",
                duration=0.5
            )

    def test_duration_validation_maximum(self):
        """Test that duration above maximum is rejected."""
        with pytest.raises(ValueError):
            GenerationRequest(
                prompt="Test",
                duration=60.0
            )

    def test_sample_rate_validation_minimum(self):
        """Test that sample rate below minimum is rejected."""
        with pytest.raises(ValueError):
            GenerationRequest(
                prompt="Test",
                sample_rate=8000
            )

    def test_sample_rate_validation_maximum(self):
        """Test that sample rate above maximum is rejected."""
        with pytest.raises(ValueError):
            GenerationRequest(
                prompt="Test",
                sample_rate=96000
            )

    def test_model_validation_valid_models(self):
        """Test that only valid model names are accepted."""
        for model in [ModelName.MUSICGEN, ModelName.ACESTEP]:
            request = GenerationRequest(
                prompt="Test",
                model=model
            )
            assert request.model == model


class TestGenerationResponse:
    """Tests for GenerationResponse model."""

    def test_successful_response(self):
        """Test creation of successful generation response."""
        response = GenerationResponse(
            success=True,
            audio_url="/audio/generated_123.wav",
            duration=5.0,
            sample_rate=44100,
            model="musicgen",
            generation_time=2.5,
            file_size=441000
        )

        assert response.success is True
        assert response.audio_url == "/audio/generated_123.wav"
        assert response.duration == 5.0
        assert response.error is None

    def test_error_response(self):
        """Test creation of error response."""
        response = GenerationResponse(
            success=False,
            duration=0.0,
            sample_rate=44100,
            model="musicgen",
            generation_time=0.0,
            error="Model loading failed"
        )

        assert response.success is False
        assert response.error == "Model loading failed"
        assert response.audio_url is None


class TestInferenceEngine:
    """Tests for InferenceEngine music generation."""

    def test_inference_engine_initializes(self):
        """Test that InferenceEngine can be initialized."""
        engine = InferenceEngine()
        assert engine is not None
        assert engine.settings is not None
        assert engine.model_pool is not None

    def test_estimate_vram_required(self):
        """Test VRAM estimation for generation."""
        engine = InferenceEngine()

        # Test MusicGen with different durations
        vram_5s = engine.estimate_vram_required(ModelName.MUSICGEN, 5.0)
        vram_10s = engine.estimate_vram_required(ModelName.MUSICGEN, 10.0)

        assert vram_5s > 0
        assert vram_10s > vram_5s  # Longer duration requires more VRAM

    def test_estimate_vram_duration_multiplier(self):
        """Test that VRAM estimate scales with duration."""
        engine = InferenceEngine()

        base_vram = engine.estimate_vram_required(ModelName.MUSICGEN, 5.0)
        double_vram = engine.estimate_vram_required(ModelName.MUSICGEN, 10.0)

        # Should increase but not strictly double due to cap
        assert double_vram > base_vram
        # Cap at 2x multiplier
        assert double_vram <= base_vram * 2.0


class TestModelName:
    """Tests for ModelName enum."""

    def test_model_name_values(self):
        """Test that ModelName enum has correct values."""
        assert ModelName.MUSICGEN.value == "musicgen"
        assert ModelName.ACESTEP.value == "acestep"

    def test_model_name_from_string(self):
        """Test creating ModelName from string."""
        model = ModelName("musicgen")
        assert model == ModelName.MUSICGEN


class TestIntegration:
    """Integration tests for music generation workflow."""

    def test_audio_processor_integration(self):
        """Test AudioProcessor with actual audio data."""
        processor = AudioProcessor()

        # Create realistic audio test case
        duration = 2.0  # seconds
        sample_rate = 44100
        num_samples = int(duration * sample_rate)

        # Generate test audio with some structure
        t = np.linspace(0, duration, num_samples)
        audio = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)

        # Add silence at beginning and end
        silence = np.zeros(int(sample_rate * 0.5)).astype(np.float32)
        audio_with_silence = np.concatenate([silence, audio, silence])

        # Process
        wav_bytes, metadata = processor.process(
            audio_with_silence,
            sample_rate,
            normalize=True,
            trim=True
        )

        assert wav_bytes is not None
        assert len(wav_bytes) > 0
        assert metadata["format"] == "wav"
        # Duration should be reduced after trimming silence
        assert metadata["duration_seconds"] < 3.0

    def test_request_response_flow(self):
        """Test complete request to response flow."""
        request = GenerationRequest(
            prompt="Generate cinematic orchestral music",
            model=ModelName.MUSICGEN,
            duration=10.0,
            sample_rate=44100
        )

        # Verify request is valid
        assert request.prompt == "Generate cinematic orchestral music"
        assert request.duration == 10.0

        # Create corresponding response (without actual generation)
        response = GenerationResponse(
            success=True,
            audio_url="/audio/test.wav",
            duration=request.duration,
            sample_rate=request.sample_rate,
            model=request.model.value,
            generation_time=3.5,
            file_size=176400  # Approximate
        )

        assert response.success is True
        assert response.duration == request.duration
        assert response.sample_rate == request.sample_rate
        assert response.model == request.model.value


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_audio_processor_with_mono_audio(self):
        """Test processing mono (1-channel) audio."""
        processor = AudioProcessor()

        # Mono audio: 1D array
        audio = np.random.randn(22050).astype(np.float32)
        wav_bytes, metadata = processor.to_wav(audio, 44100)

        assert metadata["channels"] == 1

    def test_audio_processor_with_stereo_audio(self):
        """Test processing stereo (2-channel) audio."""
        processor = AudioProcessor()

        # Stereo audio: 2D array (samples, channels)
        audio = np.random.randn(22050, 2).astype(np.float32)
        wav_bytes, metadata = processor.to_wav(audio, 44100)

        assert metadata["channels"] == 2

    def test_generation_request_max_length_prompt(self):
        """Test prompt at maximum length."""
        max_prompt = "a" * 500
        request = GenerationRequest(prompt=max_prompt)
        assert len(request.prompt) == 500

    def test_generation_request_too_long_prompt(self):
        """Test that prompt exceeding maximum is rejected."""
        too_long_prompt = "a" * 501
        with pytest.raises(ValueError):
            GenerationRequest(prompt=too_long_prompt)

    def test_model_pool_concurrent_access(self):
        """Test that model pool handles concurrent access."""
        import asyncio

        async def access_model():
            pool = get_model_pool()
            # Just verify the pool exists
            return pool is not None

        async def run_concurrent():
            results = await asyncio.gather(
                access_model(),
                access_model(),
                access_model()
            )
            return all(results)

        result = asyncio.run(run_concurrent())
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
