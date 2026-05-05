#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEB_BASE_URL = "http://127.0.0.1:18080"
DEFAULT_COMMAND_TIMEOUT_SECONDS = 300
LOCAL_FETCH_HOSTS = {"127.0.0.1", "localhost"}
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class CaptureCommand:
    def __init__(self, name, argv):
        self.name = name
        self.argv = list(argv)


def default_output_dir(today=date.today):
    return REPO_ROOT / "internal" / "phase1-evidence" / today().isoformat()


def build_capture_plan(python_executable=sys.executable, web_base_url=DEFAULT_WEB_BASE_URL):
    return [
        CaptureCommand(
            "prerequisites",
            [
                python_executable,
                "verify_prerequisites.py",
            ],
        ),
        CaptureCommand(
            "smoke-demo",
            [
                python_executable,
                "services/operator-console/chimera_core.py",
                "demo",
            ],
        ),
        CaptureCommand(
            "privacy-preflight",
            [
                python_executable,
                "scripts/privacy_preflight.py",
            ],
        ),
        CaptureCommand(
            "focused-pytest",
            [
                python_executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/unit/test_chimera_cli_contract.py",
                "tests/unit/test_chimera_web_contract.py",
                "tests/unit/test_privacy_preflight.py",
                "-q",
            ],
        ),
        CaptureCommand(
            "web-state",
            [
                python_executable,
                "scripts/capture_phase1_evidence.py",
                "--fetch-url",
                f"{web_base_url}/api/state",
            ],
        ),
        CaptureCommand(
            "web-export",
            [
                python_executable,
                "scripts/capture_phase1_evidence.py",
                "--fetch-url",
                f"{web_base_url}/api/export",
            ],
        ),
    ]


def run_capture_plan(
    plan,
    output_dir,
    generated_at=None,
    cwd=REPO_ROOT,
    timeout_seconds=DEFAULT_COMMAND_TIMEOUT_SECONDS,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = generated_at or (lambda: datetime.now(timezone.utc))
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    commands = []
    results = []
    for command in plan:
        log_path = _safe_log_path(output_dir, command.name)
        commands.append({"name": command.name, "argv": command.argv})
        timed_out = False
        with log_path.open("w", encoding="utf-8") as log_file:
            try:
                completed = subprocess.run(
                    command.argv,
                    cwd=cwd,
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=False,
                    timeout=timeout_seconds,
                )
                returncode = completed.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                returncode = 124
                log_file.write(f"\ncommand timed out after {timeout_seconds} seconds\n")
        results.append(
            {
                "name": command.name,
                "returncode": returncode,
                "log_path": log_path.relative_to(output_dir).as_posix(),
                "timed_out": timed_out,
            }
        )

    manifest_path = output_dir / "manifest.json"
    manifest = {
        "generated_at": generated_at().isoformat(),
        "output_dir": str(output_dir),
        "commands": commands,
        "results": results,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def fetch_url(url):
    if not _is_local_http_url(url):
        print(f"only local http(s) URLs are allowed: {url}", file=sys.stderr)
        return 2

    try:
        with urlopen(url, timeout=10) as response:
            sys.stdout.buffer.write(response.read())
        return 0
    except URLError as exc:
        print(f"failed to fetch {url}: {exc}", file=sys.stderr)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Capture private Phase 1 closeout evidence under internal/."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Private output directory. Defaults to internal/phase1-evidence/<today>.",
    )
    parser.add_argument(
        "--fetch-url",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    if args.fetch_url:
        return fetch_url(args.fetch_url)

    output_dir = args.output_dir or default_output_dir()
    manifest_path = run_capture_plan(
        build_capture_plan(),
        output_dir=output_dir,
        cwd=REPO_ROOT,
    )
    print(f"manifest: {manifest_path}")
    return 0


def _safe_log_path(output_dir, name):
    if not SAFE_NAME_RE.fullmatch(name):
        raise ValueError(f"capture command name would write outside output directory: {name}")
    log_path = output_dir / f"{name}.log"
    resolved_output_dir = output_dir.resolve()
    resolved_log_path = log_path.resolve()
    if resolved_log_path.parent != resolved_output_dir:
        raise ValueError(f"log path is outside output directory: {log_path}")
    return log_path


def _is_local_http_url(url):
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in LOCAL_FETCH_HOSTS


if __name__ == "__main__":
    raise SystemExit(main())
