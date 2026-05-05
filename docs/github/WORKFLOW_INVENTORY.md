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
| `.github/workflows/automated-tests.yml` | Automated Testing | Push and pull request to `main`; daily schedule. | `unit-tests`, `integration-tests`, `load-tests`, `flaky-test-detection`, `test-report` | Historical broad platform test workflow. |
| `.github/workflows/cd-production.yaml` | CD - Production | Version tag pushes; manual dispatch. | `pre-deploy-checks`, `deploy`, `rollback` | Production deployment path. |
| `.github/workflows/cd-staging.yaml` | CD - Staging | Push to `develop`; manual dispatch. | `deploy`, `rollback` | Staging deployment path. |
| `.github/workflows/check-links.yml` | Check Documentation Links | Daily schedule; manual dispatch; docs Markdown push and pull request paths. | `check-links` | Overlaps with `docs-link-check.yml` but has schedule/manual trigger and issue creation. |
| `.github/workflows/chimera-quality.yml` | Chimera Quality Platform | Push to `main` and `develop`; pull request to `main`. | `platform-unit-tests`, `service-tests` | Platform quality workflow. |
| `.github/workflows/ci.yaml` | CI | Push and pull request to `master`, `main`, and `develop`; Python 3.10. | `lint`, `test`, `security`, `build`, `kubernetes-validate`, `summary` | Retained pending owner review because triggers and purpose differ from `ci.yml`; check stale branches and runtime baseline before relying on it or making it required. |
| `.github/workflows/ci.yml` | Chimera Core Pipeline | Push and pull request to `main`. | `test` | Public README badge target; active baseline. |
| `.github/workflows/docs-link-check.yml` | Documentation Link Check | Docs Markdown push and pull request paths. | `link-check` | Narrow docs link check; overlaps partly with `check-links.yml`. |
| `.github/workflows/e2e-tests.yml` | E2E Tests | Push to `main`, `master`, and `develop`; pull request to `main` and `master`; hourly schedule; manual dispatch. | `e2e-tests`, `smoke-tests`, `report-results` | E2E and smoke workflow with scheduled monitoring behavior. |
| `.github/workflows/main-ci.yml` | Main Branch CI | Push to `main` when service, platform, test, or platform deployment paths change. | `test`, `build-push-images`, `deploy-preprod`, `quality-gate`, `notify` | Main branch platform build/deploy pipeline. |
| `.github/workflows/pr-validation.yml` | PR Validation | Pull request to `main` for service/platform/test paths; push to `feature/*` and `fix/*`. | `lint`, `security-scan`, `unit-tests`, `summary` | PR validation for scoped code paths and feature/fix branches. |
| `.github/workflows/prod-deploy.yml` | Production Deployment | Manual dispatch with deployment inputs. | `validate`, `backup`, `deploy-prod`, `smoke-tests`, `rollback`, `complete` | Manual production deployment workflow. |
| `.github/workflows/test.yaml` | Tests | Push and pull request to `master`, `main`, and `develop`; manual dispatch. | `unit-tests`, `integration-tests`, `load-tests`, `safety-tests`, `accessibility-tests`, `performance-tests`, `test-summary` | Broad test workflow; ownership overlaps with other historical test workflows. |
| `.github/workflows/trust-check.yml` | Trust Score Check | Pull request events: opened, synchronize, reopened. | `check-trust` | Contributor trust labeling workflow used by auto-merge policy. |
