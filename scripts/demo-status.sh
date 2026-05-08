#!/bin/bash

# Project Chimera Demo Status Script
# Checks the status of all demo services

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================"
echo "Project Chimera Demo Status"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
ALL_OK=true

echo "Docker Containers:"
echo "------------------"
docker-compose ps 2>/dev/null || {
    echo -e "${RED}ERROR: Docker Compose services not running${NC}"
    echo "Start services with: ./scripts/demo-start.sh"
    exit 1
}

echo ""
echo "Service Health Checks:"
echo "---------------------"

# Function to check service health
check_service() {
    local name=$1
    local port=$2
    local url=$3

    echo -n "  $name (port $port): "

    # Check if port is listening
    if ! nc -zv localhost $port 2>&1 | grep -q succeeded; then
        echo -e "${RED}NOT LISTENING${NC}"
        ALL_OK=false
        return 1
    fi

    # Check health endpoint
    if [ -n "$url" ]; then
        response=$(curl -sf "http://localhost:${port}${url}" 2>&1) || {
            echo -e "${RED}HEALTH CHECK FAILED${NC}"
            ALL_OK=false
            return 1
        }

        # Try to parse status from JSON response
        status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$status" ]; then
            if [ "$status" = "healthy" ] || [ "$status" = "ok" ]; then
                echo -e "${GREEN}$status${NC}"
            else
                echo -e "${YELLOW}$status${NC}"
                ALL_OK=false
            fi
        else
            echo -e "${GREEN}OK${NC}"
        fi
    else
        echo -e "${GREEN}RUNNING${NC}"
    fi

    return 0
}

# Check all core services
check_service "OpenClaw Orchestrator" 8000 "/health/live"
check_service "SceneSpeak" 8001 "/health/live"
check_service "Captioning Service" 8002 "/health/live"
check_service "BSL Agent" 8003 "/health/live"
check_service "Sentiment Analysis" 8004 "/health/live"
check_service "LSM Service" 8005 "/health/live"
check_service "Safety Filter" 8006 "/health/live"
check_service "Operator Console" 8007 "/health/live"

echo ""
echo "Infrastructure Services:"
echo "-----------------------"

check_service "NATS" 4222 ""
check_service "NATS Streaming" 8222 ""
check_service "Prometheus" 9090 "/-/healthy"
check_service "Grafana" 3000 "/api/health"
check_service "Jaeger" 16686 "/api/health"

echo ""
echo "Quick API Tests:"
echo "----------------"

# Test orchestrator API
echo -n "  Orchestrator API: "
if response=$(curl -sf -X POST http://localhost:8000/v1/orchestrate \
    -H "Content-Type: application/json" \
    -d '{"skill": "health_check", "input": {}}' 2>&1); then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    ALL_OK=false
fi

# Test SceneSpeak API
echo -n "  SceneSpeak API: "
if response=$(curl -sf http://localhost:8001/health/live 2>&1); then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    ALL_OK=false
fi

# Test Safety Filter API
echo -n "  Safety Filter API: "
if response=$(curl -sf -X POST http://localhost:8006/v1/check \
    -H "Content-Type: application/json" \
    -d '{"text": "Hello world", "policy": "family"}' 2>&1); then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    ALL_OK=false
fi

echo ""
echo "System Resources:"
echo "-----------------"

# Check memory
MEMORY_TOTAL=$(free -h | awk '/^Mem:/{print $2}')
MEMORY_USED=$(free -h | awk '/^Mem:/{print $3}')
MEMORY_PERCENT=$(free | awk '/^Mem:/{printf("%.0f"), $3/$2*100}')
echo "  Memory: $MEMORY_USED / $MEMORY_TOTAL ($MEMORY_PERCENT%)"

# Check disk
DISK_TOTAL=$(df -h . | tail -1 | awk '{print $2}')
DISK_USED=$(df -h . | tail -1 | awk '{print $3}')
DISK_PERCENT=$(df -h . | tail -1 | awk '{print $5}')
echo "  Disk:   $DISK_USED / $DISK_TOTAL ($DISK_PERCENT)"

# Check Docker resource usage
echo "  Docker Containers:"
docker stats --no-stream --format "    {{.Name}}: {{.CPUPerc}} CPU, {{.MemUsage}} RAM" 2>/dev/null || echo "    (stats not available)"

echo ""
echo "Demo Readiness:"
echo "---------------"

# Check demo materials
DEMO_MATERIALS_OK=true

if [ -f "docs/demo/demo-script.md" ]; then
    echo -e "  ${GREEN}✓${NC} Demo script available"
else
    echo -e "  ${RED}✗${NC} Demo script missing"
    DEMO_MATERIALS_OK=false
    ALL_OK=false
fi

if [ -f "examples/sample-request.py" ]; then
    echo -e "  ${GREEN}✓${NC} Sample requests available"
else
    echo -e "  ${RED}✗${NC} Sample requests missing"
    DEMO_MATERIALS_OK=false
    ALL_OK=false
fi

if [ -f "examples/demo-scenario.json" ]; then
    echo -e "  ${GREEN}✓${NC} Demo scenario available"
else
    echo -e "  ${YELLOW}⚠${NC} Demo scenario missing"
    DEMO_MATERIALS_OK=false
fi

echo ""

# Summary
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}ALL SYSTEMS READY FOR DEMO!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "The demo environment is fully operational."
    echo ""
    echo "Access URLs:"
    echo "  Operator Console:  http://localhost:8007"
    echo "  Grafana:          http://localhost:3000"
    echo "  Jaeger:           http://localhost:16686"
    echo ""
    echo "Demo checklist:"
    echo "  [x] All services running"
    echo "  [x] Health checks passing"
    echo "  [x] API endpoints responding"
    echo "  [x] Infrastructure ready"
    echo "  [x] Demo materials available"
    echo ""
    echo "You're ready to start the demo!"
    exit 0
else
    echo -e "${RED}================================${NC}"
    echo -e "${RED}DEMO ENVIRONMENT NOT READY${NC}"
    echo -e "${RED}================================${NC}"
    echo ""
    echo "Some services are not ready. Please check:"
    echo ""
    echo "1. Service logs: docker-compose logs -f [service-name]"
    echo "2. Restart services: ./scripts/demo-start.sh"
    echo "3. Check troubleshooting: cat docs/demo/troubleshooting.md"
    echo ""
    exit 1
fi
