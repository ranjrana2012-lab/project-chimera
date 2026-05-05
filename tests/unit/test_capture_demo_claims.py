import asyncio
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "services" / "operator-console" / "capture_demo.py"
CHIMERA_CORE_PATH = REPO_ROOT / "services" / "operator-console" / "chimera_core.py"


FORBIDDEN_PUBLIC_CLAIMS = [
    "Birmingham City University",
    "GLM-4.7",
    "GLM-4.7 API (primary)",
    "Ollama Local LLM (fallback)",
    "chimera_core.py (700+ lines)",
    "20+ comprehensive documentation files",
    "Financial audit trail ready",
    "COMPLIANT - Successful Proof-of-Concept",
    "Grant_Evidence_Pack/",
    "8 pushes during Phase 1",
    "5,000+ lines",
]


def load_capture_demo_module():
    spec = importlib.util.spec_from_file_location("capture_demo", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_chimera_core_module():
    spec = importlib.util.spec_from_file_location("chimera_core", CHIMERA_CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def fake_capture_scene(scene_name, _command, output_dir):
    output_file = output_dir / f"scene_{scene_name}.txt"
    output_file.write_text("captured scene\n", encoding="utf-8")
    return output_file, "captured scene\n"


def test_summary_scene_uses_current_private_evidence_language(tmp_path, monkeypatch):
    capture_demo = load_capture_demo_module()
    monkeypatch.setattr(sys, "argv", ["capture_demo.py", "--output-dir", str(tmp_path)])
    monkeypatch.setattr(capture_demo, "capture_scene", fake_capture_scene)
    monkeypatch.setattr(capture_demo.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        capture_demo.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="demo command output\n"),
    )

    asyncio.run(capture_demo.main())

    summary = (tmp_path / "scene_06_summary.txt").read_text(encoding="utf-8")
    all_scene_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(tmp_path.glob("scene_*.txt"))
    )
    for forbidden_claim in FORBIDDEN_PUBLIC_CLAIMS:
        assert forbidden_claim not in all_scene_text
    assert "internal/phase1-evidence/" in summary
    assert "Privacy preflight" in summary
    assert "Maintainer review" in summary


def test_chimera_core_banner_uses_provider_neutral_language(capsys):
    chimera_core = load_chimera_core_module()

    chimera_core.ChimeraCore().print_banner()

    output = capsys.readouterr().out
    for forbidden_claim in FORBIDDEN_PUBLIC_CLAIMS:
        assert forbidden_claim not in output
    assert "Adaptive Routing" in output
    assert "Dialogue Generation" in output
