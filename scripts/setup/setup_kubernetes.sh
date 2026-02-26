#!/bin/bash
# Project Chimera - Kubernetes Setup Script
# This script deploys the infrastructure to a Kubernetes cluster

set -e

CLUSTER=${1:-dev}
NAMESPACE=${2:-live}

echo "Deploying Project Chimera to Kubernetes..."
echo "Cluster: $CLUSTER"
echo "Namespace: $NAMESPACE"

# Check kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found"
    exit 1
fi

# Create namespaces
echo "Creating namespaces..."
kubectl apply -f infrastructure/kubernetes/base/namespaces/

# Deploy shared services first
echo "Deploying shared services..."
kubectl apply -k infrastructure/kubernetes/overlays/$CLUSTER

# Wait for Redis
echo "Waiting for Redis..."
kubectl rollout status deployment/redis -n shared --timeout=5m

# Wait for Kafka
echo "Waiting for Kafka..."
kubectl rollout status deployment/kafka -n shared --timeout=5m

# Deploy live services
echo "Deploying live services..."
kubectl apply -f infrastructure/kubernetes/base/openclaw/
kubectl apply -f infrastructure/kubernetes/base/scenespeak/
kubectl apply -f infrastructure/kubernetes/base/captioning/
kubectl apply -f infrastructure/kubernetes/base/bsl-text2gloss/
kubectl apply -f infrastructure/kubernetes/base/sentiment/
kubectl apply -f infrastructure/kubernetes/base/lighting-control/
kubectl apply -f infrastructure/kubernetes/base/safety-filter/
kubectl apply -f infrastructure/kubernetes/base/operator-console/

# Wait for key services
echo "Waiting for OpenClaw..."
kubectl rollout status deployment/openclaw-orchestrator -n $NAMESPACE --timeout=10m

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Check status:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl get services -n $NAMESPACE"
