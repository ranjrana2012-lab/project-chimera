# Project Chimera - Quick Start Guide

This guide will get you up and running with Project Chimera as quickly as possible.

## 1. Determine Your Runtime Profile

Run the profile detection script to see which route your environment supports:
```bash
python scripts/detect_runtime_profile.py
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
python -m venv venv

# Windows/Powershell:
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe chimera_core.py demo
$env:PORT='18080'; .\venv\Scripts\python.exe chimera_web.py

# Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt
python chimera_core.py demo
PORT=18080 python chimera_web.py
```
**Access the Web UI**: `http://127.0.0.1:18080`

### Optional: Docker Preview 
For a lightweight, heuristic-only container preview:
```bash
docker compose -f docker-compose.student.yml up -d --build
```
**Access the Web UI**: `http://127.0.0.1:8080`

---

## 3. Advanced Route: NVIDIA DGX Spark / GB10 (ARM64)
Use this route **only** if you are on an NVIDIA DGX Spark / Grace Blackwell host (ARM64), with Docker, NVIDIA Container Runtime (`--gpus all`), and NGC Registry access.

```bash
# 1. Login to NVIDIA container registry (required for PyTorch base images)
docker login nvcr.io

# 2. Verify your Compose Configuration
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml config --services

# 3. Boot the Multi-Service Application Stack
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d --build

# 4. Verify Services are Running
docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml ps
```

The Operator Console will be exposed on **port 8007**.
```bash
http://<dgx-host-ip>:8007
```

## Useful Test Inputs
Once running (in either environment), try passing these input phrases to see how Chimera adapts the theatrical scene:
- `I am very happy today!` -> expected: `momentum_build`
- `I'm feeling anxious and overwhelmed.` -> expected: `supportive_care`
- `compare "I love this performance"` -> shows baseline vs adaptive output
- `caption "Can you tell me more about the system?"` -> enforces accessibility mode
