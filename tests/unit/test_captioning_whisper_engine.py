"""
Unit tests for Captioning Agent Whisper Engine

Tests the Whisper ASR engine implementation.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import numpy as np
import torch

import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from captioning_agent.src.config import Settings
from captioning_agent.src.core.whisper_engine import WhisperEngine


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        whisper_model="base",
        language="en",
        app_name="captioning-agent-test",
        app_version="0.1.0-test",
    )


@pytest.fixture
def mock_whisper_model():
    """Create a mock Whisper model."""
    model = MagicMock()
    model.transcribe = MagicMock(return_value={
        "text": "Hello, world!",
        "language": "en",
        "segments": [
            {
                "id": 0,
                "text": "Hello, world!",
                "start": 0.0,
                "end": 2.5,
            }
        ],
        "no_speech_prob": 0.05,
    })
    model.detect_language = MagicMock(return_value=("en", {"en": 0.95}))
    return model


@pytest.fixture
def whisper_engine(settings):
    """Create a Whisper engine instance."""
    engine = WhisperEngine(settings)
    return engine


class TestWhisperEngine:
    """Tests for WhisperEngine class."""

    def test_initialization(self, whisper_engine):
        """Test engine initialization."""
        assert whisper_engine.settings is not None
        assert whisper_engine.model_name == "base"
        assert whisper_engine.is_loaded is False
        assert whisper_engine.model is None

    def test_get_device_cuda(self, settings):
        """Test device detection with CUDA."""
        with patch('torch.cuda.is_available', return_value=True):
            engine = WhisperEngine(settings)
            device = engine._get_device()
            assert device.type == "cuda"

    def test_get_device_cpu(self, settings):
        """Test device detection with CPU."""
        with patch('torch.cuda.is_available', return_value=False):
            engine = WhisperEngine(settings)
            device = engine._get_device()
            assert device.type == "cpu"

    @pytest.mark.asyncio
    async def test_load_model(self, whisper_engine, mock_whisper_model):
        """Test loading the Whisper model."""
        with patch('captioning_agent.src.core.whisper_engine.whisper') as mock_whisper_module:
            mock_whisper_module.load_model.return_value = mock_whisper_model

            await whisper_engine.load_model()

            assert whisper_engine.is_loaded is True
            assert whisper_engine.model == mock_whisper_model
            mock_whisper_module.load_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_model_import_error(self, whisper_engine):
        """Test load_model fails when whisper is not installed."""
        with patch('captioning_agent.src.core.whisper_engine.whisper', side_effect=ImportError):
            with pytest.raises(RuntimeError, match="Whisper is not installed"):
                await whisper_engine.load_model()

    @pytest.mark.asyncio
    async def test_transcribe_without_model(self, whisper_engine):
        """Test transcription fails when model is not loaded."""
        with pytest.raises(RuntimeError, match="Model not loaded"):
            await whisper_engine.transcribe(audio=np.array([1.0, 2.0, 3.0]))

    @pytest.mark.asyncio
    async def test_transcribe_with_numpy_array(self, whisper_engine, mock_whisper_model):
        """Test transcription with numpy array input."""
        whisper_engine.model = mock_whisper_model
        whisper_engine.is_loaded = True

        audio = np.random.randn(16000).astype(np.float32)  # 1 second at 16kHz

        result = await whisper_engine.transcribe(
            audio=audio,
            language="en",
            task="transcribe",
        )

        assert "request_id" in result
        assert result["text"] == "Hello, world!"
        assert result["language"] == "en"
        assert result["duration"] == 1.0
        assert len(result["segments"]) == 1
        assert "confidence" in result
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_transcribe_with_word_timestamps(self, whisper_engine):
        """Test transcription with word-level timestamps."""
        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(return_value={
            "text": "Hello world",
            "language": "en",
            "segments": [
                {
                    "id": 0,
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 1.0,
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.95},
                        {"word": "world", "start": 0.5, "end": 1.0, "probability": 0.92},
                    ]
                }
            ],
        })

        whisper_engine.model = mock_model
        whisper_engine.is_loaded = True

        audio = np.random.randn(16000).astype(np.float32)

        result = await whisper_engine.transcribe(
            audio=audio,
            word_timestamps=True,
        )

        assert len(result["words"]) == 2
        assert result["words"][0]["word"] == "Hello"
        assert result["words"][0]["confidence"] == 0.95
        assert result["words"][1]["word"] == "world"

    @pytest.mark.asyncio
    async def test_prepare_audio_numpy(self, whisper_engine):
        """Test preparing numpy array audio."""
        audio = np.random.randn(1600).astype(np.float32)

        result = await whisper_engine._prepare_audio(audio)

        assert result.shape == audio.shape
        assert result.dtype == np.float32

    @pytest.mark.asyncio
    async def test_prepare_audio_multichannel(self, whisper_engine):
        """Test preparing multi-channel audio (mixes to mono)."""
        audio = np.random.randn(1600, 2).astype(np.float32)

        result = await whisper_engine._prepare_audio(audio)

        assert result.ndim == 1  # Mixed to mono
        assert len(result) == 1600

    @pytest.mark.asyncio
    async def test_calculate_confidence(self, whisper_engine):
        """Test confidence calculation."""
        # Test with word-level confidences
        result = {"no_speech_prob": 0.1}
        segments = [
            {
                "words": [
                    {"confidence": 0.9},
                    {"confidence": 0.8},
                ]
            }
        ]

        confidence = whisper_engine._calculate_confidence(result, segments)

        assert confidence == 0.85  # Average of 0.9 and 0.8

    @pytest.mark.asyncio
    async def test_calculate_confidence_fallback(self, whisper_engine):
        """Test confidence calculation fallback (no word timestamps)."""
        result = {"no_speech_prob": 0.1}
        segments = []  # No word-level confidences

        confidence = whisper_engine._calculate_confidence(result, segments)

        assert confidence == 0.9  # 1.0 - 0.1

    def test_detect_language(self, whisper_engine, mock_whisper_model):
        """Test language detection."""
        whisper_engine.model = mock_whisper_model
        whisper_engine.is_loaded = True

        audio = np.random.randn(16000).astype(np.float32)

        with patch('torch.from_numpy'):
            language, confidence = whisper_engine.detect_language(audio)

            assert language == "en"
            assert confidence == 0.95

    def test_detect_language_not_loaded(self, whisper_engine):
        """Test language detection fails when model not loaded."""
        audio = np.random.randn(16000).astype(np.float32)

        with pytest.raises(RuntimeError, match="Model not loaded"):
            whisper_engine.detect_language(audio)

    def test_detect_language_short_audio(self, whisper_engine):
        """Test language detection fails with too short audio."""
        whisper_engine.model = MagicMock()
        whisper_engine.is_loaded = True

        audio = np.random.randn(1000).astype(np.float32)  # Less than 1 second

        with pytest.raises(ValueError, match="Audio too short"):
            whisper_engine.detect_language(audio)

    @pytest.mark.asyncio
    async def test_close(self, whisper_engine):
        """Test closing the engine and unloading model."""
        whisper_engine.model = MagicMock()
        whisper_engine.is_loaded = True

        await whisper_engine.close()

        assert whisper_engine.model is None
        assert whisper_engine.is_loaded is False


class TestWhisperEngineModels:
    """Tests for Whisper model constants."""

    def test_models_dict(self):
        """Test available models."""
        models = WhisperEngine.MODELS

        assert "tiny" in models
        assert "base" in models
        assert "small" in models
        assert "medium" in models
        assert "large" in models
        assert "large-v3" in models

        # Check model info structure
        for name, info in models.items():
            assert "size_mb" in info
            assert "speed" in info
            assert "accuracy" in info

    def test_languages_dict(self):
        """Test available languages."""
        languages = WhisperEngine.LANGUAGES

        assert "en" in languages
        assert "es" in languages
        assert "fr" in languages
        assert "de" in languages
        assert "ja" in languages
        assert "zh" in languages


@pytest.mark.asyncio
async def test_whisper_engine_integration():
    """Integration test for WhisperEngine with actual model loading mocked."""
    settings = Settings(
        whisper_model="tiny",  # Use smallest for speed
        language="en",
    )

    engine = WhisperEngine(settings)

    # Mock the whisper module
    with patch('captioning_agent.src.core.whisper_engine.whisper') as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe = MagicMock(return_value={
            "text": "Test transcription",
            "language": "en",
            "segments": [{"id": 0, "text": "Test", "start": 0.0, "end": 1.0}],
        })
        mock_whisper.load_model.return_value = mock_model

        await engine.load_model()
        assert engine.is_loaded is True

        # Test transcription
        audio = np.random.randn(16000).astype(np.float32)
        result = await engine.transcribe(audio)

        assert result["text"] == "Test transcription"
        assert result["language"] == "en"

        await engine.close()
        assert engine.is_loaded is False
