#!/bin/bash

NAMESPACE="live"
echo "⏳ [7/7] Verifying deployment..."

PODS_NOT_READY=$(kubectl get pods -n $NAMESPACE --no-headers | grep -v "Running\|Completed" | wc -l)
if [ "$PODS_NOT_READY" -gt 0 ]; then
    echo "⏳ Waiting for pods to stabilize..."
    sleep 30
fi

echo "🌊 Live namespace:"
kubectl get pods -n $NAMESPACE
echo ""
echo "🌊 Shared namespace:"
kubectl get pods -n shared

echo ""
echo "🎉 Project Chimera bootstrap complete!"
echo "📊 Grafana: http://localhost:3000 (admin/admin)"
echo "📊 Prometheus: http://localhost:9090"
echo "📊 Jaeger: http://localhost:16686"
echo ""
echo "🔌 make run-openclaw | make run-scenespeak | make logs"
echo "✅ [7/7] Verification complete"
