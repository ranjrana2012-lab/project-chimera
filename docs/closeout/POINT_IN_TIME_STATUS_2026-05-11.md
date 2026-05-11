# Project Chimera Point-In-Time Close-Out Map - 2026-05-11

Status: CURRENT CLOSE-OUT ACTION MAP - HUMAN REVIEW REQUIRED.

This document captures the current state of Project Chimera on 11 May 2026 and
sets out what has been completed, what remains outstanding, and what the owner
needs to do next. It is written for practical planning. It is not legal,
accounting, or grant-management advice, and it is not a substitute for actual
BCU/AHRC correspondence, invoices, bank evidence, or signed declarations.

## 1. Executive Summary

Project Chimera is now positioned most safely as a Phase 1 local-first adaptive
AI demonstrator. The repository supports a narrow, evidence-safe claim: a local
operator-console demo can process audience-style text, classify or route tone,
select adaptive response states, expose CLI/web demo paths, and provide
reusable technical documentation plus a close-out pack structure.

The repository is substantially cleaner for public review than it was at the
start of the close-out sprint. The remaining blockers are mostly outside git:
scope correspondence, financial evidence, final video evidence, signed forms,
and human review.

Overall readiness on 11 May 2026:

| Area | Status | Meaning |
| --- | --- | --- |
| Phase 1 technical repo | GREEN | Local demonstrator path, tests, and docs exist. |
| Public/private boundary | GREEN | Privacy, secret, and overclaim checks have current passing runs. |
| Close-out documentation templates | AMBER | Drafts/templates exist, but need human completion and review. |
| Final evidence pack | RED | Private proof files are still required and must not be committed. |
| Financial evidence | RED | Actual invoices, bank evidence, MFA, and reallocation approval are still human actions. |
| Final grant submission | RED | Not ready until human evidence and approval gates are complete. |

## 2. Safe Current Narrative

Use this narrative unless new evidence changes it:

> Project Chimera closed this grant period as a Phase 1 local-first adaptive AI
> demonstrator. The work focused on a controlled technical build that
> demonstrates a core adaptive pipeline, supporting documentation, and reusable
> code assets. Within the remaining delivery window, the project prioritised
> demonstrable technical proof and reproducible documentation over a full public
> performance workflow. Public-facing performance outputs remain a later-stage
> development path rather than a completed claim within this submission.

Do not expand this narrative unless the evidence exists in private files and has
been reviewed.

## 3. Current Git And GitHub Position

At the start of the 11 May 2026 push preparation:

- Local branch: `main`.
- Remote: `origin` at `https://github.com/ranjrana2012-lab/project-chimera.git`.
- Local branch had a stack of public-safe close-out commits ahead of
  `origin/main`.
- No private grant evidence, generated run logs, receipts, invoices, bank
  statements, or `.env` files were staged.
- Ignored evidence and run-log folders remain local-only unless a human
  deliberately copies reviewed material into a private evidence pack.

Recent local public-safe work included:

- Phase 1 close-out pack and templates.
- README/docs simplification and safer Phase 1 wording.
- Operator-console route hardening and demo-state tests.
- Privacy preflight improvements.
- Secret and overclaim scanner improvements.
- Public local-path cleanup.
- BSL/avatar and educational-platform boundary wording.
- Current point-in-time status snapshots.

## 4. What Is Completed Inside The Repository

### 4.1 Phase 1 Demonstrator

Completed:

- `services/operator-console/chimera_core.py` is the canonical Phase 1 CLI demo
  path.
- `services/operator-console/chimera_web.py` is the local web/API demo route.
- `scripts/run_phase1_demo.py` runs a repeatable demonstration and writes a real
  JSON log under ignored `outputs/run_logs/`.
- `test_chimera_smoke.py` exercises the core CLI-style behaviours.
- Unit tests cover the Phase 1 routing and public cleanup contracts.

Current evidenced adaptive states:

- `supportive_care`
- `momentum_build`
- `grounding_support`
- `reflective_transition`
- `standard_response`

What this proves:

- The repository can support a controlled local technical demonstration.
- The local demo route can be used as technical evidence once a human records
  the video and stores the resulting artefacts privately.

What this does not prove:

- It does not prove a completed public show.
- It does not prove a livestream.
- It does not prove a production deployment.
- It does not prove formal accessibility validation.
- It does not prove financial spend.

### 4.2 Close-Out Documentation

Completed repository files:

- `docs/closeout/SUBMISSION_READINESS.md`
- `docs/closeout/CASE_STUDY_PHASE1.md`
- `docs/closeout/REPLICATION_TOOLKIT.md`
- `docs/closeout/EVIDENCE_PACK_INDEX.md`
- `docs/closeout/CLAIMS_REGISTER.md`
- `docs/closeout/POINT_IN_TIME_STATUS_2026-05-08.md`
- `docs/closeout/POINT_IN_TIME_STATUS_2026-05-10.md`
- `docs/closeout/POINT_IN_TIME_STATUS_2026-05-11.md`
- `chimera_closeout_pack/`
- `CODEX_COMPLETION_REPORT.md`

Purpose:

- Give reviewers a clear Phase 1 technical story.
- Separate evidenced repo claims from private owner-supplied evidence.
- Provide templates for spending summary, evidence index, MFA declaration, and
  stakeholder communications.

Important limitation:

- Generated templates are not evidence. They become useful only after the owner
  fills them with verified facts and attaches private proof.

### 4.3 Public/Private Boundary

Completed:

- `.gitignore` excludes generated logs and private/local artefacts.
- `scripts/privacy_preflight.py` blocks known private evidence and grant paths.
- `scripts/scan_for_secrets.py` checks public text for secret-like values
  without printing values.
- `scripts/scan_for_overclaims.py` checks public wording for risky close-out
  claims and classifies guarded or Phase 2 language.
- Public machine-specific paths have been removed from tracked public files.

Current boundary rule:

- Keep real receipts, invoices, bank statements, participant data, `.env` files,
  tokens, screenshots with private data, and grant correspondence out of public
  git.

### 4.4 Documentation And Claim Hygiene

Completed:

- `CONTRIBUTORS.md` no longer claims a completed student cohort.
- BSL/avatar docs now identify those surfaces as future-stage research, not
  evidenced Phase 1 delivery.
- Educational-platform docs now identify that service as experimental /
  historical, not a current Phase 1 close-out claim.
- Generic maturity wording in the shared service template has been softened.
- The close-out pack now repeatedly separates draft/template files from actual
  evidence.

## 5. Validation Commands Run Recently

Latest known local validation before this status file:

| Command | Result |
| --- | --- |
| `python3 scripts/scan_for_secrets.py --include-untracked --fail-on-findings` | Passed: no secret-like findings found |
| `python3 scripts/privacy_preflight.py` | Passed |
| `python3 scripts/scan_for_overclaims.py --include-untracked --fail-on-review` | Passed: guarded and `experimental_or_phase2` findings remain, no unresolved `review` findings |
| `python3 -m pytest -p no:cacheprovider tests/unit/test_chimera_core.py tests/unit/test_chimera_web_contract.py tests/unit/test_public_repo_cleanup_contract.py tests/unit/test_privacy_preflight.py -q` | 45 passed |
| `python3 test_chimera_smoke.py` | 6 passed, 0 failed |
| `python3 -m pytest -p no:cacheprovider platform/cicd-gateway/tests/test_webhook.py tests/test_alertmanager_config.py services/scenespeak-agent/tests/test_metrics.py services/scenespeak-agent/tests/test_tracing.py -q` | 60 passed; emitted an OpenTelemetry exporter shutdown warning after completion |
| `python3 scripts/check_markdown_links.py` | No broken markdown links |
| `git diff --check` | Passed |

Before any final submission or new public push, rerun at minimum:

```bash
python3 scripts/privacy_preflight.py
python3 scripts/scan_for_secrets.py --include-untracked --fail-on-findings
python3 scripts/scan_for_overclaims.py --include-untracked --fail-on-review
python3 test_chimera_smoke.py
python3 scripts/check_markdown_links.py
git diff --check
```

## 6. What Is Still Outstanding

### 6.1 Critical Human Actions

These are required for close-out but cannot be completed honestly inside the
repository without the real underlying evidence.

| Priority | Item | Owner Action | Evidence To Store Privately | Status |
| --- | --- | --- | --- | --- |
| Critical | Scope pivot notification | Send scope pivot / close-out framing email to Sisi Yuen, James Green, and Laura. | Sent email PDF/export and replies. | HUMAN ACTION REQUIRED |
| Critical | Written response | Obtain BCU/partner response before claiming agreement or approval. | Email thread or written approval. | HUMAN ACTION REQUIRED |
| Critical | Demo video | Record 3-5 minute narrated screen recording of the local Phase 1 demo. | MP4/WebM, screenshots, command transcript, run log. | HUMAN ACTION REQUIRED |
| Critical | Demo evidence index | Copy reviewed run logs/screenshots/video into private evidence pack. | Private evidence folder or secure drive. | HUMAN ACTION REQUIRED |
| Critical | Financial evidence | Gather actual invoices addressed to Secure-Wireless Ltd. | Invoice PDFs/images. | HUMAN ACTION REQUIRED |
| Critical | Payment proof | Gather redacted bank statements showing date, payee, and amount. | Redacted bank PDFs. | HUMAN ACTION REQUIRED |
| Critical | MFA declaration | Complete and sign the Minimal Financial Assistance declaration using approved wording/form. | Signed declaration. | HUMAN ACTION REQUIRED |
| Critical | Budget reallocation | Ask BCU whether reallocation into paid development time needs written approval. | Written confirmation. | HUMAN ACTION REQUIRED |
| Critical | Final human review | Check all dates, names, amounts, claims, and attachments. | Reviewed final pack. | HUMAN ACTION REQUIRED |
| Critical | Submission | Submit only after evidence and approval gates pass. | Submission receipt / confirmation. | HUMAN ACTION REQUIRED |

### 6.2 Financial Evidence Still Needed

Prepare private evidence for each spend line. Do not commit these files.

| Spend Area | Planned Amount | Current Close-Out Treatment | Required Evidence |
| --- | --- | --- | --- |
| Equipment: DGX Spark | GBP 4,000 | Claim only if invoice and payment proof exist. | Supplier invoice to Secure-Wireless Ltd, payment evidence, delivery/order proof if available. |
| AI Development | GBP 2,000 | Claim actual paid labour only if evidenced. | Contractor invoice, timesheet, payment proof, description of work. |
| Student Bursaries | GBP 1,200 | Do not claim as spent unless paid and evidenced. | Student agreement, payment proof, consent/participation evidence if relevant. |
| Creative/Rehearsal | GBP 1,500 | Do not claim as delivered unless evidenced; may need reallocation approval. | Supplier invoice, payment proof, scope note, approval if reallocated. |
| Accessibility/Other | GBP 1,300 | Claim actual spend only if evidenced; describe design notes cautiously. | Receipts/invoices, payment proof, accessibility review evidence if claiming validation. |

Financial pack files to complete privately:

- Spending summary.
- Evidence reference index.
- Invoice folder.
- Redacted bank statement folder.
- MFA declaration.
- Budget reallocation correspondence.

### 6.3 Evidence Pack Still Needed

Private evidence should include:

- Demo video.
- Demo screenshots.
- Run logs generated from actual commands.
- Hardware screenshot/log if using DGX/GB10 as context.
- GitHub release URL or commit URL after push.
- Final README/repo screenshot if useful.
- Scope-pivot email thread.
- BCU/partner responses.
- Spending summary.
- Invoices.
- Redacted bank statements.
- MFA declaration.
- Final submission checklist.

Do not add private files to this public repository.

### 6.4 Wording Still To Review

Before submission, manually review:

- `README.md`
- `QUICKSTART.md`
- `CHANGELOG.md`
- `docs/closeout/*`
- `chimera_closeout_pack/01_Reports/01_Chimera_Final_Report_DRAFT.md`
- `chimera_closeout_pack/03_Project_Outputs/02_Technical_Case_Study_and_Toolkit_DRAFT.md`
- Any external final report, PDF, email, or form.

Remove or rewrite any wording that makes these unsupported claims:

- Do not claim a completed public show.
- Do not claim livestream delivered.
- Do not claim 40 students participated/upskilled.
- Do not claim formal accessibility validation.
- Do not claim completed BSL/avatar delivery.
- Do not claim production deployment.
- Do not claim partner approval.
- Do not claim spend or reallocation approval.

Only make those claims if direct evidence is present and reviewed.

## 7. Priority Timeline From 11 May 2026

Important dates from the close-out brief:

- Internal target submission date: 28 May 2026.
- Critical deadline: 4 June 2026.

Recommended planning:

### By 12 May 2026

- Send scope pivot and budget clarification emails.
- Create private evidence folder structure.
- Confirm where actual invoices and bank statements are stored.
- Decide whether to publish the current public-safe GitHub commits.

### By 14 May 2026

- Record the 3-5 minute narrated demo video.
- Save the video and run logs privately.
- Capture screenshots of command output and repository state.

### By 18 May 2026

- Complete spending summary draft.
- Match every claimed spend line to an invoice and bank statement.
- Mark unsupported spend as not claimed or requiring approval.

### By 21 May 2026

- Complete final report draft.
- Complete case study/toolkit draft.
- Add approved acknowledgement wording if supplied.
- Run claim review against every document.

### By 28 May 2026

- Complete final human review.
- Confirm written scope/reallocation response is stored.
- Confirm every financial line has evidence.
- Assemble private submission pack.
- Submit only if all gates are satisfied.

### By 4 June 2026

- Final deadline. Keep proof of submission and any BCU/AHRC response.

## 8. Recommended Next Repo Actions

The repository is now in a reasonable state for the narrowed Phase 1 support
role. Remaining repository work is secondary to human evidence gathering.

Useful but not as urgent as the human blockers:

1. Push public-safe commits to GitHub.
2. Confirm GitHub Actions status after push.
3. Create or update a GitHub release/tag only after the pushed state is checked.
4. Add a final link from the private evidence index to the commit SHA/release
   used for submission.
5. Consider archiving or further labelling broader Phase 2 services if external
   reviewers are expected to inspect beyond the operator-console path.

## 9. Recommended Next Human Actions

Start here:

1. Send the scope pivot / pre-submission clarification email.
2. Record the demo video.
3. Gather DGX/invoice/payment evidence.
4. Fill the spending summary and evidence reference index.
5. Get written response or approval for scope/budget variance.
6. Complete MFA declaration.
7. Review the final report and case study line by line.
8. Submit only when all gates are satisfied.

## 10. Submission Gate Checklist

Do not submit until these are true:

- [ ] Scope Gate: written notification sent and response stored.
- [ ] Demo Gate: narrated demo video recorded and private copy stored.
- [ ] Repo Gate: public repo pushed, clean, licensed, and checked.
- [ ] Spend Gate: every claimed amount maps to invoice and bank proof.
- [ ] MFA Gate: declaration completed and signed.
- [ ] Narrative Gate: final report avoids unsupported claims.
- [ ] Privacy Gate: no private evidence committed to public git.
- [ ] Final Review Gate: owner has checked all dates, names, amounts, and
      attachments.

## 11. Current Bottom Line

Project Chimera has a credible repository-supported Phase 1 close-out baseline.
The code and docs now support a cautious technical demonstrator story. The
grant submission itself remains blocked by human evidence and approval tasks,
especially scope correspondence, demo video capture, financial evidence, budget
reallocation confirmation, and MFA completion.

The next owner action is not more feature development. It is evidence capture
and written correspondence.
