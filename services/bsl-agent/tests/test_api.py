"""
Tests for BSL Agent API Endpoints

Comprehensive test suite for API endpoint coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient


@pytest.fixture
def mock_translator():
    """Mock translator instance."""
    with patch('api.main.get_translator') as mock:
        translator = Mock()
        mock.return_value = translator
        yield translator


@pytest.fixture
def client(mock_translator):
    """Create test client with mocked translator."""
    # Import after mocking to avoid initialization issues
    from api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_data(self, client):
        """Test health check returns correct service information."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bsl-agent"
        assert "version" in data


class TestTranslateEndpoint:
    """Tests for translate endpoint."""

    def test_translate_returns_200_on_success(self, client, mock_translator):
        """Test translate endpoint returns 200 on successful translation."""
        # Mock translation response
        mock_response = Mock()
        mock_response.request_id = "test-123"
        mock_response.source_text = "Hello"
        mock_response.gloss = "HELLO"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 1.5
        mock_response.confidence = 0.85
        mock_response.translation_time_ms = 100
        mock_response.breakdown = ["HELLO"]
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": "Hello",
            "language": "en",
            "gloss_format": "singspell"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == "test-123"
        assert data["source_text"] == "Hello"
        assert data["gloss"] == "HELLO"

    def test_translate_handles_missing_optional_fields(self, client, mock_translator):
        """Test translate endpoint handles missing optional fields."""
        mock_response = Mock()
        mock_response.request_id = "test-456"
        mock_response.source_text = "Test"
        mock_response.gloss = "TEST"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 1.0
        mock_response.confidence = 0.9
        mock_response.translation_time_ms = 50
        mock_response.breakdown = ["TEST"]
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": "Test"
        })

        assert response.status_code == 200

    def test_translate_handles_empty_text(self, client, mock_translator):
        """Test translate endpoint handles empty text."""
        mock_response = Mock()
        mock_response.request_id = "empty-123"
        mock_response.source_text = ""
        mock_response.gloss = ""
        mock_response.gloss_format = "singspell"
        mock_response.duration = 0.5
        mock_response.confidence = 0.0
        mock_response.translation_time_ms = 10
        mock_response.breakdown = []
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": ""
        })

        assert response.status_code == 200

    def test_translate_returns_500_on_error(self, client, mock_translator):
        """Test translate endpoint returns 500 on error."""
        mock_translator.translate.side_effect = Exception("Translation failed")

        response = client.post("/api/v1/translate", json={
            "text": "Hello"
        })

        assert response.status_code == 500

    def test_translate_with_region(self, client, mock_translator):
        """Test translate endpoint with region parameter."""
        mock_response = Mock()
        mock_response.request_id = "regional-123"
        mock_response.source_text = "Hello"
        mock_response.gloss = "HELLO[north]"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 1.5
        mock_response.confidence = 0.85
        mock_response.translation_time_ms = 100
        mock_response.breakdown = ["HELLO[north]"]
        mock_response.non_manual_markers = []
        mock_response.region = "northern"
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": "Hello",
            "region": "northern"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "northern"


class TestBatchTranslateEndpoint:
    """Tests for batch translate endpoint."""

    def test_batch_translate_returns_200_on_success(self, client, mock_translator):
        """Test batch translate returns 200 on success."""
        mock_results = [
            Mock(
                request_id=f"batch-{i}",
                source_text=f"Text {i}",
                gloss=f"GLOSS {i}",
                gloss_format="singspell",
                duration=1.0,
                confidence=0.8 + (i * 0.05)
            )
            for i in range(3)
        ]

        mock_translator.translate_batch.return_value = mock_results

        response = client.post("/api/v1/translate/batch", json={
            "texts": [
                {"text": "Text 0"},
                {"text": "Text 1"},
                {"text": "Text 2"}
            ]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["translations"]) == 3
        assert "processing_time_ms" in data

    def test_batch_translate_handles_empty_list(self, client, mock_translator):
        """Test batch translate handles empty list."""
        mock_translator.translate_batch.return_value = []

        response = client.post("/api/v1/translate/batch", json={
            "texts": []
        })

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["translations"] == []

    def test_batch_translate_with_options(self, client, mock_translator):
        """Test batch translate with format and language options."""
        mock_results = [
            Mock(
                request_id="opts-123",
                source_text="Test",
                gloss="TEST",
                gloss_format="singspell",
                duration=1.0,
                confidence=0.85
            )
        ]

        mock_translator.translate_batch.return_value = mock_results

        response = client.post("/api/v1/translate/batch", json={
            "texts": [
                {
                    "text": "Test",
                    "language": "en",
                    "gloss_format": "singspell",
                    "region": "southern"
                }
            ]
        })

        assert response.status_code == 200

    def test_batch_translate_returns_500_on_error(self, client, mock_translator):
        """Test batch translate returns 500 on error."""
        mock_translator.translate_batch.side_effect = Exception("Batch failed")

        response = client.post("/api/v1/translate/batch", json={
            "texts": [{"text": "Test"}]
        })

        assert response.status_code == 500


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""

    def test_metrics_returns_200(self, client):
        """Test metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_plain_text(self, client):
        """Test metrics endpoint returns plain text content type."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_translate_with_long_text(self, client, mock_translator):
        """Test translate with very long text."""
        long_text = "Hello " * 1000

        mock_response = Mock()
        mock_response.request_id = "long-123"
        mock_response.source_text = long_text
        mock_response.gloss = "HELLO " * 1000
        mock_response.gloss_format = "singspell"
        mock_response.duration = 5.0
        mock_response.confidence = 0.7
        mock_response.translation_time_ms = 500
        mock_response.breakdown = ["HELLO"] * 1000
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": long_text
        })

        assert response.status_code == 200

    def test_translate_with_special_characters(self, client, mock_translator):
        """Test translate with special characters."""
        special_text = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?"

        mock_response = Mock()
        mock_response.request_id = "special-123"
        mock_response.source_text = special_text
        mock_response.gloss = "HELLO"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 1.5
        mock_response.confidence = 0.8
        mock_response.translation_time_ms = 120
        mock_response.breakdown = ["HELLO"]
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": special_text
        })

        assert response.status_code == 200

    def test_translate_with_unicode(self, client, mock_translator):
        """Test translate with unicode characters."""
        unicode_text = "Hello 世界 🌍"

        mock_response = Mock()
        mock_response.request_id = "unicode-123"
        mock_response.source_text = unicode_text
        mock_response.gloss = "HELLO"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 1.5
        mock_response.confidence = 0.8
        mock_response.translation_time_ms = 120
        mock_response.breakdown = ["HELLO"]
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": unicode_text
        })

        assert response.status_code == 200

    def test_translate_with_non_standard_language(self, client, mock_translator):
        """Test translate with non-standard language code."""
        mock_response = Mock()
        mock_response.request_id = "lang-123"
        mock_response.source_text = "Bonjour"
        mock_response.gloss = "BONJOUR"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 1.5
        mock_response.confidence = 0.85
        mock_response.translation_time_ms = 100
        mock_response.breakdown = ["BONJOUR"]
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": "Bonjour",
            "language": "fr"
        })

        assert response.status_code == 200


class TestCachedTranslations:
    """Tests for cached translation behavior."""

    def test_translate_with_cached_result(self, client, mock_translator):
        """Test translate returns correct response when result is from cache."""
        mock_response = Mock()
        mock_response.request_id = "cached-123"
        mock_response.source_text = "Hello"
        mock_response.gloss = "HELLO"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 0.1
        mock_response.confidence = 0.9
        mock_response.translation_time_ms = 10
        mock_response.breakdown = ["HELLO"]
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = True
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": "Hello"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["from_cache"] is True


class TestDegradedTranslations:
    """Tests for degraded translation behavior."""

    def test_translate_with_degraded_result(self, client, mock_translator):
        """Test translate returns correct response when result is degraded."""
        mock_response = Mock()
        mock_response.request_id = "degraded-123"
        mock_response.source_text = "Hello"
        mock_response.gloss = "HELLO"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 3.0
        mock_response.confidence = 0.5
        mock_response.translation_time_ms = 200
        mock_response.breakdown = ["HELLO"]
        mock_response.non_manual_markers = []
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = True

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": "Hello"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["degraded"] is True


class TestNonManualMarkers:
    """Tests for non-manual markers in translations."""

    def test_translate_with_non_manual_markers(self, client, mock_translator):
        """Test translate returns non-manual markers."""
        mock_response = Mock()
        mock_response.request_id = "nmm-123"
        mock_response.source_text = "Really good"
        mock_response.gloss = "GOOD[really]"
        mock_response.gloss_format = "singspell"
        mock_response.duration = 2.0
        mock_response.confidence = 0.85
        mock_response.translation_time_ms = 150
        mock_response.breakdown = ["GOOD[really]"]
        mock_response.non_manual_markers = ["facial_expression", "body_movement"]
        mock_response.region = None
        mock_response.from_cache = False
        mock_response.error = None
        mock_response.degraded = False

        mock_translator.translate.return_value = mock_response

        response = client.post("/api/v1/translate", json={
            "text": "Really good"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["non_manual_markers"] == ["facial_expression", "body_movement"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
