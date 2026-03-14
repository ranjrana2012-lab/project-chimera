# Security Quick Reference

## Pod Security Standards at a Glance

### Policy Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **Privileged** | Unrestricted access | System-level workloads only |
| **Baseline** | Prevents privilege escalation | Standard production applications |
| **Restricted** | Maximum security hardening | Security-critical applications |

### Current Policy

**Enforced**: Baseline
**Audited**: Restricted
**Exception**: lighting-control (Privileged - documented)

## Quick Commands

### Check Pod Security

```bash
# Check a pod's security context
kubectl get pod <pod-name> -n project-chimera -o jsonpath='{.spec.securityContext}'

# Check all pods for compliance
kubectl get pods -n project-chimera -o json | jq -r '.items[] | "\(.metadata.name): \(.spec.securityContext.runAsNonRoot)"'

# View security violations
kubectl describe pod <pod-name> -n project-chimera | grep -A 10 "Warnings"
```

### Test Security Compliance

```bash
# Run security validation script
./scripts/test-security-contexts.sh

# Check for policy violations
kubectl get pods -n project-chimera --field-selector=status.phase!=Running

# View audit log for Restricted violations
kubectl get events -n project-chimera --field-selector reason=Violation
```

### Apply Security Policies

```bash
# Apply Pod Security Admission configuration
kubectl apply -f infrastructure/kubernetes/cluster/pod-security-policy.yaml

# Apply all service manifests with security contexts
kubectl apply -f services/openclaw-orchestrator/manifests/k8s.yaml
kubectl apply -f services/scenespeak-agent/manifests/k8s.yaml
# ... (repeat for all services)
```

## Security Context Template

```yaml
spec:
  # Pod-level security
  hostNetwork: false
  hostPID: false
  hostIPC: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: my-service
    # Container-level security
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
```

## Troubleshooting

### Pod Won't Start (Permission Denied)

**Check**: UID/GID permissions
```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
```

### GPU Services Failing

**Check**: Tolerations and node affinity
```yaml
tolerations:
- key: nvidia.com/gpu
  operator: Exists
  effect: NoSchedule
nodeAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    nodeSelectorTerms:
    - matchExpressions:
      - key: nvidia.com/gpu.product
        operator: In
        values:
        - NVIDIA_GB10
```

### Policy Violation Errors

**Check**: Pod Security Admission labels
```bash
kubectl get namespace project-chimera -o json | jq -r '.metadata.labels'
```

## Service-Specific Notes

### GPU Services (scenespeak-agent, captioning-agent, bsl-agent)
- Require GPU resources
- Maintain Baseline compliance
- Use device plugins (not privileged mode)

### Lighting Control (lighting-control)
- **Security Exception**: Requires privileged access
- **Reason**: Hardware communication (DMX/USB, sACN protocol)
- **Mitigation**: Dedicated hardware node, network isolation
- **Status**: Documented exception

### All Other Services
- Must run as non-root (UID 1000)
- Must drop all capabilities
- Must use RuntimeDefault seccomp profile
- Cannot use HostPath volumes

## Validation Checklist

Before deploying to production:

- [ ] Namespace has Pod Security Admission labels
- [ ] All pods have securityContext at pod level
- [ ] All pods have securityContext at container level
- [ ] runAsNonRoot is true (except lighting-control)
- [ ] allowPrivilegeEscalation is false (except lighting-control)
- [ ] All capabilities are dropped
- [ ] seccompProfile is RuntimeDefault
- [ ] Host namespaces are disabled
- [ ] No HostPath volumes (except lighting-control)
- [ ] GPU services have proper tolerations

## Resources

- Full Guide: `docs/security/PRODUCTION_HARDENING_GUIDE.md`
- Test Script: `scripts/test-security-contexts.sh`
- Policy Config: `infrastructure/kubernetes/cluster/pod-security-policy.yaml`
- K8s Docs: https://kubernetes.io/docs/concepts/security/pod-security-standards/

## Emergency Procedures

### Rollback Security Contexts

If services fail after security hardening:

```bash
# Rollback to previous version
kubectl rollout undo deployment/<service-name> -n project-chimera

# Check specific pod errors
kubectl logs <pod-name> -n project-chimera --previous

# Temporarily disable enforcement (emergency only)
kubectl label namespace project-chimera pod-security.kubernetes.io/enforce- --overwrite
```

### Contact

- Security Issues: security@project-chimera.org
- Infrastructure Issues: infra@project-chimera.org
- Documentation: See `docs/security/` directory
