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
