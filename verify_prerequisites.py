#!/usr/bin/env python3
"""Pre-execution prerequisite verification for Project Chimera."""

import importlib.util
import os
import shutil
import sys
from pathlib import Path

# Keep console output portable on Windows shells that default to cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


class PrerequisiteChecker:
    """Checks system prerequisites for automation tools."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def check(self, name: str, passed: bool, message: str = ""):
        """Record a check result."""
        if passed:
            print(f"[OK] {name}")
            self.checks_passed += 1
            return

        print(f"[FAIL] {name}")
        if message:
            print(f"   {message}")
        self.checks_failed += 1

    def warn(self, message: str):
        """Record a warning."""
        print(f"[WARN] {message}")
        self.warnings += 1

    def check_python_version(self):
        """Check Python version."""
        version = sys.version_info
        passed = version >= (3, 10)
        self.check(
            f"Python Version: {version.major}.{version.minor}.{version.micro}",
            passed,
            "Python 3.10+ required" if not passed else "",
        )

    def check_module(self, module_name: str, package_name: str = None, required: bool = True):
        """Check if a Python module is available."""
        package_name = package_name or module_name
        spec = importlib.util.find_spec(module_name)
        passed = spec is not None
        if required:
            self.check(
                f"Module: {module_name}",
                passed,
                f"Install: pip install {package_name}" if not passed else "",
            )
            return

        if passed:
            print(f"[OK] Module: {module_name} (optional)")
        else:
            self.warn(f"Optional module: {module_name} (install with: pip install {package_name})")

    def check_file_exists(self, path: str, required: bool = True):
        """Check if a file exists."""
        file_path = Path(path)
        passed = file_path.exists()
        if required:
            self.check(
                f"File: {path}",
                passed,
                "Required file missing" if not passed else "",
            )
            return

        if passed:
            print(f"[OK] File: {path} (optional)")
        else:
            self.warn(f"Optional file: {path} (not found)")

    def resolve_command(self, *candidates: str):
        """Return the resolved path for the first available command candidate."""
        for candidate in candidates:
            if not candidate:
                continue
            candidate_path = Path(candidate)
            if candidate_path.is_absolute():
                if candidate_path.exists():
                    return str(candidate_path)
                continue
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
        return None

    def check_command_available(self, command: str, aliases=None, failure_message: str = ""):
        """Check if a command is available."""
        aliases = aliases or []
        matched = self.resolve_command(command, *aliases)
        self.check(
            f"Command: {command}",
            matched is not None,
            failure_message or (f"Install {command}" if matched is None else ""),
        )
        return matched

    def check_shell_python_command(self):
        """Verify the Python command students are expected to use."""
        if os.name == "nt":
            python_path = self.resolve_command("python")
            if python_path:
                self.check("Command: python", True)
                if Path(python_path).resolve().parent == Path(sys.executable).resolve().parent:
                    self.warn(
                        "`python` currently resolves inside the active interpreter environment. Open a fresh PowerShell window and run `python --version` if you need machine-wide setup confirmation."
                    )
                return

            if self.resolve_command("py"):
                self.check(
                    "Command: python",
                    False,
                    "Python is installed, but python.exe is not on PATH. Add Python 3.12 to PATH or use the py launcher explicitly.",
                )
                self.warn(
                    "Windows launcher 'py' is available, but fresh-shell commands that assume `python` will still fail until PATH is fixed."
                )
                return

            self.check(
                "Command: python",
                False,
                "Install Python 3.12+ and add python.exe to PATH.",
            )
            return

        if self.resolve_command("python3", "python"):
            self.check("Command: python3", True)
        else:
            self.check(
                "Command: python3",
                False,
                "Install Python 3.12+ and make it available as python3.",
            )

    def check_current_interpreter(self):
        """Show whether the current interpreter path exists."""
        interpreter_path = Path(sys.executable)
        self.check(
            "Current interpreter path",
            interpreter_path.exists(),
            f"Interpreter path not found: {interpreter_path}" if not interpreter_path.exists() else "",
        )
        if interpreter_path.exists():
            print(f"   {interpreter_path}")

    def check_chimera_core(self):
        """Verify chimera_core.py exists and is syntactically valid."""
        chimera_path = Path("services/operator-console/chimera_core.py")
        if not chimera_path.exists():
            self.check("chimera_core.py", False, "File not found")
            return

        try:
            with chimera_path.open("r", encoding="utf-8") as handle:
                compile(handle.read(), str(chimera_path), "exec")
            self.check("chimera_core.py syntax", True)
        except SyntaxError as exc:
            self.check("chimera_core.py syntax", False, str(exc))

    def run_all_checks(self):
        """Run all prerequisite checks."""
        print("=" * 60)
        print("PROJECT CHIMERA - PREREQUISITE VERIFICATION")
        print("=" * 60)
        print()

        print("Python Environment:")
        self.check_python_version()
        self.check_module("torch", "torch")
        self.check_module("transformers", "transformers")
        self.check_module("openai", "openai", required=False)
        print()

        print("Required Files:")
        self.check_file_exists("services/operator-console/chimera_core.py")
        self.check_file_exists("services/operator-console/requirements.txt")
        self.check_file_exists("services/operator-console/chimera_web.py")
        self.check_file_exists("docker-compose.student.yml")
        print()

        print("System Commands:")
        self.check_shell_python_command()
        if os.name != "nt":
            self.check_command_available("bash")
        self.check_command_available("git")
        self.check_current_interpreter()
        print()

        print("Code Quality:")
        self.check_chimera_core()
        print()

        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"[OK] Passed: {self.checks_passed}")
        print(f"[FAIL] Failed: {self.checks_failed}")
        print(f"[WARN] Warnings: {self.warnings}")
        print()

        if self.checks_failed == 0:
            print("[OK] All prerequisites met! Ready to execute Project Chimera.")
            print()
            print("Next steps:")
            print("1. Create or reuse the monolith virtual environment in services/operator-console.")
            print("2. Install operator-console dependencies with pip install -r requirements.txt.")
            if os.name == "nt":
                print(
                    r"3. If PowerShell blocks .\venv\Scripts\Activate.ps1, use Set-ExecutionPolicy -Scope Process Bypass, venv\Scripts\activate.bat, or call venv\Scripts\python.exe directly."
                )
                print(r"4. Start the web dashboard with .\venv\Scripts\python.exe chimera_web.py.")
            else:
                print("3. Start the web dashboard with ./venv/bin/python chimera_web.py.")
            print("5. Use docker compose only after the monolith path is already working." if os.name == "nt" else "4. Use docker compose only after the monolith path is already working.")
            return True

        print("[FAIL] Some prerequisites are not met. Please fix the failed checks above.")
        return False


def main():
    """Main entry point."""
    checker = PrerequisiteChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
