# Contributing To Project Chimera

Project Chimera welcomes focused, tested contributions. Keep public/private
boundaries clear: do not commit private grant records, receipts, invoices,
tokens, participant data, generated evidence, or `.env` files.

## Code Of Conduct

Follow `CODE_OF_CONDUCT.md`.

## Default Setup

Use Python 3.12.

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
```

Windows users should follow `docs/guides/STUDENT_LAPTOP_SETUP.md`.

## Branch Naming

- `feature/<name>`
- `fix/<name>`
- `docs/<name>`
- `chore/<name>`

## Before Opening A Pull Request

Run the checks that match your change:

```bash
./services/operator-console/venv/bin/python verify_prerequisites.py
./services/operator-console/venv/bin/python test_chimera_smoke.py
./services/operator-console/venv/bin/python scripts/privacy_preflight.py
./services/operator-console/venv/bin/python -m pytest tests/unit -q
```

For narrow changes, run the focused test files you touched and explain the
scope in the PR.

## Pull Request Expectations

- Keep changes focused.
- Include tests for behavior changes.
- Update docs when user-facing commands or routes change.
- Mention whether the change affects Student / Laptop, DGX Spark / GB10, Kimi,
  or documentation-only routes.
- Confirm no private evidence or generated artifacts are committed.

## More Detail

- Developer setup: `docs/DEVELOPER_SETUP.md`
- Student setup: `docs/guides/STUDENT_LAPTOP_SETUP.md`
- GitHub workflow: `docs/guides/github-workflow.md`
- Security policy: `SECURITY.md`
