# whisper_service.py
"""Whisper model wrapper for speech-to-text transcription"""
import logging
import time
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

# Try to import whisper, but provide mock if not available
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available, using mock implementation")


class WhisperService:
    """Wrapper for OpenAI Whisper speech-to-text model"""

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "float32"):
        """
        Initialize Whisper service

        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to run on (cpu or cuda)
            compute_type: Compute type (float32, float16, int8)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._model_loaded = False
        self._loading = False

        # Load model in background for faster startup
        # Service will be immediately available, model loads asynchronously
        logger.info(f"Whisper service initialized (model: {self.model_size}, lazy loading enabled)")

    def _ensure_model_loaded(self):
        """Ensure the model is loaded before processing (lazy loading)"""
        if self._model_loaded:
            return True

        if self._loading:
            # Wait for loading to complete
            import time as _time
            for _ in range(100):  # Wait up to 10 seconds
                if self._model_loaded:
                    return True
                _time.sleep(0.1)
            return False

        # Start loading
        self._load_model()
        return self._model_loaded

    def _load_model(self):
        """Load the Whisper model (called lazily or on startup)"""
        self._loading = True
        start_time = time.time()

        if not WHISPER_AVAILABLE:
            logger.warning(f"Mock Whisper model loaded (size: {self.model_size})")
            self.model = _MockWhisperModel()
            self._model_loaded = True
            self._loading = False
            return

        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            load_time = time.time() - start_time
            self._model_loaded = True
            self._loading = False
            logger.info(f"Whisper model loaded in {load_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            logger.warning("Falling back to mock implementation")
            self.model = _MockWhisperModel()
            self._model_loaded = True
            self._loading = False

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es')
            task: Task type ('transcribe' or 'translate')
            temperature: Sampling temperature

        Returns:
            Dictionary with transcription results
        """
        # Ensure model is loaded before processing (lazy loading)
        if not self._ensure_model_loaded():
            raise RuntimeError("Failed to load Whisper model")

        start_time = time.time()

        try:
            if isinstance(self.model, _MockWhisperModel):
                result = self.model.transcribe(
                    audio_path,
                    language=language,
                    task=task,
                    temperature=temperature
                )
            else:
                result = self.model.transcribe(
                    audio_path,
                    language=language,
                    task=task,
                    temperature=temperature
                )

            duration = time.time() - start_time
            result["processing_time"] = duration

            logger.info(f"Transcription completed in {duration:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def detect_language(self, audio_path: str) -> str:
        """
        Detect spoken language in audio

        Args:
            audio_path: Path to audio file

        Returns:
            Language code (e.g., 'en', 'es')
        """
        try:
            if isinstance(self.model, _MockWhisperModel):
                return self.model.detect_language(audio_path)
            else:
                # Load audio and detect language
                audio = whisper.load_audio(audio_path)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
                _, probs = self.model.detect_language(mel)
                return max(probs, key=probs.get)
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"  # Default to English

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._model_loaded and self.model is not None


class _MockWhisperModel:
    """Mock Whisper model for testing and fallback"""

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Mock transcription"""
        # Simulate processing time
        time.sleep(0.1)

        return {
            "text": "[MOCK] This is a simulated transcription. The Whisper model is not installed.",
            "language": language or "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "[MOCK] This is a simulated transcription."
                },
                {
                    "start": 2.5,
                    "end": 5.0,
                    "text": "The Whisper model is not installed."
                }
            ],
            "duration": 5.0
        }

    def detect_language(self, audio_path: str) -> str:
        """Mock language detection"""
        return "en"
