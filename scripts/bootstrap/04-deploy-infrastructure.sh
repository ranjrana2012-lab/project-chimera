#!/bin/bash
set -e

NAMESPACE="shared"
echo "⏳ [4/7] Deploying shared infrastructure..."

kubectl apply -k infrastructure/kubernetes/base/redis/ -n $NAMESPACE
kubectl apply -k infrastructure/kubernetes/base/kafka/ -n $NAMESPACE
kubectl apply -k infrastructure/kubernetes/base/vector-db/ -n $NAMESPACE

kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=redis --timeout=180s || echo "⚠️  Redis not ready"
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=kafka --timeout=180s || echo "⚠️  Kafka not ready"
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=milvus --timeout=180s || echo "⚠️  Milvus not ready"

echo "✅ Shared infrastructure deployed"
kubectl get svc -n $NAMESPACE
echo "✅ [4/7] Infrastructure deployment complete"
