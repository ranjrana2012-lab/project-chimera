# Phase 1 Replication Toolkit

This toolkit helps a reviewer reproduce the public Phase 1 local demo. It does
not require API keys, private grant records, or advanced GPU hardware.

## Prerequisites

- Python 3.12 preferred.
- A local checkout of the public repository.
- Internet access may be needed for the first dependency install.

## Setup

```bash
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
```

On Windows PowerShell, use `.\venv\Scripts\python.exe`.

## Run The CLI Demo

```bash
./venv/bin/python chimera_core.py demo
```

Expected behavior:

- the command exits successfully;
- positive, negative, and neutral sample inputs are processed;
- selected adaptive strategies are printed.

For the close-out scripted inputs, `scripts/run_phase1_demo.py` should show:

- `I am sad` -> `supportive_care`;
- `I feel excited and ready` -> `momentum_build`;
- `I am confused and overwhelmed` -> `grounding_support`;
- `This is intense but inspiring` -> `reflective_transition`.

## Run A Direct Comparison

```bash
./venv/bin/python chimera_core.py compare "The audience is unsure but curious."
```

This shows baseline-versus-adaptive response behavior for a local text input.

## Run Caption-Style Output

```bash
./venv/bin/python chimera_core.py caption "Welcome to Project Chimera."
```

This is a local formatter demonstration. It is not evidence of formal
accessibility testing or completed BSL/avatar delivery.

## Run The Web Route

```bash
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080`.

Suggested checks:

- page loads locally;
- `/api/state` returns JSON state;
- `/api/process` accepts a text input;
- `/api/export` returns CSV after input has been processed.

## Run Smoke And Privacy Checks

From the repository root:

```bash
./services/operator-console/venv/bin/python test_chimera_smoke.py
python3 scripts/privacy_preflight.py
python3 scripts/run_phase1_demo.py
```

`scripts/run_phase1_demo.py` writes a JSON log under `outputs/run_logs/`. The
log is generated from an actual local run and is ignored by git.

If `pytest` is installed in the operator-console environment:

```bash
./services/operator-console/venv/bin/python -m pytest -p no:cacheprovider tests/unit/test_public_repo_cleanup_contract.py -q
```

## Evidence Handling

Do not commit generated recordings, screenshots, logs, CSV exports, receipts,
invoices, bank statements, participant data, tokens, `.env` files, or private
grant records. Store real evidence outside public git and reference it in the
private evidence pack.
