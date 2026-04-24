#!/usr/bin/env python3
"""
Pre-Execution Prerequisites Verification Script

This script verifies that all prerequisites are met before executing
the automation tools for final submission.

Usage:
    python verify_prerequisites.py
"""

import sys
import subprocess
from pathlib import Path
import importlib.util


class PrerequisiteChecker:
    """Checks system prerequisites for automation tools."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def check(self, name: str, passed: bool, message: str = ""):
        """Record a check result."""
        if passed:
            print(f"✅ {name}")
            self.checks_passed += 1
        else:
            print(f"❌ {name}")
            if message:
                print(f"   {message}")
            self.checks_failed += 1

    def warn(self, message: str):
        """Record a warning."""
        print(f"⚠️  {message}")
        self.warnings += 1

    def check_python_version(self):
        """Check Python version."""
        version = sys.version_info
        passed = version >= (3, 10)
        self.check(
            f"Python Version: {version.major}.{version.minor}.{version.micro}",
            passed,
            "Python 3.10+ required" if not passed else ""
        )

    def check_module(self, module_name: str, package_name: str = None):
        """Check if a Python module is available."""
        package_name = package_name or module_name
        spec = importlib.util.find_spec(module_name)
        passed = spec is not None
        self.check(
            f"Module: {module_name}",
            passed,
            f"Install: pip install {package_name}" if not passed else ""
        )

    def check_file_exists(self, path: str, required: bool = True):
        """Check if a file exists."""
        p = Path(path)
        passed = p.exists()
        if required:
            self.check(
                f"File: {path}",
                passed,
                "Required file missing" if not passed else ""
            )
        else:
            if passed:
                print(f"✅ File: {path} (optional)")
            else:
                self.warn(f"Optional file: {path} (not found)")

    def check_directory_exists(self, path: str, required: bool = True):
        """Check if a directory exists."""
        p = Path(path)
        passed = p.is_dir()
        if required:
            self.check(
                f"Directory: {path}",
                passed,
                "Required directory missing" if not passed else ""
            )
        else:
            if passed:
                print(f"✅ Directory: {path} (optional)")
            else:
                self.warn(f"Optional directory: {path} (not found)")

    def check_command_available(self, command: str):
        """Check if a command is available."""
        try:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                text=True
            )
            passed = result.returncode == 0
            self.check(
                f"Command: {command}",
                passed,
                f"Install {command}" if not passed else ""
            )
        except Exception:
            self.check(f"Command: {command}", False, "Could not check")

    def check_chimera_core(self):
        """Verify chimera_core.py exists and is syntactically valid."""
        chimera_path = Path("services/operator-console/chimera_core.py")
        if not chimera_path.exists():
            self.check("chimera_core.py", False, "File not found")
            return

        try:
            # Try to compile the file
            with open(chimera_path, 'r') as f:
                compile(f.read(), chimera_path, 'exec')
            self.check("chimera_core.py syntax", True)
        except SyntaxError as e:
            self.check("chimera_core.py syntax", False, str(e))

    def run_all_checks(self):
        """Run all prerequisite checks."""
        print("="*60)
        print("PROJECT CHIMERA - PREREQUISITE VERIFICATION")
        print("="*60)
        print()

        # Python environment
        print("🐍 Python Environment:")
        self.check_python_version()
        self.check_module("torch", "torch")
        self.check_module("transformers", "transformers")
        self.check_module("openai", "openai")
        print()

        # Required files
        print("📁 Required Files:")
        self.check_file_exists("services/operator-console/chimera_core.py")
        self.check_file_exists("services/operator-console/requirements.txt")
        self.check_file_exists("services/operator-console/chimera_web.py")
        self.check_file_exists("docker-compose.student.yml")
        print()

        # Commands
        print("🔧 System Commands:")
        self.check_command_available("python3")
        self.check_command_available("bash")
        self.check_command_available("git")
        print()

        # chimera_core.py syntax
        print("🔍 Code Quality:")
        self.check_chimera_core()
        print()

        # Summary
        print("="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print()

        if self.checks_failed == 0:
            print("✅ All prerequisites met! Ready to execute Project Chimera.")
            print()
            print("Next steps:")
            print("1. Run: docker compose -f docker-compose.student.yml up")
            print("2. Or to run locally: cd services/operator-console && python chimera_web.py")
            return True
        else:
            print("❌ Some prerequisites not met. Please fix failed checks above.")
            return False


def main():
    """Main entry point."""
    checker = PrerequisiteChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
