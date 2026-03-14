# Production Security Hardening Guide

## Overview

This document describes the Kubernetes Pod Security Standards implementation for Project Chimera, a multi-agent AI platform for live theatre. The implementation follows the [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) to achieve a production-ready security posture.

## Security Policy Levels

### Kubernetes Pod Security Standards

Project Chimera implements three tiers of security policies:

1. **Privileged**: Unrestricted access (system-level workloads only)
2. **Baseline**: Prevents privilege escalation (minimum for production applications)
3. **Restricted**: Hardening best practices (security-critical applications)

### Current Implementation

**Default Policy**: Baseline (enforced)
- All services must meet Baseline requirements
- Violations are blocked at pod creation time
- Auditing enabled for Restricted policy compliance tracking

**Exception Policy**: Privileged (lighting-control only)
- Lighting control service requires hardware access
- Documented security exception with justification
- Runs on dedicated hardware node for isolation

## Security Controls Implemented

### Baseline Policy Controls (All Services)

The following controls are enforced across all services:

#### Host Namespace Isolation
```yaml
spec:
  hostNetwork: false   # Cannot use host network namespace
  hostPID: false      # Cannot use host PID namespace
  hostIPC: false      # Cannot use host IPC namespace
```

#### Non-Root User Enforcement
```yaml
spec:
  securityContext:
    runAsNonRoot: true  # Containers must run as non-root user
    runAsUser: 1000     # Specific UID (or use UID from pod annotation)
    runAsGroup: 1000    # Specific GID
    fsGroup: 1000       # File system group
```

#### Privilege Escalation Prevention
```yaml
spec:
  containers:
  - securityContext:
      allowPrivilegeEscalation: false  # Prevent privilege escalation
      capabilities:
        drop:
        - ALL  # Drop all Linux capabilities
```

#### Seccomp Profile Enforcement
```yaml
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault  # Use runtime's default seccomp profile
```

#### Volume Type Restrictions
Only approved volume types are permitted:
- ConfigMap (for configuration)
- PersistentVolumeClaim (for persistent storage)
- EmptyDir (for ephemeral storage)
- Secret (for sensitive data)
- DownwardAPI (for pod metadata)
- CSI (for CSI-backed volumes)

**Forbidden volumes:**
- HostPath (except for lighting-control with documented exception)
- All other volume types

### Restricted Policy Controls (Future Goal)

The following controls are audited but not yet enforced:

1. **Volume Types**: Stricter enforcement of allowed volume types
2. **Capabilities**: Only NET_BIND_SERVICE should be added (not dropped)
3. **Privilege Escalation**: Must be explicitly set to false
4. **Seccomp**: Must be explicitly set (RuntimeDefault or Localhost)

## Service Security Matrix

### Standard Services (Baseline Policy)

| Service | Port | Security Level | Special Capabilities | Status |
|---------|------|----------------|---------------------|--------|
| openclaw-orchestrator | 8000 | Baseline | None | Compliant |
| scenespeak-agent | 8001 | Baseline | GPU access | Compliant |
| captioning-agent | 8002 | Baseline | GPU access | Compliant |
| bsl-agent | 8003 | Baseline | GPU access | Compliant |
| sentiment-agent | 8004 | Baseline | None | Compliant |
| safety-filter | 8006 | Baseline | None | Compliant |
| operator-console | 8007 | Baseline | None | Compliant |
| autonomous-agent | 8008 | Baseline | None | Compliant |

### Exception Services (Privileged Policy)

| Service | Port | Security Level | Justification | Mitigation |
|---------|------|----------------|--------------|------------|
| lighting-control | 8005 | Privileged | Hardware access for DMX/USB devices, sACN protocol (UDP 6454) | Dedicated hardware node, network isolation, strict node selection |

## GPU-Accelerated Services

The following services require GPU resources and have additional considerations:

- **scenespeak-agent**: LLM inference
- **captioning-agent**: Whisper speech-to-text
- **bsl-agent**: BSL avatar generation

### GPU Security Considerations

1. **Device Access**: GPU access is granted via device plugins, not privileged mode
2. **Node Affinity**: GPU services scheduled on specific GPU nodes
3. **Tolerations**: Services tolerate GPU-specific taints
4. **Resource Limits**: GPU resources explicitly requested and limited

These services maintain Baseline compliance while accessing GPU resources through Kubernetes device plugins.

## Deployment Procedure

### 1. Apply Pod Security Policies

```bash
# Apply namespace-level Pod Security Admission configuration
kubectl apply -f infrastructure/kubernetes/cluster/pod-security-policy.yaml
```

### 2. Update Service Manifests

All service manifests have been updated with security contexts. Apply them:

```bash
# Apply all service manifests
for service in services/*/manifests/k8s.yaml; do
  kubectl apply -f "$service"
done

# Apply autonomous-agent manifests
kubectl apply -f services/autonomous-agent/k8s-deployment.yaml
kubectl apply -f services/autonomous-agent/k8s-service.yaml
```

### 3. Verify Compliance

```bash
# Check for policy violations
kubectl get pods -n project-chimera --field-selector=status.phase!=Running

# View pod security violations
kubectl describe pod <pod-name> -n project-chimera | grep -A 10 "Warnings"

# Check audit log for Restricted policy violations
kubectl get events -n project-chimera --field-selector reason=Violation
```

### 4. Monitor Security Events

```bash
# Watch for security-restricted pod creation failures
kubectl get events -n project-chimera --watch | grep -i "security"

# Check pod security context
kubectl get pod <pod-name> -n project-chimera -o jsonpath='{.spec.securityContext}'
```

## Troubleshooting

### Common Issues

#### 1. Pod Creation Fails with "Forbidden" Error

**Symptom**: Pod cannot be created due to security policy violation

**Solution**:
```bash
# Check specific violation
kubectl describe pod <pod-name> -n project-chimera

# Common fixes:
# - Add runAsNonRoot: true
# - Add runAsUser: <uid>
# - Drop all capabilities
# - Set seccompProfile to RuntimeDefault
```

#### 2. Permission Denied Errors in Container

**Symptom**: Container cannot write to directories or files

**Solution**:
```yaml
spec:
  securityContext:
    runAsUser: 1000
    fsGroup: 1000
    runAsGroup: 1000
```

#### 3. GPU Services Fail to Start

**Symptom**: GPU-accelelerated services cannot access GPU

**Solution**: Ensure GPU device plugin is installed and resources are available:
```bash
# Check available GPU resources
kubectl describe nodes | grep nvidia.com/gpu

# Verify tolerations and node affinity in service manifest
```

### Validation Checklist

Before deploying to production:

- [ ] All services have securityContext defined at pod level
- [ ] All services have securityContext defined at container level
- [ ] runAsNonRoot is set to true
- [ ] runAsUser/runAsGroup are set to non-zero UIDs
- [ ] allowPrivilegeEscalation is false (except lighting-control)
- [ ] All capabilities are dropped
- [ ] seccompProfile is set to RuntimeDefault
- [ ] Host namespaces are disabled (hostNetwork, hostPID, hostIPC)
- [ ] HostPath volumes are avoided (except documented exceptions)
- [ ] GPU services have proper tolerations and node affinity
- [ ] Pod Security Admission labels are applied to namespace

## Security Monitoring

### Metrics to Monitor

1. **Policy Violations**: Track Baseline and Restricted violations
2. **Pod Security Events**: Monitor for privilege escalation attempts
3. **Container Failures**: Track security-related container startup failures
4. **Audit Logs**: Review Restricted policy violations for improvement

### Prometheus Alerts

Configure alerts for:
- Repeated policy violations
- Pods running with unexpected security contexts
- Privileged containers (except lighting-control)
- HostPath volume usage (except lighting-control)

## Future Improvements

### Path to Restricted Policy

To achieve Restricted compliance:

1. **Update Docker Images**: Ensure all services run as non-root by default
2. **Read-Only Root Filesystem**: Implement for all services
3. **Reduce Capabilities**: Only add NET_BIND_SERVICE where needed
4. **Volume Type Review**: Eliminate non-compliant volume types
5. **Seccomp Profiles**: Create custom profiles for each service

### Advanced Security Features

1. **Network Policies**: Implement service-to-service communication rules
2. **Service Mesh**: Add mTLS for service communication (Istio/Linkerd)
3. **Image Signing**: Verify container image signatures (Notary/cosign)
4. **Runtime Security**: Implement Falco for runtime threat detection
5. **Admission Controllers**: Add OPA/Gatekeeper for policy enforcement

## References

- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Security Contexts](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Seccomp Profiles](https://kubernetes.io/docs/tutorials/clusters/seccomp/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

## Appendix: Lighting Control Security Exception

### Justification

The lighting-control service requires privileged access for:

1. **DMX/USB Device Access**: Direct hardware communication with DMX interfaces
2. **sACN Protocol**: UDP traffic on port 6454 (streaming ACN protocol)
3. **Device Mount**: HostPath volume to `/dev` for device access

### Mitigation Strategies

1. **Dedicated Hardware**: Runs on node with `hardware: lighting-controller` label
2. **Network Isolation**: Separate network namespace for lighting infrastructure
3. **Strict Scheduling**: Node selector prevents scheduling on other nodes
4. **Limited Privileges**: Only this service has privileged access
5. **Monitoring**: Enhanced monitoring for anomalous behavior
6. **Future Improvement**: Investigate USB device plugins to eliminate privileged mode

### Compliance Path

To achieve Baseline compliance for lighting-control:

1. Implement custom CSI driver for USB/DMX devices
2. Use Device Plugins instead of privileged mode
3. Implement network policies for sACN traffic isolation
4. Remove HostPath volume usage

## Change History

- 2026-03-14: Initial implementation of Pod Security Standards
  - Applied Baseline policy to all services
  - Created security exception documentation for lighting-control
  - Implemented seccomp profiles and non-root user enforcement
  - Added comprehensive security documentation

## Contact

For security concerns or questions about this implementation:

- Security Team: security@project-chimera.org
- Infrastructure Team: infra@project-chimera.org
- Documentation: /docs/security/
