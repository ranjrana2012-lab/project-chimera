# Overclaim Scan Report

Status: DRAFT AUDIT REPORT - HUMAN ACTION REQUIRED.
Last refreshed: 2026-05-09.

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

The 2026-05-09 broad scan still reports review findings concentrated in:

- legacy and Phase 2 BSL/avatar service files;
- monitoring dashboards, alert rules, and tracing examples;
- integration examples and tests;
- educational-platform implementation notes;
- shared service templates;
- planning documents that quote risky terms as search patterns or replacement
  instructions.

Close-out docs contain guarded "do not claim" language by design. The Phase 1
public claim remains limited to the operator-console demonstrator unless those
broader surfaces are separately evidenced.

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

## Files Requiring Human Review

- Final report draft.
- Scope-pivot email templates.
- Spending summary templates.
- Legacy/Phase 2 service folders if reviewers will inspect the full repository
  rather than the Phase 1 operator-console path.
- BSL/avatar service, monitoring, integration, and test surfaces that still
  appear in the broad scanner as review findings.
- Superpowers plan/spec files if they are published publicly; scanner hits there
  are planning/search-term context, not delivery claims.
- Any private grant report or submission PDF created outside git.
