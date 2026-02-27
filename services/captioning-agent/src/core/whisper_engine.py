"""
Whisper ASR Engine for Captioning Agent

Provides speech-to-text functionality using OpenAI Whisper models.
Supports multiple languages, real-time transcription, and word-level timestamps.
"""

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from ..config import Settings


class WhisperEngine:
    """Manages Whisper ASR model for speech-to-text transcription.

    Features:
    - Multi-language support (99 languages)
    - Word-level timestamps
    - Voice activity detection
    - Translation to English
    - Real-time streaming support
    """

    # Supported Whisper models
    MODELS = {
        "tiny": {"size_mb": 39, "speed": "fastest", "accuracy": "lower"},
        "base": {"size_mb": 74, "speed": "fast", "accuracy": "medium"},
        "small": {"size_mb": 244, "speed": "medium", "accuracy": "good"},
        "medium": {"size_mb": 769, "speed": "slow", "accuracy": "better"},
        "large": {"size_mb": 1550, "speed": "slowest", "accuracy": "best"},
        "large-v1": {"size_mb": 1550, "speed": "slowest", "accuracy": "best"},
        "large-v2": {"size_mb": 1550, "speed": "slowest", "accuracy": "best_v2"},
        "large-v3": {"size_mb": 1550, "speed": "slowest", "accuracy": "best_v3"},
    }

    # Supported languages
    LANGUAGES = {
        "en": "english",
        "es": "spanish",
        "fr": "french",
        "de": "german",
        "it": "italian",
        "pt": "portuguese",
        "ru": "russian",
        "ja": "japanese",
        "ko": "korean",
        "zh": "chinese",
        "ar": "arabic",
        "hi": "hindi",
        # ... and many more
    }

    def __init__(self, settings: Settings):
        """Initialize the Whisper engine.

        Args:
            settings: Application settings containing model configuration
        """
        self.settings = settings
        self.model = None
        self.model_name = settings.whisper_model
        self.device = self._get_device()
        self.is_loaded = False
        self._load_time = 0.0

    def _get_device(self) -> torch.device:
        """Determine the best device for model inference.

        Returns:
            torch.device: The device to use for inference
        """
        if torch.cuda.is_available():
            device = torch.device("cuda")
            print(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = torch.device("mps")
            print("Using MPS (Apple Silicon) device")
        else:
            device = torch.device("cpu")
            print("Using CPU device")
        return device

    async def load_model(self) -> None:
        """Load the Whisper model.

        Loads the model into memory for fast inference. The model is loaded
        once and reused for all transcription requests.
        """
        if self.is_loaded:
            return

        start_time = time.time()

        try:
            # Import whisper here to avoid unnecessary import overhead
            import whisper

            print(f"Loading Whisper model '{self.model_name}' on {self.device}...")

            # Load the model
            self.model = whisper.load_model(
                self.model_name,
                device=self.device,
                download_root=str(self.settings.model_path.parent),
            )

            # Warm up the model with a dummy inference
            dummy_audio = torch.randn(16000).to(self.device)
            with torch.no_grad():
                _ = self.model.transcribe(
                    dummy_audio.cpu().numpy(),
                    language="en",
                    fp16=self.device.type != "cpu",
                )

            self._load_time = time.time() - start_time
            self.is_loaded = True

            print(
                f"Whisper model '{self.model_name}' loaded successfully "
                f"in {self._load_time:.2f}s"
            )

        except ImportError as e:
            raise RuntimeError(
                "Whisper is not installed. Install with: pip install openai-whisper"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {e}") from e

    async def transcribe(
        self,
        audio: np.ndarray | str | bytes,
        language: Optional[str] = None,
        task: str = "transcribe",
        timestamps: bool = True,
        vad_filter: bool = False,
        word_timestamps: bool = False,
    ) -> Dict[str, Any]:
        """Transcribe audio using Whisper.

        Args:
            audio: Audio input as numpy array (float32, 16kHz), file path, or bytes
            language: Language code (auto-detect if None)
            task: 'transcribe' or 'translate' to English
            timestamps: Whether to include segment timestamps
            vad_filter: Whether to apply voice activity detection
            word_timestamps: Whether to include word-level timestamps

        Returns:
            Dictionary containing:
                - text: Full transcribed text
                - language: Detected/specified language
                - duration: Audio duration in seconds
                - segments: List of transcribed segments
                - words: Word-level timestamps (if requested)
                - confidence: Overall confidence score

        Raises:
            RuntimeError: If model is not loaded
            ValueError: If audio format is invalid
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Prepare audio
        audio_array = await self._prepare_audio(audio)
        duration = len(audio_array) / 16000.0  # Whisper uses 16kHz

        # Run transcription
        try:
            result = self.model.transcribe(
                audio_array,
                language=language or self.settings.language or None,
                task=task,
                fp16=self.device.type != "cpu",
                verbose=False,
                word_timestamps=word_timestamps,
            )

            # Extract segments
            segments = []
            all_words = []

            for seg in result.get("segments", []):
                segment = {
                    "id": seg["id"],
                    "text": seg["text"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "language": result.get("language"),
                }

                # Add word timestamps if available
                if word_timestamps and "words" in seg:
                    words = [
                        {
                            "word": w["word"],
                            "start": w["start"],
                            "end": w["end"],
                            "confidence": w.get("probability", 1.0),
                        }
                        for w in seg["words"]
                    ]
                    segment["words"] = words
                    all_words.extend(words)

                segments.append(segment)

            # Calculate confidence
            confidence = self._calculate_confidence(result, segments)

            processing_time = time.time() - start_time

            return {
                "request_id": request_id,
                "text": result["text"],
                "language": result.get("language", language or "unknown"),
                "duration": duration,
                "segments": segments,
                "words": all_words if word_timestamps else None,
                "confidence": confidence,
                "processing_time_ms": processing_time * 1000,
                "model_version": f"whisper-{self.model_name}",
            }

        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}") from e

    async def _prepare_audio(
        self, audio: np.ndarray | str | bytes
    ) -> np.ndarray:
        """Prepare audio for transcription.

        Args:
            audio: Audio input in various formats

        Returns:
            numpy array of float32 audio samples at 16kHz

        Raises:
            ValueError: If audio format is invalid
        """
        import librosa

        if isinstance(audio, np.ndarray):
            # Already a numpy array
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            if audio.ndim == 1:
                return audio
            elif audio.ndim == 2:
                # Multi-channel, mix to mono
                return np.mean(audio, axis=1)
            else:
                raise ValueError(f"Invalid audio dimensions: {audio.ndim}")

        elif isinstance(audio, str):
            # File path
            if not Path(audio).exists():
                raise ValueError(f"Audio file not found: {audio}")

            # Load audio with librosa
            audio_array, sr = librosa.load(audio, sr=16000, mono=True)
            return audio_array.astype(np.float32)

        elif isinstance(audio, bytes):
            # Raw audio bytes - assume WAV/PCM
            import io

            audio_array, sr = librosa.load(io.BytesIO(audio), sr=16000, mono=True)
            return audio_array.astype(np.float32)

        else:
            raise ValueError(f"Unsupported audio type: {type(audio)}")

    def _calculate_confidence(
        self, result: Dict[str, Any], segments: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence score.

        Args:
            result: Whisper transcription result
            segments: List of transcribed segments

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not segments:
            return 0.0

        # Use word-level probabilities if available
        confidences = []
        for seg in segments:
            if "words" in seg and seg["words"]:
                for word in seg["words"]:
                    if "confidence" in word:
                        confidences.append(word["confidence"])

        if confidences:
            return float(np.mean(confidences))

        # Fallback: use no_speech_prob if available
        no_speech_prob = result.get("no_speech_prob", 0.0)
        return float(1.0 - no_speech_prob)

    def detect_language(self, audio: np.ndarray) -> Tuple[str, float]:
        """Detect the language of audio.

        Args:
            audio: Audio array at 16kHz

        Returns:
            Tuple of (language_code, confidence)
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        # Make sure audio is the right length (30 seconds for language detection)
        if len(audio) < 16000:
            raise ValueError("Audio too short for language detection (min 1 second)")

        audio_clip = audio[: min(len(audio), 30 * 16000)]

        # Detect language
        audio_tensor = torch.from_numpy(audio_clip).to(self.device)
        with torch.no_grad():
            _, probs = self.model.detect_language(audio_tensor)

        # Get top language
        language_code = max(probs, key=probs.get)
        confidence = float(probs[language_code])

        return language_code, confidence

    async def close(self) -> None:
        """Clean up resources.

        Unloads the model from memory.
        """
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False

            # Force garbage collection
            if self.device.type == "cuda":
                torch.cuda.empty_cache()

            print("Whisper model unloaded")
