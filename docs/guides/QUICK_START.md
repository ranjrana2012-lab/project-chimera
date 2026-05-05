# Quick Start

This page is the short public pointer for Phase 1.

Use the default local route:

- `docs/guides/STUDENT_LAPTOP_SETUP.md`

Fast path:

```bash
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080`.

Use DGX Spark, Kimi, and service-compose routes only when the local hardware,
Docker/GPU access, credentials, and guide prerequisites match.
