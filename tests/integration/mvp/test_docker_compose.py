"""Tests for Docker Compose stack validation."""

import pytest
import requests


@pytest.mark.integration
@pytest.mark.requires_docker
def test_orchestrator_health(orchestrator_url):
    """Test OpenClaw Orchestrator health endpoint."""
    response = requests.get(f"{orchestrator_url}/health", timeout=5)
    assert response.status_code == 200
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    assert data.get("status") == "healthy"


@pytest.mark.integration
@pytest.mark.requires_docker
def test_scenespeak_health(scenespeak_url):
    """Test SceneSpeak Agent health endpoint."""
    response = requests.get(f"{scenespeak_url}/health", timeout=5)
    assert response.status_code == 200
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    assert data.get("status") == "healthy"


@pytest.mark.integration
@pytest.mark.requires_docker
def test_sentiment_health(sentiment_url):
    """Test Sentiment Agent health endpoint."""
    response = requests.get(f"{sentiment_url}/health", timeout=5)
    assert response.status_code == 200
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    assert data.get("status") == "healthy"


@pytest.mark.integration
@pytest.mark.requires_docker
def test_safety_filter_health(safety_url):
    """Test Safety Filter health endpoint."""
    response = requests.get(f"{safety_url}/health", timeout=5)
    assert response.status_code == 200
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    assert data.get("status") == "healthy"


@pytest.mark.integration
@pytest.mark.requires_docker
def test_translation_health(translation_url):
    """Test Translation Agent health endpoint."""
    response = requests.get(f"{translation_url}/health", timeout=5)
    assert response.status_code == 200
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    assert data.get("status") == "healthy"


@pytest.mark.integration
@pytest.mark.requires_docker
def test_hardware_bridge_health(hardware_url):
    """Test Hardware Bridge health endpoint."""
    response = requests.get(f"{hardware_url}/health", timeout=5)
    assert response.status_code == 200
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    assert data.get("status") == "healthy"


@pytest.mark.integration
@pytest.mark.requires_docker
def test_operator_console_health(console_url):
    """Test Operator Console health endpoint."""
    response = requests.get(f"{console_url}/health", timeout=5)
    assert response.status_code == 200
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    assert data.get("status") == "healthy"
