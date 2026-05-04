import importlib.util
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "capture_phase1_evidence.py"


def load_capture_module():
    spec = importlib.util.spec_from_file_location("capture_phase1_evidence", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_output_directory_uses_injected_date_under_internal():
    capture = load_capture_module()

    output_dir = capture.default_output_dir(today=lambda: date(2026, 5, 4))

    assert output_dir == REPO_ROOT / "internal" / "phase1-evidence" / "2026-05-04"


def test_build_capture_plan_returns_named_argv_commands():
    capture = load_capture_module()

    plan = capture.build_capture_plan(python_executable="/python")

    commands = {command.name: command.argv for command in plan}
    assert {
        "prerequisites",
        "smoke-demo",
        "privacy-preflight",
        "focused-pytest",
        "web-state",
        "web-export",
    }.issubset(commands)
    assert all(isinstance(argv, list) for argv in commands.values())
    assert all(all(isinstance(part, str) for part in argv) for argv in commands.values())
    assert commands["prerequisites"] == [
        "/python",
        "services/operator-console/verify_prerequisites.py",
    ]
    assert commands["smoke-demo"] == [
        "/python",
        "services/operator-console/chimera_core.py",
        "demo",
    ]
    assert commands["privacy-preflight"] == ["/python", "scripts/privacy_preflight.py"]
    assert commands["focused-pytest"][:3] == ["/python", "-m", "pytest"]
    assert commands["web-state"][:2] == ["/python", "scripts/capture_phase1_evidence.py"]
    assert commands["web-export"][:2] == ["/python", "scripts/capture_phase1_evidence.py"]


def test_run_capture_plan_writes_logs_and_manifest(tmp_path):
    capture = load_capture_module()
    output_dir = tmp_path / "private-evidence"
    plan = [
        capture.CaptureCommand("first", [sys.executable, "-c", "print('alpha')"]),
        capture.CaptureCommand("second", [sys.executable, "-c", "print('beta')"]),
    ]
    generated_at = datetime(2026, 5, 4, 12, 30, tzinfo=timezone.utc)

    manifest_path = capture.run_capture_plan(
        plan,
        output_dir=output_dir,
        generated_at=lambda: generated_at,
        cwd=tmp_path,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_path == output_dir / "manifest.json"
    assert manifest["generated_at"] == "2026-05-04T12:30:00+00:00"
    assert manifest["output_dir"] == str(output_dir)
    assert [command["name"] for command in manifest["commands"]] == ["first", "second"]
    assert [result["returncode"] for result in manifest["results"]] == [0, 0]
    assert [result["log_path"] for result in manifest["results"]] == [
        "first.log",
        "second.log",
    ]
    assert (output_dir / "first.log").read_text(encoding="utf-8").strip() == "alpha"
    assert (output_dir / "second.log").read_text(encoding="utf-8").strip() == "beta"


def test_run_capture_plan_records_failure_and_keeps_previous_logs(tmp_path):
    capture = load_capture_module()
    output_dir = tmp_path / "private-evidence"
    plan = [
        capture.CaptureCommand("passing", [sys.executable, "-c", "print('kept')"]),
        capture.CaptureCommand(
            "failing",
            [sys.executable, "-c", "import sys; print('failed'); sys.exit(7)"],
        ),
    ]

    manifest_path = capture.run_capture_plan(plan, output_dir=output_dir, cwd=tmp_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [result["returncode"] for result in manifest["results"]] == [0, 7]
    assert (output_dir / "passing.log").read_text(encoding="utf-8").strip() == "kept"
    assert (output_dir / "failing.log").read_text(encoding="utf-8").strip() == "failed"


def test_run_capture_plan_rejects_log_paths_outside_output_directory(tmp_path):
    capture = load_capture_module()
    output_dir = tmp_path / "private-evidence"
    plan = [
        capture.CaptureCommand(
            "../outside",
            [sys.executable, "-c", "print('should not run')"],
        )
    ]

    try:
        capture.run_capture_plan(plan, output_dir=output_dir, cwd=tmp_path)
    except ValueError as exc:
        assert "outside output directory" in str(exc)
    else:
        raise AssertionError("expected unsafe log path to be rejected")

    assert not (tmp_path / "outside.log").exists()
