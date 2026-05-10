# Overclaim Scan Report

Status: DRAFT AUDIT REPORT - HUMAN ACTION REQUIRED.
Last refreshed: 2026-05-10.

## Terms Searched

- public show delivered
- livestream delivered
- 40 students
- two DGX
- audience-driven live
- production-ready
- fully deployed
- completed performance
- validated accessibility
- BSL avatar
- venue
- rehearsal

## Files Containing Risk Language

The repository contains guarded close-out wording that names risky claims so
they can be avoided. Guarded wording is acceptable when it clearly says not to
claim an item without evidence.

The 2026-05-10 broad scan with `--fail-on-review` exits successfully. It still
reports guarded close-out wording and explicitly classified Phase 2 /
experimental surfaces, but no unresolved `review` findings remain.

Remaining classified surfaces include:

- legacy and Phase 2 BSL/avatar service files;
- monitoring dashboards, alert rules, and tracing examples;
- integration examples and tests;
- educational-platform implementation notes;
- broad deployment helper scripts;
- public close-out checklists that deliberately name claims to avoid.

Close-out docs contain guarded "do not claim" language by design. The Phase 1
public claim remains limited to the operator-console demonstrator unless those
broader surfaces are separately evidenced.

`docs/superpowers/` is intentionally excluded from the overclaim scanner because
those files are agent workflow specifications and plans that quote risky terms
as search patterns and replacement instructions, not delivery claims.

## Edits Made

- Added `scripts/scan_for_overclaims.py`.
- Added close-out templates that distinguish drafts and templates from evidence.
- Added release and demo-video checklists with claim guardrails.
- Reduced unguarded high-risk wording in generated close-out templates.
- Softened local ignored evidence-pack wording in `evidence/PHASE_1_DELIVERED.md`
  and `evidence/evidence_pack/limitations.md`; these files are ignored by git
  and must not be force-added without human review.
- Confirmed the tracked public evidence placeholder remains
  `evidence/README.md`.
- Rewrote `CONTRIBUTORS.md` as a Phase 1 contributor record rather than a
  completed community/student programme claim.
- Added Phase 1 boundary notes to the BSL/avatar and educational-platform
  documentation.
- Replaced the shared service template's generic maturity wording with
  experimental service-template wording.
- Classified known Phase 2 scripts and test fixtures in
  `scripts/scan_for_overclaims.py` so the scanner distinguishes future-stage
  surfaces from current Phase 1 claims.

## Files Requiring Human Review

- Final report draft.
- Scope-pivot email templates.
- Spending summary templates.
- Legacy/Phase 2 service folders if reviewers will inspect the full repository
  rather than the Phase 1 operator-console path.
- BSL/avatar service, monitoring, integration, and test surfaces that still
  appear in the broad scanner as `experimental_or_phase2` findings.
- Any private grant report or submission PDF created outside git.
