"""Audio processing utilities for music generation."""

import io
from typing import Any

import numpy as np
import soundfile as sf

from config import get_settings


class AudioProcessor:
    """Process and normalize generated audio."""

    def __init__(self) -> None:
        """Initialize audio processor with settings."""
        self.settings = get_settings()

    def normalize(self, audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
        """Normalize audio to target dB level.

        Args:
            audio: Input audio array (float32, [-1.0, 1.0])
            target_db: Target level in dB (default: -1.0)

        Returns:
            Normalized audio array
        """
        if audio.size == 0:
            return audio

        # Calculate current RMS (Root Mean Square)
        rms = np.sqrt(np.mean(audio ** 2))

        if rms == 0:
            return audio

        # Calculate required gain
        target_rms = 10 ** (target_db / 20)
        gain = target_rms / rms

        # Apply gain with clipping to prevent distortion
        normalized = audio * gain
        normalized = np.clip(normalized, -1.0, 1.0)

        return normalized

    def trim_silence(
        self,
        audio: np.ndarray,
        sample_rate: int,
        margin_ms: int = 100
    ) -> np.ndarray:
        """Trim silence from start and end of audio.

        Args:
            audio: Input audio array
            sample_rate: Sample rate in Hz
            margin_ms: Margin in milliseconds to keep (default: 100)

        Returns:
            Trimmed audio array
        """
        # Calculate margin in samples
        margin_samples = int(margin_ms * sample_rate / 1000)

        # Find non-silent regions
        # Use a threshold to detect silence (-40dB)
        threshold = 1e-4

        # Get indices where audio exceeds threshold
        non_silent = np.where(np.abs(audio) > threshold)[0]

        if len(non_silent) == 0:
            # All silence, return as is
            return audio

        # Calculate start and end with margin
        start = max(0, non_silent[0] - margin_samples)
        end = min(len(audio), non_silent[-1] + margin_samples + 1)

        return audio[start:end]

    def to_wav(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> tuple[bytes, dict[str, Any]]:
        """Convert numpy array to WAV format bytes.

        Args:
            audio: Input audio array
            sample_rate: Sample rate in Hz

        Returns:
            Tuple of (wav_bytes, metadata)
        """
        # Create in-memory file
        buffer = io.BytesIO()

        # Ensure audio is in correct format (converts to float32 if needed)
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Write as WAV
        sf.write(
            buffer,
            audio,
            sample_rate,
            format='WAV',
            subtype='PCM_16'
        )

        # Get bytes
        wav_bytes = buffer.getvalue()
        buffer.close()

        # Prepare metadata
        metadata = {
            "format": "wav",
            "sample_rate": sample_rate,
            "channels": 1 if audio.ndim == 1 else audio.shape[1],
            "duration_seconds": len(audio) / sample_rate,
            "dtype": str(audio.dtype)
        }

        return wav_bytes, metadata

    def process(
        self,
        audio: np.ndarray,
        sample_rate: int,
        normalize: bool = True,
        trim: bool = True
    ) -> tuple[bytes, dict[str, Any]]:
        """Process audio through full pipeline.

        Args:
            audio: Input audio array
            sample_rate: Sample rate in Hz
            normalize: Whether to normalize audio
            trim: Whether to trim silence

        Returns:
            Tuple of (wav_bytes, metadata)
        """
        processed = audio

        # Normalize
        if normalize:
            processed = self.normalize(
                processed,
                target_db=self.settings.normalize_db
            )

        # Trim silence
        if trim:
            processed = self.trim_silence(
                processed,
                sample_rate,
                margin_ms=100
            )

        # Convert to WAV
        return self.to_wav(processed, sample_rate)


def get_audio_processor() -> AudioProcessor:
    """Get singleton audio processor instance.

    Returns:
        AudioProcessor instance
    """
    return AudioProcessor()
