#!/usr/bin/env python3

import subprocess
import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

VIDEO_SUFFIXES = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}
FINANCIAL_KEYWORDS = ("receipt", "invoice", "bank", "tax")
PUBLIC_EXPERIMENT_PREFIXES = (
    ".autonomous/",
    ".claude/",
    "demo-materials-2026-03-02/",
    "future_concepts/",
    "progress/",
    "proposals/",
)
ROOT_REPORT_FILES = {
    "LOCAL_VALIDATION_REPORT.md",
    "PATCH_SUMMARY.md",
    "RELEASE_SYNC_REPORT.md",
    "REMAINING_GAPS.md",
}
CONTACT_SPREADSHEET_SUFFIXES = {".csv", ".ods", ".xls", ".xlsx"}
PUBLIC_CLOSEOUT_TEMPLATE_PREFIX = "chimera_closeout_pack/"
PUBLIC_CLOSEOUT_TEMPLATE_SUFFIXES = {".csv", ".md"}
NGC_TOKEN_LITERAL_RE = re.compile(
    r"\bnvapi-(?!REDACTED\b)(?!\.\.\.\b)[A-Za-z0-9_-]{20,}\b"
)
MAX_PRINTED_FINDINGS = 200


@dataclass(frozen=True)
class Finding:
    path: str
    reason: str


def _normalize(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _is_allowed_env_file(path: str) -> bool:
    return Path(path).name.startswith(".env.") and Path(path).name.endswith(".example")


def _is_allowed_evidence_placeholder(path: str) -> bool:
    return path == "evidence/README.md" or (
        path.startswith("evidence/") and Path(path).name == ".gitkeep"
    )


def _has_financial_keyword(path: str) -> bool:
    tokens = [token for token in re.split(r"[^a-z0-9]+", path.lower()) if token]
    return any(keyword in tokens for keyword in FINANCIAL_KEYWORDS)


def _is_allowed_closeout_template(path: str) -> bool:
    return (
        path.startswith(PUBLIC_CLOSEOUT_TEMPLATE_PREFIX)
        and Path(path).suffix.lower() in PUBLIC_CLOSEOUT_TEMPLATE_SUFFIXES
    )


def _is_student_contact_path(path: str) -> bool:
    name_lower = Path(path).name.lower()
    suffix = Path(path).suffix.lower()
    if path == "data/students.csv":
        return True
    if path.startswith("data/") and suffix == ".csv" and "students" in name_lower:
        return not name_lower.endswith(".example.csv")
    return suffix in CONTACT_SPREADSHEET_SUFFIXES and "contact" in name_lower


def classify_paths(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []

    for raw_path in paths:
        path = _normalize(raw_path)
        parts = Path(path).parts
        name = Path(path).name
        suffix = Path(path).suffix.lower()

        reason = ""
        if path.startswith("internal/"):
            reason = "internal private path"
        elif any(path.startswith(prefix) for prefix in PUBLIC_EXPERIMENT_PREFIXES):
            reason = "public experiment or prototype path"
        elif path in ROOT_REPORT_FILES:
            reason = "root maintainer report path"
        elif path.startswith("docs/@ Ranj Notes/"):
            reason = "private notes path"
        elif name.startswith(".~lock."):
            reason = "office lock file"
        elif path.startswith("Grant_Evidence_Pack/"):
            reason = "grant evidence pack path"
        elif _is_student_contact_path(path):
            reason = "student or contact data path"
        elif path.startswith("project-chimera-submission"):
            reason = "submission package path"
        elif path.startswith("demo_footage/"):
            reason = "demo footage path"
        elif path.startswith("demo_captures/") or path.startswith(
            "services/operator-console/demo_captures/"
        ):
            reason = "demo captures path"
        elif path.startswith("services/zai-auth-proxy/tokens/") and suffix == ".json":
            reason = "auth proxy token file"
        elif "node_modules" in parts:
            reason = "node_modules dependency path"
        elif name.startswith(".env") and not _is_allowed_env_file(path):
            reason = "real environment file"
        elif path.startswith("evidence/") and not _is_allowed_evidence_placeholder(path):
            reason = "evidence artifact path"
        elif _is_allowed_closeout_template(path):
            reason = ""
        elif _has_financial_keyword(path):
            reason = "financial or tax document path"
        elif suffix in VIDEO_SUFFIXES:
            reason = "video recording path"

        if reason:
            findings.append(Finding(path=path, reason=reason))

    return findings


def classify_file_contents(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []

    for raw_path in paths:
        path = _normalize(raw_path)
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = REPO_ROOT / path
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if NGC_TOKEN_LITERAL_RE.search(content):
            findings.append(
                Finding(path=path, reason="NGC/NVIDIA API key/token literal")
            )

    return findings


def _git_paths(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def collect_publication_risk_paths() -> list[str]:
    paths = set()
    paths.update(_git_paths(["ls-files"]))
    paths.update(_git_paths(["diff", "--cached", "--name-only", "--diff-filter=AM"]))
    paths.update(_git_paths(["ls-files", "--others", "--exclude-standard"]))
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    del argv
    paths = collect_publication_risk_paths()
    findings = classify_paths(paths)
    findings.extend(classify_file_contents(paths))

    if findings:
        print("Privacy preflight failed:")
        for finding in findings[:MAX_PRINTED_FINDINGS]:
            print(f"- {finding.path}: {finding.reason}")
        remaining = len(findings) - MAX_PRINTED_FINDINGS
        if remaining > 0:
            print(f"- ... {remaining} more finding(s) omitted")
        return 1

    print("Privacy preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
