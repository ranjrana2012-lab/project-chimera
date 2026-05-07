# Project Chimera

Project Chimera is an AI-powered live theatre research platform. Phase 1 is a
local adaptive AI foundation: it accepts audience-style text, detects emotional
tone, routes the input to an adaptive response strategy, and exposes a small CLI
and web console for review.

[![CI/CD](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml/badge.svg)](https://github.com/ranjrana2012-lab/project-chimera/actions/workflows/ci.yml)
![Release](https://img.shields.io/github/v/tag/ranjrana2012-lab/project-chimera?label=release)
![Python](https://img.shields.io/badge/python-3.12-blue)

## Phase 1 Status

The current public claim is deliberately narrow: Project Chimera has a working
local adaptive AI demonstrator and supporting service experiments. It is not yet
a finished theatre production, public audience workflow, BSL/avatar system, or
complete grant evidence pack.

## What The Local Demo Shows

- Sentiment routing for positive, negative, and neutral text.
- Adaptive strategies: `momentum_build`, `supportive_care`, and
  `standard_response`.
- Baseline-versus-adaptive comparison mode.
- Caption-style output and SRT export.
- A lightweight operator-console web route with state, process, and CSV export
  endpoints.

## Quick Start: Student / Laptop

Use this route first on ordinary Windows, macOS, Linux, or WSL machines.

```bash
git clone https://github.com/ranjrana2012-lab/project-chimera.git
cd project-chimera

cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
```

On Windows PowerShell, use `.\venv\Scripts\python.exe` instead of
`./venv/bin/python`.

To run the local web console:

```bash
cd services/operator-console
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080`.

## Setup Guides

- Student / Laptop: `docs/guides/STUDENT_LAPTOP_SETUP.md`
- DGX Spark / GB10: `docs/guides/DGX_SPARK_SETUP.md`
- Kimi advanced route: `docs/guides/KIMI_QUICKSTART.md`
- Developer setup: `docs/DEVELOPER_SETUP.md`

Use the Student / Laptop route unless you have clear DGX Spark / GB10 hardware
evidence and Docker GPU access.

## Private Evidence

The public repository contains source, tests, setup docs, and public-safe
templates. Private evidence stays outside public git:

- receipts and invoices;
- private grant records;
- meeting notes;
- generated screenshots, recordings, and logs;
- participant data;
- API keys, tokens, and `.env` files.

Local private evidence should live under `internal/` or another private storage
location. Run `scripts/privacy_preflight.py` before publishing.

## Repository Map

```text
services/operator-console/  Phase 1 local CLI and web demonstrator
services/                   Experimental and advanced service components
tests/                      Unit, integration, and smoke tests
docs/                       Documentation hub and setup guides
scripts/                    Validation, setup, and maintenance helpers
demos/                      Public-safe demo scripts and checklists
evidence/                   Public-safe placeholders only
```

See `docs/architecture/services.md` for the supported, experimental, advanced,
and legacy service labels used in the public source set.

## Contributing

See `CONTRIBUTING.md` for branch naming, local validation, and PR expectations.
See `SECURITY.md` for vulnerability reporting.

## License

MIT License.
