"""Unit tests for GitHub webhook integration."""
import sys
from pathlib import Path

# Add parent directory to sys.path to avoid conflict with built-in platform module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from ci_gateway.github import GitHubClient, verify_github_signature
import hmac
import hashlib


@pytest.mark.asyncio
async def test_verify_github_signature_valid():
    """Test signature verification with valid signature."""
    secret = "test-secret"
    payload = b'{"test": "data"}'

    # Create valid signature
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"

    result = await verify_github_signature(payload, expected_signature, secret)
    assert result is True


@pytest.mark.asyncio
async def test_verify_github_signature_invalid():
    """Test signature verification with invalid signature."""
    secret = "test-secret"
    payload = b'{"test": "data"}'
    invalid_signature = "sha256=invalid"

    result = await verify_github_signature(payload, invalid_signature, secret)
    assert result is False


@pytest.mark.asyncio
async def test_verify_github_signature_empty():
    """Test signature verification with empty signature."""
    secret = "test-secret"
    payload = b'{"test": "data"}'

    result = await verify_github_signature(payload, "", secret)
    assert result is False


@pytest.mark.asyncio
async def test_verify_github_signature_wrong_algorithm():
    """Test signature verification with wrong algorithm."""
    secret = "test-secret"
    payload = b'{"test": "data"}'
    wrong_signature = "sha1=something"

    result = await verify_github_signature(payload, wrong_signature, secret)
    assert result is False


def test_github_client_initialization():
    """Test GitHubClient initialization."""
    client = GitHubClient("test-token")
    assert client.token == "test-token"
    assert client.base_url == "https://api.github.com"
    assert "Authorization" in client.headers
    assert client.headers["Authorization"] == "token test-token"
    assert "Accept" in client.headers
