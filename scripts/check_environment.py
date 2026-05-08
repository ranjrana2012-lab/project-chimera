#!/usr/bin/env python3
"""Report public-safe local environment facts for Phase 1 close-out checks."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_command(argv: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            argv,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return completed.returncode, completed.stdout.strip() or completed.stderr.strip()


def nvidia_summary() -> dict[str, str | bool]:
    if not shutil.which("nvidia-smi"):
        return {
            "available": False,
            "summary": "nvidia-smi not available; local hardware evidence not confirmed",
        }

    code, output = run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,power.draw,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    if code != 0:
        return {
            "available": False,
            "summary": "nvidia-smi failed; local hardware evidence not confirmed",
        }

    return {
        "available": True,
        "summary": output,
        "caution": "Hardware visibility does not prove grant spend, public delivery, or production deployment.",
    }


def main() -> int:
    code, branch = run_command(["git", "branch", "--show-current"])
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "git_branch": branch if code == 0 else "unknown",
        "nvidia": nvidia_summary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
