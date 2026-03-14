# Security Hardening Validation Checklist

## Pre-Deployment Validation

### 1. File Changes Verification

- [ ] Pod Security Admission configuration created
  - [ ] File: `infrastructure/kubernetes/cluster/pod-security-policy.yaml`
  - [ ] Contains namespace labels for Baseline enforcement
  - [ ] Contains audit configuration for Restricted policy
  - [ ] Contains exception namespace for lighting-control

- [ ] Service manifests updated (9 services)
  - [ ] openclaw-orchestrator/manifests/k8s.yaml
  - [ ] scenespeak-agent/manifests/k8s.yaml
  - [ ] captioning-agent/manifests/k8s.yaml
  - [ ] bsl-agent/manifests/k8s.yaml
  - [ ] sentiment-agent/manifests/k8s.yaml
  - [ ] lighting-sound-music/manifests/k8s.yaml (with exception documentation)
  - [ ] safety-filter/manifests/k8s.yaml
  - [ ] operator-console/manifests/k8s.yaml
  - [ ] autonomous-agent/k8s-deployment.yaml

- [ ] Documentation created
  - [ ] docs/security/PRODUCTION_HARDENING_GUIDE.md
  - [ ] docs/security/SECURITY_QUICK_REFERENCE.md
  - [ ] SECURITY_HARDENING_SUMMARY.md

- [ ] Testing tools created
  - [ ] scripts/test-security-contexts.sh (executable)

### 2. Security Context Validation

For each standard service (8 services):

- [ ] `hostNetwork: false`
- [ ] `hostPID: false`
- [ ] `hostIPC: false`
- [ ] Pod-level `securityContext` present
- [ ] `runAsNonRoot: true`
- [ ] `runAsUser: 1000` (or non-zero UID)
- [ ] `runAsGroup: 1000`
- [ ] `fsGroup: 1000`
- [ ] `seccompProfile.type: RuntimeDefault`
- [ ] Container-level `securityContext` present
- [ ] `allowPrivilegeEscalation: false`
- [ ] `capabilities.drop: [ALL]`

For lighting-control service:

- [ ] Security exception documented in manifest
- [ ] Privileged mode justified in comments
- [ ] Mitigation strategies documented
- [ ] `hostNetwork: true` (exception)
- [ ] `privileged: true` (exception)
- [ ] Non-root user still enforced where possible

### 3. Pod Security Admission Validation

```bash
# Check namespace labels
kubectl get namespace project-chimera -o jsonpath='{.metadata.labels}' | jq .

# Verify these labels are present:
# - pod-security.kubernetes.io/enforce: baseline
# - pod-security.kubernetes.io/audit: restricted
# - pod-security.kubernetes.io/warn: restricted
```

- [ ] Namespace has enforce label set to baseline
- [ ] Namespace has audit label set to restricted
- [ ] Namespace has warn label set to restricted
- [ ] Exception namespace created for lighting-control (if applicable)

## Deployment Validation

### 4. Apply Changes

```bash
# Apply Pod Security Admission configuration
kubectl apply -f infrastructure/kubernetes/cluster/pod-security-policy.yaml
```

- [ ] Pod Security Admission configuration applied successfully
- [ ] Namespace labels verified

```bash
# Apply all service manifests
for service in openclaw-orchestrator scenespeak-agent captioning-agent bsl-agent sentiment-agent safety-filter operator-console; do
  kubectl apply -f services/$service/manifests/k8s.yaml
done
kubectl apply -f services/lighting-sound-music/manifests/k8s.yaml
kubectl apply -f services/autonomous-agent/k8s-deployment.yaml
kubectl apply -f services/autonomous-agent/k8s-service.yaml
```

- [ ] All service manifests applied successfully
- [ ] No syntax errors in manifests
- [ ] All deployments created/updated

### 5. Pod Startup Validation

```bash
# Check all pods are starting
kubectl get pods -n project-chimera
```

- [ ] All pods are in Running or ContainerCreating state
- [ ] No pods in Error state
- [ ] No pods stuck in Pending state due to security violations

### 6. Automated Security Testing

```bash
# Run security validation script
./scripts/test-security-contexts.sh
```

- [ ] Script runs without errors
- [ ] All standard services show green checks
- [ ] Lighting-control shows appropriate warnings
- [ ] No red failures (except expected exceptions)

### 7. Individual Service Validation

For each service, verify:

```bash
# Check pod security context
kubectl get pod <pod-name> -n project-chimera -o jsonpath='{.spec.securityContext}' | jq .

# Check container security context
kubectl get pod <pod-name> -n project-chimera -o jsonpath='{.spec.containers[0].securityContext}' | jq .
```

- [ ] All pods have pod-level securityContext
- [ ] All containers have container-level securityContext
- [ ] runAsNonRoot is true
- [ ] runAsUser is non-zero
- [ ] seccompProfile is RuntimeDefault
- [ ] allowPrivilegeEscalation is false (except lighting-control)
- [ ] Capabilities are dropped

## Functional Testing

### 8. Service Health Checks

```bash
# Check all services are healthy
kubectl get pods -n project-chimera -o json | jq -r '.items[] | select(.status.phase != "Running") | "\(.metadata.name): \(.status.phase)"'
```

- [ ] All services respond to health checks
- [ ] No 403 Forbidden errors due to permissions
- [ ] No permission denied errors in logs

### 9. Log Verification

```bash
# Check for permission errors
kubectl logs -n project-chimera -l app=<service-name> --tail=50 | grep -i "permission\|denied\|forbidden"
```

For each service:
- [ ] No permission denied errors
- [ ] No file system errors
- [ ] No capability-related errors
- [ ] Services start up successfully

### 10. GPU Services Validation

For scenespeak-agent, captioning-agent, bsl-agent:

- [ ] Services can access GPU resources
- [ ] No GPU-related errors in logs
- [ ] Services scheduled on GPU nodes
- [ ] GPU tolerations working correctly

### 11. Lighting Control Validation

For lighting-control service:

- [ ] Privileged mode is required and documented
- [ ] Service can access DMX/USB devices
- [ ] sACN protocol working (UDP 6454)
- [ ] Service scheduled on correct hardware node
- [ ] Security exception documented

## Post-Deployment Monitoring

### 12. Continuous Monitoring

```bash
# Watch for security events
kubectl get events -n project-chimera --watch | grep -i "security\|violation"
```

- [ ] Monitor for 24 hours after deployment
- [ ] Check for policy violations
- [ ] Verify no security-related errors
- [ ] Confirm all services stable

### 13. Performance Validation

- [ ] No performance degradation
- [ ] Resource limits within bounds
- [ ] No increased memory/CPU usage
- [ ] Service response times acceptable

### 14. Rollback Testing

Verify rollback procedure works:

```bash
# Test rollback for one service
kubectl rollout undo deployment/<service-name> -n project-chimera
```

- [ ] Rollback procedure documented
- [ ] Rollback tested successfully
- [ ] Re-deployment works after rollback

## Compliance Verification

### 15. Baseline Policy Compliance

- [ ] All standard services meet Baseline requirements
- [ ] No policy violations in audit logs
- [ ] Pod Security Admission enforcement working
- [ ] Exceptions documented and justified

### 16. Restricted Policy Audit

```bash
# Check Restricted policy violations
kubectl get events -n project-chimera --field-selector reason=Violation
```

- [ ] Audit log reviewed
- [ ] Violations documented for future improvement
- [ ] Critical violations addressed
- [ ] Path to Restricted compliance planned

## Documentation Verification

### 17. Documentation Completeness

- [ ] Production Hardening Guide is complete
- [ ] Quick Reference Guide is accurate
- [ ] Security exceptions documented
- [ ] Troubleshooting procedures tested
- [ ] Contact information correct

### 18. Team Training

- [ ] Operations team trained on new security contexts
- [ ] Development team aware of security requirements
- [ ] Runbooks updated for security incidents
- [ ] Monitoring dashboards updated

## Final Sign-Off

### 19. Approvals

- [ ] Security Team Lead approval
- [ ] Infrastructure Team Lead approval
- [ ] Operations Team approval
- [ ] Documentation review complete

### 20. Production Readiness

- [ ] All validation checks passed
- [ ] No critical issues identified
- [ ] Monitoring in place
- [ ] Rollback procedure tested
- [ ] Team trained and ready

## Issue Tracking

Record any issues found during validation:

| Issue | Service | Severity | Status | Resolution |
|-------|---------|----------|--------|------------|
|       |         |          |        |            |

## Notes

Additional observations or concerns:

```
(Record any additional notes here)
```

---

**Validation Date**: _______________
**Validated By**: _______________
**Approved By**: _______________
**Deployment Date**: _______________
