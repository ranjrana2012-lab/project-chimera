# Public GitHub Repository Surgery Design

Date: 2026-05-05
Base branch: `release-hardening-closeout`

## Purpose

Project Chimera needs a broad public repository cleanup before the current work
is presented as the public GitHub `main` branch. The previous release-hardening
pass added privacy gates, demo behaviour tests, local evidence capture, and
private artifact separation, but it did not update the live GitHub landing page
or complete broader repository hygiene.

This cleanup will make the public repository easier to understand, safer to
publish, and less cluttered for contributors and reviewers.

## Branch Strategy

Use the clean `release-hardening-closeout` branch as the base for public cleanup.
Do not build from dirty local `main`.

The cleanup branch should include:

- the verified hardening commits already present on `release-hardening-closeout`;
- focused public documentation cleanup commits;
- root and generated-artifact cleanup commits;
- GitHub metadata and repository settings documentation commits.

Remote branch deletion and legacy branch archiving are post-merge operations.
They must not be bundled into the file cleanup commits.

## Non-Negotiable Privacy Rules

The public repo must not track:

- private grant documents;
- receipts or invoices;
- private financial records;
- private meeting notes;
- generated demo recordings, screenshots, or evidence logs;
- participant personal data;
- API keys, tokens, `.env` files, or session files;
- local virtual environments, caches, coverage files, or test output.

`internal/` remains local/private. Public-safe evidence templates may remain only
if they contain placeholders and instructions, not real evidence.

`scripts/privacy_preflight.py` remains the publication gate before every public
commit and push.

## File And Directory Cleanup

Remove public-tracked generated/private/local artifacts already identified by
the hardening branch:

- `.env.docker`;
- `.env.nemotron`;
- tracked `node_modules`;
- coverage files;
- test result files;
- token JSON;
- compiled local binaries;
- old generated demo captures.

Remove public-tracked experiment and prototype clutter instead of moving it to a
public archive:

- `.autonomous/`;
- `.claude/`;
- `future_concepts/`;
- `demo-materials-2026-03-02/`;
- `progress/`;
- `proposals/`;
- private `internal/grant-tracking/grant_closeout/`.

Before each removal, use reference scans to find docs, tests, scripts, or import
paths that still mention those locations. Update references when the referenced
content is being removed. Defer a removal if it would break active code or tests.

Do not rename risky service/package paths such as `kimi-super-agent` in this
pass. That rename requires a dedicated refactor and test plan.

## Reports And Validation Docs

Root machine-specific reports should not be first-read public material. Move or
remove them from the root public story:

- `LOCAL_VALIDATION_REPORT.md`;
- `PATCH_SUMMARY.md`;
- `REMAINING_GAPS.md`;
- `RELEASE_SYNC_REPORT.md`.

Preferred destination is `docs/reports/` with a short `docs/reports/README.md`
that explains these files are maintainer-facing validation history, not setup
instructions.

README should not lead with local host details, hardware validation, or large
pass counts.

## Public README Design

`README.md` should become a concise landing page:

- one-paragraph project description;
- honest Phase 1 status;
- short feature list;
- default student/laptop quick start;
- links to advanced setup guides;
- privacy note;
- small repository map;
- links to contribution, security, and docs hub.

Remove from README:

- "Last validated locally" hardware lines;
- large pass-count summaries;
- detailed DGX/Kimi command blocks;
- monitoring setup details;
- long pytest command blocks;
- root report links as primary evidence.

Advanced routes should be linked, not expanded:

- `docs/guides/STUDENT_LAPTOP_SETUP.md`;
- `docs/guides/DGX_SPARK_SETUP.md`;
- `docs/guides/KIMI_QUICKSTART.md`;
- a monitoring guide if present or added.

## Documentation Cleanup

`docs/README.md` becomes the main documentation hub.

`docs/guides/README.md` lists setup guides by runtime profile:

- Student / Laptop;
- DGX Spark / GB10;
- Kimi;
- monitoring, if maintained.

`CONTRIBUTING.md` should be shortened and aligned to Python 3.12. It should point
to detailed developer setup docs instead of duplicating all setup and standards.

Branch naming guidance:

- `feature/<name>`;
- `fix/<name>`;
- `docs/<name>`;
- `chore/<name>`.

`CHANGELOG.md` should reflect the existing release/tag story, including
`v1.0.0-phase1`, without pretending a GitHub Release exists until one is
published.

## Deployment And Structure Cleanup

Do not physically move Compose files in this pass unless a reference scan proves
the move is safe. Many docs and scripts may reference them.

Prefer documenting active deployment profiles first:

- student/laptop compose preview;
- MVP compose stack;
- DGX Spark override;
- Kimi service route.

Kubernetes consolidation (`k8s/` vs `infrastructure/kubernetes/`) is deferred
unless scans prove one directory is unused and safe to remove. If both are stale,
document a follow-up instead of guessing.

## GitHub Hygiene

Keep or clean:

- `.github/CODEOWNERS`;
- `.github/PULL_REQUEST_TEMPLATE.md`;
- issue templates;
- repository description checklist.

De-duplicate issue templates. For example, keep one modern bug template and one
modern feature template instead of maintaining both `bug.md` / `bug_report.md`
and `feature.md` / `feature_request.md`.

Workflow cleanup must be conservative. There are many overlapping workflow files.
Read triggers before removing anything. Keep the active CI workflow for pushes
and PRs to `main`. Remove or disable only clearly duplicate or stale workflows.
Document deferred workflow consolidation when risk is high.

Add or update `docs/github/REPOSITORY_SETTINGS.md` for settings that cannot be
safely solved by file edits:

- branch protection on `main`;
- require CI;
- require at least one review;
- auto-delete merged branches;
- secret scanning;
- repository topics and description;
- release and changelog process.

## Branch Cleanup Plan

Branch cleanup happens after the public cleanup branch is reviewed and merged.

Safety checks before deleting or archiving a branch:

- fetch and prune;
- compare against `origin/main`;
- confirm no open PR references the branch;
- tag legacy state where needed.

Candidate actions:

- delete `origin/codex-chimera-validation-fixes-20260424` if PR #13 is merged
  and no open PR uses it;
- delete `origin/codex/student-dgx-runtime-profiles` if it has no needed unique
  commits;
- tag/archive `origin/master` as legacy after explicit confirmation.

Keep `main` and active cleanup branches only.

## Validation Gates

Before pushing the cleanup branch, run:

- privacy preflight;
- focused pytest suite from the hardening branch;
- `verify_prerequisites.py`;
- `test_chimera_smoke.py`;
- README/docs reference scans with `rg`;
- `git status --short`;
- `git ls-files` checks for forbidden paths.

Confirm no tracked paths include:

- `internal/`;
- `.env` files other than examples;
- receipts or invoices;
- videos or screenshots;
- generated evidence;
- `node_modules`;
- local virtual environments.

## Commit Shape

Use small commits with clear rollback points:

1. `docs: simplify public README and docs index`
2. `docs: move maintainer validation reports under docs reports`
3. `chore: remove public tracked experiments and generated artifacts`
4. `chore: tidy github templates and repository settings docs`
5. `docs: update contributing branch and release guidance`
6. optional: `chore: clean duplicate workflows`

Only add the optional workflow cleanup if the triggers and ownership are clear.

## Rollout

1. Build from `release-hardening-closeout`.
2. Add cleanup commits.
3. Run validation gates.
4. Push the cleanup branch.
5. Open a PR against `main`.
6. Review the diff for accidental private material.
7. Merge only after CI and privacy preflight pass.
8. Perform branch deletion/tagging as a separate controlled operation.

## Residual Risks

Removing experimental folders may break hidden references in docs/tests. Use
reference scans before each deletion.

Workflow cleanup can break CI if handled aggressively. Keep it conservative.

GitHub settings and Releases require repository-owner actions and cannot be
fully completed through file edits alone.
