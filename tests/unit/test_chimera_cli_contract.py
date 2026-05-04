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
