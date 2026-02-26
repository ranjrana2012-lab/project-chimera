#!/bin/bash

echo ""
echo "❌ Bootstrap failed. Cleaning up..."
echo ""

pkill -f "port-forward" || true

echo ""
read -p "Remove k3s and all resources? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⏳ Removing k3s..."
    /usr/local/bin/k3s-uninstall.sh 2>/dev/null || true
    echo "🧹 k3s removed"
    rm -f ~/.kube/config
    echo "🧹 Kubeconfig removed"
else
    echo "⚠️  k3s left intact for debugging"
    echo ""
    echo "💡 Debug commands:"
    echo "   kubectl get pods -A"
    echo "   kubectl get svc -A"
    echo "   journalctl -u k3s -n 50"
fi

echo ""
echo "📋 Bootstrap log location: /tmp/project-chimera-bootstrap.log"
exit 1
