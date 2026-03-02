#!/bin/bash
# Demo Preparation Script - Run before 4pm demo
# Checks and starts all required services

set -e

echo "=== Project Chimera Demo Preparation ==="
echo "Checking services..."

# Check k3s is running
if ! sudo k3s kubectl get nodes &>/dev/null; then
    echo "❌ k3s is not running"
    echo "Start with: sudo systemctl start k3s"
    exit 1
fi
echo "✅ k3s is running"

# Function to check a service
check_service() {
    local port=$1
    local name=$2
    if curl -s "http://localhost:${port}/health/live" &>/dev/null; then
        echo "✅ $name (port $port) is running"
        return 0
    else
        echo "❌ $name (port $port) is NOT responding"
        return 1
    fi
}

# Check all services
SERVICES_OK=true
check_service 8000 "OpenClaw Orchestrator" || SERVICES_OK=false
check_service 8001 "SceneSpeak Agent" || SERVICES_OK=false
check_service 8002 "Captioning Agent" || SERVICES_OK=false
check_service 8003 "BSL Translation Agent" || SERVICES_OK=false
check_service 8004 "Sentiment Agent" || SERVICES_OK=false
check_service 8005 "Lighting Control" || SERVICES_OK=false
check_service 8006 "Safety Filter" || SERVICES_OK=false
check_service 8007 "Operator Console" || SERVICES_OK=false

if [ "$SERVICES_OK" = false ]; then
    echo ""
    echo "Some services are not running. Start services with:"
    echo "  make bootstrap"
    echo "Or individual services:"
    echo "  cd services/<service-name> && source venv/bin/activate && python -m uvicorn main:app --port <port>"
    exit 1
fi

echo ""
echo "=== All Systems Ready for Demo! ==="
echo ""
echo "Quick health checks:"
echo "  curl http://localhost:8000/health/live"
echo "  curl http://localhost:8001/health/live"
echo ""
echo "Port forwards (if needed):"
sudo k3s kubectl port-forward -n chimera svc/openclaw 8000:8000 &
sudo k3s kubectl port-forward -n chimera svc/scenespeak 8001:8001 &
