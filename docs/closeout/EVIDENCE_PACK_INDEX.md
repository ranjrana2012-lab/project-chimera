# Evidence Pack Index

This index separates public repository evidence from private evidence that the
owner must supply outside git.

## Public Repository Evidence

These files are public-safe and can be referenced directly:

- `README.md` - Phase 1 scope and repository orientation.
- `QUICKSTART.md` - local reviewer route.
- `docs/demo/README.md` - demo guide and evidence boundary.
- `docs/closeout/CASE_STUDY_PHASE1.md` - narrowed case study.
- `docs/closeout/REPLICATION_TOOLKIT.md` - commands for local replication.
- `docs/closeout/CLAIMS_REGISTER.md` - claim status and guardrails.
- `evidence/README.md` - placeholder policy for public-safe evidence folders.
- `scripts/privacy_preflight.py` - public/private boundary check.
- `test_chimera_smoke.py` - direct smoke check for the Phase 1 route.

## Private Evidence Needed

Do not commit these files to public git. Store them in private project storage:

- final demo recording or screen capture, if submitted;
- screenshots showing the CLI demo, web route, and smoke/privacy checks;
- terminal logs for `chimera_core.py demo`, `test_chimera_smoke.py`, and
  `scripts/privacy_preflight.py`;
- receipts, invoices, bank statements, and payment confirmations;
- spending summary mapped to eligible grant cost categories;
- private grant correspondence and submission records;
- meeting notes, supervision notes, or reviewer notes;
- any participant, student, collaborator, or audience records;
- any final report PDF or funder portal export containing private information.

## Evidence Not Present In Public Git

The public repository does not contain, and should not be used as proof of:

- a completed public performance;
- livestream delivery;
- formal accessibility testing;
- BSL/avatar delivery;
- public audience attendance or impact metrics;
- testimonials;
- a complete financial evidence pack.

## Suggested Private Folder Structure

```text
private-closeout-evidence/
  demo-recording/
  screenshots/
  command-logs/
  spend-evidence/
  grant-correspondence/
  final-submission/
```

Run `scripts/privacy_preflight.py` before publishing or pushing any public
source changes.
