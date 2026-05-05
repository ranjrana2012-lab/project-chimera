import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


FORBIDDEN_TRACKED_PREFIXES = (
    ".autonomous/",
    ".claude/",
    "demo-materials-2026-03-02/",
    "future_concepts/",
    "internal/",
    "platform/dashboard/frontend/node_modules/",
    "progress/",
    "proposals/",
)


FORBIDDEN_TRACKED_EXACT = {
    ".env.docker",
    ".env.nemotron",
    "LOCAL_VALIDATION_REPORT.md",
    "PATCH_SUMMARY.md",
    "RELEASE_SYNC_REPORT.md",
    "REMAINING_GAPS.md",
    "services/zai-auth-proxy/tokens/session_token.json",
}


FORBIDDEN_COMPILED_BINARY_EXACT = {
    "services/claude-orchestrator/bin/cli",
    "services/claude-orchestrator/bin/orchestrator",
}


FORBIDDEN_COMPILED_BINARY_SUFFIXES = (
    ".dll",
    ".dylib",
    ".exe",
    ".o",
    ".so",
)


FORBIDDEN_MEDIA_SUFFIXES = (
    ".avi",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".webm",
)


FORBIDDEN_RECEIPT_INVOICE_TOKENS = {
    "invoice",
    "invoices",
    "receipt",
    "receipts",
}


FORBIDDEN_README_PHRASES = (
    "Last validated locally",
    "Last locally validated",
    "Current local sign-off",
    "Final regression",
    "Ubuntu 24.04.4 ARM64 / NVIDIA GB10",
    "737 passed",
    "96 skipped",
    "Monitoring Stack",
    "Validated Checks",
    "docker login nvcr.io",
    "Download Kimi K2.6 model",
    "LOCAL_VALIDATION_REPORT.md",
    "PATCH_SUMMARY.md",
    "REMAINING_GAPS.md",
    "RELEASE_SYNC_REPORT.md",
)


FORBIDDEN_PUBLIC_METADATA_PHRASES = (
    "admin/admin",
    "all 8 services",
    "8 core services operational",
    "8 microservices",
    "BSL Translation",
    "Captioning Agent",
    "Production-ready",
    "Ready to apply",
    "real-time adaptive performances",
    "adapt in real-time",
    "k3s Bootstrap",
    "git clone https://github.com/project-chimera/main.git",
)


REQUIRED_README_PHRASES = (
    "Project Chimera",
    "Phase 1",
    "local adaptive AI foundation",
    "Student / Laptop",
    "Private evidence",
    "docs/guides/STUDENT_LAPTOP_SETUP.md",
    "docs/guides/DGX_SPARK_SETUP.md",
    "docs/guides/KIMI_QUICKSTART.md",
)


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def path_tokens(path: str) -> set[str]:
    return {token for token in re.split(r"[^A-Za-z0-9]+", path.lower()) if token}


def is_allowed_env_example(path: str) -> bool:
    name = Path(path).name
    return name == ".env.example" or (
        name.startswith(".env.") and name.endswith(".example")
    )


def is_forbidden_tracked_path(path: str) -> bool:
    lower_path = path.lower()
    parts = Path(path).parts

    return (
        path in FORBIDDEN_TRACKED_EXACT
        or path in FORBIDDEN_COMPILED_BINARY_EXACT
        or any(path.startswith(prefix) for prefix in FORBIDDEN_TRACKED_PREFIXES)
        or (Path(path).name.startswith(".env") and not is_allowed_env_example(path))
        or bool(path_tokens(path) & FORBIDDEN_RECEIPT_INVOICE_TOKENS)
        or lower_path.endswith(FORBIDDEN_MEDIA_SUFFIXES)
        or lower_path.endswith(FORBIDDEN_COMPILED_BINARY_SUFFIXES)
        or "node_modules" in parts
        or "test-results" in lower_path
        or "demo_captures" in parts
        or lower_path.endswith("/coverage.json")
    )


def test_public_git_index_excludes_private_generated_and_experimental_paths():
    tracked = set(git_ls_files())

    forbidden = sorted(path for path in tracked if is_forbidden_tracked_path(path))

    assert forbidden == [], (
        "Tracked public git index still contains private/generated/local cleanup "
        f"paths:\n" + "\n".join(forbidden)
    )


def test_validation_reports_are_under_docs_reports_not_root():
    tracked = set(git_ls_files())

    assert "LOCAL_VALIDATION_REPORT.md" not in tracked
    assert "PATCH_SUMMARY.md" not in tracked
    assert "REMAINING_GAPS.md" not in tracked
    assert "RELEASE_SYNC_REPORT.md" not in tracked
    assert "docs/reports/README.md" in tracked
    assert "docs/reports/LOCAL_VALIDATION_REPORT.md" in tracked
    assert "docs/reports/PATCH_SUMMARY.md" in tracked
    assert "docs/reports/REMAINING_GAPS.md" in tracked
    assert "docs/reports/RELEASE_SYNC_REPORT.md" in tracked


def test_readme_is_concise_public_landing_page():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for phrase in FORBIDDEN_README_PHRASES:
        assert phrase not in readme
    for phrase in REQUIRED_README_PHRASES:
        assert phrase in readme
    assert len(readme.splitlines()) <= 180


def test_github_issue_templates_are_deduplicated():
    templates = {
        path.name
        for path in (REPO_ROOT / ".github" / "ISSUE_TEMPLATE").glob("*")
        if path.is_file()
    }

    assert "bug_report.md" in templates
    assert "feature_request.md" in templates
    assert "bug.md" not in templates
    assert "feature.md" not in templates


def test_public_github_metadata_does_not_recreate_stale_claims():
    public_metadata_paths = [
        "README.md",
        "docs/README.md",
        *[
            str(path.relative_to(REPO_ROOT))
            for path in (REPO_ROOT / ".github").glob("*.md")
        ],
        *[
            str(path.relative_to(REPO_ROOT))
            for path in (REPO_ROOT / ".github" / "workflows").glob("*.y*ml")
        ],
        *[
            str(path.relative_to(REPO_ROOT))
            for path in (REPO_ROOT / "docs" / "demo").glob("*.md")
        ],
    ]

    stale_matches = []
    for relative_path in public_metadata_paths:
        path = REPO_ROOT / relative_path
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        stale_matches.extend(
            f"{relative_path}: {phrase}"
            for phrase in FORBIDDEN_PUBLIC_METADATA_PHRASES
            if phrase in content
        )

    assert stale_matches == []


def test_public_evidence_placeholder_exists_when_referenced():
    tracked = set(git_ls_files())
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    docs_demo = (REPO_ROOT / "docs" / "demo" / "README.md").read_text(
        encoding="utf-8"
    )

    assert "evidence/" in readme
    assert "../../evidence/README.md" in docs_demo
    assert "evidence/README.md" in tracked
