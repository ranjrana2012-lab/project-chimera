# Security Hardening Guide

## Network Security

- Network policies deny all by default
- Service-to-service communication controlled
- Ingress only via nginx-ingress

## Pod Security

- Run as non-root user (UID 1000)
- Read-only root filesystem where possible
- Drop all Linux capabilities
- Seccomp profile: runtime/default

## Secrets Management

- Use Sealed Secrets for Kubernetes
- Store secrets in Git (encrypted)
- Rotate secrets every 90 days

## Image Security

- Scan images with Trivy
- Block images with high/critical vulnerabilities
- Use minimal base images

## Access Control

- RBAC configured per namespace
- Service accounts with minimal permissions
- Audit logging enabled
