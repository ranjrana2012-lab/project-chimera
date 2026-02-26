#!/bin/bash
# Project Chimera - Deployment Script
# Deploys services to Kubernetes

set -e

ENV=${1:-dev}
NAMESPACE=${2:-live}

echo "Deploying to $ENV environment..."

# Build and push images (if using local registry)
# docker build -t chimera-$ENV:latest .

# Apply Kustomize overlay
kubectl apply -k infrastructure/kubernetes/overlays/$ENV

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=600s \
    deployment/-n $NAMESPACE --all

echo "Deployment complete!"
echo ""
echo "Services:"
kubectl get services -n $NAMESPACE
