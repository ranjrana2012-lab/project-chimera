# Phase 1 Demo Guide

This demo guide is public-safe and scoped to the current Phase 1 claim: a local
adaptive AI foundation with an operator-console CLI and lightweight web route.

It does not claim a finished theatre production, live audience workflow,
captioning platform, BSL/avatar system, or full multi-service deployment.

## What To Show

- Sentiment routing for positive, negative, and neutral audience-style text.
- Adaptive response strategies: `momentum_build`, `supportive_care`, and
  `standard_response`, plus `grounding_support` and `reflective_transition` for
  selected close-out demo inputs.
- Baseline-versus-adaptive comparison output.
- Caption-style output and SRT export.
- Operator-console web state, process, and CSV export endpoints.

## Local Setup

Use the Student / Laptop route unless the host has verified DGX Spark / GB10
hardware and Docker GPU access.

```bash
cd services/operator-console
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python chimera_core.py demo
PORT=18080 ./venv/bin/python chimera_web.py
```

Open `http://127.0.0.1:18080` for the local web console.

## Demo Checklist

- [ ] Run `./venv/bin/python chimera_core.py demo`.
- [ ] Run one positive, one negative, and one neutral input.
- [ ] Run comparison mode.
- [ ] Run caption/SRT export.
- [ ] Start the web route on `PORT=18080`.
- [ ] Check `/api/state`, `/api/process`, and `/api/export` through the web UI
      or browser/dev tools.

## Evidence Boundary

Generated screenshots, recordings, logs, receipts, invoices, participant data,
private grant records, and `.env` files stay outside public git. Store evidence
under private local storage and run `scripts/privacy_preflight.py` before
publishing.

## Related Docs

- Demo script: `demo-script.md`
- Student setup: `../guides/STUDENT_LAPTOP_SETUP.md`
- Evidence placeholders: `../../evidence/README.md`

---

**Demo Version:** 1.0 Phase 1 close-out route
**Last Updated:** 2026-05-08
**Next Review:** After private evidence pack assembly
