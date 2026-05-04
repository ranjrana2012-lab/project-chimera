# Release Hardening Closeout Design

Date: 2026-05-04

## Purpose

Project Chimera is in a Phase 1 closeout state. The next pass will harden the
public source set, lock the expected local demo behaviours with tests, capture
private evidence, and commit only public-safe repository changes.

The pass must preserve the current closeout identity: Chimera Core Phase 1 is a
local-first adaptive AI foundation, not a completed public theatre production.

## Scope

The release-hardening pass has five workstreams:

1. TDD behaviour lock.
2. Validation and evidence capture.
3. Public/private boundary audit.
4. Release-quality cleanup.
5. Commit gate.

The pass may run long local validation, including student Docker and DGX/Kimi
checks when the host evidence supports them. Local operator-console validation
remains the required first route.

## Public Source Surface

The public source surface may include:

- source code and tests,
- public-safe setup and route guides,
- public-safe validation summaries,
- demo scripts and capture checklists,
- `.env.example` style files without real secrets,
- empty evidence placeholders and templates.

It must not include real grant evidence, receipts, invoices, private logs,
private correspondence, tokens, `.env` files, screenshots, recordings, or
generated dependencies.

## Private Evidence Surface

The private evidence surface includes:

- grant drafts and final submission material,
- receipts, invoices, spend records, and payment evidence,
- raw screenshots and demo recordings,
- run logs and endpoint captures with local machine detail,
- `.env` files, API keys, tokens, and registry credentials,
- private meeting notes or participant data.

These artefacts should stay outside Git or inside ignored local paths such as
`internal/`, `Grant_Evidence_Pack/`, `project-chimera-submission*`, or ignored
evidence output folders. Public docs may refer to private evidence locations
generically but must not expose private content.

## Data Flow

The hardening pass will follow this sequence:

1. Add or strengthen tests for the Phase 1 demo contract through TDD.
2. Run local operator-console CLI and web validation.
3. Capture logs, endpoint output, screenshots, and demo recording into private
   ignored paths where tooling permits.
4. Run student Docker validation after the local route passes.
5. Run DGX/Kimi validation only if current host evidence supports the advanced
   route.
6. Audit tracked, staged, untracked, and ignored paths for public/private
   boundary violations.
7. Stage only public-safe source, tests, docs, placeholders, and cleanup
   removals.
8. Re-run the final selected validation commands.
9. Commit only after tests and privacy checks pass.

## Testing Strategy

After this design is approved and reviewed, implementation will use the
`superpowers:test-driven-development` workflow for any new or changed
behaviour.

The test targets are:

- core behaviour: positive input selects `momentum_build`, negative or anxious
  input selects `supportive_care`, and neutral input selects
  `standard_response`;
- CLI contract: normal input, `demo`, `compare`, and `caption` modes produce
  stable evidence-friendly output;
- web/API contract: `/api/state`, `/api/process`, `/api/export`, and invalid or
  empty input handling behave predictably;
- privacy checks: forbidden private paths and sensitive file categories are not
  tracked or staged;
- validation commands: prerequisites, smoke tests, focused pytest, broader
  regression, student Docker, and optional DGX/Kimi checks when supported.

Existing adequate coverage should be run and preserved. Missing or incorrect
behaviour should be locked by a failing test before production code changes.

## Error Handling And Guardrails

The pass fails closed around privacy:

- Stop before commit if a private grant doc, `.env`, token, receipt, invoice,
  raw screenshot, raw video, or private log is tracked or staged.
- Fix missing or incorrect behaviour through TDD.
- If DGX/Kimi fails while local and student routes pass, do not block Phase 1
  closeout. Mark DGX/Kimi as optional and needing revalidation before making
  advanced claims.
- If screenshot or recording tooling is unavailable, keep command logs and
  checklist output, then leave manual capture as an owner action.
- If Git history appears to contain secrets or private grant files, do not
  rewrite history automatically. Record the finding and require separate
  approval for history cleanup and secret rotation.
- Correct public docs that overclaim completed theatre production, BSL/avatar,
  live venue readiness, live audience workflows, or unsupported hardware
  operation.

## Deliverables

The pass should produce:

- new or strengthened tests for the Phase 1 demo contract;
- private evidence artefacts captured locally and not committed;
- public-safe documentation updates where needed;
- a privacy audit result showing forbidden files are not tracked or staged;
- a final public-source commit containing only safe source, tests, docs,
  placeholders, and cleanup removals;
- a closeout note listing what passed, what was captured privately, and what
  remains owner-only.

## Commit Policy

Do not commit:

- `internal/`,
- `Grant_Evidence_Pack/`,
- real `evidence/**` artefacts,
- `.env*` files except approved examples,
- receipts, invoices, grant correspondence, or private financial records,
- private logs, screenshots, or recordings,
- generated dependency folders,
- coverage outputs,
- runtime tokens,
- build outputs.

Do not rewrite Git history without explicit separate approval. Do not claim
DGX/Kimi validation unless that route passes during this pass on the current
host.

## Success Criteria

The release-hardening pass is complete when:

1. expected Phase 1 demo behaviours are locked by tests;
2. local operator-console CLI and web validation pass;
3. student Docker validation passes or is clearly documented as blocked;
4. DGX/Kimi validation either passes on supported host evidence or is described
   as optional and needing revalidation;
5. private evidence is captured or owner manual actions are clearly listed;
6. privacy checks show no forbidden tracked or staged files;
7. the public commit contains only safe source, tests, docs, templates, and
   cleanup removals.
