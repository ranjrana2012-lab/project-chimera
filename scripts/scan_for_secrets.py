#!/usr/bin/env python3
"""Scan tracked public files for secret-like values without printing values."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKIP_PREFIXES = (
    ".git/",
    "internal/",
    "Grant_Evidence_Pack/",
    "project-chimera-submission/",
    "demo_footage/",
    "models/",
    "venv/",
    ".venv_kimi/",
    "htmlcov/",
)
TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OpenAI-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9_-]{20,}\b")),
    ("NVIDIA API token", re.compile(r"\bnvapi-[A-Za-z0-9_-]{20,}\b")),
    (
        "assigned secret-like value",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|bearer)\b\s*[:=]\s*['\"]?(?!"
            r"REDACTED|CHANGE_ME|CHANGEME|example|placeholder|your_|args\.|self\.|request\.|"
            r"config\.|get_|os\.getenv|None\b|<|$)"
            r"[A-Za-z0-9_./+=:-]{12,}"
        ),
    ),
    ("local absolute home path", re.compile(r"(/home/|/Users/|C:\\Users\\)")),
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    risk_type: str


def git_paths(include_untracked: bool) -> list[str]:
    commands = [["git", "ls-files"]]
    if include_untracked:
        commands.append(["git", "ls-files", "--others", "--exclude-standard"])
    paths: set[str] = set()
    for argv in commands:
        completed = subprocess.run(
            argv,
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        paths.update(line for line in completed.stdout.splitlines() if line)
    return sorted(paths)


def is_text_candidate(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    suffix = Path(path).suffix.lower()
    return suffix in TEXT_SUFFIXES or Path(path).name in {".gitignore", ".dockerignore"}


def scan(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if not is_text_candidate(path):
            continue
        try:
            content = (REPO_ROOT / path).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            for risk_type, pattern in PATTERNS:
                if path == "scripts/scan_for_secrets.py" and risk_type == "local absolute home path":
                    continue
                if pattern.search(line):
                    findings.append(Finding(path=path, line=line_no, risk_type=risk_type))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-untracked", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)

    findings = scan(git_paths(args.include_untracked))
    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
    elif findings:
        print("Secret scan findings; values are intentionally not printed:")
        for finding in findings:
            print(f"- {finding.path}:{finding.line}: {finding.risk_type}")
    else:
        print("No secret-like findings found.")

    return 1 if args.fail_on_findings and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
