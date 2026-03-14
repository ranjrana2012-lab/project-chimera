# Project Chimera Security Documentation

This directory contains comprehensive security documentation for Project Chimera's Kubernetes deployment, implementing Pod Security Standards for production hardening.

## Quick Links

- [Production Hardening Guide](PRODUCTION_HARDENING_GUIDE.md) - Comprehensive security implementation guide
- [Security Quick Reference](SECURITY_QUICK_REFERENCE.md) - Quick commands and troubleshooting
- [Validation Checklist](VALIDATION_CHECKLIST.md) - Pre and post-deployment validation
- [Security Hardening Summary](../../SECURITY_HARDENING_SUMMARY.md) - Implementation overview

## Security Implementation Overview

Project Chimera implements **Baseline** Pod Security Standards across all 9 core services:

- ✅ **openclaw-orchestrator** (port 8000)
- ✅ **scenespeak-agent** (port 8001)
- ✅ **captioning-agent** (port 8002)
- ✅ **bsl-agent** (port 8003)
- ✅ **sentiment-agent** (port 8004)
- ⚠️ **lighting-control** (port 8005) - Security exception (hardware access)
- ✅ **safety-filter** (port 8006)
- ✅ **operator-console** (port 8007)
- ✅ **autonomous-agent** (port 8008)

## Security Controls

### Enforced Controls (Baseline)

All standard services implement:

```yaml
spec:
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
  - securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
```

### Key Security Features

1. **Non-Root User Enforcement**: All containers run as UID 1000
2. **Privilege Escalation Prevention**: `allowPrivilegeEscalation: false`
3. **Capability Dropping**: All Linux capabilities dropped
4. **Seccomp Profiles**: RuntimeDefault profile enforced
5. **Host Namespace Isolation**: Host network, PID, and IPC namespaces disabled
6. **Volume Restrictions**: Only approved volume types (ConfigMap, PVC, EmptyDir, Secret)

### Documented Exception

**lighting-control** service requires privileged access for:
- DMX/USB hardware communication
- sACN protocol (UDP port 6454)
- Professional lighting control systems

**Mitigation**: Dedicated hardware node, network isolation, strict node selection

## Deployment

### Quick Start

```bash
# Deploy all security hardening changes
./scripts/deploy-security-hardening.sh

# Validate security contexts
./scripts/test-security-contexts.sh
```

### Manual Deployment

```bash
# 1. Apply Pod Security Admission configuration
kubectl apply -f infrastructure/kubernetes/cluster/pod-security-policy.yaml

# 2. Apply service manifests
kubectl apply -f services/openclaw-orchestrator/manifests/k8s.yaml
kubectl apply -f services/scenespeak-agent/manifests/k8s.yaml
# ... (repeat for all services)

# 3. Validate deployment
kubectl get pods -n project-chimera
./scripts/test-security-contexts.sh
```

## Validation

### Automated Testing

```bash
# Run comprehensive security validation
./scripts/test-security-contexts.sh
```

This script validates:
- Host namespace isolation
- Non-root user enforcement
- Privilege escalation prevention
- Capability dropping
- Seccomp profile configuration
- HostPath volume usage
- Privileged container detection

### Manual Validation

```bash
# Check Pod Security Admission labels
kubectl get namespace project-chimera -o jsonpath='{.metadata.labels}' | jq .

# Verify pod security contexts
kubectl get pods -n project-chimera -o json | jq -r '.items[] | {name: .metadata.name, securityContext: .spec.securityContext}'

# Check for policy violations
kubectl get events -n project-chimera --field-selector reason=Violation
```

## Troubleshooting

### Common Issues

**Pod Won't Start (Permission Denied)**
```yaml
# Verify UID/GID permissions
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
```

**GPU Services Failing**
```bash
# Check GPU resources
kubectl describe nodes | grep nvidia.com/gpu

# Verify tolerations in manifest
```

**Policy Violation Errors**
```bash
# Check specific violation
kubectl describe pod <pod-name> -n project-chimera | grep -A 10 "Warnings"
```

For detailed troubleshooting, see [Production Hardening Guide](PRODUCTION_HARDENING_GUIDE.md#troubleshooting).

## Monitoring

### Key Metrics

Monitor these security-related metrics:

1. **Policy Violations**: Track Baseline and Restricted violations
2. **Pod Security Events**: Monitor for privilege escalation attempts
3. **Container Failures**: Track security-related container startup failures
4. **Audit Logs**: Review Restricted policy violations

### Prometheus Alerts

Configure alerts for:
- Repeated policy violations
- Pods running with unexpected security contexts
- Privileged containers (except lighting-control)
- HostPath volume usage (except lighting-control)

## Compliance

### Baseline Policy Compliance

✅ **All standard services meet Baseline requirements**

### Restricted Policy Compliance

⚠️ **Lighting-control service has documented exception**

📋 **Audit trail maintained for all security decisions**

## Future Improvements

### Path to Restricted Policy

1. Update Docker images to run as non-root by default
2. Implement read-only root filesystems
3. Reduce capabilities to only NET_BIND_SERVICE where needed
4. Eliminate non-compliant volume types
5. Create custom seccomp profiles for each service

### Advanced Security Features

1. **Network Policies**: Service-to-service communication rules
2. **Service Mesh**: mTLS for service communication (Istio/Linkerd)
3. **Image Signing**: Container image verification (Notary/cosign)
4. **Runtime Security**: Falco for runtime threat detection
5. **Admission Controllers**: OPA/Gatekeeper for policy enforcement

## Documentation Structure

```
docs/security/
├── README.md (this file)
├── PRODUCTION_HARDENING_GUIDE.md     - Comprehensive implementation guide
├── SECURITY_QUICK_REFERENCE.md       - Quick commands and reference
└── VALIDATION_CHECKLIST.md           - Deployment validation checklist

scripts/
├── deploy-security-hardening.sh      - Automated deployment script
└── test-security-contexts.sh         - Security validation script

infrastructure/kubernetes/cluster/
└── pod-security-policy.yaml          - Pod Security Admission configuration

SECURITY_HARDENING_SUMMARY.md         - Implementation summary (project root)
```

## Support

For security questions or concerns:

- **Security Team**: security@project-chimera.org
- **Infrastructure Team**: infra@project-chimera.org
- **Documentation**: See individual guides above

## External References

- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [Seccomp Profiles](https://kubernetes.io/docs/tutorials/clusters/seccomp/)

## Version History

- **2026-03-14**: Initial implementation of Pod Security Standards
  - Applied Baseline policy to all services
  - Created security exception documentation for lighting-control
  - Implemented seccomp profiles and non-root user enforcement
  - Added comprehensive security documentation and testing tools

---

**Last Updated**: 2026-03-14
**Next Review**: 2026-04-14 (30 days)
**Status**: ✅ Production Ready
