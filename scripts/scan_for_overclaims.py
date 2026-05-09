#!/usr/bin/env python3
"""Scan tracked public files for close-out overclaim language."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TERMS = (
    "public show delivered",
    "livestream delivered",
    "40 students",
    "two DGX",
    "audience-driven live",
    "production-ready",
    "fully deployed",
    "completed performance",
    "validated accessibility",
    "BSL avatar",
    "venue",
    "rehearsal",
)
SKIP_PREFIXES = (
    ".git/",
    "internal/",
    "Grant_Evidence_Pack/",
    "project-chimera-submission/",
    "demo_footage/",
    "docs/superpowers/",
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


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    term: str
    note: str


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


def guarded_context(line: str) -> bool:
    lowered = line.lower()
    return any(
        marker in lowered
        for marker in (
            "do not claim",
            "not claim",
            "avoid",
            "not achieved",
            "human action required",
            "postponed",
            "future",
            "future-stage",
            "not evidence",
            "not a public show",
            "not a livestream",
            "claims to avoid",
            "terms searched",
            "stop ",
            "human action required",
            "only claim if evidenced",
            "unless external evidence exists",
            "unless direct evidence is supplied",
            "do not present",
            "do not imply",
            "do not invent",
            "do not treat",
            "reallocated",
        )
    )


def scan(paths: list[str], terms: tuple[str, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if path == "scripts/scan_for_overclaims.py":
            continue
        if not is_text_candidate(path):
            continue
        file_path = REPO_ROOT / path
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        guarded_section = False
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip().lower()
            if stripped.startswith("#"):
                guarded_section = any(
                    marker in stripped
                    for marker in (
                        "claims to avoid",
                        "what was not claimed",
                        "limitations",
                        "terms searched",
                        "stop-doing",
                        "claim guardrails",
                    )
                )
            lowered = line.lower()
            for term in terms:
                if term.lower() in lowered:
                    findings.append(
                        Finding(
                            path=path,
                            line=line_no,
                            term=term,
                            note="guarded" if guarded_section or guarded_context(line) else "review",
                        )
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-untracked", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-review", action="store_true")
    args = parser.parse_args(argv)

    findings = scan(git_paths(args.include_untracked), DEFAULT_TERMS)
    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
    elif findings:
        print("Overclaim scan findings:")
        for finding in findings:
            print(f"- {finding.path}:{finding.line}: {finding.term} [{finding.note}]")
    else:
        print("No overclaim terms found.")

    has_review = any(finding.note == "review" for finding in findings)
    return 1 if args.fail_on_review and has_review else 0


if __name__ == "__main__":
    raise SystemExit(main())
