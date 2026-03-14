#!/usr/bin/env python3
"""
Test script for Director Agent

Validates show definition loading, execution engine, and API endpoints.
"""

import asyncio
import httpx
import json
import sys
from pathlib import Path

# Configuration
DIRECTOR_URL = "http://localhost:8013"
SHOW_FILE = Path(__file__).parent / "shows" / "welcome_show.yaml"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


async def test_health_check():
    """Test director agent health check."""
    print_info("Testing health check...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DIRECTOR_URL}/health")

            if response.status_code == 200:
                data = response.json()
                print_success(f"Health check passed: {data['status']}")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_list_shows():
    """Test listing available shows."""
    print_info("Testing list shows...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DIRECTOR_URL}/api/shows")

            if response.status_code == 200:
                data = response.json()
                shows = data.get("shows", [])
                print_success(f"Found {len(shows)} shows")

                for show in shows:
                    print_info(f"  - {show['show_id']}: {show['title']}")

                return True, shows
            else:
                print_error(f"List shows failed: {response.status_code}")
                return False, []

    except Exception as e:
        print_error(f"List shows error: {e}")
        return False, []


async def test_get_show(show_id):
    """Test getting show details."""
    print_info(f"Testing get show: {show_id}...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DIRECTOR_URL}/api/shows/{show_id}")

            if response.status_code == 200:
                data = response.json()
                print_success(f"Show loaded: {data['metadata']['title']}")
                print_info(f"  Scenes: {len(data['scenes'])}")
                return True
            else:
                print_error(f"Get show failed: {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Get show error: {e}")
        return False


async def test_load_show(show_id, file_path):
    """Test loading a show from file."""
    print_info(f"Testing load show from: {file_path}...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DIRECTOR_URL}/api/shows/load",
                json={
                    "show_id": show_id,
                    "file_path": str(file_path)
                }
            )

            if response.status_code == 200:
                data = response.json()
                print_success(f"Show loaded: {data['show_id']}")
                print_info(f"  Title: {data['title']}")
                print_info(f"  Scenes: {data['scenes_count']}")
                return True
            else:
                print_error(f"Load show failed: {response.status_code}")
                print_error(f"  {response.text}")
                return False

    except Exception as e:
        print_error(f"Load show error: {e}")
        return False


async def test_start_show(show_id):
    """Test starting show execution."""
    print_info(f"Testing start show: {show_id}...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DIRECTOR_URL}/api/shows/{show_id}/start",
                json={
                    "start_scene": 0,
                    "require_approval": True
                }
            )

            if response.status_code == 200:
                data = response.json()
                print_success(f"Show started: {data['show_id']}")
                print_info(f"  Status: {data['status']}")
                return True
            else:
                print_error(f"Start show failed: {response.status_code}")
                print_error(f"  {response.text}")
                return False

    except Exception as e:
        print_error(f"Start show error: {e}")
        return False


async def test_get_show_state(show_id):
    """Test getting show state."""
    print_info(f"Testing get show state: {show_id}...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DIRECTOR_URL}/api/shows/{show_id}/state")

            if response.status_code == 200:
                data = response.json()
                print_success(f"Show state retrieved")
                print_info(f"  State: {data['state']}")
                print_info(f"  Scene Index: {data.get('current_scene_index', 'N/A')}")
                return True, data
            else:
                print_error(f"Get show state failed: {response.status_code}")
                return False, None

    except Exception as e:
        print_error(f"Get show state error: {e}")
        return False, None


async def test_pause_show(show_id):
    """Test pausing show."""
    print_info(f"Testing pause show: {show_id}...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{DIRECTOR_URL}/api/shows/{show_id}/pause"
            )

            if response.status_code == 200:
                print_success("Show paused")
                return True
            else:
                print_error(f"Pause show failed: {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Pause show error: {e}")
        return False


async def test_resume_show(show_id):
    """Test resuming show."""
    print_info(f"Testing resume show: {show_id}...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{DIRECTOR_URL}/api/shows/{show_id}/resume"
            )

            if response.status_code == 200:
                print_success("Show resumed")
                return True
            else:
                print_error(f"Resume show failed: {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Resume show error: {e}")
        return False


async def test_stop_show(show_id):
    """Test stopping show."""
    print_info(f"Testing stop show: {show_id}...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{DIRECTOR_URL}/api/shows/{show_id}/stop"
            )

            if response.status_code == 200:
                print_success("Show stopped")
                return True
            else:
                print_error(f"Stop show failed: {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Stop show error: {e}")
        return False


async def run_tests():
    """Run all tests."""
    print(f"\n{Colors.BOLD}Director Agent Test Suite{Colors.END}\n")

    test_show_id = "test_welcome_show"

    # Test 1: Health check
    if not await test_health_check():
        print_error("Director agent is not running. Please start it first:")
        print_error("  python main.py")
        return False

    print()

    # Test 2: List shows
    success, shows = await test_list_shows()
    if not success:
        return False

    print()

    # Test 3: Load show from file
    if not await test_load_show(test_show_id, SHOW_FILE):
        print_warning("Show loading failed, but continuing if show already loaded...")

    print()

    # Test 4: Get show details
    if not await test_get_show(test_show_id):
        print_warning("Get show failed, but continuing...")

    print()

    # Test 5: Start show
    print_warning("Starting show - this will execute in background...")
    if not await test_start_show(test_show_id):
        return False

    print()
    print_info("Waiting 3 seconds for show to start...")

    # Wait for show to start
    await asyncio.sleep(3)

    print()

    # Test 6: Get show state
    success, state = await test_get_show_state(test_show_id)
    if success:
        print_info(f"Current state: {state.get('state', 'unknown')}")

    print()

    # Test 7: Pause show
    if not await test_pause_show(test_show_id):
        print_warning("Pause failed, but continuing...")

    print()
    await asyncio.sleep(1)

    # Test 8: Resume show
    if not await test_resume_show(test_show_id):
        print_warning("Resume failed, but continuing...")

    print()
    await asyncio.sleep(1)

    # Test 9: Stop show
    if not await test_stop_show(test_show_id):
        return False

    print()
    print_success("All tests completed!")

    return True


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test suite error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
