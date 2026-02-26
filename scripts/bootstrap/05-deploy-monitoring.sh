#!/bin/bash
set -e

NAMESPACE="shared"
echo "⏳ [5/7] Deploying monitoring stack..."

kubectl apply -k infrastructure/kubernetes/base/monitoring/prometheus/ -n $NAMESPACE
kubectl apply -k infrastructure/kubernetes/base/monitoring/grafana/ -n $NAMESPACE
kubectl apply -k infrastructure/kubernetes/base/monitoring/jaeger/ -n $NAMESPACE

kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=prometheus --timeout=180s || echo "⚠️  Prometheus not ready"
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=grafana --timeout=180s || echo "⚠️  Grafana not ready"
kubectl wait --for=condition=ready -n $NAMESPACE pod -l app=jaeger --timeout=180s || echo "⚠️  Jaeger not ready"

pkill -f "port-forward.*prometheus" || true
pkill -f "port-forward.*grafana" || true
pkill -f "port-forward.*jaeger" || true

kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090 > /dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000 > /dev/null 2>&1 &
kubectl port-forward -n $NAMESPACE svc/jaeger 16686:16686 > /dev/null 2>&1 &

sleep 3
echo "✅ Port forwards active"
echo "📊 Grafana: http://localhost:3000 (admin/admin)"
echo "✅ [5/7] Monitoring deployment complete"
