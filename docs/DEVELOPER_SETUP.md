# Developer Setup

Use the same public Phase 1 route as reviewers before touching broader service
work.

## Required Tools

- Python 3.12+
- Git
- Optional: Docker Compose v2 for the student sandbox or advanced stacks

## First Validation

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080`.

## Development Checks

From the repository root:

```bash
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python test_chimera_smoke.py
./services/operator-console/venv/bin/python -m pytest tests/unit/test_chimera_cli_contract.py tests/unit/test_chimera_web_contract.py -q
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
```

## Public / Private Boundary

Keep these out of public git:

- `.env` files and API keys;
- grant records;
- receipts and invoices;
- generated screenshots, recordings, exports, and logs;
- participant or student contact data;
- machine-specific validation notes.

Use `internal/` or another private location for real evidence and local working
notes.

## Broader Routes

Use broader Docker, DGX Spark, or Kimi paths only after the local operator-console
route is healthy and the relevant guide prerequisites are true:

- `docs/guides/DOCKER.md`
- `docs/guides/DGX_SPARK_SETUP.md`
- `docs/guides/KIMI_QUICKSTART.md`

Do not claim an advanced route works without fresh local evidence from the
matching hardware and credentials.
