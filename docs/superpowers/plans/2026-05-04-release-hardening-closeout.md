# Release Hardening Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Project Chimera Phase 1 for public closeout by locking demo behaviour with tests, capturing evidence privately, auditing public/private boundaries, and committing only safe public source changes.

**Architecture:** Keep the local operator-console route as the required proof path. Add focused tests around core CLI/web contracts, add one privacy preflight script, add one private evidence capture helper, and update stale capture helper wording so public source no longer overclaims Phase 1.

**Tech Stack:** Python 3.12, pytest, FastAPI TestClient, subprocess-based CLI tests, Git CLI, Docker Compose for optional route validation.

---

## File Structure

- Create: `tests/unit/test_chimera_cli_contract.py`
  - Subprocess contract tests for normal CLI input, `demo`, `compare`, and `caption` modes.
- Create: `tests/unit/test_chimera_web_contract.py`
  - FastAPI TestClient contract tests for `/api/state`, `/api/process`, `/api/export`, and empty input handling.
- Modify: `services/operator-console/chimera_web.py`
  - Reject empty or whitespace-only `/api/process` text with HTTP 400 before mutating app history.
- Create: `scripts/privacy_preflight.py`
  - Public/private boundary checker for tracked, staged, and untracked publication-risk paths.
- Create: `tests/unit/test_privacy_preflight.py`
  - Unit tests for forbidden path classification and CLI exit behaviour.
- Create: `scripts/capture_phase1_evidence.py`
  - Evidence capture helper that writes command output and a manifest to ignored private paths.
- Create: `tests/unit/test_phase1_evidence_capture.py`
  - Unit tests for private output defaults, command construction, and manifest writing.
- Modify: `services/operator-console/capture_demo.py`
  - Replace stale overclaiming summary text with current Phase 1 scope wording.
- Create: `tests/unit/test_phase1_capture_scripts.py`
  - Source-level guard that prevents stale overclaiming capture text from returning.

Do not modify or revert unrelated cleanup already staged in the working tree. Do not add private evidence files to Git.

---

### Task 1: Lock CLI Demo Contract

**Files:**
- Create: `tests/unit/test_chimera_cli_contract.py`
- Modify only if tests reveal a real bug: `services/operator-console/chimera_core.py`

- [ ] **Step 1: Write the CLI contract tests**

Create `tests/unit/test_chimera_cli_contract.py`:

```python
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CHIMERA_CORE = REPO_ROOT / "services" / "operator-console" / "chimera_core.py"


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def run_cli(tmp_path: Path, *args: str) -> str:
    env = os.environ.copy()
    env["CHIMERA_ENABLE_VOICE"] = "0"
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"

    result = subprocess.run(
        [sys.executable, str(CHIMERA_CORE), *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )

    output = ANSI_RE.sub("", result.stdout + result.stderr)
    assert result.returncode == 0, output
    return output


@pytest.mark.parametrize(
    ("text", "expected_sentiment", "expected_strategy"),
    [
        ("I am very happy today!", "POSITIVE", "momentum_build"),
        ("I'm feeling anxious and overwhelmed.", "NEGATIVE", "supportive_care"),
        ("It's an okay experience, nothing special so far.", "NEUTRAL", "standard_response"),
    ],
)
def test_direct_cli_input_routes_to_expected_strategy(
    tmp_path: Path,
    text: str,
    expected_sentiment: str,
    expected_strategy: str,
) -> None:
    output = run_cli(tmp_path, text)

    assert f"Sentiment: {expected_sentiment} -> Strategy: {expected_strategy}" in output
    assert "Adaptive Dialogue:" in output
    assert "Latency:" in output


def test_demo_mode_processes_positive_negative_and_neutral_examples(tmp_path: Path) -> None:
    output = run_cli(tmp_path, "demo")

    assert output.count("Processing Demo Input:") == 3
    assert "momentum_build" in output
    assert "supportive_care" in output
    assert "standard_response" in output


def test_compare_mode_shows_baseline_and_adaptive_output(tmp_path: Path) -> None:
    output = run_cli(tmp_path, "compare", "I love this performance")

    assert "--- Comparison Mode ---" in output
    assert "[Non-Adaptive Baseline System]" in output
    assert "[Project Chimera Adaptive System]" in output
    assert "Selected Strategy: momentum_build" in output


def test_caption_mode_writes_srt_in_private_working_directory(tmp_path: Path) -> None:
    output = run_cli(tmp_path, "caption", "Can you tell me more about the system?")

    srt_path = tmp_path / "captions.srt"
    assert "--- High-Contrast Caption Format ---" in output
    assert "SRT output successfully generated." in output
    assert srt_path.exists()
    assert "Can you tell me more about the system?" in srt_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the CLI contract tests and record the result**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_chimera_cli_contract.py -q
```

Expected if current behaviour is intact: all tests pass. If a test fails because expected demo behaviour is missing, keep the failing test and continue to Step 3. If a test fails because the assertion is too brittle around harmless wording, adjust only the assertion and rerun Step 2.

- [ ] **Step 3: Write minimal core fix only if Step 2 exposes a real behaviour bug**

If direct positive, negative, or neutral routing fails, inspect `services/operator-console/chimera_core.py` and make the smallest cue or routing change needed. For example, if anxious input is not routed to `supportive_care`, ensure the negative cue set includes the exact term:

```python
self.negative_cues = {
    "anxious", "angry", "bad", "frustrated", "overwhelmed",
    "sad", "terrible", "worried",
}
```

- [ ] **Step 4: Re-run CLI tests**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_chimera_cli_contract.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the CLI contract tests and any core fix**

Run:

```bash
git add tests/unit/test_chimera_cli_contract.py services/operator-console/chimera_core.py
git commit -m "test: lock phase1 cli demo contract"
```

If `services/operator-console/chimera_core.py` was not changed, stage only `tests/unit/test_chimera_cli_contract.py`.

---

### Task 2: Add Web/API Contract Tests

**Files:**
- Create: `tests/unit/test_chimera_web_contract.py`
- Modify: `services/operator-console/chimera_web.py`

- [ ] **Step 1: Write failing web/API tests**

Create `tests/unit/test_chimera_web_contract.py`:

```python
import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_DIR = REPO_ROOT / "services" / "operator-console"


def load_web_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(OPERATOR_DIR)
    sys.path.insert(0, str(OPERATOR_DIR))

    for module_name in ("chimera_web", "chimera_core"):
        sys.modules.pop(module_name, None)

    core_spec = importlib.util.spec_from_file_location(
        "chimera_core",
        OPERATOR_DIR / "chimera_core.py",
    )
    core_module = importlib.util.module_from_spec(core_spec)
    assert core_spec.loader is not None
    core_spec.loader.exec_module(core_module)
    core_module.pipeline = None
    sys.modules["chimera_core"] = core_module

    web_spec = importlib.util.spec_from_file_location(
        "chimera_web",
        OPERATOR_DIR / "chimera_web.py",
    )
    web_module = importlib.util.module_from_spec(web_spec)
    assert web_spec.loader is not None
    web_spec.loader.exec_module(web_module)

    web_module.chimera.sentiment_analyzer = web_module.chimera.heuristic_sentiment
    web_module.chimera.text_generator = None
    web_module.app.state.history = []
    web_module.app.state.latest_response = {
        "text": "",
        "sentiment": "NEUTRAL",
        "strategy": "standard_response",
        "response": "Awaiting initial dialogue...",
    }
    return web_module


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    web_module = load_web_module(monkeypatch)
    return TestClient(web_module.app)


def test_state_starts_with_neutral_waiting_response(client: TestClient) -> None:
    response = client.get("/api/state")

    assert response.status_code == 200
    assert response.json() == {
        "text": "",
        "sentiment": "NEUTRAL",
        "strategy": "standard_response",
        "response": "Awaiting initial dialogue...",
    }


def test_process_positive_input_updates_state_and_export(client: TestClient) -> None:
    process_response = client.post(
        "/api/process",
        json={"text": "I am very happy today!"},
    )

    assert process_response.status_code == 200
    payload = process_response.json()
    assert payload["text"] == "I am very happy today!"
    assert payload["sentiment"] == "POSITIVE"
    assert payload["strategy"] == "momentum_build"
    assert "response" in payload
    assert payload["latency_ms"] >= 0

    state_response = client.get("/api/state")
    assert state_response.status_code == 200
    assert state_response.json()["strategy"] == "momentum_build"

    export_response = client.get("/api/export")
    assert export_response.status_code == 200
    assert "strategy_routed" in export_response.text
    assert "I am very happy today!" in export_response.text
    assert "momentum_build" in export_response.text


def test_process_rejects_empty_text_without_mutating_history(client: TestClient) -> None:
    response = client.post("/api/process", json={"text": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "text is required"}

    export_response = client.get("/api/export")
    assert export_response.status_code == 200
    assert export_response.text.strip() == (
        "timestamp,input,sentiment,confidence_score,strategy_routed,latency_ms"
    )
```

- [ ] **Step 2: Run the web/API tests and verify the red failure**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_chimera_web_contract.py -q
```

Expected: `test_process_rejects_empty_text_without_mutating_history` fails because `/api/process` currently accepts whitespace text and returns HTTP 200.

- [ ] **Step 3: Implement minimal `/api/process` validation**

In `services/operator-console/chimera_web.py`, change the import and the first lines of `process`:

```python
from fastapi import FastAPI, Request, HTTPException
```

Replace:

```python
    data = await req.json()
    text = data.get("text", "")
```

with:

```python
    data = await req.json()
    text = str(data.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
```

- [ ] **Step 4: Run the web/API tests and verify green**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_chimera_web_contract.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the web/API contract**

Run:

```bash
git add tests/unit/test_chimera_web_contract.py services/operator-console/chimera_web.py
git commit -m "test: lock phase1 web api contract"
```

---

### Task 3: Add Public/Private Privacy Preflight

**Files:**
- Create: `scripts/privacy_preflight.py`
- Create: `tests/unit/test_privacy_preflight.py`

- [ ] **Step 1: Write failing privacy preflight tests**

Create `tests/unit/test_privacy_preflight.py`:

```python
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "privacy_preflight.py"


def load_preflight():
    spec = importlib.util.spec_from_file_location("privacy_preflight", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_forbidden_private_paths_are_rejected() -> None:
    preflight = load_preflight()

    findings = preflight.classify_paths(
        [
            "internal/grant-tracking/grant_closeout/final_report.md",
            ".env.nemotron",
            "evidence/screenshots/2026-05-04-demo.png",
            "services/zai-auth-proxy/tokens/session_token.json",
            "Grant_Evidence_Pack/receipt.pdf",
            "platform/dashboard/frontend/node_modules/vite/package.json",
        ]
    )

    rejected_paths = {finding.path for finding in findings}
    assert "internal/grant-tracking/grant_closeout/final_report.md" in rejected_paths
    assert ".env.nemotron" in rejected_paths
    assert "evidence/screenshots/2026-05-04-demo.png" in rejected_paths
    assert "services/zai-auth-proxy/tokens/session_token.json" in rejected_paths
    assert "Grant_Evidence_Pack/receipt.pdf" in rejected_paths
    assert "platform/dashboard/frontend/node_modules/vite/package.json" in rejected_paths


def test_public_placeholders_and_examples_are_allowed() -> None:
    preflight = load_preflight()

    findings = preflight.classify_paths(
        [
            "evidence/README.md",
            "evidence/screenshots/.gitkeep",
            ".env.example",
            ".env.dgx-spark.example",
            "services/operator-console/.env.example",
            "docs/PHASE_1_SCOPE.md",
        ]
    )

    assert findings == []


def test_main_returns_failure_when_collector_reports_forbidden_path(monkeypatch, capsys) -> None:
    preflight = load_preflight()

    monkeypatch.setattr(
        preflight,
        "collect_publication_risk_paths",
        lambda: ["internal/grant-tracking/grant_closeout/final_report.md"],
    )

    assert preflight.main([]) == 1
    captured = capsys.readouterr()
    assert "Privacy preflight failed" in captured.out
    assert "internal/grant-tracking/grant_closeout/final_report.md" in captured.out


def test_main_returns_success_when_no_forbidden_paths(monkeypatch, capsys) -> None:
    preflight = load_preflight()

    monkeypatch.setattr(
        preflight,
        "collect_publication_risk_paths",
        lambda: ["docs/PHASE_1_SCOPE.md", "evidence/README.md"],
    )

    assert preflight.main([]) == 0
    captured = capsys.readouterr()
    assert "Privacy preflight passed" in captured.out
```

- [ ] **Step 2: Run the privacy tests and verify the red failure**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_privacy_preflight.py -q
```

Expected: fails with `FileNotFoundError` because `scripts/privacy_preflight.py` does not exist.

- [ ] **Step 3: Implement the privacy preflight script**

Create `scripts/privacy_preflight.py`:

```python
#!/usr/bin/env python3
"""Fail a public-source commit when private or generated paths are publishable."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    path: str
    reason: str


ALLOWED_EXACT = {
    ".env.example",
    ".env.production.example",
    ".env.dgx-spark.example",
    "evidence/README.md",
}

ALLOWED_SUFFIXES = (
    "/.env.example",
    "/.env.production.example",
    "/.env.dgx-spark.example",
)

FORBIDDEN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(^|/)internal/"), "internal grant/private material must stay local"),
    (re.compile(r"(^|/)Grant_Evidence_Pack(/|$)"), "grant evidence pack must stay private"),
    (re.compile(r"(^|/)project-chimera-submission"), "submission bundle must stay private"),
    (re.compile(r"(^|/)demo_footage(/|$)"), "raw demo footage must stay private"),
    (re.compile(r"(^|/)demo_captures(/|$)"), "raw demo captures must stay private"),
    (re.compile(r"(^|/)services/operator-console/demo_captures(/|$)"), "raw demo captures must stay private"),
    (re.compile(r"(^|/)services/zai-auth-proxy/tokens/.*\.json$"), "runtime token JSON must stay private"),
    (re.compile(r"(^|/)node_modules(/|$)"), "generated node_modules must not be public source"),
    (re.compile(r"(^|/)\.env($|\.)"), "real environment files must stay private"),
    (re.compile(r"(^|/)evidence/(?!README\.md$)(?![^/]+/\.gitkeep$).+"), "real evidence artefacts must stay private"),
    (re.compile(r"(^|/).*(receipt|receipts|invoice|invoices|bank|tax).*\.(pdf|png|jpg|jpeg|csv|xlsx|doc|docx)$", re.IGNORECASE), "financial evidence must stay private"),
    (re.compile(r".*\.(mp4|mov|mkv|webm)$", re.IGNORECASE), "raw video recordings must stay private"),
)


def is_allowed_placeholder(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in ALLOWED_EXACT:
        return True
    if normalized.startswith("evidence/") and normalized.endswith("/.gitkeep"):
        return True
    return normalized.endswith(ALLOWED_SUFFIXES)


def classify_paths(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for raw_path in paths:
        path = raw_path.replace("\\", "/").strip()
        if not path or is_allowed_placeholder(path):
            continue
        for pattern, reason in FORBIDDEN_PATTERNS:
            if pattern.search(path):
                findings.append(Finding(path=path, reason=reason))
                break
    return findings


def run_git(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def staged_publication_paths() -> list[str]:
    rows = run_git(["diff", "--cached", "--name-status", "--diff-filter=ACMRTUXB"])
    paths: list[str] = []
    for row in rows:
        parts = row.split("\t")
        if len(parts) >= 2:
            paths.append(parts[-1])
    return paths


def untracked_paths() -> list[str]:
    rows = run_git(["status", "--short", "--untracked-files=all"])
    return [row[3:] for row in rows if row.startswith("?? ")]


def collect_publication_risk_paths() -> list[str]:
    paths: set[str] = set()
    paths.update(run_git(["ls-files"]))
    paths.update(staged_publication_paths())
    paths.update(untracked_paths())
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check public/private source boundary")
    parser.add_argument("--repo-root", default=".", help="Repository root to check")
    args = parser.parse_args(argv)

    original_cwd = Path.cwd()
    repo_root = Path(args.repo_root).resolve()
    try:
        import os

        os.chdir(repo_root)
        findings = classify_paths(collect_publication_risk_paths())
    finally:
        import os

        os.chdir(original_cwd)

    if findings:
        print("Privacy preflight failed:")
        for finding in findings:
            print(f"- {finding.path}: {finding.reason}")
        return 1

    print("Privacy preflight passed: no forbidden public/private boundary paths found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the privacy tests and verify green**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_privacy_preflight.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Run privacy preflight against the current repo**

Run:

```bash
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Expected: pass after generated/private removals are staged as deletions and no forbidden private additions are present. If it fails, do not commit public cleanup until each finding is either removed from tracking, ignored, or confirmed as a false positive with a test adjustment.

- [ ] **Step 6: Commit the privacy preflight**

Run:

```bash
git add scripts/privacy_preflight.py tests/unit/test_privacy_preflight.py
git commit -m "test: add public private privacy preflight"
```

---

### Task 4: Add Private Evidence Capture Helper

**Files:**
- Create: `scripts/capture_phase1_evidence.py`
- Create: `tests/unit/test_phase1_evidence_capture.py`

- [ ] **Step 1: Write failing evidence capture tests**

Create `tests/unit/test_phase1_evidence_capture.py`:

```python
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "capture_phase1_evidence.py"


def load_capture():
    spec = importlib.util.spec_from_file_location("capture_phase1_evidence", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_output_dir_is_private_and_ignored() -> None:
    capture = load_capture()

    output_dir = capture.default_output_dir("2026-05-04")

    assert output_dir == Path("internal/phase1-evidence/2026-05-04")


def test_build_commands_use_explicit_python_path() -> None:
    capture = load_capture()

    commands = capture.build_commands(Path("services/operator-console/venv/bin/python"))

    assert commands["cli_demo"] == [
        "services/operator-console/venv/bin/python",
        "services/operator-console/chimera_core.py",
        "demo",
    ]
    assert commands["cli_compare"][2:] == [
        "compare",
        "I love this performance",
    ]
    assert commands["cli_caption"][2:] == [
        "caption",
        "Can you tell me more about the system?",
    ]


def test_write_manifest_records_files_and_owner_actions(tmp_path: Path) -> None:
    capture = load_capture()
    output_dir = tmp_path / "evidence"
    output_dir.mkdir()
    (output_dir / "cli_demo.log").write_text("demo output", encoding="utf-8")

    manifest = capture.write_manifest(
        output_dir=output_dir,
        commands={"cli_demo": ["python", "chimera_core.py", "demo"]},
        owner_actions=["Record final MP4 privately"],
    )

    text = manifest.read_text(encoding="utf-8")
    assert "Project Chimera Phase 1 Private Evidence Manifest" in text
    assert "cli_demo.log" in text
    assert "python chimera_core.py demo" in text
    assert "Record final MP4 privately" in text
```

- [ ] **Step 2: Run the evidence tests and verify the red failure**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_phase1_evidence_capture.py -q
```

Expected: fails with `FileNotFoundError` because `scripts/capture_phase1_evidence.py` does not exist.

- [ ] **Step 3: Implement the evidence capture helper**

Create `scripts/capture_phase1_evidence.py`:

```python
#!/usr/bin/env python3
"""Capture Phase 1 command evidence into ignored private local storage."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def default_output_dir(date_text: str | None = None) -> Path:
    date_part = date_text or datetime.now().strftime("%Y-%m-%d")
    return Path("internal") / "phase1-evidence" / date_part


def build_commands(python_bin: Path) -> dict[str, list[str]]:
    python_text = str(python_bin)
    return {
        "verify_prerequisites": [python_text, "verify_prerequisites.py"],
        "smoke": [python_text, "test_chimera_smoke.py"],
        "cli_demo": [python_text, "services/operator-console/chimera_core.py", "demo"],
        "cli_positive": [python_text, "services/operator-console/chimera_core.py", "I am very happy today!"],
        "cli_negative": [python_text, "services/operator-console/chimera_core.py", "I'm feeling anxious and overwhelmed."],
        "cli_neutral": [python_text, "services/operator-console/chimera_core.py", "It's an okay experience, nothing special so far."],
        "cli_compare": [python_text, "services/operator-console/chimera_core.py", "compare", "I love this performance"],
        "cli_caption": [python_text, "services/operator-console/chimera_core.py", "caption", "Can you tell me more about the system?"],
    }


def run_command(name: str, command: list[str], output_dir: Path, cwd: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=180,
    )
    output_path = output_dir / f"{name}.log"
    output_path.write_text(
        "\n".join(
            [
                f"$ {' '.join(command)}",
                f"returncode={result.returncode}",
                "",
                "[stdout]",
                result.stdout,
                "",
                "[stderr]",
                result.stderr,
            ]
        ),
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"{name} failed with return code {result.returncode}; see {output_path}")
    return output_path


def write_manifest(
    output_dir: Path,
    commands: dict[str, list[str]],
    owner_actions: list[str],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = output_dir / "MANIFEST.md"
    captured_logs = sorted(path.name for path in output_dir.glob("*.log"))
    lines = [
        "# Project Chimera Phase 1 Private Evidence Manifest",
        "",
        f"Created: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Captured Logs",
        "",
    ]
    lines.extend(f"- `{name}`" for name in captured_logs)
    lines.extend(["", "## Commands", ""])
    lines.extend(f"- `{name}`: `{' '.join(command)}`" for name, command in commands.items())
    lines.extend(["", "## Owner Actions", ""])
    lines.extend(f"- [ ] {action}" for action in owner_actions)
    lines.append("")
    manifest.write_text("\n".join(lines), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture private Phase 1 evidence logs")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--output-dir", default=None, help="Private output directory")
    parser.add_argument("--python", default="services/operator-console/venv/bin/python", help="Python executable")
    parser.add_argument("--skip-run", action="store_true", help="Only create the manifest")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir) if args.output_dir else repo_root / default_output_dir()
    python_bin = Path(args.python)
    commands = build_commands(python_bin)

    if not args.skip_run:
        for name, command in commands.items():
            run_command(name, command, output_dir, repo_root)

    write_manifest(
        output_dir=output_dir,
        commands=commands,
        owner_actions=[
            "Capture CLI screenshot privately",
            "Capture comparison-mode screenshot privately",
            "Capture caption-mode screenshot privately",
            "Capture web UI screenshot privately",
            "Record final MP4 demo privately",
            "Store receipts and invoices outside public Git",
        ],
    )
    print(f"Private evidence manifest written to {output_dir / 'MANIFEST.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the evidence tests and verify green**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_phase1_evidence_capture.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the evidence helper**

Run:

```bash
git add scripts/capture_phase1_evidence.py tests/unit/test_phase1_evidence_capture.py
git commit -m "test: add private phase1 evidence capture helper"
```

---

### Task 5: Remove Stale Overclaims From Capture Helpers

**Files:**
- Create: `tests/unit/test_phase1_capture_scripts.py`
- Modify: `services/operator-console/capture_demo.py`

- [ ] **Step 1: Write failing source guard for stale capture claims**

Create `tests/unit/test_phase1_capture_scripts.py`:

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CAPTURE_DEMO = REPO_ROOT / "services" / "operator-console" / "capture_demo.py"


def test_capture_demo_uses_current_phase1_scope_language() -> None:
    text = CAPTURE_DEMO.read_text(encoding="utf-8")

    stale_claims = [
        "Birmingham City University",
        "GLM-4.7 API (primary)",
        "Ollama Local LLM (fallback)",
        "700+ lines",
        "20+ comprehensive documentation files",
        "Financial audit trail ready",
        "COMPLIANT - Successful Proof-of-Concept",
    ]

    for claim in stale_claims:
        assert claim not in text

    assert "local-first adaptive AI foundation" in text
    assert "not a completed public theatre production" in text
```

- [ ] **Step 2: Run the stale-claim guard and verify the red failure**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_phase1_capture_scripts.py -q
```

Expected: fails because `capture_demo.py` contains stale Phase 1 overclaims.

- [ ] **Step 3: Replace stale summary/pipeline wording**

In `services/operator-console/capture_demo.py`, replace the `pipeline_output` string with:

```python
    pipeline_output = """=== Project Chimera Core Phase 1 Pipeline ===

1. Text Input -> Sentiment Analysis
   - Detects positive, negative/anxious, and neutral input
   - Uses local ML when available and a heuristic fallback when not
   - No external API key is required for the default route

2. Sentiment -> Adaptive Routing Strategy
   - Positive -> momentum_build
   - Negative/anxious -> supportive_care
   - Neutral -> standard_response

3. Strategy -> Evidence-Friendly Output
   - CLI output shows sentiment, strategy, response, and latency
   - Comparison mode shows static baseline beside adaptive output
   - Caption mode writes caption-style output and SRT text

Phase 1 proves a local-first adaptive AI foundation.
It is not a completed public theatre production.
"""
```

Replace the `summary_output` string with:

```python
    summary_output = f"""=== Project Chimera Phase 1 - Closeout Summary ===

Date: {datetime.now().strftime('%Y-%m-%d')}
Phase: 1 closeout

=== Core Deliverable ===
- Local operator-console CLI and web demonstrator
- Sentiment-driven adaptive routing
- Baseline-versus-adaptive comparison mode
- Caption-style output path

=== Evidence Position ===
- Public repository contains source, tests, docs, templates, and placeholders
- Real screenshots, recordings, receipts, invoices, and grant evidence stay private
- DGX/Kimi routes are optional advanced validation, not the default reviewer path

=== Status ===
- Demonstrates a local-first adaptive AI foundation
- Does not claim a completed public theatre production
- Does not publish private grant or financial evidence
"""
```

- [ ] **Step 4: Run the stale-claim guard and verify green**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest tests/unit/test_phase1_capture_scripts.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the capture wording guard**

Run:

```bash
git add tests/unit/test_phase1_capture_scripts.py services/operator-console/capture_demo.py
git commit -m "docs: align capture helper with phase1 closeout scope"
```

---

### Task 6: Run Focused TDD Regression Set

**Files:**
- No new files expected.
- Modify only files already touched by Tasks 1-5 if failures identify defects in those changes.

- [ ] **Step 1: Run focused tests**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest \
  tests/unit/test_chimera_core.py \
  tests/unit/test_chimera_cli_contract.py \
  tests/unit/test_chimera_web_contract.py \
  tests/unit/test_privacy_preflight.py \
  tests/unit/test_phase1_evidence_capture.py \
  tests/unit/test_phase1_capture_scripts.py \
  test_chimera_smoke.py \
  -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Fix failures with the smallest local change**

If a test fails, use this loop:

```bash
./services/operator-console/venv/bin/python -m pytest <failing-test-path>::<failing-test-name> -q
```

Expected before fix: the failing test reproduces consistently. Change only the source file named by the failing contract. Re-run the single failing test until it passes, then re-run Step 1.

- [ ] **Step 3: Commit any focused regression fixes**

If Step 2 changed files after the task-specific commits, run:

```bash
git add tests/unit/test_chimera_core.py tests/unit/test_chimera_cli_contract.py tests/unit/test_chimera_web_contract.py tests/unit/test_privacy_preflight.py tests/unit/test_phase1_evidence_capture.py tests/unit/test_phase1_capture_scripts.py services/operator-console/chimera_core.py services/operator-console/chimera_web.py scripts/privacy_preflight.py scripts/capture_phase1_evidence.py services/operator-console/capture_demo.py
git commit -m "fix: stabilize phase1 closeout contract tests"
```

If there are no changes, do not create an empty commit.

---

### Task 7: Capture Private Evidence Locally

**Files:**
- Private ignored output: `internal/phase1-evidence/<YYYY-MM-DD>/`
- Public source changes: none expected.

- [ ] **Step 1: Run the private evidence helper**

Run:

```bash
./services/operator-console/venv/bin/python scripts/capture_phase1_evidence.py
```

Expected: command logs and `MANIFEST.md` are written under `internal/phase1-evidence/<date>/`. This directory is ignored by Git through `internal/`.

- [ ] **Step 2: Run local web route and capture endpoint output privately**

Start the web server:

```bash
PORT=18080 ./services/operator-console/venv/bin/python services/operator-console/chimera_web.py
```

In another terminal, run:

```bash
mkdir -p internal/phase1-evidence/2026-05-04
curl -fsS http://127.0.0.1:18080/api/state > internal/phase1-evidence/2026-05-04/web-api-state.json
curl -fsS -X POST http://127.0.0.1:18080/api/process \
  -H "Content-Type: application/json" \
  -d '{"text":"I am very happy today!"}' \
  > internal/phase1-evidence/2026-05-04/web-api-process-positive.json
curl -fsS http://127.0.0.1:18080/api/export > internal/phase1-evidence/2026-05-04/web-api-export.csv
```

Expected: files are written under `internal/phase1-evidence/2026-05-04/` and are not staged.

- [ ] **Step 3: Capture screenshots and demo recording privately**

Use `demos/phase1/demo_capture_checklist.md` and save files outside public Git. Use these private filenames:

```text
internal/phase1-evidence/2026-05-04/2026-05-04-cli-positive-input.png
internal/phase1-evidence/2026-05-04/2026-05-04-cli-compare-mode.png
internal/phase1-evidence/2026-05-04/2026-05-04-cli-caption-mode.png
internal/phase1-evidence/2026-05-04/2026-05-04-web-ui.png
internal/phase1-evidence/2026-05-04/2026-05-04-phase1-demo-recording.mp4
```

Expected: the files exist locally and are ignored by Git.

- [ ] **Step 4: Confirm private evidence is not visible to Git**

Run:

```bash
git status --short --ignored internal/phase1-evidence/2026-05-04
```

Expected: every captured file appears with `!!` ignored status or does not appear because parent ignore rules hide it. No line should begin with `??`, `A`, or `M`.

---

### Task 8: Validate Student Docker And Optional DGX/Kimi Routes

**Files:**
- Public source changes only if docs need downgrade wording after route failure.
- Private ignored output: `internal/phase1-evidence/2026-05-04/`

- [ ] **Step 1: Run student Docker preview**

Run:

```bash
docker compose -f docker-compose.student.yml up -d --build
curl -fsS http://127.0.0.1:8080/api/state > internal/phase1-evidence/2026-05-04/student-api-state.json
curl -fsS -X POST http://127.0.0.1:8080/api/process \
  -H "Content-Type: application/json" \
  -d '{"text":"I am very happy today!"}' \
  > internal/phase1-evidence/2026-05-04/student-api-process-positive.json
curl -fsS http://127.0.0.1:8080/api/export > internal/phase1-evidence/2026-05-04/student-api-export.csv
```

Expected: student route responds on port `8080`.

- [ ] **Step 2: Detect whether DGX/Kimi route is supported on the current host**

Run:

```bash
python3 scripts/detect_runtime_profile.py > internal/phase1-evidence/2026-05-04/runtime-profile.txt
```

Expected on current GB10 host: high-confidence DGX Spark profile. If output does not show DGX/GB10/aarch64/Docker GPU support, skip Step 3 and document DGX/Kimi as optional not revalidated.

- [ ] **Step 3: Run optional DGX/Kimi validation only if Step 2 supports it**

Run:

```bash
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services \
  > internal/phase1-evidence/2026-05-04/dgx-compose-services.txt
curl -fsS http://127.0.0.1:8012/health > internal/phase1-evidence/2026-05-04/kimi-vllm-health.txt
curl -fsS http://127.0.0.1:8012/v1/models > internal/phase1-evidence/2026-05-04/kimi-vllm-models.json
```

Expected: Kimi/vLLM host-facing HTTP route responds. If it fails while local and student routes pass, do not block closeout. Update public docs only if they currently claim this pass revalidated DGX/Kimi.

- [ ] **Step 4: Run MVP/Kimi targeted tests only if services are available**

Run:

```bash
KIMI_VLLM_TEST_URL=http://127.0.0.1:8012 \
KIMI_GRPC_TEST_TARGET=127.0.0.1:50052 \
./services/operator-console/venv/bin/python -m pytest tests/integration/kimi tests/integration/mvp -q \
  > internal/phase1-evidence/2026-05-04/advanced-route-pytest.log
```

Expected on validated GB10 host: tests pass or skip only optional external-service checks. If tests fail because services are unavailable, preserve the log privately and downgrade advanced route claims before final public commit.

---

### Task 9: Run Final Regression And Privacy Gate

**Files:**
- Modify only test/code/docs files already touched if failures require fixes.

- [ ] **Step 1: Run default closeout validation**

Run:

```bash
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python test_chimera_smoke.py
./services/operator-console/venv/bin/python -m pytest tests/unit/test_chimera_core.py test_chimera_smoke.py -q
```

Expected: all commands pass.

- [ ] **Step 2: Run focused hardening tests**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest \
  tests/unit/test_chimera_cli_contract.py \
  tests/unit/test_chimera_web_contract.py \
  tests/unit/test_privacy_preflight.py \
  tests/unit/test_phase1_evidence_capture.py \
  tests/unit/test_phase1_capture_scripts.py \
  -q
```

Expected: all tests pass.

- [ ] **Step 3: Run privacy preflight**

Run:

```bash
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Expected: privacy preflight passes. If it fails, remove forbidden additions from staging/tracking before proceeding.

- [ ] **Step 4: Inspect staged and untracked files manually**

Run:

```bash
git status --short
git diff --cached --name-status
git diff --cached --stat
```

Expected:

- staged deletions for generated/private files are acceptable;
- staged additions/modifications must be public-safe source, tests, docs, templates, or placeholders;
- no `.env`, `internal/`, `Grant_Evidence_Pack/`, real `evidence/**`, token JSON, screenshot, video, receipt, invoice, private log, or `node_modules` addition is staged.

- [ ] **Step 5: Run broad pytest regression**

Run:

```bash
./services/operator-console/venv/bin/python -m pytest -q -ra
```

Expected: matches or improves the previous baseline. Optional skips are acceptable when they correspond to external secrets, unsupported extended stack, or environment-gated tests.

---

### Task 10: Final Public Commit

**Files:**
- Commit all public-safe release-hardening changes and already staged cleanup removals.
- Do not commit private evidence outputs.

- [ ] **Step 1: Stage only safe public files**

Run:

```bash
git add -u
git add tests/unit/test_chimera_cli_contract.py \
  tests/unit/test_chimera_web_contract.py \
  tests/unit/test_privacy_preflight.py \
  tests/unit/test_phase1_evidence_capture.py \
  tests/unit/test_phase1_capture_scripts.py \
  scripts/privacy_preflight.py \
  scripts/capture_phase1_evidence.py \
  services/operator-console/chimera_web.py \
  services/operator-console/capture_demo.py
```

Expected: only public-safe files and cleanup removals are staged.

- [ ] **Step 2: Re-run privacy preflight after staging**

Run:

```bash
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Expected: pass.

- [ ] **Step 3: Commit the public release-hardening set**

Run:

```bash
git commit -m "chore: harden phase1 closeout validation"
```

Expected: commit succeeds and does not include private evidence.

- [ ] **Step 4: Record final commit and residual owner actions**

Run:

```bash
git rev-parse HEAD
git status --short
```

Expected: final commit hash is available. Remaining untracked/ignored private evidence is local-only. Owner actions that remain are receipt/invoice storage, final report submission, and manual grant correspondence outside public Git.
