# GitHub Repository Update Checklist

Use this checklist after merging a reviewed public cleanup branch.

Status: completed for the 2026-05-06 public Phase 1 baseline.

## Repository Metadata

- [x] Apply the description from `.github/REPOSITORY_DESCRIPTION.md`.
- [x] Apply the topics from `docs/github/REPOSITORY_SETTINGS.md`.
- [x] Leave the website URL blank unless a maintained public docs site exists.
- [x] Confirm the About section does not claim a finished production, public
      audience workflow, complete accessibility platform, or complete grant
      evidence pack.

## Public/Private Boundary

- [x] Run `scripts/privacy_preflight.py`.
- [x] Confirm private grant records, receipts, invoices, generated evidence,
      participant data, tokens, and `.env` files are not tracked.
- [x] Keep real evidence in private storage, not public git.

## GitHub Hygiene

- [x] Enable branch protection for `main`.
- [x] Require the active CI workflow before merge.
- [x] Enable secret scanning.
- [x] Enable automatic deletion of merged branches.
- [x] Use `docs/github/BRANCH_CLEANUP_RUNBOOK.md` for stale branch cleanup.

Dependabot alerts are available for public repositories; automated security
updates should be enabled after dependency ownership is reviewed.
