import pytest
import numpy as np

from music_generation.audio import AudioProcessor


def test_normalize_audio():
    processor = AudioProcessor()

    # Create fake audio (stereo, 44100 Hz, 1 second)
    audio = np.random.randn(2, 44100).astype(np.float32) * 0.5
    normalized = processor.normalize(audio)

    # Check peak is within range
    assert np.max(np.abs(normalized)) <= 1.0


def test_trim_silence():
    processor = AudioProcessor()

    # Create audio with silence at start/end
    audio = np.zeros((2, 44100), dtype=np.float32)
    audio[:, 1000:-1000] = 0.5  # Add signal in middle

    trimmed = processor.trim_silence(audio, threshold_db=-40)

    # Should be shorter
    assert trimmed.shape[1] < audio.shape[1]
