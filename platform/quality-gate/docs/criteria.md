# Quality Gate Criteria

**Version:** 1.0.0
**Date:** 2026-03-04
**Author:** Project Chimera Team

---

## Overview

Quality gates ensure that code changes meet minimum quality standards before being merged. This document defines the criteria that must be satisfied for a pull request to be approved.

---

## Coverage Thresholds

### Overall Coverage Requirements

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Overall Code Coverage | **≥ 80%** | Industry standard for production code |
| New Code Coverage | **≥ 85%** | Higher bar for new code |
| Critical Path Coverage | **≥ 90%** | Core functionality must be well-tested |

### Per-Service Coverage

| Service | Threshold | Notes |
|---------|-----------|-------|
| scenespeak-agent | ≥ 85% | ML model logic |
| captioning-agent | ≥ 80% | Translation accuracy |
| bsl-agent | ≥ 85% | Sign language generation |
| sentiment-agent | ≥ 75% | Sentiment analysis complexity |
| lighting-service | ≥ 90% | Hardware control |
| safety-filter | ≥ 95% | Safety-critical component |
| openclaw-orchestrator | ≥ 80% | Core orchestration |
| operator-console | ≥ 75% | UI complexity |

### Coverage Calculation Rules

- **Line Coverage**: Percentage of executable lines executed
- **Branch Coverage**: Percentage of conditional branches taken
- **Threshold**: Based on line coverage (primary metric)

---

## Test Requirements

### Test Success Rate

| Scenario | Pass Rate | Description |
|----------|-----------|-------------|
| Pre-Merge CI | **≥ 95%** | All tests must pass |
| Full Test Suite | **≥ 90%** | Allowed regression tolerance |
| Smoke Tests | **100%** | Critical path must pass |

### Test Categories

| Category | Minimum Tests | Description |
|----------|---------------|-------------|
| Unit Tests | 5 per file | Code logic testing |
| Integration Tests | 3 per service | Service interaction |
| End-to-End Tests | 1 per feature | User workflow |
| Performance Tests | Per endpoint | Response time validation |

### Flaky Test Limits

| Metric | Threshold | Action |
|--------|-----------|--------|
| Flakiness Rate | **≤ 5%** | Max tests allowed to be flaky |
| Retry Limit | **3 attempts** | Tests can fail up to 3 times before being flaky |
| Exemption Window | **7 days** | Time to fix newly flagged flaky tests |

---

## Performance Thresholds

### Response Time Requirements

| Endpoint | P95 Latency | P99 Latency | Notes |
|----------|-------------|-------------|-------|
| GET /health | ≤ 100ms | ≤ 200ms | Health check |
| POST /generate | ≤ 2s | ≤ 5s | Content generation |
| WebSocket | ≤ 50ms | ≤ 100ms | Event delivery |

### Resource Limits

| Resource | Limit | Measurement |
|----------|-------|-------------|
| Memory Per Service | ≤ 512MB | RSS |
| CPU Per Service | ≤ 80% | 1 core |
| Connection Pool | ≥ 5 | Database/HTTP |

---

## Security Requirements

### Code Quality

| Check | Tool | Threshold |
|-------|------|-----------|
| Linting | pylint | Score ≥ 8.0 |
| Type Checking | mypy | Strict mode |
| Security Scan | Bandit | No high/critical issues |

### Dependencies

| Requirement | Tool | Action |
|-------------|------|--------|
| Known Vulnerabilities | pip-audit | 0 high/critical |
| License Compliance | pip-licenses | Approved licenses only |
| Outdated Packages | pip-outdated | Update within 30 days |

---

## Documentation Requirements

### Required Documentation

| Artifact | Requirement |
|----------|------------|
| New Feature | README with usage example |
| API Change | Updated API documentation |
| Bug Fix | Changelog entry |
| Configuration | Environment variable documentation |

### Code Documentation

| Element | Coverage |
|---------|----------|
| Module Docstrings | 100% |
| Class Docstrings | 100% |
| Function Docstrings | 100% public, 80% private |

---

## Gate Enforcement

### Pre-Merge Checks

All PRs must pass:
1. **Automated Checks**
   - All tests pass (≥95% pass rate)
   - Coverage ≥ 80% overall
   - No high/critical security vulnerabilities
   - Linting checks pass

2. **Manual Review**
   - Code review approval
   - Documentation review
   - Architecture compliance

3. **Quality Validation**
   - Performance benchmarks met
   - No breaking changes without migration
   - Backward compatibility maintained

### Blocking Conditions

PR is **blocked** if:
- Any test in critical path fails
- Coverage drops below threshold by >5%
- New security vulnerability introduced
- Performance regression >20%
- Documentation incomplete

### Warning Conditions

PR generates **warning** if:
- Coverage drops below threshold (≤5%)
- Flaky tests detected
- Non-critical dependencies outdated
- Minor performance regression (≤20%)

---

## Threshold Exceptions

### Emergency Exceptions

Temporary lowering of thresholds requires:
1. Architect approval
2. Documented rationale
3. Defined remediation plan
4. Maximum 7-day exception period

### Feature Exceptions

某些功能特性可能需要不同的阈值:
- Experimental features: 60% coverage
- Deprecated code: 50% coverage
- External integrations: Best effort testing

---

## Monitoring and Reporting

### Daily Reports

- Coverage trend (last 7 days)
- Test pass rates
- Flaky test list
- Performance benchmarks

### Weekly Reports

- Quality gate compliance rate
- PR merge time to compliance
- Threshold exception summary
- Remediation progress

### Alerting

Alerts generated for:
- Threshold violation
- Sudden coverage drop (>10%)
- New flaky tests
- Performance regression
- Security vulnerability

---

## Continuous Improvement

### Threshold Review Schedule

- **Monthly**: Review and adjust thresholds
- **Quarterly**: Comprehensive quality assessment
- **Annually**: Strategic quality planning

### Feedback Loop

1. Monitor metrics for 30 days post-change
2. Adjust thresholds based on data
3. Communicate changes to team
4. Update documentation

---

**Status:** ✅ Criteria Defined
**Next Step:** Implement threshold enforcement (Task 3.4.2)
