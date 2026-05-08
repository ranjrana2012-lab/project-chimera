# Project Chimera Final Report Draft

Status: DRAFT - HUMAN ACTION REQUIRED.

This document is prepared for human review. It is not legal, accounting, or
grant-management advice. Do not submit it until all claims, dates, amounts,
names, evidence references, and approvals have been checked by Secure-Wireless
Ltd and the relevant BCU/AHRC contacts.

## 1. Executive Summary

Project Chimera is presented for Phase 1 close-out as a local-first adaptive AI
demonstrator. During this grant period, the work focused on a controlled
technical build that demonstrates a core adaptive pipeline, supporting
documentation, and reusable code assets.

Public-facing performance elements are not claimed as completed outputs in this
draft unless separate private evidence is supplied and reviewed. Public
performance, livestream delivery, live audience adaptation, formal
accessibility validation, and complete student-programme delivery remain future
development paths unless direct evidence is added by the project owner.

## 2. Strategic Context

The project began with a live-performance ambition. The close-out position is a
Phase 1 R&D pivot: within the remaining delivery window, the project prioritised
demonstrable technical proof and reproducible documentation over a full public
performance workflow.

This reframing is intended to be transparent about delivery constraints while
preserving the value of the technical work completed. It should be communicated
to BCU and partners for review. Any material change requiring written agreement
under GOL Clause 5.1 is a human compliance action and is not evidenced by this
draft.

## 3. Deliverables Matrix

| Requirement / Deliverable | Contractual Source | Current Status | Evidence Location | Close-Out Treatment | Human Action Required |
| --- | --- | --- | --- | --- | --- |
| Dynamic Performance Hub | GOL Schedule 3 | In progress | Repository and demo docs | Reframed as local-first adaptive AI framework | Confirm BCU acceptance of Phase 1 framing |
| Adaptive AI Routing | GOL Schedule 3 | Partially evidenced by repository; final demo evidence required | `services/operator-console/chimera_core.py`, `test_chimera_smoke.py`, private run log to be added | Prove via controlled demo | Record demo video and attach run log |
| 1-Hour Public Show | GOL Schedule 3 | Not achieved unless external evidence exists | None in public repo | Postponed / Phase 2 | Do not claim unless direct evidence is supplied |
| Public Livestream | GOL Schedule 3 | Not achieved unless external evidence exists | None in public repo | Exclude from claims | Do not claim unless direct evidence is supplied |
| Open-Source Code | GOL Schedule 3 | In progress / local release support | Public repository, `LICENSE`, `README.md` | Prepare Phase 1 public release | Human confirms licence and pushes release/tag |
| Case Study | GOL Schedule 3 | Draft created | `chimera_closeout_pack/03_Project_Outputs/02_Technical_Case_Study_and_Toolkit_DRAFT.md` | Submit as Phase 1 technical case study after review | Human review and export if required |
| Replication Toolkit | GOL Schedule 3 | Draft created | `docs/closeout/REPLICATION_TOOLKIT.md`, `QUICKSTART.md` | Submit as setup and reproduction guide | Human verifies commands on final machine |
| Student Workshops | GOL Schedule 3 | Only claim if evidenced | Evidence required outside git | Claim early scoping only if supported | Provide attendance, notes, or remove claim |

## 4. Technical Work Completed

The repository contains a Phase 1 operator-console demonstrator with:

- sentiment analysis or heuristic fallback in `services/operator-console/chimera_core.py`;
- adaptive strategy routing for local text inputs;
- CLI demo, comparison, caption-style output, and export paths;
- a lightweight local web route in `services/operator-console/chimera_web.py`;
- setup, replication, demo, and close-out documentation;
- privacy and public-repository contract checks.

HUMAN ACTION REQUIRED: attach the final private run log, screenshot set, and demo
recording after they have been generated from actual commands.

## 5. Evidence Pack

Draft and repository artefacts:

- `README.md`
- `QUICKSTART.md`
- `docs/closeout/`
- `docs/demo/`
- `chimera_closeout_pack/`
- `scripts/run_phase1_demo.py`
- `scripts/privacy_preflight.py`
- `test_chimera_smoke.py`

Verified evidence must be supplied separately:

- narrated demo video;
- final run logs from actual execution;
- screenshots of CLI/web route;
- financial evidence;
- scope/pivot communication thread;
- signed MFA declaration if required.

## 6. Budget Reallocation Narrative

Draft wording for human review:

"Due to the strategic pivot to a Phase 1 technical demonstrator, unspent
delivery lines originally associated with live activity, student bursary, or
creative activity may need to be reallocated to Category 1: paid development
time, subject to BCU approval and supported by actual invoices, timesheets, and
bank evidence. This draft does not assert that reallocation has been approved."

## 7. Financial Evidence Requirements

HUMAN ACTION REQUIRED:

- itemised invoices addressed to Secure-Wireless Ltd;
- VAT breakdown where applicable;
- redacted bank statements showing date, payee, and amount;
- evidence reference index mapping every spend line to proof;
- signed MFA declaration under GOL Schedule 7 if required;
- no unsupported claims about spend or payment.

## 8. Risk Register

| Risk | Status | Mitigation |
| --- | --- | --- |
| Missing scope approval | RED | Send scope pivot email and retain response |
| Missing demo video | RED | Record 3-5 minute narrated controlled demo |
| Missing run logs | AMBER | Generate logs from actual local commands |
| Missing invoices | RED | Add real invoices privately |
| Missing bank evidence | RED | Add redacted statements privately |
| Unsupported public-delivery claims | AMBER | Use claims register and QA checklist |
| Budget variance approval missing | RED | Ask BCU whether written approval is required |
| Missing MFA declaration | RED | Complete and sign human-approved declaration |

## 9. Submission Gates

- [ ] Scope Gate: written notification or approval regarding Phase 1 pivot.
- [ ] Demo Gate: private video and run log proving the local adaptive pipeline.
- [ ] Repo Gate: cleaned repository, licence, README, no secrets.
- [ ] Spend Gate: invoices and redacted bank statements match claimed spend.
- [ ] Narrative Gate: final report and MFA declaration avoid overclaims.

## 10. Final Human Review Checklist

- [ ] All claims evidenced.
- [ ] All amounts checked.
- [ ] All dates checked.
- [ ] All names checked.
- [ ] Sensitive data redacted.
- [ ] All required files present.
- [ ] BCU approval confirmed where required.

Do not sign, certify, or submit this draft without human review.
