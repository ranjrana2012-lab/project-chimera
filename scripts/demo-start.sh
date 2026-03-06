#!/bin/bash

# Project Chimera Demo Start Script
# Starts all services for the demo in the correct order

set -e

PROJECT_ROOT="/home/ranj/Project_Chimera"
cd "$PROJECT_ROOT"

echo "================================"
echo "Starting Project Chimera Demo"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if demo-prep.sh has been run
if [ ! -d "logs/demo" ]; then
    echo -e "${YELLOW}WARNING: demo-prep.sh may not have been run${NC}"
    echo "Running preparation checks..."
    ./scripts/demo-prep.sh
fi

# Function to wait for service to be healthy
wait_for_service() {
    local name=$1
    local port=$2
    local max_attempts=30
    local attempt=1

    echo -n "  Waiting for $name (port $port)..."
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "http://localhost:${port}/health/live" > /dev/null 2>&1; then
            echo -e " ${GREEN}READY${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done

    echo -e " ${RED}FAILED${NC}"
    echo "  $name did not become healthy in time"
    return 1
}

# Step 1: Start infrastructure services first
echo "Step 1: Starting infrastructure services..."
echo ""

echo "  Starting NATS..."
docker-compose up -d nats 2>&1 | grep -v "WARNING" || true
sleep 2
echo -e "  ${GREEN}✓ NATS started${NC}"

echo "  Starting Prometheus..."
docker-compose up -d prometheus 2>&1 | grep -v "WARNING" || true
sleep 2
echo -e "  ${GREEN}✓ Prometheus started${NC}"

echo "  Starting Grafana..."
docker-compose up -d grafana 2>&1 | grep -v "WARNING" || true
sleep 2
echo -e "  ${GREEN}✓ Grafana started${NC}"

echo "  Starting Jaeger..."
docker-compose up -d jaeger 2>&1 | grep -v "WARNING" || true
sleep 2
echo -e "  ${GREEN}✓ Jaeger started${NC}"

echo ""
echo "Step 2: Starting core services..."
echo ""

# Start core services in parallel for faster startup
echo "  Starting SceneSpeak..."
docker-compose up -d scenespeak 2>&1 | grep -v "WARNING" || true

echo "  Starting Captioning Service..."
docker-compose up -d captioning 2>&1 | grep -v "WARNING" || true

echo "  Starting BSL Agent..."
docker-compose up -d bsl 2>&1 | grep -v "WARNING" || true

echo "  Starting Sentiment Analysis..."
docker-compose up -d sentiment 2>&1 | grep -v "WARNING" || true

echo "  Starting LSM Service..."
docker-compose up -d lsm 2>&1 | grep -v "WARNING" || true

echo "  Starting Safety Filter..."
docker-compose up -d safety 2>&1 | grep -v "WARNING" || true

# Wait for AI services to be ready
echo ""
echo "  Waiting for AI services to initialize..."
sleep 10

echo ""
echo "Step 3: Starting orchestrator..."
docker-compose up -d orchestrator 2>&1 | grep -v "WARNING" || true

echo ""
echo "Step 4: Starting operator console..."
docker-compose up -d console 2>&1 | grep -v "WARNING" || true

echo ""
echo "Step 5: Verifying service health..."
echo ""

# Verify all services are healthy
ALL_HEALTHY=true

wait_for_service "OpenClaw Orchestrator" 8000 || ALL_HEALTHY=false
wait_for_service "SceneSpeak" 8001 || ALL_HEALTHY=false
wait_for_service "Captioning Service" 8002 || ALL_HEALTHY=false
wait_for_service "BSL Agent" 8003 || ALL_HEALTHY=false
wait_for_service "Sentiment Analysis" 8004 || ALL_HEALTHY=false
wait_for_service "LSM Service" 8005 || ALL_HEALTHY=false
wait_for_service "Safety Filter" 8006 || ALL_HEALTHY=false
wait_for_service "Operator Console" 8007 || ALL_HEALTHY=false

echo ""

if [ "$ALL_HEALTHY" = false ]; then
    echo -e "${RED}ERROR: Some services failed to start${NC}"
    echo ""
    echo "Checking logs for failed services..."
    docker-compose logs --tail=20
    exit 1
fi

echo "Step 6: Testing connectivity..."
echo ""

# Test NATS connection
if docker exec chimera-orchestrator nc -zv nats 4222 2>&1 | grep -q succeeded; then
    echo -e "  ${GREEN}✓ NATS connection verified${NC}"
else
    echo -e "  ${YELLOW}⚠ Could not verify NATS connection${NC}"
fi

# Test Prometheus scraping
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Prometheus healthy${NC}"
else
    echo -e "  ${YELLOW}⚠ Prometheus not healthy${NC}"
fi

# Test Grafana
if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Grafana accessible${NC}"
else
    echo -e "  ${YELLOW}⚠ Grafana not accessible${NC}"
fi

# Test Jaeger
if curl -sf http://localhost:16686/api/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Jaeger accessible${NC}"
else
    echo -e "  ${YELLOW}⚠ Jaeger not accessible${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}Demo Environment Ready!${NC}"
echo "================================"
echo ""
echo "All services are running and healthy!"
echo ""
echo "Access URLs:"
echo -e "  ${BLUE}Operator Console:${NC}  http://localhost:8007"
echo -e "  ${BLUE}Grafana:${NC}          http://localhost:3000 (admin/admin)"
echo -e "  ${BLUE}Jaeger:${NC}           http://localhost:16686"
echo -e "  ${BLUE}Prometheus:${NC}       http://localhost:9090"
echo ""
echo "Service Endpoints:"
echo "  Orchestrator:    http://localhost:8000"
echo "  SceneSpeak:      http://localhost:8001"
echo "  Captioning:      http://localhost:8002"
echo "  BSL:             http://localhost:8003"
echo "  Sentiment:       http://localhost:8004"
echo "  LSM:             http://localhost:8005"
echo "  Safety:          http://localhost:8006"
echo ""
echo "Next steps:"
echo "  1. Run health checks:  ./scripts/demo-status.sh"
echo "  2. Open Operator Console in browser"
echo "  3. Run sample requests: python examples/sample-request.py"
echo "  4. Follow demo script:  cat docs/demo/demo-script.md"
echo ""
echo "To stop all services:"
echo "  docker-compose down"
echo ""

# Optional: Open browser tabs
read -p "Open browser tabs? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8007
        xdg-open http://localhost:3000
        xdg-open http://localhost:16686
    elif command -v open &> /dev/null; then
        open http://localhost:8007
        open http://localhost:3000
        open http://localhost:16686
    else
        echo "Could not open browser. Please open URLs manually."
    fi
fi

echo ""
echo -e "${GREEN}Demo start complete!${NC}"
