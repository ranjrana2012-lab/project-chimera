#!/usr/bin/env python3
"""
Manual test runner for docker_setup tests.
This allows us to run tests without needing pytest installed.
"""
import subprocess
import sys
import os

def test_docker_group_exists():
    """Test that docker group exists."""
    result = subprocess.run(["getent", "group", "docker"], capture_output=True)
    assert result.returncode == 0, "docker group should exist"
    print("✓ test_docker_group_exists PASSED")

def test_user_in_docker_group():
    """Test that current user is in docker group."""
    user = os.getenv("USER")
    result = subprocess.run(["groups", user], capture_output=True, text=True)
    assert "docker" in result.stdout, f"User {user} should be in docker group. Got: {result.stdout}"
    print("✓ test_user_in_docker_group PASSED")

def test_docker_command_works():
    """Test that docker ps works without sudo."""
    result = subprocess.run(["docker", "ps"], capture_output=True)
    # Should succeed (exit code 0) even if no containers running
    assert result.returncode == 0, f"docker ps should work without sudo. Got exit code: {result.returncode}. Stderr: {result.stderr.decode()}"
    print("✓ test_docker_command_works PASSED")

if __name__ == "__main__":
    print("Running docker setup tests...")
    tests = [
        test_docker_group_exists,
        test_user_in_docker_group,
        test_docker_command_works
    ]
    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed.append((test.__name__, str(e)))
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed.append((test.__name__, str(e)))

    print("\n" + "="*60)
    if failed:
        print(f"FAILED: {len(failed)} test(s) failed")
        for name, error in failed:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print("PASSED: All tests passed")
        sys.exit(0)
