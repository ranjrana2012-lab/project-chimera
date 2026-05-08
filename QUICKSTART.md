# Project Chimera Quick Start

This guide is scoped to the public Phase 1 close-out claim: a local adaptive AI
demonstrator with an operator-console CLI and lightweight web route. It is the
recommended route for BCU, R&D, funder, and reviewer checks on an ordinary
laptop or desktop.

Do not use this guide to claim a completed public show, livestream, student
programme, formal accessibility testing, BSL/avatar delivery, audience impact,
or complete grant evidence pack.

## 1. Determine Your Runtime Profile

Run the profile detection script to see which route your environment supports:
```bash
python3 scripts/detect_runtime_profile.py
```
> **Note**: If detection is ambiguous or fails, default to the **Student / Laptop Route**.

---

## 2. Default Route: Student / Laptop
Use this route for Windows/macOS/Linux laptops without specialized NVIDIA GPU environments.

### Local Monolithic Environment Setup
```bash
# 1. Navigate to the operator console
cd services/operator-console

# 2. Setup your virtual environment
python3 -m venv venv

# Windows/Powershell:
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe chimera_core.py demo
$env:PORT='18080'; .\venv\Scripts\python.exe chimera_web.py

# Linux/macOS:
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
PORT=18080 ./venv/bin/python chimera_web.py
```
**Access the Web UI**: `http://127.0.0.1:18080`

### Optional: Docker Preview 
For a lightweight, heuristic-only container preview:
```bash
docker compose -f docker-compose.student.yml up -d --build
```
**Access the Web UI**: `http://127.0.0.1:8080`

---

## 3. Advanced Routes

DGX Spark / GB10, Kimi, monitoring, and broader Compose routes are advanced
maintainer paths. They are not needed to evidence the narrowed Phase 1
close-out claim unless a maintainer has matching hardware, credentials, and
fresh run logs.

Use these only when the host evidence supports them:

- [DGX Spark setup](docs/guides/DGX_SPARK_SETUP.md)
- [Kimi quick start](docs/guides/KIMI_QUICKSTART.md)
- [Docker guide](docs/guides/DOCKER.md)

## Validation

Validate the route you are using on your own machine. For the default local route, run:

```bash
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python test_chimera_smoke.py
python3 scripts/privacy_preflight.py
```

Advanced DGX, Kimi, monitoring, and broader Compose checks should only be
claimed after they have been run on matching hardware or service configuration.

## Useful Test Inputs
Once running (in either environment), try passing these input phrases to see how Chimera adapts the theatrical scene:
- `I am very happy today!` -> expected: `momentum_build`
- `I'm feeling anxious and overwhelmed.` -> expected: `supportive_care`
- `compare "I love this performance"` -> shows baseline vs adaptive output
- `caption "Can you tell me more about the system?"` -> shows local caption-style output

## Close-Out Review Docs

- `docs/closeout/SUBMISSION_READINESS.md`
- `docs/closeout/CLAIMS_REGISTER.md`
- `docs/closeout/EVIDENCE_PACK_INDEX.md`
- `docs/closeout/REPLICATION_TOOLKIT.md`
- `docs/closeout/CASE_STUDY_PHASE1.md`
