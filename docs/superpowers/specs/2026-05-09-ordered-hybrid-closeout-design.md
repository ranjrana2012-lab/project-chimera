# Project Chimera Ordered Hybrid Close-Out Design

Date: 2026-05-09
Status: approved design for implementation planning
Scope: repository-side work only

## 1. Purpose

This design defines the next autonomous work run for Project Chimera. The goal
is to make the repository stronger for a narrowed Phase 1 close-out while
avoiding unsupported claims.

The working narrative remains:

> Project Chimera is a Phase 1 local-first adaptive AI demonstrator. It supports
> a controlled technical demo and reusable documentation. Public performance,
> livestream, formal student programme, completed accessibility validation, and
> final grant evidence are not claimed unless independently evidenced.

## 2. Priority Order

The approved route is an ordered hybrid:

1. Grant close-out readiness first.
2. Public GitHub readiness second.
3. Technical demo hardening third.
4. Broader repository surgery only where it reduces review risk.

This order prevents useful engineering work from weakening the grant narrative
or public/private evidence boundary.

## 3. Non-Goals

This run must not:

- invent invoices, bank transactions, approvals, stakeholder responses, student
  participation, accessibility test outcomes, public delivery, or impact data;
- commit receipts, bank statements, participant data, tokens, `.env` files, or
  private grant records;
- claim a completed public show, livestream, production deployment, BSL/avatar
  delivery, or completed evidence pack;
- merge blocked dependency PRs without targeted compatibility work;
- perform large architecture rewrites unless a narrow change clearly reduces
  close-out review risk.

## 4. Workstream A: Grant Close-Out Readiness

Review the existing close-out material and tighten it where needed:

- `docs/closeout/SUBMISSION_READINESS.md`
- `docs/closeout/CASE_STUDY_PHASE1.md`
- `docs/closeout/REPLICATION_TOOLKIT.md`
- `docs/closeout/EVIDENCE_PACK_INDEX.md`
- `docs/closeout/CLAIMS_REGISTER.md`
- `docs/closeout/POINT_IN_TIME_STATUS_2026-05-08.md`
- `chimera_closeout_pack/**`
- `CODEX_COMPLETION_REPORT.md`

Expected improvements:

- make missing human evidence explicit;
- keep all grant-facing claims inside the evidenced Phase 1 demonstrator scope;
- distinguish drafts/templates from verified evidence;
- preserve British English;
- make the final payment blockers clear enough for a human owner to act on.

Success criteria:

- no close-out doc implies completed public delivery without evidence;
- all financial material remains template-only unless real private evidence is
  intentionally supplied by the owner outside public git;
- blockers are listed in practical, human-action terms.

## 5. Workstream B: Public GitHub Readiness

Review the main public-facing files:

- `README.md`
- `QUICKSTART.md`
- `CHANGELOG.md`
- `docs/README.md`
- `docs/demo/**`
- `docs/reports/**` if present
- `evidence/README.md`
- `services/operator-console/DEMO_VIDEO_PRODUCTION_NOTES.md`

Expected improvements:

- reduce stale, production-looking, or overbroad wording;
- link users towards the Phase 1 operator-console path;
- mark advanced, legacy, or Phase 2 surfaces cautiously where needed;
- avoid presenting the whole repository as a complete production platform.

Success criteria:

- a reviewer can understand the current public baseline quickly;
- README and quick-start instructions match the tested local route;
- public/private boundary remains intact.

## 6. Workstream C: Technical Demo Hardening

Re-run and refine only the supported Phase 1 path:

- `services/operator-console/chimera_core.py`
- `services/operator-console/chimera_web.py`
- `scripts/run_phase1_demo.py`
- `scripts/check_environment.py`
- `scripts/privacy_preflight.py`
- `test_chimera_smoke.py`
- focused unit tests around the operator console and public repo contract.

Expected improvements:

- clearer demo instructions and failure notes;
- reproducible run-log guidance;
- no cloud/API-key dependency for the Phase 1 claim;
- updated validation notes based only on commands actually run.

Success criteria:

- local CLI demo can run or, if blocked, the blocker is recorded truthfully;
- smoke tests and focused tests pass where available;
- generated logs remain ignored by git and suitable for private evidence review.

## 7. Workstream D: Broader Repo Surgery With Restraint

Broader edits are allowed only when they directly reduce risk. Examples:

- remove or rewrite unsupported public-facing claims;
- add labels or notes for legacy/Phase 2 surfaces;
- fix broken public links;
- improve `.gitignore` or privacy scan behaviour;
- quarantine generated artefacts from public commits.

Avoid:

- renaming major service directories;
- moving large trees;
- deleting potentially useful history or private evidence paths;
- broad refactors not required for the close-out.

## 8. Validation Plan

Run the practical checks available in the local environment:

```bash
python3 scripts/privacy_preflight.py
python3 test_chimera_smoke.py
python3 scripts/check_markdown_links.py
python3 scripts/run_phase1_demo.py
python3 -m pytest -p no:cacheprovider tests/unit/test_chimera_core.py tests/unit/test_chimera_web_contract.py tests/unit/test_public_repo_cleanup_contract.py tests/unit/test_privacy_preflight.py -q
git diff --check
```

Also check GPU/process state before heavy demo work. A `VLLM::EngineCore`
process was observed using a large amount of GB10 memory on 2026-05-09, and the
advanced `chimera-kimi-vllm` container was stopped because it is not required
for the Phase 1 close-out route. Keep Kimi/vLLM off by default and restart it
only for explicit DGX/Kimi validation.

## 9. Expected Outputs

The implementation run should produce:

- updated close-out documentation if gaps are found;
- updated public-facing documentation if wording or navigation needs tightening;
- fresh validation results with exact commands and outcomes;
- a clear list of remaining human/admin blockers;
- local commits for completed repository work.

Remote pushing remains a separate explicit decision.

## 10. Risks And Controls

| Risk | Control |
| --- | --- |
| Overclaiming grant delivery | Use the claims register and close-out wording guardrails. |
| Accidentally committing private evidence | Run privacy preflight and inspect git status before commits. |
| Wasting time on broad rewrites | Apply the ordered priority and only edit broad surfaces when review risk is reduced. |
| Treating generated templates as evidence | Label templates and drafts clearly as human-action material. |
| Demo blocked by local GPU/VLLM load | Keep Kimi/vLLM off by default; restart only for explicit DGX/Kimi validation. |

## 11. Approval State

The user approved the ordered hybrid approach on 2026-05-09. This document is
the written design checkpoint required before implementation planning.
