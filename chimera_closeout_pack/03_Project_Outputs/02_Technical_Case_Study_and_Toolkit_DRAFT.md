# Project Chimera: Phase 1 Local-First Adaptive AI Demonstrator

Status: DRAFT - HUMAN ACTION REQUIRED.

## 1. Context

Project Chimera is an R&D project exploring adaptive AI for theatre and live
creative contexts. This Phase 1 close-out frames the current repository as a
local adaptive AI framework and controlled demonstrator. Public performance,
livestream, formal accessibility testing, and full production deployment remain
future-stage work unless separate evidence is supplied.

## 2. Technical Architecture

The Phase 1 demonstrator follows this local flow:

1. Text input from a reviewer, operator, or scripted demo.
2. Sentiment analysis through the available local model path or heuristic
   fallback.
3. Adaptive state routing, such as `momentum_build`, `supportive_care`, or
   `standard_response`.
4. Response generation through the local generator path or a deterministic
   fallback response.
5. Optional local logs generated from actual runs.
6. Future integration path for audience input, livestream workflow, formal
   accessibility testing, and performance deployment.

## 3. Demo Workflow

From the repository root:

```bash
python3 services/operator-console/chimera_core.py demo
python3 scripts/run_phase1_demo.py
python3 test_chimera_smoke.py
python3 scripts/privacy_preflight.py
```

Suggested demo inputs:

- `I am sad`
- `I feel excited and ready`
- `I am confused and overwhelmed`
- `This is intense but inspiring`

Expected strategy labels for the current close-out demo path are
`supportive_care`, `momentum_build`, `grounding_support`, and
`reflective_transition`. Do not invent confidence claims.

Generated run logs are written under `outputs/run_logs/` and are ignored by git.
They may be copied into the private evidence pack after human review.

## 4. Reproduction Toolkit

Prerequisites:

- Python 3.12 preferred.
- Local checkout of the repository.
- Dependencies installed for `services/operator-console`.
- No private API key required for the default Student / Laptop route.

Setup:

```bash
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
```

Troubleshooting:

- Use `QUICKSTART.md` for the default route.
- Use `docs/closeout/REPLICATION_TOOLKIT.md` for close-out replication.
- If `python` is unavailable, use `python3`.
- If dependencies are missing, install them in the service virtual environment.
- If advanced DGX/Kimi routes are not available, do not claim them.

## 5. Limitations

This Phase 1 case study does not evidence:

- a public show;
- a livestream;
- validation with 40 students;
- formal accessibility testing;
- BSL/avatar delivery;
- final production deployment;
- financial spend or payment.

## 6. Future Phase 2 Path

Future development may include live audience input, livestream workflow,
accessibility testing, student workshops, and performance deployment. Those
items should be planned, evidenced, and approved separately.
