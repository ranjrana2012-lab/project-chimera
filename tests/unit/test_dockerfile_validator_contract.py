import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_current_service_dockerfiles_pass_ci_validator():
    result = subprocess.run(
        ["bash", "scripts/validate-dockerfiles.sh"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
