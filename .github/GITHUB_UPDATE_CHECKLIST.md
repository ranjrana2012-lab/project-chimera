# GitHub Repository Update Checklist

Use this checklist after merging a reviewed public cleanup branch.

## Repository Metadata

- [ ] Apply the description from `.github/REPOSITORY_DESCRIPTION.md`.
- [ ] Apply the topics from `docs/github/REPOSITORY_SETTINGS.md`.
- [ ] Leave the website URL blank unless a maintained public docs site exists.
- [ ] Confirm the About section does not claim a finished production, public
      audience workflow, complete accessibility platform, or complete grant
      evidence pack.

## Public/Private Boundary

- [ ] Run `scripts/privacy_preflight.py`.
- [ ] Confirm private grant records, receipts, invoices, generated evidence,
      participant data, tokens, and `.env` files are not tracked.
- [ ] Keep real evidence in private storage, not public git.

## GitHub Hygiene

- [ ] Enable branch protection for `main`.
- [ ] Require the active CI workflow before merge.
- [ ] Enable secret scanning and Dependabot alerts.
- [ ] Enable automatic deletion of merged branches.
- [ ] Use `docs/github/BRANCH_CLEANUP_RUNBOOK.md` for stale branch cleanup.
