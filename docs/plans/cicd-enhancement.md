# CI/CD Pipeline Enhancement Plan

**Version:** 1.0
**Date:** March 2026
**Status:** Implementation Guide

---

## Overview

This document outlines enhancements to the CI/CD pipeline for Project Chimera, including automated testing, code coverage reporting, security scanning, and deployment automation.

---

## Current CI/CD Pipeline

### Existing Workflows

1. **PR Validation** (`.github/workflows/pr-validation.yml`)
2. **CI** (`.github/workflows/ci.yaml`)
3. **Main CI** (`.github/workflows/main-ci.yml`)
4. **Automated Tests** (`.github/workflows/automated-tests.yml`)
5. **Chimera Quality Platform** (`.github/workflows/chimera-quality.yml`)
6. **Documentation Link Check** (`.github/workflows/docs-link-check.yml`)

---

## Enhancement Plan

### Phase 1: Automated Testing on PR

**Current State:** Tests run on push, not on PR

**Enhancement:** Create comprehensive PR validation workflow

**File:** `.github/workflows/pr-validation-enhanced.yml`

```yaml
name: Enhanced PR Validation

on:
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff black mypy

      - name: Run ruff
        run: ruff check .

      - name: Run black --check
        run: black --check .

      - name: Run mypy
        run: mypy services/ || true

  test-unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            -v \
            --tb=short \
            --cov=services \
            --cov-report=xml \
            --cov-report=html \
            -m "not integration and not load"

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

      - name: Check 80% coverage threshold
        run: |
          coverage=$(python -c "
          import xml.etree.ElementTree as ET
          tree = ET.parse('coverage.xml').getroot()
          line_rate = float(tree.attrib.get('line-rate', 0))
          print(f'Coverage: {line_rate:.2%}')
          exit(0 if line_rate >= 0.80 else 1)
          ")

  test-integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: chimera_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/chimera_test
          REDIS_URL: redis://localhost:6379
          TESTING: "true"
        run: |
          pytest tests/integration/ \
            -v \
            --junitxml=integration-results.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: integration-test-results
          path: integration-results.xml

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@0.24.0
        with:
          scan-type: 'fs'
          scan-ref: 'refs/heads/main'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

---

### Phase 2: Dependency Checking

**File:** `.github/workflows/dependency-check.yml`

```yaml
name: Dependency Check

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6am
  workflow_dispatch:

jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install pip-audit
        run: |
          python -m pip install pip-audit

      - name: Run pip-audit
        run: pip-audit --format json > audit-results.json

      - name: Check for vulnerabilities
        run: |
          python << 'EOF'
          import json
          with open('audit-results.json') as f:
              audit = json.load(f)

          vulnerabilities = [v for v in audit if v['vulnerability'] > 0]
          high_vulns = [v for v in vulnerabilities if v['severity'] == 'HIGH']

          if high_vulns:
              print(f"❌ Found {len(high_vulns)} HIGH severity vulnerabilities")
              for vuln in high_vulns:
                  print(f"  - {v['name']}: {v['affected_versions']}")
              exit(1)
          else:
              print("✅ No HIGH severity vulnerabilities found")
          EOF

      - name: Upload audit results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: dependency-audit-results
          path: audit-results.json
```

---

### Phase 3: Staged Deployment

**File:** `.github/workflows/deploy-staging.yml`

```yaml
name: Deploy to Staging

on:
  push:
    branches: [develop]
  workflow_dispatch:

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBE_CONFIG }}" > $HOME/.kube/config

      - name: Deploy to staging
        run: |
          kubectl set image deployment/scenespeak-agent \
            scenespeak-agent:${{ github.sha }} \
            -n staging

          kubectl set image deployment/captioning-agent \
            captioning-agent:${{ github.sha }} \
            -n staging

          kubectl set image deployment/sentiment-agent \
            sentiment-agent:${{ github.sha }} \
            -n staging

          kubectl set image deployment/bsl-agent \
            bsl-agent:${{ github.sha }} \
            -n staging

          kubectl rollout restart deployment/scenespeak-agent -n staging
          kubectl rollout restart deployment/captioning-agent -n staging
          kubectl rollout restart deployment/sentiment-agent -n staging
          kubectl rollout restart deployment/bsl-agent -n staging

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/scenespeak-agent -n staging --timeout=5m

      - name: Run smoke tests
        run: |
          # Smoke test staging deployment
          kubectl run smoke-test --image=curlimages/curl:latest --rm -n staging --restart=Never -- \
            curl -f http://scenespeak-agent:8001/health

      - name: Notify deployment status
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            Staging deployment ${{ job.status }}
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

### Phase 4: Production Deployment

**File:** `.github/workflows/deploy-production.yml`

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  quality-gate-check:
    name: Quality Gate Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check SLO compliance
        run: |
          curl -f http://quality-gate:8013/api/v1/gate/check \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{
              "service": "scenespeak-agent",
              "version": "${{ github.ref_name }}",
              "commit_sha": "${{ github.sha }}"
            }' \
            | tee gate-result.json

          CAN_DEPLOY=$(jq -r '.can_deploy // false' gate-result.json)

          if [ "$CAN_DEPLOY" != "true" ]; then
            echo "❌ Quality Gate blocked deployment"
            jq -r '.reason' gate-result.json
            exit 1
          fi

          echo "✅ Quality Gate passed - deployment approved"

      - name: Upload gate result
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: quality-gate-result
          path: gate-result.json

  deploy-production:
    name: Deploy to Production
    needs: quality-gate-check
    runs-on: ubuntu-latest
    environment:
      PRODUCTION_NAMESPACE: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBE_CONFIG_PROD }}" > $HOME/.kube/config

      - name: Deploy tagged image to production
        run: |
          TAG=${GITHUB_REF#refs/tags/}
          IMAGE="scenespeak-agent:$TAG"

          kubectl set image deployment/scenespeak-agent \
            scenespeak-agent:$TAG \
            -n production

          kubectl rollout restart deployment/scenespeak-agent -n production

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/scenespeak-agent -n production --timeout=10m

      - name: Run smoke tests
        run: |
          kubectl run smoke-test --image=curlimages/curl:latest --rm -n production --restart=Never -- \
            curl -f http://scenespeak-agent:8001/health

      - name: Notify deployment success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            ✅ Production deployment successful
            Tag: ${{ github.ref_name }}
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

      - name: Notify deployment failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            ❌ Production deployment FAILED
            Tag: ${{ github.ref_name }}
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

      - name: Rollback on failure
        if: failure()
        run: |
          echo "Deployment failed - initiating rollback..."
          PREV_IMAGE=$(kubectl get deployment/scenespeak-agent -n production -o jsonpath='{.spec.template.spec.containers[0].image}')

          kubectl set image deployment/scenespeak-agent \
            scenespeak-agent:$PREV_IMAGE \
            -n production

          kubectl rollout restart deployment/scenespeak-agent -n production
```

---

## Pipeline Configuration

### Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: format-check
        name: Format Check
        entry: make format-check
        language: system

      - id: lint-check
        name: Lint Check
        entry: make lint
        language: system

      - id: test-unit
        name: Unit Tests
        entry: pytest tests/unit/ -v
        language: system

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
      - id: prettier
        name: Prettier Check
        types_or: [markdown, yaml]

  - repo: https://github.com/pre-commit/mirrors-yamlfix
    rev: v0.10.0
    hooks:
      - id: yamlfix
        name: YAML Fix
        types: [yaml]
```

---

## Automation Scripts

### Dependency Update Script

**File:** `scripts/ci/update-dependencies.sh`

```bash
#!/bin/bash
# Automated dependency update and PR creation

echo "Checking for dependency updates..."

# Check for updates
pip list --outdated > /tmp/outdated.txt

# Create PR if updates found
if [ -s /tmp/outdated.txt ]; then
  echo "Found outdated dependencies, creating PR..."

  gh pr create \
    --title "chore: update dependencies" \
    --body "Automated dependency update by CI" \
    --base develop \
    --label "dependencies" \
    --label "automated"
fi
```

### Deployment Validation Script

**File:** `scripts/ci/validate-deployment.sh`

```bash
#!/bin/bash
# Validate deployment after rollout

echo "Validating deployment..."

# Check all pods are ready
kubectl wait --for=condition=ready pod -l app=scenespeak-agent -n $1 --timeout=5m

# Check health endpoints
SERVICES=("scenespeak-agent" "captioning-agent" "sentiment-agent" "bsl-agent")
NAMESPACE=$1

for service in "${SERVICES[@]}"; do
  echo "Checking $service..."
  kubectl run curl-debug --rm -n $NAMESPACE --restart=Never -- \
    curl -f http://$service:8001/health || \
    echo "❌ $service health check failed"
done

echo "✅ Deployment validation complete"
```

---

## Monitoring CI/CD

### Metrics to Track

| Metric | Target | Description |
|--------|--------|-------------|
| PR build time | <5 min | Time from PR to CI completion |
| Test pass rate | >95% | Percentage of CI test runs passing |
| Deployment success rate | >98% | Percentage of successful deployments |
| Mean time to recovery (MTTR) | <30 min | Time to recover from failed deployment |
| Change failure rate | <15% | Percentage of changes causing incidents |

### Dashboards

**Grafana Dashboard:** CI/CD Pipeline Overview

- PR build duration trends
- Test pass rate trends
- Deployment frequency
- Failed deployment rate
- Pipeline bottleneck identification

---

## Rollback Procedures

### Automatic Rollback

Triggered when:
- Smoke tests fail
- Health checks fail
- Error rate spike detected

### Manual Rollback

```bash
# Manual rollback to previous version
kubectl rollout undo deployment/scenespeak-agent -n production

# Rollback to specific revision
kubectl rollout undo deployment/scenespeak-agent --to-revision=5 -n production

# Rollback to tagged version
kubectl set image deployment/scenespeak-agent \
  scenespeak-agent:v0.3.9 \
  -n production
```

---

## Security Considerations

### Secrets Management

- Use GitHub Secrets for sensitive data
- Rotate secrets regularly
- Never log secrets
- Use encrypted secrets in Kubernetes

### Access Control

- Require approval for production deployments
- Restrict who can trigger deployments
- Audit all deployment activities

### Image Scanning

- Scan all images before deployment
- Block deployments with critical vulnerabilities
- Track vulnerability trends

---

## Related Documentation

- [Deployment Guide](../DEPLOYMENT.md) - Deployment procedures
- [Quality Gate Documentation](../services/quality-platform.md) - SLO-based blocking
- [Incident Response Runbook](../runbooks/incident-response.md) - Handling deployment failures
- [SLO Response Runbook](../runbooks/slo-response.md) - SLO breach procedures

---

*CI/CD Pipeline Enhancement Plan - Project Chimera v0.4.0 - March 2026*
