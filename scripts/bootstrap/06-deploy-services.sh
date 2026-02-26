#!/bin/bash
set -e

REGISTRY="localhost:30500"
NAMESPACE="live"
echo "⏳ [6/7] Deploying AI services..."

for service in openclaw-orchestrator scenespeak-agent captioning-agent bsl-text2gloss-agent sentiment-agent lighting-control safety-filter operator-console; do
    if [ -f "infrastructure/kubernetes/base/$service/deployment.yaml" ]; then
        echo "⏳ Deploying $service..."
        kubectl apply -f infrastructure/kubernetes/base/$service/deployment.yaml -n $NAMESPACE
        kubectl apply -f infrastructure/kubernetes/base/$service/service.yaml -n $NAMESPACE
        kubectl rollout status deployment/$service -n $NAMESPACE --timeout=300s || echo "⚠️  $service timeout"
        echo "✅ $service deployed"
    fi
done

echo "✅ All AI services deployed"
kubectl get pods -n $NAMESPACE
echo "✅ [6/7] Services deployment complete"
