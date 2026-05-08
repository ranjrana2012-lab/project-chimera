# Project Chimera Phase 1 Submission Readiness

This page supports a narrowed CreaTech Frontiers Foundations close-out claim:
Project Chimera Phase 1 produced a local adaptive AI demonstrator with CLI/web
routes, public-safe documentation, an open-source release, and a public/private
evidence boundary.

Do not use this page to claim a completed public show, livestream, full student
programme, formal accessibility testing, BSL/avatar delivery, testimonials,
audience impact, or a complete evidence pack unless those items are supplied
separately in private evidence.

## Technical Readiness

Status: repo-supported.

The repository contains a local operator-console demonstrator that can be run
from `services/operator-console/chimera_core.py` and a lightweight web route in
`services/operator-console/chimera_web.py`.

Reviewer commands:

```bash
cd services/operator-console
./venv/bin/python chimera_core.py demo
PORT=18080 ./venv/bin/python chimera_web.py
```

Repository smoke checks:

```bash
./services/operator-console/venv/bin/python test_chimera_smoke.py
python3 scripts/privacy_preflight.py
```

Technical readiness does not imply production deployment, live audience use, or
network-hardened operation.

## Documentation Readiness

Status: repo-supported.

Public reviewer entry points:

- `README.md`
- `QUICKSTART.md`
- `docs/demo/README.md`
- `docs/closeout/REPLICATION_TOOLKIT.md`
- `docs/closeout/CASE_STUDY_PHASE1.md`
- `docs/closeout/CLAIMS_REGISTER.md`

Maintainer validation history is under `docs/reports/`. Treat those reports as
engineering history, not as a substitute for the final private grant evidence
pack.

## Evidence Readiness

Status: partially repo-supported; owner input required.

The public repository can evidence source code, setup guidance, tests, privacy
preflight, and public-safe placeholders. It must not contain real receipts,
invoices, bank statements, participant data, private grant records, generated
screenshots, recordings, logs, tokens, or `.env` files.

Private evidence still needed from the owner is listed in
`docs/closeout/EVIDENCE_PACK_INDEX.md`.

## Spending Summary Readiness

Status: owner input required.

The repository must not store spending evidence. The owner should assemble a
private spending summary with receipts, invoices, payment records, and any
eligible cost notes required by the funder. Public git should only reference
that private pack at a high level.

## Final Payment Readiness

Status: owner input required.

Before requesting final payment, the owner should confirm:

- the private evidence pack is complete;
- spending evidence matches the funder claim;
- any final report narrative stays within the evidenced Phase 1 scope;
- private files have not been added to public git;
- `scripts/privacy_preflight.py` passes from the public checkout.

The repository is suitable as supporting technical evidence only after those
private, non-repo items are assembled separately.
