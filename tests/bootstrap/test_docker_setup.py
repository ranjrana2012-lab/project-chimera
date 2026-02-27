import subprocess
import pytest

def test_docker_group_exists():
    """Test that docker group exists."""
    result = subprocess.run(["getent", "group", "docker"], capture_output=True)
    assert result.returncode == 0, "docker group should exist"

def test_user_in_docker_group():
    """Test that current user is in docker group."""
    import os
    user = os.getenv("USER")
    result = subprocess.run(["groups", user], capture_output=True, text=True)
    assert "docker" in result.stdout, f"User {user} should be in docker group"

def test_docker_command_works():
    """Test that docker ps works without sudo."""
    result = subprocess.run(["docker", "ps"], capture_output=True)
    # Should succeed (exit code 0) even if no containers running
    assert result.returncode == 0, "docker ps should work without sudo"
