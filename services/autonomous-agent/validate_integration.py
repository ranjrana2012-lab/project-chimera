#!/usr/bin/env python3
"""
Validation script for multi-agent integration.

Checks that all components are properly configured and can be imported.
"""

import sys
from pathlib import Path


def print_success(msg):
    print(f"✓ {msg}")


def print_error(msg):
    print(f"✗ {msg}")


def print_info(msg):
    print(f"ℹ {msg}")


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print_success(f"{description} imports successfully")
        return True
    except ImportError as e:
        print_error(f"{description} import failed: {e}")
        return False
    except Exception as e:
        print_error(f"{description} error: {e}")
        return False


def main():
    """Run validation checks."""
    print_header = "=" * 70
    print(f"\n{print_header}")
    print("Multi-Agent Integration Validation".center(70))
    print(f"{print_header}\n")

    all_passed = True

    # Check new files exist
    print("Checking new files...")
    all_passed &= check_file_exists(
        "openclaw_client.py",
        "OpenClaw Client"
    )
    all_passed &= check_file_exists(
        "vmao_verifier.py",
        "VMAO Verifier"
    )
    all_passed &= check_file_exists(
        "tests/integration/test_multi_agent_integration.py",
        "Integration Tests"
    )
    all_passed &= check_file_exists(
        "demo_multi_agent.py",
        "Demo Script"
    )
    all_passed &= check_file_exists(
        "MULTI_AGENT_INTEGRATION.md",
        "Integration Documentation"
    )

    print()

    # Check imports
    print("Checking imports...")
    all_passed &= check_import("openclaw_client", "OpenClaw Client")
    all_passed &= check_import("vmao_verifier", "VMAO Verifier")
    all_passed &= check_import("gsd_orchestrator", "GSD Orchestrator")
    all_passed &= check_import("ralph_engine", "Ralph Engine")

    print()

    # Check configuration
    print("Checking configuration...")
    try:
        from config import get_settings
        settings = get_settings()

        if hasattr(settings, 'openclaw_url'):
            print_success(f"OpenClaw URL configured: {settings.openclaw_url}")
        else:
            print_error("OpenClaw URL not configured")
            all_passed = False

        if hasattr(settings, 'enable_multi_agent'):
            status = "enabled" if settings.enable_multi_agent else "disabled"
            print_info(f"Multi-agent mode: {status}")
        else:
            print_warning("enable_multi_agent not in config (uses default)")

    except Exception as e:
        print_error(f"Configuration check failed: {e}")
        all_passed = False

    print()

    # Summary
    if all_passed:
        print("=" * 70)
        print("✓ All validation checks passed!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Start OpenClaw Orchestrator: cd ../openclaw-orchestrator && python main.py")
        print("  2. Start Autonomous Agent: python main.py")
        print("  3. Run demo: python demo_multi_agent.py")
        print("  4. Run tests: pytest tests/integration/test_multi_agent_integration.py -v")
        return 0
    else:
        print("=" * 70)
        print("✗ Some validation checks failed")
        print("=" * 70)
        print("\nPlease review the errors above and fix them before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
