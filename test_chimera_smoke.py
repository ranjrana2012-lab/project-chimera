#!/usr/bin/env python3
"""
Smoke Test Runner for chimera_core.py

This script runs quick smoke tests to verify chimera_core.py works correctly.

Usage:
    python test_chimera_smoke.py
"""

import sys
import subprocess
import time
from pathlib import Path


class SmokeTestRunner:
    """Runs smoke tests against chimera_core.py."""

    def __init__(self):
        self.chimera_path = Path("services/operator-console/chimera_core.py")
        self.tests_passed = 0
        self.tests_failed = 0

    def test(self, name: str, passed: bool, output: str = ""):
        """Record a test result."""
        if passed:
            print(f"✅ {name}")
            self.tests_passed += 1
        else:
            print(f"❌ {name}")
            if output:
                print(f"   Output: {output[:200]}")
            self.tests_failed += 1

    def test_help(self):
        """Test --help flag."""
        try:
            result = subprocess.run(
                [sys.executable, str(self.chimera_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.chimera_path.parent
            )
            passed = result.returncode == 0 and "usage" in result.stdout.lower()
            self.test("Help flag", passed)
        except Exception as e:
            self.test("Help flag", False, str(e))

    def test_sentiment_only(self):
        """Test sentiment-only mode."""
        try:
            result = subprocess.run(
                [sys.executable, str(self.chimera_path), "--sentiment-only"],
                input="I'm so excited to be here!\n",
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self.chimera_path.parent
            )
            passed = (
                result.returncode == 0 and
                ("sentiment" in result.stdout.lower() or "positive" in result.stdout.lower())
            )
            self.test("Sentiment-only mode", passed)
        except subprocess.TimeoutExpired:
            self.test("Sentiment-only mode", False, "Timeout")
        except Exception as e:
            self.test("Sentiment-only mode", False, str(e))

    def test_batch_mode(self):
        """Test batch mode."""
        try:
            input_text = "I'm excited\nI'm worried\nquit\n"
            result = subprocess.run(
                [sys.executable, str(self.chimera_path), "--batch"],
                input=input_text,
                capture_output=True,
                text=True,
                timeout=20,
                cwd=self.chimera_path.parent
            )
            passed = result.returncode == 0
            self.test("Batch mode", passed)
        except subprocess.TimeoutExpired:
            self.test("Batch mode", False, "Timeout")
        except Exception as e:
            self.test("Batch mode", False, str(e))

    def test_caption_mode(self):
        """Test caption mode."""
        try:
            input_text = "caption\nThis is wonderful!\nquit\n"
            result = subprocess.run(
                [sys.executable, str(self.chimera_path)],
                input=input_text,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self.chimera_path.parent
            )
            passed = (
                result.returncode == 0 and
                ("caption" in result.stdout.lower() or "subtitle" in result.stdout.lower())
            )
            self.test("Caption mode", passed)
        except subprocess.TimeoutExpired:
            self.test("Caption mode", False, "Timeout")
        except Exception as e:
            self.test("Caption mode", False, str(e))

    def test_export_functionality(self):
        """Test export functionality."""
        try:
            input_text = "I'm testing exports\nexport json\nquit\n"
            result = subprocess.run(
                [sys.executable, str(self.chimera_path)],
                input=input_text,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self.chimera_path.parent
            )
            passed = result.returncode == 0
            self.test("Export functionality", passed)
        except subprocess.TimeoutExpired:
            self.test("Export functionality", False, "Timeout")
        except Exception as e:
            self.test("Export functionality", False, str(e))

    def test_comparison_mode(self):
        """Test comparison mode."""
        try:
            input_text = "compare\nI love this performance\nquit\n"
            result = subprocess.run(
                [sys.executable, str(self.chimera_path)],
                input=input_text,
                capture_output=True,
                text=True,
                timeout=20,
                cwd=self.chimera_path.parent
            )
            passed = (
                result.returncode == 0 and
                ("compare" in result.stdout.lower() or "adaptive" in result.stdout.lower())
            )
            self.test("Comparison mode", passed)
        except subprocess.TimeoutExpired:
            self.test("Comparison mode", False, "Timeout")
        except Exception as e:
            self.test("Comparison mode", False, str(e))

    def run_all_tests(self):
        """Run all smoke tests."""
        print("="*60)
        print("PROJECT CHIMERA - SMOKE TESTS")
        print("="*60)
        print()

        # Verify chimera_core.py exists
        if not self.chimera_path.exists():
            print(f"❌ Error: {self.chimera_path} not found")
            print("   Please run from Project Chimera root directory")
            return False

        print(f"Testing: {self.chimera_path}")
        print()

        # Run tests
        print("🧪 Running Tests:")
        print()
        self.test_help()
        time.sleep(1)
        self.test_sentiment_only()
        time.sleep(1)
        self.test_batch_mode()
        time.sleep(1)
        self.test_caption_mode()
        time.sleep(1)
        self.test_export_functionality()
        time.sleep(1)
        self.test_comparison_mode()
        print()

        # Summary
        print("="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"📊 Success Rate: {self.tests_passed/(self.tests_passed+self.tests_failed)*100:.1f}%")
        print()

        if self.tests_failed == 0:
            print("✅ All smoke tests passed! chimera_core.py is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Review output above for details.")
            return False


def main():
    """Main entry point."""
    runner = SmokeTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
