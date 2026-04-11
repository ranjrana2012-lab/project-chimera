"""Integration tests for Hardware Bridge (echo-agent DMX output).

Tests the sentiment-to-DMX lighting control bridge.
"""

import pytest
import requests


@pytest.mark.integration
def test_hardware_dmx_output_positive(hardware_url):
    """Test DMX output for positive sentiment produces warm colors.

    SPEC REQUIREMENT:
    - Positive sentiment → warm colors (high red/green, low blue)
    - Red channel should be high (>150)
    - Green channel should be high (>150)
    - Blue channel should be low (<100)
    """
    response = requests.post(
        f"{hardware_url}/dmx/output",
        json={
            "sentiment": "positive",
            "score": 0.95
        },
        timeout=10
    )

    assert response.status_code == 200
    data = response.json()

    # Response structure
    assert "status" in data
    assert data["status"] == "sent"
    assert "channels" in data
    assert "timestamp" in data

    # Warm color validation
    channels = data["channels"]
    assert "1_red" in channels
    assert "2_green" in channels
    assert "3_blue" in channels

    # Positive = warm colors (high red/green, low blue)
    assert channels["1_red"] > 150, f"Red should be high for positive, got {channels['1_red']}"
    assert channels["2_green"] > 150, f"Green should be medium-high for positive, got {channels['2_green']}"
    assert channels["3_blue"] < 100, f"Blue should be low for positive, got {channels['3_blue']}"


@pytest.mark.integration
def test_hardware_dmx_output_negative(hardware_url):
    """Test DMX output for negative sentiment produces cool colors.

    SPEC REQUIREMENT:
    - Negative sentiment → cool colors (low red/green, high blue)
    - Red channel should be low (<100)
    - Green channel should be low (<100)
    - Blue channel should be high (>200)
    """
    response = requests.post(
        f"{hardware_url}/dmx/output",
        json={
            "sentiment": "negative",
            "score": -0.85
        },
        timeout=10
    )

    assert response.status_code == 200
    data = response.json()

    # Response structure
    assert "channels" in data
    channels = data["channels"]

    # Cool color validation
    assert "1_red" in channels
    assert "2_green" in channels
    assert "3_blue" in channels

    # Negative = cool colors (low red/green, high blue)
    assert channels["1_red"] < 100, f"Red should be low for negative, got {channels['1_red']}"
    assert channels["2_green"] < 100, f"Green should be low for negative, got {channels['2_green']}"
    assert channels["3_blue"] > 200, f"Blue should be high for negative, got {channels['3_blue']}"


@pytest.mark.integration
def test_hardware_dmx_output_neutral(hardware_url):
    """Test DMX output for neutral sentiment produces balanced/white colors.

    SPEC REQUIREMENT:
    - Neutral sentiment → white/balanced colors
    - All RGB channels should be high (>150) to produce white/bright output
    """
    response = requests.post(
        f"{hardware_url}/dmx/output",
        json={
            "sentiment": "neutral",
            "score": 0.0
        },
        timeout=10
    )

    assert response.status_code == 200
    data = response.json()

    # Response structure
    assert "channels" in data
    channels = data["channels"]

    # Balanced color validation
    assert "1_red" in channels
    assert "2_green" in channels
    assert "3_blue" in channels

    # Neutral = balanced colors (all channels high for white/bright)
    assert channels["1_red"] > 150, f"Red should be high for neutral, got {channels['1_red']}"
    assert channels["2_green"] > 150, f"Green should be high for neutral, got {channels['2_green']}"
    assert channels["3_blue"] > 150, f"Blue should be high for neutral, got {channels['3_blue']}"


@pytest.mark.integration
def test_hardware_dmx_custom_channels(hardware_url):
    """Test custom channel override functionality.

    SPEC REQUIREMENT:
    - Optional 'channels' parameter overrides calculated values
    - Custom channels should be returned in response
    - All channel values must be 0-255
    """
    custom_channels = {
        "1_red": 10,
        "2_green": 20,
        "3_blue": 30,
        "4_brightness": 255,
        "5_effect": 3
    }

    response = requests.post(
        f"{hardware_url}/dmx/output",
        json={
            "sentiment": "positive",
            "score": 0.5,
            "channels": custom_channels
        },
        timeout=10
    )

    assert response.status_code == 200
    data = response.json()

    # Custom channels should be reflected in response
    assert "channels" in data
    channels = data["channels"]

    for key, value in custom_channels.items():
        assert key in channels, f"Custom channel {key} not in response"
        assert channels[key] == value, f"Custom channel {key} has value {channels[key]}, expected {value}"


@pytest.mark.integration
def test_hardware_dmx_sentiment_extremes(hardware_url):
    """Test DMX output for sentiment score extremes.

    SPEC REQUIREMENT:
    - Score 1.0 (maximum positive) → maximum warm colors
    - Score -1.0 (maximum negative) → maximum cool colors
    - Brightness/effect speed should scale with score magnitude
    """
    # Test maximum positive
    response_pos = requests.post(
        f"{hardware_url}/dmx/output",
        json={
            "sentiment": "positive",
            "score": 1.0
        },
        timeout=10
    )

    assert response_pos.status_code == 200
    data_pos = response_pos.json()

    # Maximum positive should have maximum brightness
    assert data_pos["channels"]["4_brightness"] >= 200

    # Test maximum negative
    response_neg = requests.post(
        f"{hardware_url}/dmx/output",
        json={
            "sentiment": "negative",
            "score": -1.0
        },
        timeout=10
    )

    assert response_neg.status_code == 200
    data_neg = response_neg.json()

    # Maximum negative should have high cool color intensity
    assert data_neg["channels"]["3_blue"] >= 200


@pytest.mark.integration
def test_hardware_channel_calculations(hardware_url):
    """Test that all DMX channel values are within valid range.

    SPEC REQUIREMENT:
    - All DMX channel values must be 0-255
    - Standard DMX protocol range validation
    """
    test_cases = [
        {"sentiment": "positive", "score": 0.75},
        {"sentiment": "negative", "score": -0.75},
        {"sentiment": "neutral", "score": 0.0},
        {"sentiment": "positive", "score": 1.0},
        {"sentiment": "negative", "score": -1.0},
    ]

    for test_case in test_cases:
        response = requests.post(
            f"{hardware_url}/dmx/output",
            json=test_case,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()

        # All channels must be in valid DMX range (0-255)
        for channel_name, channel_value in data["channels"].items():
            assert 0 <= channel_value <= 255, \
                f"Channel {channel_name} value {channel_value} not in valid DMX range [0-255] for {test_case}"


@pytest.mark.integration
def test_hardware_health_indicates_dmx_mode(hardware_url):
    """Test that health endpoint indicates hardware/DMX mode.

    SPEC REQUIREMENT:
    - Health endpoint should show "hardware" or "echo" in service name
    - Health endpoint should indicate DMX capability
    - Status should be healthy
    """
    response = requests.get(f"{hardware_url}/health", timeout=10)

    assert response.status_code == 200
    data = response.json()

    # Health response structure
    assert "status" in data
    assert "service" in data
    assert data["status"] == "healthy"

    # Should indicate hardware or echo service
    service_name = data["service"].lower()
    assert "hardware" in service_name or "echo" in service_name, \
        f"Service name should indicate hardware/echo capability, got: {data['service']}"
