"""
Enhanced tests for Whisper Service covering edge cases and error handling.

Tests the speech-to-text transcription functionality including:
- Advanced transcription scenarios
- Error handling
- Performance tests
- Integration scenarios
"""

import pytest
import time
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from whisper_service import WhisperService, _MockWhisperModel, WHISPER_AVAILABLE


@pytest.fixture
def service():
    """Create WhisperService instance for testing"""
    return WhisperService(model_size="base")


@pytest.fixture
def mock_service():
    """Create WhisperService with forced mock model"""
    with patch('whisper_service.WHISPER_AVAILABLE', False):
        service = WhisperService(model_size="tiny")
        yield service


class TestWhisperServiceInitialization:
    """Test WhisperService initialization scenarios"""

    def test_initialization_default_parameters(self):
        """Test initialization with default parameters"""
        service = WhisperService()
        assert service.model_size == "base"
        assert service.device == "cpu"
        assert service.compute_type == "float32"
        assert service.model is not None

    def test_initialization_custom_model_size(self):
        """Test initialization with custom model size"""
        for size in ["tiny", "base", "small", "medium", "large"]:
            service = WhisperService(model_size=size)
            assert service.model_size == size

    def test_initialization_with_cuda_device(self):
        """Test initialization with CUDA device"""
        service = WhisperService(device="cuda")
        assert service.device == "cuda"

    def test_initialization_with_compute_type(self):
        """Test initialization with different compute types"""
        for compute_type in ["float32", "float16", "int8"]:
            service = WhisperService(compute_type=compute_type)
            assert service.compute_type == compute_type

    @patch('whisper_service.WHISPER_AVAILABLE', False)
    def test_initialization_with_whisper_unavailable(self):
        """Test initialization falls back to mock when Whisper unavailable"""
        service = WhisperService()
        assert isinstance(service.model, _MockWhisperModel)


class TestTranscription:
    """Test transcription functionality"""

    def test_transcribe_basic(self, mock_service):
        """Test basic transcription"""
        result = mock_service.transcribe("/fake/audio.wav")
        assert "text" in result
        assert "language" in result
        assert "segments" in result
        assert "processing_time" in result

    def test_transcribe_with_language(self, mock_service):
        """Test transcription with explicit language"""
        result = mock_service.transcribe("/fake/audio.wav", language="es")
        assert result["language"] == "es"

    def test_transcribe_with_task_translate(self, mock_service):
        """Test transcription with translate task"""
        result = mock_service.transcribe("/fake/audio.wav", task="translate")
        assert "text" in result

    def test_transcribe_with_temperature(self, mock_service):
        """Test transcription with custom temperature"""
        result = mock_service.transcribe("/fake/audio.wav", temperature=0.5)
        assert "text" in result

    def test_transcribe_returns_segments(self, mock_service):
        """Test that transcription returns segments"""
        result = mock_service.transcribe("/fake/audio.wav")
        assert isinstance(result["segments"], list)
        assert len(result["segments"]) > 0

    def test_transcribe_segment_structure(self, mock_service):
        """Test that segments have correct structure"""
        result = mock_service.transcribe("/fake/audio.wav")
        segment = result["segments"][0]
        assert "start" in segment
        assert "end" in segment
        assert "text" in segment

    def test_transcribe_processing_time(self, mock_service):
        """Test that processing time is recorded"""
        result = mock_service.transcribe("/fake/audio.wav")
        assert "processing_time" in result
        assert result["processing_time"] >= 0

    def test_transcribe_duration_field(self, mock_service):
        """Test that duration field is present"""
        result = mock_service.transcribe("/fake/audio.wav")
        assert "duration" in result
        assert result["duration"] >= 0

    def test_transcribe_invalid_path(self, service):
        """Test transcription with invalid audio path"""
        # With mock model, this should still work
        result = service.transcribe("/nonexistent/path.wav")
        assert "text" in result

    def test_transcribe_empty_path(self, service):
        """Test transcription with empty path"""
        result = service.transcribe("")
        assert "text" in result


class TestLanguageDetection:
    """Test language detection functionality"""

    def test_detect_language_basic(self, mock_service):
        """Test basic language detection"""
        language = mock_service.detect_language("/fake/audio.wav")
        assert isinstance(language, str)
        assert len(language) == 2

    def test_detect_language_returns_code(self, mock_service):
        """Test that language detection returns valid code"""
        language = mock_service.detect_language("/fake/audio.wav")
        assert language == "en"  # Mock always returns "en"

    def test_detect_language_invalid_path(self, service):
        """Test language detection with invalid path"""
        language = service.detect_language("/nonexistent/path.wav")
        assert language == "en"  # Should default to English

    def test_detect_language_empty_path(self, service):
        """Test language detection with empty path"""
        language = service.detect_language("")
        assert language == "en"  # Should default to English


class TestModelStatus:
    """Test model status checks"""

    def test_is_loaded_true(self, mock_service):
        """Test that is_loaded returns True when model is loaded"""
        assert mock_service.is_loaded() is True

    def test_model_not_none(self, mock_service):
        """Test that model is not None after initialization"""
        assert mock_service.model is not None

    def test_model_instance_check(self, mock_service):
        """Test that model is correct instance"""
        assert isinstance(mock_service.model, _MockWhisperModel)


class TestMockWhisperModel:
    """Test _MockWhisperModel directly"""

    @pytest.fixture
    def mock_model(self):
        """Create mock model instance"""
        return _MockWhisperModel()

    def test_mock_transcribe(self, mock_model):
        """Test mock transcription"""
        result = mock_model.transcribe("/fake/audio.wav")
        assert "text" in result
        assert "language" in result
        assert "segments" in result

    def test_mock_transcribe_contains_marker(self, mock_model):
        """Test that mock transcription contains MOCK marker"""
        result = mock_model.transcribe("/fake/audio.wav")
        assert "MOCK" in result["text"]

    def test_mock_transcribe_with_language(self, mock_model):
        """Test mock transcription with language"""
        result = mock_model.transcribe("/fake/audio.wav", language="fr")
        assert result["language"] == "fr"

    def test_mock_transcribe_segments_count(self, mock_model):
        """Test mock transcription returns segments"""
        result = mock_model.transcribe("/fake/audio.wav")
        assert len(result["segments"]) == 2

    def test_mock_transcribe_segment_timing(self, mock_model):
        """Test mock segments have timing info"""
        result = mock_model.transcribe("/fake/audio.wav")
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 2.5

    def test_mock_detect_language(self, mock_model):
        """Test mock language detection"""
        language = mock_model.detect_language("/fake/audio.wav")
        assert language == "en"

    def test_mock_transcribe_duration(self, mock_model):
        """Test mock transcription duration"""
        result = mock_model.transcribe("/fake/audio.wav")
        assert result["duration"] == 5.0


class TestTranscriptionParameters:
    """Test various transcription parameters"""

    def test_transcribe_all_languages(self, mock_service):
        """Test transcription with various language codes"""
        languages = ["en", "es", "fr", "de", "it", "pt", "zh", "ja"]
        for lang in languages:
            result = mock_service.transcribe("/fake/audio.wav", language=lang)
            assert result["language"] == lang

    def test_transcribe_temperature_range(self, mock_service):
        """Test transcription with different temperature values"""
        for temp in [0.0, 0.5, 1.0]:
            result = mock_service.transcribe("/fake/audio.wav", temperature=temp)
            assert "text" in result

    def test_transcribe_both_tasks(self, mock_service):
        """Test both transcribe and translate tasks"""
        for task in ["transcribe", "translate"]:
            result = mock_service.transcribe("/fake/audio.wav", task=task)
            assert "text" in result


class TestTranscriptionPerformance:
    """Test performance characteristics"""

    def test_transcription_speed(self, mock_service):
        """Test that transcription completes in reasonable time"""
        start = time.time()
        mock_service.transcribe("/fake/audio.wav")
        duration = time.time() - start
        assert duration < 1.0  # Should be very fast for mock

    def test_language_detection_speed(self, mock_service):
        """Test language detection speed"""
        start = time.time()
        mock_service.detect_language("/fake/audio.wav")
        duration = time.time() - start
        assert duration < 1.0


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_transcribe_with_none_path(self, service):
        """Test transcription with None path"""
        # Mock model should handle gracefully
        result = service.transcribe(None)
        assert "text" in result

    def test_transcribe_with_special_characters(self, service):
        """Test transcription with special characters in path"""
        result = service.transcribe("/path/with spaces/audio.wav")
        assert "text" in result


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_detect_then_transcribe(self, mock_service):
        """Test language detection followed by transcription"""
        language = mock_service.detect_language("/fake/audio.wav")
        result = mock_service.transcribe("/fake/audio.wav", language=language)
        assert result["language"] == language

    def test_multiple_transcriptions_consistency(self, mock_service):
        """Test that multiple transcriptions are consistent"""
        path = "/fake/audio.wav"
        result1 = mock_service.transcribe(path)
        result2 = mock_service.transcribe(path)
        # Mock should return consistent results
        assert result1["text"] == result2["text"]

    def test_batch_transcription(self, mock_service):
        """Test transcribing multiple files"""
        paths = [f"/fake/audio{i}.wav" for i in range(5)]
        results = [mock_service.transcribe(path) for path in paths]
        assert all("text" in r for r in results)


class TestModelLoading:
    """Test model loading behavior"""

    @patch('whisper_service.WHISPER_AVAILABLE', True)
    @patch('whisper_service.whisper.load_model')
    def test_real_model_loading_success(self, mock_load_model):
        """Test successful loading of real Whisper model"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Test transcription",
            "language": "en",
            "segments": []
        }
        mock_load_model.return_value = mock_model

        service = WhisperService(model_size="base")
        assert service.model is not None

    @patch('whisper_service.WHISPER_AVAILABLE', True)
    @patch('whisper_service.whisper.load_model')
    def test_model_loading_failure_fallback(self, mock_load_model):
        """Test fallback to mock when model loading fails"""
        mock_load_model.side_effect = Exception("Load failed")

        service = WhisperService(model_size="base")
        assert isinstance(service.model, _MockWhisperModel)


class TestTranscriptionOutput:
    """Test transcription output format"""

    def test_output_has_all_required_fields(self, mock_service):
        """Test transcription has all required fields"""
        result = mock_service.transcribe("/fake/audio.wav")
        required_fields = ["text", "language", "segments", "duration", "processing_time"]
        for field in required_fields:
            assert field in result

    def test_segments_structure_complete(self, mock_service):
        """Test that segments have complete structure"""
        result = mock_service.transcribe("/fake/audio.wav")
        for segment in result["segments"]:
            assert "start" in segment
            assert "end" in segment
            assert "text" in segment

    def test_text_is_string(self, mock_service):
        """Test that text field is string"""
        result = mock_service.transcribe("/fake/audio.wav")
        assert isinstance(result["text"], str)

    def test_language_is_string(self, mock_service):
        """Test that language field is string"""
        result = mock_service.transcribe("/fake/audio.wav")
        assert isinstance(result["language"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
