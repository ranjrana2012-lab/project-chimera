# CI/CD Pipeline Architecture

**Version:** 1.0.0
**Date:** 2026-03-04
**Author:** Project Chimera Team

---

## Overview

This document defines the CI/CD pipeline architecture for Project Chimera, leveraging GitHub Actions for continuous integration and continuous deployment to the k3s cluster on DGX Spark.

---

## Pipeline Stages

### Stage 1: Pre-Flight Checks

**Trigger:** All pull requests and pushes to main branch

**Steps:**
1. **Code Quality Checks**
   - Linting (pylint for Python, eslint for JavaScript)
   - Type checking (mypy for Python)
   - Security scanning (Bandit for Python)

2. **License Compliance**
   - Scan for prohibited licenses
   - Check dependency licenses

3. **Secret Detection**
   - Scan for leaked credentials
   - Reject commits with secrets

**Success Criteria:**
- All linting checks pass
- No high/critical security issues
- No secrets detected
- License compliant

---

### Stage 2: Build and Test

**Trigger:** All pull requests and pushes to main branch

**Steps:**
1. **Unit Tests**
   - Run pytest with coverage
   - Enforce 80% coverage threshold
   - Parallel execution across services

2. **Integration Tests**
   - Test service-to-service communication
   - Test OpenClaw skill invocation
   - Test platform services integration

3. **Container Image Build**
   - Build Docker images for changed services
   - Tag with commit SHA and branch name
   - Scan images for vulnerabilities

**Success Criteria:**
- All unit tests pass (≥95% pass rate)
- All integration tests pass
- Container images build successfully
- No high/critical vulnerabilities in images

---

### Stage 3: Deploy to Pre-Production

**Trigger:** Merge to main branch (after PR approval)

**Steps:**
1. **Push Container Images**
   - Push images to GitHub Container Registry (ghcr.io)
   - Tag as `:latest` and `:v0.5.X`

2. **Helm Deploy to preprod**
   - Deploy to preprod namespace
   - Run smoke tests
   - Verify health endpoints

3. **Automated Testing**
   - Run end-to-end tests against preprod
   - Load testing (simulated audience)
   - Performance validation

**Success Criteria:**
- All pods Running in preprod
- All health checks passing
- E2E tests pass
- Performance targets met (p95 latency < 5s)

---

### Stage 4: Quality Gate

**Trigger:** Successful preprod deployment

**Steps:**
1. **Quality Metrics Collection**
   - Coverage report from test orchestrator
   - Test pass rate
   - Flaky test detection

2. **Quality Gate Evaluation**
   - Check against defined thresholds
   - Generate quality report
   - Block deployment if thresholds not met

3. **Manual Review** (if quality gate passes with warnings)
   - Review quality report
   - Approve or reject deployment

**Success Criteria:**
- Quality gate passes (or approved with warnings)
- No new critical issues introduced
- Performance regression < 20%

---

### Stage 5: Deploy to Production

**Trigger:** Manual approval after quality gate passes

**Steps:**
1. **Production Deployment**
   - Deploy to live namespace using Helm
   - Roll out with zero-downtime (rolling updates)
   - Monitor deployment progress

2. **Smoke Tests**
   - Verify all services responding
   - Test critical user flows
   - Check monitoring dashboards

3. **Rollback on Failure**
   - Automatic rollback if smoke tests fail
   - Alert operations team
   - Create incident

**Success Criteria:**
- All services healthy in production
- Smoke tests pass
- No errors in logs
- User-facing functionality working

---

## Pipeline Workflows

### Workflow 1: PR Validation

**File:** `.github/workflows/pr-validation.yml`

**Trigger:**
- Pull request to main branch
- Push to feature branch

**Jobs:**
1. **lint** - Run linters
2. **security-scan** - Run security scanners
3. **unit-tests** - Run unit tests with coverage
4. **build-images** - Build container images (no push)

**Matrix:**
- Services: openclaw, scenespeak, captioning, bsl, sentiment, lighting, safety, console, platform

### Workflow 2: Main Branch CI

**File:** `.github/workflows/main-ci.yml`

**Trigger:**
- Push to main branch

**Jobs:**
1. **lint** - Run linters
2. **security-scan** - Run security scanners
3. **unit-tests** - Run unit tests with coverage
4. **integration-tests** - Run integration tests
5. **build-and-push** - Build and push container images
6. **deploy-preprod** - Deploy to preprod namespace
7. **quality-gate** - Evaluate quality thresholds
8. **smoke-tests** - Run smoke tests on preprod

### Workflow 3: Production Deployment

**File:** `.github/workflows/prod-deploy.yml`

**Trigger:**
- Manual workflow_dispatch
- After successful main CI and quality gate

**Jobs:**
1. **validate** - Confirm pre-deployment checks
2. **deploy-prod** - Deploy to production
3. **smoke-tests** - Run production smoke tests
4. **monitor** - Verify deployment health

### Workflow 4: Nightly Tests

**File:** `.github/workflows/nightly-tests.yml`

**Trigger:**
- Schedule (cron: 0 2 * * *)

**Jobs:**
1. **full-test-suite** - Run all tests
2. **load-tests** - Run load tests
3. **security-scan** - Deep security scan
4. **dependency-check** - Check for outdated dependencies

---

## Container Image Strategy

### Image Naming

```
ghcr.io/project-chimera/<service>:<tag>
```

**Tags:**
- `:commit-<SHA>` - Immutable tag for each commit
- `:branch-<name>` - Latest build for a branch
- `:v0.5.X` - Semantic version for releases
- `:latest` - Latest main branch build

### Build Optimization

**Layer Caching:**
- Base Python image cached
- Dependencies installed in separate layer
- Application code in final layer

**Multi-Stage Builds:**
- Build stage with full dependencies
- Runtime stage with minimal dependencies
- Reduces final image size

### Image Scanning

**Tools:**
- Trivy for vulnerability scanning
- Snyk for dependency scanning

**Policies:**
- Block images with high/critical vulnerabilities
- Warn on medium vulnerabilities
- Allow low vulnerabilities with documentation

---

## Helm Deployment Strategy

### Value File Management

**Files:**
- `values.yaml` - Base values
- `values-preprod.yaml` - Preprod overrides
- `values-prod.yaml` - Production overrides

**Overrides:**
- Image tags
- Resource limits
- Replica counts
- Feature flags

### Deployment Process

1. **Helm Lint**
   ```bash
   helm lint ./helm/project-chimera
   ```

2. **Helm Diff**
   ```bash
   helm diff upgrade chimera ./helm/project-chimera
   ```

3. **Helm Upgrade**
   ```bash
   helm upgrade chimera ./helm/project-chimera --namespace chimera-live
   ```

4. **Helm Rollback** (if needed)
   ```bash
   helm rollback chimera -n chimera-live
   ```

---

## Quality Gate Integration

### Automatic Quality Checks

**Metrics:**
- Code coverage (≥80%)
- Test pass rate (≥95%)
- Flaky test rate (≤5%)
- Performance regression (≤20%)

**Actions:**
- Pass: Continue to deployment
- Warning: Require manual approval
- Fail: Block deployment

### Manual Approval Gates

**When:**
- Quality gate passes with warnings
- Major version changes
- Database migrations
- Configuration changes

**Process:**
1. Create GitHub issue with quality report
2. Assign to technical lead
3. Approve or reject within 24 hours

---

## Monitoring and Alerting

### Pipeline Monitoring

**Metrics:**
- Pipeline duration
- Success rate
- Failure reasons
- Stage bottlenecks

**Dashboards:**
- GitHub Actions insights
- Custom Grafana dashboard

### Alerting

**Alerts:**
- Pipeline failure (immediate)
- Quality gate failure (immediate)
- Deployment failure (immediate)
- Performance regression (daily)

**Channels:**
- Slack #project-chimera-ci
- Email to technical lead

---

## Rollback Procedures

### Automatic Rollback

**Triggers:**
- Smoke test failures
- Critical errors in logs
- Health check failures

**Process:**
1. Helm rollback to previous release
2. Create incident ticket
3. Alert operations team

### Manual Rollback

**Command:**
```bash
helm rollback chimera -n chimera-live
```

**Verification:**
1. Check pod status
2. Verify health endpoints
3. Check logs for errors
4. Monitor metrics

---

## Security Considerations

### Secrets Management

**Tools:**
- GitHub Secrets for CI/CD
- Sealed Secrets for Kubernetes

**Secrets:**
- Container registry credentials
- Kubernetes config
- API keys

**Rotation:**
- Every 90 days
- After security incident

### Access Control

**Permissions:**
- PR validation: All contributors
- Main CI: Maintainers only
- Production deployment: Technical leads only

**Approvals:**
- At least one maintainer approval required
- Code review required for all changes

---

## Performance Targets

| Stage | Target Duration |
|-------|----------------|
| PR Validation | < 10 minutes |
| Main CI | < 20 minutes |
| Preprod Deploy | < 15 minutes |
| Quality Gate | < 5 minutes |
| Production Deploy | < 30 minutes |

---

**Status:** ✅ Architecture Defined
**Next Step:** Create GitHub Actions workflows (Task 4.2.2)
