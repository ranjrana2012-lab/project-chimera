#!/usr/bin/env python3
"""Run a public-safe Phase 1 demo and write a real local run log."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = REPO_ROOT / "services" / "operator-console" / "chimera_core.py"
DEFAULT_INPUTS = (
    "I am sad",
    "I feel excited and ready",
    "I am confused and overwhelmed",
    "This is intense but inspiring",
)


def load_core_class():
    spec = importlib.util.spec_from_file_location("chimera_core", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("Could not load chimera_core.py")
    spec.loader.exec_module(module)
    return module.ChimeraCore


def hardware_note() -> str:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,power.draw,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "nvidia-smi unavailable; local hardware evidence not confirmed"

    if completed.returncode != 0:
        return "nvidia-smi failed; local hardware evidence not confirmed"
    return completed.stdout.strip()


def safe_log_path(output_dir: Path, generated_at: datetime) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = generated_at.strftime("phase1_demo_%Y%m%dT%H%M%SZ.json")
    log_path = output_dir / filename
    if log_path.resolve().parent != output_dir.resolve():
        raise ValueError("Unsafe log output path")
    return log_path


def run_demo(inputs: list[str], output_dir: Path) -> Path:
    generated_at = datetime.now(timezone.utc)
    ChimeraCore = load_core_class()
    core = ChimeraCore()
    core.load_models()

    results = []
    for text in inputs:
        core.process_input(text)
        results.append(core.history[-1])

    payload = {
        "generated_at": generated_at.isoformat(),
        "claim_boundary": (
            "Real local Phase 1 demo run. This log does not evidence a public show, "
            "livestream, accessibility validation, spend, approval, or partner sign-off."
        ),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hardware_note": hardware_note(),
        "core_entry_point": str(CORE_PATH.relative_to(REPO_ROOT)),
        "inputs": inputs,
        "results": results,
    }
    log_path = safe_log_path(output_dir, generated_at)
    log_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return log_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "outputs" / "run_logs",
        help="Directory for generated local run logs.",
    )
    parser.add_argument("inputs", nargs="*", help="Optional custom demo inputs.")
    args = parser.parse_args(argv)

    inputs = args.inputs or list(DEFAULT_INPUTS)
    log_path = run_demo(inputs, args.output_dir)
    print(f"Phase 1 demo run log written to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
