import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "privacy_preflight.py"


def load_privacy_preflight():
    spec = importlib.util.spec_from_file_location("privacy_preflight", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_forbidden_private_paths_are_rejected():
    privacy_preflight = load_privacy_preflight()

    findings = privacy_preflight.classify_paths(
        [
            "internal/grant-tracking/grant_closeout/final_report.md",
            ".env.nemotron",
            "evidence/screenshots/2026-05-04-demo.png",
            "services/zai-auth-proxy/tokens/session_token.json",
            "Grant_Evidence_Pack/receipt.pdf",
            "platform/dashboard/frontend/node_modules/vite/package.json",
        ]
    )

    assert {finding.path for finding in findings} == {
        "internal/grant-tracking/grant_closeout/final_report.md",
        ".env.nemotron",
        "evidence/screenshots/2026-05-04-demo.png",
        "services/zai-auth-proxy/tokens/session_token.json",
        "Grant_Evidence_Pack/receipt.pdf",
        "platform/dashboard/frontend/node_modules/vite/package.json",
    }


def test_public_placeholders_and_examples_are_allowed():
    privacy_preflight = load_privacy_preflight()

    findings = privacy_preflight.classify_paths(
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


def test_venv_paths_are_classified_when_they_are_private_artifacts():
    privacy_preflight = load_privacy_preflight()

    findings = privacy_preflight.classify_paths(
        ["services/operator-console/venv/.env", "venv/demo.mp4"]
    )

    assert {finding.path for finding in findings} == {
        "services/operator-console/venv/.env",
        "venv/demo.mp4",
    }


def test_nested_env_example_variants_are_allowed():
    privacy_preflight = load_privacy_preflight()

    findings = privacy_preflight.classify_paths(
        ["services/foo/.env.local.example", "profiles/.env.production.example"]
    )

    assert findings == []


def test_financial_keywords_match_tokens_not_substrings():
    privacy_preflight = load_privacy_preflight()

    findings = privacy_preflight.classify_paths(
        [
            "docs/syntax.md",
            "docs/private-tax.pdf",
            "docs/bank_statement.pdf",
            "receipts/invoice-001.pdf",
            "records/receipt.png",
        ]
    )

    assert {finding.path for finding in findings} == {
        "docs/private-tax.pdf",
        "docs/bank_statement.pdf",
        "receipts/invoice-001.pdf",
        "records/receipt.png",
    }


def test_main_returns_failure_when_collector_reports_forbidden_path(monkeypatch, capsys):
    privacy_preflight = load_privacy_preflight()
    path = "internal/grant-tracking/grant_closeout/final_report.md"
    monkeypatch.setattr(
        privacy_preflight,
        "collect_publication_risk_paths",
        lambda: [path],
    )

    assert privacy_preflight.main([]) == 1

    output = capsys.readouterr().out
    assert "Privacy preflight failed" in output
    assert path in output


def test_main_returns_success_when_no_forbidden_paths(monkeypatch, capsys):
    privacy_preflight = load_privacy_preflight()
    monkeypatch.setattr(
        privacy_preflight,
        "collect_publication_risk_paths",
        lambda: [
            "evidence/README.md",
            "evidence/screenshots/.gitkeep",
            ".env.example",
            "docs/PHASE_1_SCOPE.md",
        ],
    )

    assert privacy_preflight.main([]) == 0

    output = capsys.readouterr().out
    assert "Privacy preflight passed" in output


def test_main_rejects_ngc_token_literals_in_publication_risk_files(
    monkeypatch, tmp_path, capsys
):
    privacy_preflight = load_privacy_preflight()
    doc_path = tmp_path / "docs" / "setup.md"
    doc_path.parent.mkdir()
    token = "nvapi-" + "abc123def456ghi789jkl012mno345pqr678"
    doc_path.write_text(
        f"NGC_API_KEY={token}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(privacy_preflight, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        privacy_preflight,
        "collect_publication_risk_paths",
        lambda: ["docs/setup.md"],
    )

    assert privacy_preflight.main([]) == 1

    output = capsys.readouterr().out
    assert "Privacy preflight failed" in output
    assert "docs/setup.md" in output
    assert "NGC/NVIDIA API key/token literal" in output


def test_public_cleanup_experiment_and_root_report_paths_are_rejected():
    privacy_preflight = load_privacy_preflight()

    findings = privacy_preflight.classify_paths(
        [
            ".autonomous/state.json",
            ".claude/settings.local.json",
            "future_concepts/services/old-agent/app.py",
            "demo-materials-2026-03-02/raw_capture.txt",
            "progress/week-1.md",
            "proposals/venue-proposal.md",
            "LOCAL_VALIDATION_REPORT.md",
            "PATCH_SUMMARY.md",
            "REMAINING_GAPS.md",
            "RELEASE_SYNC_REPORT.md",
            "docs/reports/LOCAL_VALIDATION_REPORT.md",
            "docs/reports/PATCH_SUMMARY.md",
        ]
    )

    assert {finding.path for finding in findings} == {
        ".autonomous/state.json",
        ".claude/settings.local.json",
        "future_concepts/services/old-agent/app.py",
        "demo-materials-2026-03-02/raw_capture.txt",
        "progress/week-1.md",
        "proposals/venue-proposal.md",
        "LOCAL_VALIDATION_REPORT.md",
        "PATCH_SUMMARY.md",
        "REMAINING_GAPS.md",
        "RELEASE_SYNC_REPORT.md",
    }
