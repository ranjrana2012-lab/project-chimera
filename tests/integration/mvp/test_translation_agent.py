"""Integration tests for Translation Agent.

Tests the mock-based translation service for MVP.
"""

import pytest
import requests


def test_translation_mock(translation_url):
    """Test mock translation (MVP uses mock).

    Verify that the translation service returns mock translations
    with the expected language prefix format.
    """
    response = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Hello world",
            "source_language": "en",
            "target_language": "es",
        },
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert "translated_text" in data
    assert data["translated_text"] == "[ES] Hello world"
    assert data["source_language"] == "en"
    assert data["target_language"] == "es"
    assert data["status"] == "completed"
    assert "confidence" in data
    assert isinstance(data["confidence"], (int, float))
    assert 0.0 <= data["confidence"] <= 1.0


def test_translation_language_detection(translation_url):
    """Test automatic language detection.

    Verify that the service accepts explicit source_language parameter.
    In MVP, language detection is not implemented - source language
    must be provided explicitly.
    """
    response = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Bonjour le monde",
            "source_language": "fr",
            "target_language": "en",
        },
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert data["translated_text"] == "[EN] Bonjour le monde"
    assert data["source_language"] == "fr"
    assert data["target_language"] == "en"


def test_translation_missing_text(translation_url):
    """Test translation with missing text field asserts 422.

    The API should return 422 (Unprocessable Entity) when the required
    'text' field is missing from the request.
    """
    response = requests.post(
        f"{translation_url}/translate",
        json={
            "source_language": "en",
            "target_language": "es",
        },
        timeout=30
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data or "detail" in data


def test_translation_missing_target_language(translation_url):
    """Test translation with missing target_language asserts 422.

    The API should return 422 (Unprocessable Entity) when the required
    'target_language' field is missing from the request.
    """
    response = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Hello world",
            "source_language": "en",
        },
        timeout=30
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data or "detail" in data


def test_translation_cache(translation_url):
    """Test translation result caching.

    Verify that repeated translation requests return cached results.
    The cached flag should be True for cached translations.
    """
    # First request - not cached
    response1 = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Cache test",
            "source_language": "en",
            "target_language": "de",
        },
        timeout=30
    )

    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["cached"] is False

    # Second request - should be cached
    response2 = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Cache test",
            "source_language": "en",
            "target_language": "de",
        },
        timeout=30
    )

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["cached"] is True
    assert data2["translated_text"] == data1["translated_text"]


def test_translation_supported_languages(translation_url):
    """Test GET /languages endpoint.

    Verify that the /languages endpoint returns a list of supported
    languages with proper language codes and names.
    """
    response = requests.get(f"{translation_url}/languages", timeout=30)

    assert response.status_code == 200
    data = response.json()

    assert "languages" in data
    languages = data["languages"]
    assert isinstance(languages, list)
    assert len(languages) > 0

    # Check structure of language entries
    for lang in languages:
        assert "code" in lang
        assert "name" in lang
        assert isinstance(lang["code"], str)
        assert isinstance(lang["name"], str)

    # Verify expected languages are present
    language_codes = [lang["code"] for lang in languages]
    assert "en" in language_codes  # English
    assert "es" in language_codes  # Spanish
    assert "fr" in language_codes  # French
    assert "de" in language_codes  # German
    assert "bsl" in language_codes  # British Sign Language


def test_translation_mock_note(translation_url):
    """Test health endpoint indicates mock mode.

    Verify that the health endpoint shows the service is running in
    mock mode, which is the expected configuration for MVP.
    """
    response = requests.get(f"{translation_url}/health", timeout=30)

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data

    # Check engine health info
    assert "engine" in data
    engine = data["engine"]
    assert "mock_mode" in engine
    assert engine["mock_mode"] is True


def test_translation_empty_text(translation_url):
    """Test translation with empty text returns 422.

    The API should return 422 (Unprocessable Entity) when text is empty
    due to Pydantic validation (min_length=1).
    """
    response = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "",
            "source_language": "en",
            "target_language": "es",
        },
        timeout=30
    )

    assert response.status_code == 422


def test_translation_bsl_mock(translation_url):
    """Test BSL (British Sign Language) translation mock.

    BSL translation uses a special mock prefix [BSL] in MVP.
    """
    response = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Hello",
            "source_language": "en",
            "target_language": "bsl",
        },
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()

    assert data["translated_text"] == "[BSL] Hello"
    assert data["target_language"] == "bsl"


def test_translation_multiple_languages(translation_url):
    """Test translation to multiple target languages.

    Verify that the service correctly handles different target languages
    with appropriate language prefixes.
    """
    test_cases = [
        ("en", "es", "[ES] "),
        ("en", "fr", "[FR] "),
        ("en", "de", "[DE] "),
        ("en", "ja", "[JA] "),
        ("en", "zh", "[ZH] "),
    ]

    for source, target, expected_prefix in test_cases:
        response = requests.post(
            f"{translation_url}/translate",
            json={
                "text": "Test",
                "source_language": source,
                "target_language": target,
            },
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"].startswith(expected_prefix)


def test_translation_cache_clear(translation_url):
    """Test clearing translation cache.

    Verify that the cache can be cleared via the /translate/cache/clear endpoint.
    """
    # Make a request to populate cache
    requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Cache clear test",
            "source_language": "en",
            "target_language": "it",
        },
        timeout=30
    )

    # Clear cache
    clear_response = requests.post(f"{translation_url}/translate/cache/clear", timeout=30)
    assert clear_response.status_code == 200
    data = clear_response.json()
    assert data["status"] == "cache_cleared"

    # Verify next request is not cached
    response = requests.post(
        f"{translation_url}/translate",
        json={
            "text": "Cache clear test",
            "source_language": "en",
            "target_language": "it",
        },
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cached"] is False


def test_translation_root_endpoint(translation_url):
    """Test root endpoint returns service information.

    Verify that the root endpoint provides basic service info and
    lists available endpoints.
    """
    response = requests.get(f"{translation_url}/", timeout=30)

    assert response.status_code == 200
    data = response.json()

    assert "service" in data
    assert data["service"] == "translation-agent"
    assert "version" in data
    assert "endpoints" in data

    endpoints = data["endpoints"]
    assert "health" in endpoints
    assert "languages" in endpoints
    assert "translate" in endpoints


def test_translation_readiness(translation_url):
    """Test readiness check endpoint.

    Verify that the readiness endpoint returns proper status.
    """
    response = requests.get(f"{translation_url}/readiness", timeout=30)

    assert response.status_code == 200
    data = response.json()

    assert "ready" in data
    assert isinstance(data["ready"], bool)
    assert "engine" in data


def test_translation_liveness(translation_url):
    """Test liveness check endpoint.

    Verify that the liveness endpoint indicates the service is alive.
    """
    response = requests.get(f"{translation_url}/liveness", timeout=30)

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "alive"
