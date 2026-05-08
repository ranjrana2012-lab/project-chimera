# Secret Scan Report

Status: DRAFT AUDIT REPORT - HUMAN ACTION REQUIRED.

## Scan Method

The repository uses:

- `scripts/privacy_preflight.py` for publication boundary checks;
- `scripts/scan_for_secrets.py` for tracked-file secret-like pattern checks;
- targeted ripgrep checks for local absolute paths and common token terms.

The scan reports file paths and risk types only. Secret values must not be
copied into this report.

## Files Checked

Public tracked files and untracked close-out templates were checked. Ignored
private folders such as `internal/`, real `.env` files, model caches, generated
evidence, and private financial material remain outside the public commit.

## Risks Found

- Earlier inspection found hard-coded local home-directory paths in helper
  scripts. These were replaced with repository-relative or `$HOME` based paths.
- The broad tracked/untracked scan still reports local absolute paths and
  secret-like variable assignments in legacy, experimental, integration,
  orchestration, and test surfaces outside the Phase 1 operator-console path.
  Values were not printed. These findings should be reviewed before any broader
  public release claim.

## Action Taken

- Added `scripts/scan_for_secrets.py`.
- Kept scan output value-free.
- Updated local-path defaults in demo helper scripts.
- Replaced the top-level `.env.example` and dashboard Compose `PROJECT_ROOT`
  examples with repository-relative defaults.

## Remaining Human Action

- Review any private `.env` file locally and never commit it.
- Review ignored private evidence before submission.
- Triage remaining legacy/experimental findings if the public release scope is
  widened beyond the Phase 1 operator-console baseline.
- Re-run `python3 scripts/privacy_preflight.py` before every push.
