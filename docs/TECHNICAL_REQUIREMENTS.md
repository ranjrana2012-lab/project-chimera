# Project Chimera - Full Technical Requirements Document

This document captures the holistic system architecture, runtime constraints, technical components, and dependencies for Project Chimera, serving as the single source of truth for deployments.

## 1. System Architecture Overview

Project Chimera is an AI-powered live theatre platform that ingests audience input and adapts performance logic in real-time. It operates using a microservices-driven architecture backed by asynchronous messaging.

### Core Microservices

When deployed using the full MVP stack, the following separate domain services are launched:
- **`openclaw-orchestrator`** (Port `8000`): The central coordinating brain routing data between agents.
- **`scenespeak-agent`** (Port `8001`): Connects to large language models (local DGX or external GLM_API) to evaluate scene context.
- **`translation-agent`** (Port `8002`): Translates theatrical cues for internationalisation and BSL outputs.
- **`sentiment-agent`** (Port `8004`): Conducts ML-based sentiment parsing using `distilbert`.
- **`safety-filter`** (Port `8006`): Applies strict Pydantic-based guardrails on output to ensure actor safety.
- **`operator-console`** (Port `8007`): The overarching UI dashboard and administration toolkit.
- **`hardware-bridge`** (Port `8008`): Interfaces with external DMX/Hardware lighting and sound queues.
- **`redis`** (Port `6379`): Synchronous/Asynchronous state and memory routing.

---

## 2. Hardware Profiles & Deployment Requirements

Project Chimera supports two distinct deployment routes. **Optimistic hardware assumptions will cause critical failures.**

### A) The Default Route (Student/Laptop)
**Target Profile**: Local development, students, code-reviewers, typical x86 Windows/macOS/Linux machines.
- **Compute Constraints**: No GPU required. Uses lightweight mock responses or pre-baked heuristics.
- **Docker**: Single `docker-compose.student.yml` setup without NVIDIA dependencies. 
- **Standalone Mode**: The platform can be ran as a monolithic script (`chimera_core.py`) directly from python `venv` to prevent resource starvation.

### B) The Advanced Route (DGX Spark / GB10 ARM64)
**Target Profile**: Live performance deployment on NVIDIA DGX Spark or Grace Blackwell cluster environments.
- **Compute Constraints**: Requires Linux ARM64 (`aarch64`) architecture.
- **Hardware Integration**: Requires full GPU pass-through (`--gpus all`) and the **NVIDIA Container Runtime**.
- **PyTorch Image**: Fetches heavily-optimized PyTorch base images from NGC (`nvcr.io/nvidia/pytorch:25.11-py3`). 
- **Local LLM Inference**: Can optionally route connections to local instances of `nemotron-3-super-120b-a12b-nvfp4` for fully air-gapped performance.

---

## 3. Technology Stack

- **Language**: Python 3.12+
- **Containerization**: Docker Compose
- **Orchestration / Routing**: Redis
- **APIs**: FastAPI / Uvicorn
- **Safety / Schemas**: Pydantic
- **Machine Learning**: PyTorch, HuggingFace `transformers` (DistilBERT)
- **Formatting / Linting**: Ruff and Black
- **Testing**: Pytest

---

## 4. Dependencies & Authentication Requirements

### Docker Containers (External)
- Deployment on DGX architectures requires a valid authentication token for `nvcr.io` (NVIDIA NGC). 

### Environment Variables
While secrets are NOT actively required to bootstrap the student application, the following environment variables interact with production instances:
- `CHIMERA_RUNTIME_PROFILE`: Auto-detects between `student` and `dgx-spark`.
- `GLM_API_KEY`: Used strictly when querying upstream GLM APIs for scene dialogue generation.
- `SCENESPEAK_LOCAL_LLM_ENABLED` / `SCENESPEAK_LOCAL_LLM_URL`: Enforces routing to local LLM clusters for air-gapped performance capability.
- `CHIMERA_DGX_MODEL_CACHE`: Mounts the DGX hardware directory for storing PyTorch and Transformers model weights to avoid OOM or slow bootstrapping problems.

> **CRITICAL SECURITY NOTE**: Never commit `GLM_API_KEY`, NGC tokens, or local Nemotron endpoints inside `.env` to the repo.

---

## 5. Build System & Optimization Requirements

Because of the massive scale of PyTorch containers and Transformer models:
- **Strict Isolation**: Model files (`./models`), virtual environments (`venv`, `.venv`, `**/venv/`), and testing datasets (`final_test_env`) are vigorously blocked via `.dockerignore` to prevent Docker context ballooning.
- **Volumes**: HuggingFace volumes must be mounted via host bindings with appropriate `chmod`/`chown` capabilities so containers (binding to UID `appuser`) can write local cache.

---

## 6. Testing Prerequisites
Project Chimera employs comprehensive Pytest testing:
- **Unit Tests**: `make test-unit` will run standalone, decoupled logic tests.
- **Integration Tests**: `make test-integration` explicitly requires the `docker-compose.mvp.yml` cluster to be booted, running isolated HTTP checks against the individual microservices. Doing this without a running cluster will result in timeout errors.
