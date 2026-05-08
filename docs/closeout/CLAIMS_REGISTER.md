# Claims Register

Labels:

- `EVIDENCED` - supported by public repository files or repeatable local checks.
- `NEEDS INPUT` - plausible but requires private owner evidence outside git.
- `UNVERIFIED` - not confirmed by the reviewed public files or current local
  repo work.
- `DO NOT CLAIM YET` - should not appear in final close-out wording unless new
  direct evidence is supplied and reviewed.

| Claim | Status | Evidence / action |
| --- | --- | --- |
| Project Chimera Phase 1 has a local adaptive AI CLI demonstrator. | EVIDENCED | `services/operator-console/chimera_core.py`, `QUICKSTART.md`, `test_chimera_smoke.py`. |
| The demo routes positive, negative, and neutral inputs to different strategies. | EVIDENCED | `services/operator-console/chimera_core.py`, `docs/demo/demo-script.md`, smoke test expectations. |
| The close-out demo includes focused grounding and reflective transition routes for selected scripted inputs. | EVIDENCED | `services/operator-console/chimera_core.py`, `tests/unit/test_chimera_core.py`, `scripts/run_phase1_demo.py`. |
| The repository includes a lightweight local web route for reviewer checks. | EVIDENCED | `services/operator-console/chimera_web.py`, `docs/closeout/REPLICATION_TOOLKIT.md`. |
| The repository has public/private evidence boundary guidance. | EVIDENCED | `README.md`, `evidence/README.md`, `scripts/privacy_preflight.py`. |
| The public repository is open-source under MIT. | EVIDENCED | `LICENSE`, `README.md`. |
| A final demo recording exists and is ready for submission. | NEEDS INPUT | Owner must provide the private recording or export record. |
| Screenshots/logs from the final close-out run exist. | NEEDS INPUT | Owner must provide private screenshots/logs and keep them out of public git. |
| Spending is fully reconciled to receipts and invoices. | NEEDS INPUT | Owner must provide private financial evidence. |
| Final payment can be requested. | NEEDS INPUT | Requires private evidence pack, spending summary, and final report checks. |
| Raw demo captures are complete. | UNVERIFIED | Public git must not contain raw captures; owner must confirm privately. |
| DGX/Kimi/advanced Compose routes are part of the Phase 1 funder claim. | UNVERIFIED | Treat as maintainer history unless fresh close-out evidence is supplied. |
| Formal accessibility testing was completed. | DO NOT CLAIM YET | No formal accessibility test evidence reviewed in public repo. |
| BSL/avatar delivery was completed. | DO NOT CLAIM YET | Phase 1 docs explicitly keep this out of scope. |
| A public show, public audience workflow, or livestream was completed. | DO NOT CLAIM YET | No direct evidence reviewed in public repo. |
| Testimonials or measured audience impact are available. | DO NOT CLAIM YET | No testimonials or impact metrics reviewed in public repo. |
| A full student programme was completed. | DO NOT CLAIM YET | No complete programme evidence reviewed in public repo. |
| The public repo itself is a complete grant evidence pack. | DO NOT CLAIM YET | The repo is supporting technical evidence only; private evidence remains required. |
