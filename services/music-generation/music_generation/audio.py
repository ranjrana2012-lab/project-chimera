import numpy as np
import soundfile as sf
from io import BytesIO


class AudioProcessor:
    """Post-processing: format conversion, normalization, trimming"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def normalize(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to -1.0 to 1.0 range"""
        peak = np.max(np.abs(audio))
        if peak > 0:
            return audio / peak
        return audio

    def trim_silence(
        self,
        audio: np.ndarray,
        threshold_db: float = -40.0
    ) -> np.ndarray:
        """Trim silence from start and end of audio"""
        # Calculate RMS in dB
        rms = np.sqrt(np.mean(audio ** 2, axis=0))
        threshold = 10 ** (threshold_db / 20)

        # Find non-silent regions
        non_silent = rms > threshold

        if not np.any(non_silent):
            return audio

        # Find first and last non-silent sample
        first = np.argmax(non_silent)
        last = len(non_silent) - np.argmax(non_silent[::-1])

        return audio[:, first:last]

    def convert_format(
        self,
        audio: np.ndarray,
        output_format: str = "mp3",
        bitrate: int = 192
    ) -> bytes:
        """Convert audio to specified format and return bytes"""
        buffer = BytesIO()

        if output_format == "mp3":
            # Use soundfile to write WAV, then convert to MP3
            # (For now, just return WAV bytes)
            sf.write(buffer, audio.T, self.sample_rate, format="WAV")
        else:
            sf.write(buffer, audio.T, self.sample_rate, format=output_format.upper())

        return buffer.getvalue()

    def extract_preview(
        self,
        audio: np.ndarray,
        start_sec: float = 0.0,
        duration: float = 10.0
    ) -> np.ndarray:
        """Extract a preview clip from audio"""
        start_sample = int(start_sec * self.sample_rate)
        end_sample = int((start_sec + duration) * self.sample_rate)

        return audio[:, start_sample:end_sample]
