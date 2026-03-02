#!/bin/bash
# Project Chimera - Rollback Script
# Rolls back to the previous deployment

set -e

NAMESPACE=${1:-live}
SERVICE=${2:-all}

echo "Rolling back deployment in $NAMESPACE..."

if [ "$SERVICE" = "all" ]; then
    # Rollback all deployments
    for deployment in $(kubectl get deployments -n $NAMESPACE -o name); do
        echo "Rolling back $deployment..."
        kubectl rollout undo deployment/$deployment -n $NAMESPACE
    done
else
    # Rollback specific service
    kubectl rollout undo deployment/$SERVICE -n $NAMESPACE
fi

echo "Waiting for rollback to complete..."
kubectl rollout status deployment -n $NAMESPACE --timeout=10m

echo "Rollback complete!"
