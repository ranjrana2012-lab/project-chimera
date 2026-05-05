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
    "services/operator-console/demo_captures/",
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


FORBIDDEN_README_PHRASES = (
    "Last validated locally",
    "Last locally validated",
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


def test_public_git_index_excludes_private_generated_and_experimental_paths():
    tracked = set(git_ls_files())

    forbidden = {
        path
        for path in tracked
        if path in FORBIDDEN_TRACKED_EXACT
        or any(path.startswith(prefix) for prefix in FORBIDDEN_TRACKED_PREFIXES)
        or "/node_modules/" in path
        or path.endswith("/coverage.json")
        or path.endswith("/test-results/.last-run.json")
    }

    assert forbidden == set()


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
