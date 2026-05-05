# Workflow Inventory

This inventory records the CI/CD workflow state during the public repository
cleanup.

## Active Baseline

- `.github/workflows/ci.yml` is the public README badge target and should remain
  active for pushes and pull requests to `main`.

## Review Before Removal

The repository contains multiple historical CI, test, deploy, onboarding, and
trust-check workflows. Remove a workflow only after confirming:

- its trigger duplicates another maintained workflow;
- no README, branch protection rule, or repository setting references it;
- the owner agrees that the automation is obsolete.

## Deferred Cleanup

Workflow consolidation is deferred when trigger ownership is unclear.

During final public review, `.github/workflows/onboarding.yml` and
`.github/workflows/sprint-0-issues.yml` were removed because they were manual
public issue creators with stale onboarding content that could recreate
overbroad Phase 1 claims.

After the first public `main` push, `.github/workflows/docs-link-check.yml` was
removed because it duplicated `.github/workflows/check-links.yml` and used the
same source-agnostic shell link resolution that failed on guide-relative links.
The retained link workflow now uses `scripts/check_markdown_links.py` and does
not create GitHub issues automatically.

The first public `main` pushes also showed that several historical broad
workflows still ran on every public update and failed on stale infrastructure
assumptions. Until the owner reviews and modernizes them, these workflows are
kept as manual dispatch only: `automated-tests.yml`, `chimera-quality.yml`,
`ci.yaml`, `e2e-tests.yml`, `main-ci.yml`, and `test.yaml`.

## Stale-Risk Signals

Workflows with stale-risk signals must be verified against branch policy, the
default branch, and the current runtime baseline before enabling, deleting, or
making them required. Known review targets include `cd-production.yaml` for
Python 3.10, `cd-staging.yaml` for `develop` and Python 3.10,
`chimera-quality.yml` for `develop`, `e2e-tests.yml` for `master`/`develop`,
and `test.yaml` for `master`/`develop`.

## Inventory

| Workflow | Name | Trigger summary | Job summary | Notes |
| --- | --- | --- | --- | --- |
| `.github/workflows/auto-merge.yml` | Auto-Merge | Pull request events: opened, synchronize, reopened, ready for review. | `auto-merge` | Trust/protected-file automation; keep until owner confirms repository policy. |
| `.github/workflows/automated-tests.yml` | Automated Testing | Manual dispatch only pending owner review. | `unit-tests`, `integration-tests`, `load-tests`, `flaky-test-detection`, `test-report` | Historical broad platform test workflow. |
| `.github/workflows/cd-production.yaml` | CD - Production | Version tag pushes; manual dispatch. | `pre-deploy-checks`, `deploy`, `rollback` | Production deployment path. |
| `.github/workflows/cd-staging.yaml` | CD - Staging | Push to `develop`; manual dispatch. | `deploy`, `rollback` | Staging deployment path. |
| `.github/workflows/check-links.yml` | Check Documentation Links | Daily schedule; manual dispatch; docs Markdown/script push and pull request paths. | `check-links` | Maintained local markdown link checker; no external link-check action or issue creation. |
| `.github/workflows/chimera-quality.yml` | Chimera Quality Platform | Manual dispatch only pending owner review. | `platform-unit-tests`, `service-tests` | Platform quality workflow with stale platform dependency assumptions. |
| `.github/workflows/ci.yaml` | CI | Manual dispatch only pending owner review; Python 3.10. | `lint`, `test`, `security`, `build`, `kubernetes-validate`, `summary` | Retained pending owner review because triggers and purpose differ from `ci.yml`; check stale branches and runtime baseline before relying on it or making it required. |
| `.github/workflows/ci.yml` | Chimera Core Pipeline | Push and pull request to `main`. | `test` | Public README badge target; active baseline. |
| `.github/workflows/e2e-tests.yml` | E2E Tests | Manual dispatch only pending owner review. | `e2e-tests`, `smoke-tests`, `report-results` | Historical E2E and smoke workflow with scheduled monitoring behavior disabled for public Phase 1 baseline. |
| `.github/workflows/main-ci.yml` | Main Branch CI | Manual dispatch only pending owner review. | `test`, `build-push-images`, `deploy-preprod`, `quality-gate`, `notify` | Main branch platform build/deploy pipeline. |
| `.github/workflows/pr-validation.yml` | PR Validation | Pull request to `main` for service/platform/test paths; push to `feature/*` and `fix/*`. | `lint`, `security-scan`, `unit-tests`, `summary` | PR validation for scoped code paths and feature/fix branches. |
| `.github/workflows/prod-deploy.yml` | Production Deployment | Manual dispatch with deployment inputs. | `validate`, `backup`, `deploy-prod`, `smoke-tests`, `rollback`, `complete` | Manual production deployment workflow. |
| `.github/workflows/test.yaml` | Tests | Manual dispatch only pending owner review. | `unit-tests`, `integration-tests`, `load-tests`, `safety-tests`, `accessibility-tests`, `performance-tests`, `test-summary` | Broad test workflow; ownership overlaps with other historical test workflows. |
| `.github/workflows/trust-check.yml` | Trust Score Check | Pull request events: opened, synchronize, reopened. | `check-trust` | Contributor trust labeling workflow used by auto-merge policy. |
