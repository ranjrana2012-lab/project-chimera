# ADR-001: Use k3s for Kubernetes

## Status
Accepted

## Date
2026-02-26

## Context
Project Chimera requires a Kubernetes cluster for development and deployment. Options include:
- Full Kubernetes (complex, resource-intensive)
- Minikube (designed for local dev only)
- k3s (lightweight, production-capable)
- Managed services (EKS, GKE, AKS)

## Decision
Use **k3s** as the Kubernetes distribution for Project Chimera.

### Rationale

**Pros:**
- Lightweight (~500MB binary)
- Quick installation and setup
- Supports all essential Kubernetes features
- Production-ready (used by edge computing deployments)
- Low resource overhead
- GPU passthrough support

**Cons:**
- Not suitable for very large clusters (>1000 nodes)
- Some advanced features not available (not needed for this project)

## Consequences

- Development environment can run on a single DGX Spark
- Production can use the same distribution or migrate to managed services
- All team members use consistent Kubernetes environment
