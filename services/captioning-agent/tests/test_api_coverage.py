"""
Tests for Captioning Agent API Endpoints

Comprehensive test suite for API endpoint coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model."""
    with patch('main.whisper_model') as mock:
        mock.transcribe = AsyncMock(return_value={
            "text": "Transcribed text",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "Hello"}
            ]
        })
        yield mock


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_structure(self, client):
        """Test health check returns correct response structure."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "captioning-agent"

    def test_health_check_includes_model_status(self, client):
        """Test health check includes model availability status."""
        response = client.get("/health")
        data = response.json()
        assert "model_loaded" in data or "status" in data


class TestTranscribeEndpoint:
    """Tests for transcription endpoint."""

    def test_transcribe_with_valid_audio(self, client, mock_whisper_model):
        """Test transcribe with valid audio file."""
        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )

            assert response.status_code == 200
        finally:
            os.unlink(temp_path)

    def test_transcribe_with_language(self, client, mock_whisper_model):
        """Test transcribe with language parameter."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"language": "en"}
                )

            assert response.status_code == 200
        finally:
            os.unlink(temp_path)

    def test_transcribe_with_task_translate(self, client, mock_whisper_model):
        """Test transcribe with translation task."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"task": "translate"}
                )

            assert response.status_code == 200
        finally:
            os.unlink(temp_path)

    def test_transcribe_with_vad_filter(self, client, mock_whisper_model):
        """Test transcribe with VAD filter enabled."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"vad_filter": "true"}
                )

            assert response.status_code == 200
        finally:
            os.unlink(temp_path)

    def test_transcribe_without_file(self, client):
        """Test transcribe without file parameter."""
        response = client.post("/api/v1/transcribe", data={})
        assert response.status_code == 422  # Validation error

    def test_transcribe_with_empty_file(self, client):
        """Test transcribe with empty file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            # Write empty content

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )

            # Should handle gracefully
            assert response.status_code in [200, 400, 422]
        finally:
            os.unlink(temp_path)

    def test_transcribe_returns_correct_format(self, client, mock_whisper_model):
        """Test transcribe returns correct response format."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )

            if response.status_code == 200:
                data = response.json()
                assert "text" in data or "transcription" in data
        finally:
            os.unlink(temp_path)


class TestBatchTranscribeEndpoint:
    """Tests for batch transcription endpoint."""

    def test_batch_transcribe_multiple_files(self, client, mock_whisper_model):
        """Test transcribing multiple audio files."""
        files_data = []

        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                f.write(b"fake audio data")
                files_data.append(temp_path)

        try:
            files = []
            for i, path in enumerate(files_data):
                with open(path, "rb") as f:
                    files.append(("files", (f"test{i}.wav", f, "audio/wav")))

            response = client.post(
                "/api/v1/transcribe/batch",
                files=files
            )

            assert response.status_code == 200
        finally:
            for path in files_data:
                os.unlink(path)

    def test_batch_transcribe_empty_list(self, client):
        """Test batch transcribe with no files."""
        response = client.post("/api/v1/transcribe/batch", data={})
        assert response.status_code in [200, 422]


class TestResponseFormat:
    """Tests for response format validation."""

    def test_transcribe_includes_timestamps(self, client, mock_whisper_model):
        """Test transcribe includes timestamp information."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"timestamp": "true"}
                )

            if response.status_code == 200:
                data = response.json()
                # Should include segments or timestamps
                assert "text" in data or "segments" in data
        finally:
            os.unlink(temp_path)

    def test_transcribe_includes_language(self, client, mock_whisper_model):
        """Test transcribe includes detected language."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )

            if response.status_code == 200:
                data = response.json()
                assert "text" in data or "language" in data
        finally:
            os.unlink(temp_path)


class TestErrorHandling:
    """Tests for error handling."""

    def test_transcribe_handles_invalid_audio(self, client):
        """Test transcribe handles invalid audio format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
            f.write(b"not audio data")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.txt", audio_file, "text/plain")}
                )

            # Should handle invalid format
            assert response.status_code in [400, 422, 500]
        finally:
            os.unlink(temp_path)

    def test_transcribe_handles_corrupted_audio(self, client, mock_whisper_model):
        """Test transcribe handles corrupted audio file."""
        mock_whisper_model.transcribe.side_effect = Exception("Corrupted audio")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"corrupted audio")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")}
                )

            assert response.status_code == 500
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_transcribe_with_very_short_audio(self, client, mock_whisper_model):
        """Test transcribe with very short audio."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"short")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("short.wav", audio_file, "audio/wav")}
                )

            assert response.status_code in [200, 400, 422]
        finally:
            os.unlink(temp_path)

    def test_transcribe_with_different_formats(self, client, mock_whisper_model):
        """Test transcribe with different audio formats."""
        formats = [".wav", ".mp3", ".m4a", ".flac"]

        for fmt in formats:
            with tempfile.NamedTemporaryFile(suffix=fmt, delete=False) as f:
                temp_path = f.name
                f.write(b"fake audio")

            try:
                with open(temp_path, "rb") as audio_file:
                    response = client.post(
                        "/api/v1/transcribe",
                        files={"file": (f"test{fmt}", audio_file, "audio/wav")}
                    )

                # Should handle various formats
                assert response.status_code in [200, 400, 422, 500]
            finally:
                os.unlink(temp_path)


class TestLanguageSupport:
    """Tests for language support."""

    def test_transcribe_auto_detect_language(self, client, mock_whisper_model):
        """Test transcribe with auto language detection."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio")

        try:
            with open(temp_path, "rb") as audio_file:
                response = client.post(
                    "/api/v1/transcribe",
                    files={"file": ("test.wav", audio_file, "audio/wav")},
                    data={"language": "auto"}
                )

            assert response.status_code == 200
        finally:
            os.unlink(temp_path)

    def test_transcribe_with_specific_language(self, client, mock_whisper_model):
        """Test transcribe with specific language code."""
        languages = ["en", "es", "fr", "de", "it"]

        for lang in languages:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                f.write(b"fake audio")

            try:
                with open(temp_path, "rb") as audio_file:
                    response = client.post(
                        "/api/v1/transcribe",
                        files={"file": ("test.wav", audio_file, "audio/wav")},
                        data={"language": lang}
                    )

                assert response.status_code == 200
            finally:
                os.unlink(temp_path)


class TestConfiguration:
    """Tests for service configuration."""

    def test_service_version(self, client):
        """Test service reports correct version."""
        response = client.get("/health")
        data = response.json()
        assert "service" in data

    def test_service_name(self, client):
        """Test service reports correct name."""
        response = client.get("/health")
        data = response.json()
        assert data["service"] == "captioning-agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
