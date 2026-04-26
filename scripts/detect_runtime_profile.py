"""Detect the safest Project Chimera runtime profile for this machine.

The detector is intentionally conservative. It recommends the DGX Spark route
only when the host looks like Linux ARM64 with NVIDIA GPU/container-runtime
support. Otherwise it recommends the student/laptop route.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class CommandResult:
    available: bool
    output: str = ""


@dataclass
class RuntimeProfile:
    recommended_profile: str
    confidence: str
    reason: str
    os: str
    architecture: str
    docker: CommandResult
    docker_compose: CommandResult
    nvidia_smi: CommandResult
    docker_nvidia_runtime: bool
    next_commands: list[str]


def run_command(command: list[str], timeout: int = 8) -> CommandResult:
    if shutil.which(command[0]) is None:
        return CommandResult(False, f"{command[0]} not found")

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - defensive environment probe
        return CommandResult(False, str(exc))

    output = (completed.stdout or completed.stderr or "").strip()
    return CommandResult(completed.returncode == 0, output)


def docker_has_nvidia_runtime() -> bool:
    result = run_command(["docker", "info", "--format", "{{json .Runtimes}}"])
    if not result.available:
        return False
    return "nvidia" in result.output.lower()


def detect_dgx_signal(nvidia_output: str) -> bool:
    lowered = nvidia_output.lower()
    return any(
        token in lowered
        for token in ("dgx", "spark", "gb10", "grace", "blackwell")
    )


def build_profile() -> RuntimeProfile:
    os_name = platform.system()
    arch = platform.machine().lower()

    docker = run_command(["docker", "--version"])
    compose = run_command(["docker", "compose", "version"])
    nvidia = run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total",
            "--format=csv,noheader",
        ]
    )
    has_nvidia_runtime = docker_has_nvidia_runtime()

    is_arm64 = arch in {"aarch64", "arm64"}
    is_linux = os_name.lower() == "linux"
    has_gpu_signal = nvidia.available and detect_dgx_signal(nvidia.output)

    if is_linux and is_arm64 and has_nvidia_runtime and has_gpu_signal:
        profile = "dgx-spark"
        confidence = "high"
        reason = "Linux ARM64 host with NVIDIA GPU and Docker NVIDIA runtime detected."
        next_commands = [
            "docker login nvcr.io",
            "docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services",
            "docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build",
        ]
    elif is_linux and is_arm64 and (has_nvidia_runtime or has_gpu_signal):
        profile = "dgx-spark-candidate"
        confidence = "medium"
        reason = "Linux ARM64 host has partial DGX/GPU evidence; verify NVIDIA runtime before using DGX route."
        next_commands = [
            "docker run --rm --gpus all nvcr.io/nvidia/pytorch:25.11-py3 python -c \"import torch; print(torch.cuda.is_available())\"",
            "docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services",
        ]
    else:
        profile = "student-laptop"
        confidence = "high"
        reason = "DGX Spark / Linux ARM64 / NVIDIA runtime evidence was not complete."
        next_commands = [
            "cd services/operator-console",
            "python -m venv venv",
            "python -m pip install -r requirements.txt",
            "python chimera_core.py demo",
        ]

    return RuntimeProfile(
        recommended_profile=profile,
        confidence=confidence,
        reason=reason,
        os=os_name,
        architecture=arch,
        docker=docker,
        docker_compose=compose,
        nvidia_smi=nvidia,
        docker_nvidia_runtime=has_nvidia_runtime,
        next_commands=next_commands,
    )


def main() -> int:
    profile = build_profile()
    print(json.dumps(asdict(profile), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
