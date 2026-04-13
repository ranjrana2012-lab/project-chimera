"""Test Docker safety helper scripts."""

import subprocess
import os
from pathlib import Path


def test_preflight_script_exists():
    """Test that pre-flight check script exists and is executable."""
    script = Path("scripts/docker-preflight-check.sh")
    assert script.exists()
    assert os.access(script, os.X_OK)


def test_postbuild_script_exists():
    """Test that post-build check script exists and is executable."""
    script = Path("scripts/docker-postbuild-check.sh")
    assert script.exists()
    assert os.access(script, os.X_OK)


def test_preflight_runs():
    """Test that pre-flight check runs without error."""
    result = subprocess.run(
        ["./scripts/docker-preflight-check.sh"],
        capture_output=True,
        text=True
    )
    assert result.returncode in [0, 1]  # 0 = pass, 1 = warnings
    assert "Docker Pre-Flight Check" in result.stdout


def test_postbuild_runs():
    """Test that post-build check runs without error."""
    result = subprocess.run(
        ["./scripts/docker-postbuild-check.sh"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Docker Post-Build Check" in result.stdout


def test_master_prompt_exists():
    """Test that master prompt file exists."""
    prompt = Path(".claude/RALPH_LOOP_MASTER_PROMPT.md")
    assert prompt.exists()
    content = prompt.read_text()
    assert "CRITICAL CONSTRAINTS" in content
    assert "Docker Build Safety" in content


def test_docker_safety_reference_exists():
    """Test that Docker safety reference exists."""
    reference = Path("docs/superpowers/DOCKER_SAFETY_REFERENCE.md")
    assert reference.exists()
    content = reference.read_text()
    assert "Pre-Flight Checklist" in content
    assert "docker system df" in content
