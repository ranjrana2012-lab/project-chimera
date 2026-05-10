# Secret Scan Report

Status: DRAFT AUDIT REPORT - HUMAN ACTION REQUIRED.
Last refreshed: 2026-05-10.

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
  scripts, legacy docs, tests, and advanced model helpers. These were replaced
  with repository-relative, `$HOME`, `Path.home()`, environment-variable, or
  placeholder paths.
- Earlier inspection found secret-like placeholders and false positives in
  tests, example Kubernetes YAML, and auth/proxy documentation. These were
  replaced with obvious placeholders or scanner-safe forwarding patterns.
- The 2026-05-10 broad tracked/untracked scan with `--fail-on-findings` reports
  no secret-like findings.

## Action Taken

- Added `scripts/scan_for_secrets.py`.
- Kept scan output value-free.
- Updated local-path defaults in demo helper scripts.
- Replaced the top-level `.env.example` and dashboard Compose `PROJECT_ROOT`
  examples with repository-relative defaults.
- Removed repository-local absolute paths from public docs, tests, and advanced
  model helpers.
- Replaced example secret literals in webhook tests, Kubernetes YAML, and
  Z.ai proxy documentation.
- Tuned the secret scanner to avoid false positives for config forwarding and
  token getter calls while still catching literal secret-like values.

## Remaining Human Action

- Review any private `.env` file locally and never commit it.
- Review ignored private evidence before submission.
- Re-run `python3 scripts/scan_for_secrets.py --include-untracked
  --fail-on-findings` before every public push.
- Re-run `python3 scripts/privacy_preflight.py` before every push.
