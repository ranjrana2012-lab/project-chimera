# Phase 1 Service Status Reference

This public status reference covers the default Student / Laptop route only.
Advanced Compose, monitoring, DGX Spark / GB10, and Kimi checks should be used
only when the host evidence and credentials match those routes.

## Local CLI Checks

From `services/operator-console`:

```bash
./venv/bin/python chimera_core.py demo
./venv/bin/python chimera_core.py compare "The audience is curious."
./venv/bin/python chimera_core.py caption "Welcome to Project Chimera."
```

Expected result: each command exits successfully and prints local demonstrator
output for the requested mode.

## Local Web Route

Start the web route:

```bash
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080` and check:

- the page loads;
- `/api/state` returns JSON state;
- `/api/process` accepts text input;
- `/api/export` returns CSV data after processing input.

## Repository-Level Checks

From the repository root:

```bash
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python test_chimera_smoke.py
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

Expected result:

- prerequisite validation reports zero failures;
- smoke validation reports all six checks passing;
- privacy preflight reports no public/private boundary violations.

## Evidence Boundary

Do not commit generated screenshots, recordings, logs, receipts, invoices,
participant data, private grant records, tokens, or `.env` files. Store real
evidence privately and use `evidence/README.md` only as a public-safe placeholder.
