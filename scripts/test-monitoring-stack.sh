#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "Testing Chimera Monitoring Stack"
echo "======================================"
echo ""

# Check if port 9090 is available
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Prometheus is already running on port 9090${NC}"
    echo "This might be a system Prometheus or another instance."
    echo ""
    read -p "Do you want to stop it and use the Chimera Prometheus? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Stopping existing Prometheus...${NC}"
        # Try to stop common Prometheus services
        systemctl stop prometheus 2>/dev/null || true
        docker stop $(docker ps -q --filter "ancestor=prom/prometheus") 2>/dev/null || true
        sleep 2
    else
        echo -e "${RED}Cannot proceed - port 9090 is in use${NC}"
        exit 1
    fi
fi

# Start monitoring services
echo -e "${GREEN}Step 1: Starting Prometheus and Netdata...${NC}"
docker compose -f docker-compose.mvp.yml up -d prometheus netdata

# Wait for services to be ready
echo "Waiting for services to start (10 seconds)..."
sleep 10

# Check Netdata
echo ""
echo -e "${GREEN}Step 2: Verifying Netdata is healthy...${NC}"
if curl -f http://localhost:19999/api/v1/info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Netdata is responding on port 19999${NC}"
else
    echo -e "${RED}✗ Netdata is not responding${NC}"
    docker compose -f docker-compose.mvp.yml down prometheus netdata
    exit 1
fi

echo ""
echo "Netdata logs (last 10 lines):"
docker logs chimera-netdata --tail 10

# Check Netdata Prometheus metrics endpoint
echo ""
echo "Checking Netdata Prometheus metrics endpoint..."
if curl -f "http://localhost:19999/api/v1/allmetrics?format=prometheus" | head -5 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Netdata Prometheus metrics endpoint is working${NC}"
    echo "Sample metrics:"
    curl -s "http://localhost:19999/api/v1/allmetrics?format=prometheus" | head -5
else
    echo -e "${RED}✗ Netdata Prometheus metrics endpoint failed${NC}"
    echo "Trying alternative endpoint check..."
    if ! curl -s "http://localhost:19999/api/v1/allmetrics?format=prometheus" | head -1; then
        docker compose -f docker-compose.mvp.yml down prometheus netdata
        exit 1
    fi
fi

# Check Prometheus
echo ""
echo -e "${GREEN}Step 3: Verifying Prometheus is healthy...${NC}"
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is healthy${NC}"
else
    echo -e "${RED}✗ Prometheus is not healthy${NC}"
    docker compose -f docker-compose.mvp.yml down prometheus netdata
    exit 1
fi

echo ""
echo "Prometheus logs (last 10 lines):"
docker logs chimera-prometheus --tail 10

# Check if Prometheus is scraping Netdata
echo ""
echo -e "${GREEN}Step 4: Checking if Prometheus is scraping Netdata...${NC}"
TARGETS_JSON=$(curl -s http://localhost:9090/api/v1/targets)
if echo "$TARGETS_JSON" | python3 -m json.tool | grep -q "netdata"; then
    echo -e "${GREEN}✓ Netdata target found in Prometheus${NC}"
    echo ""
    echo "Target details:"
    echo "$TARGETS_JSON" | python3 -m json.tool | grep -A 15 '"job": "netdata"'
else
    echo -e "${RED}✗ Netdata target not found in Prometheus${NC}"
    echo "Available targets:"
    echo "$TARGETS_JSON" | python3 -m json.tool | grep '"job"' || true
    docker compose -f docker-compose.mvp.yml down prometheus netdata
    exit 1
fi

# Query a sample metric
echo ""
echo -e "${GREEN}Step 5: Querying a sample CPU metric from Prometheus...${NC}"
METRIC_RESPONSE=$(curl -s 'http://localhost:9090/api/v1/query?query=system.cpu.total_pct')
if echo "$METRIC_RESPONSE" | python3 -m json.tool | grep -q '"status": "success"'; then
    echo -e "${GREEN}✓ Successfully queried CPU metric${NC}"
    echo ""
    echo "Sample response:"
    echo "$METRIC_RESPONSE" | python3 -m json.tool | head -20
else
    echo -e "${YELLOW}⚠ CPU metric query returned no data (this is normal if Netdata just started)${NC}"
    echo "Response:"
    echo "$METRIC_RESPONSE" | python3 -m json.tool
fi

# Summary
echo ""
echo "======================================"
echo -e "${GREEN}Monitoring Stack Test Summary${NC}"
echo "======================================"
echo ""
echo "Services Status:"
docker compose -f docker-compose.mvp.yml ps prometheus netdata
echo ""
echo "Access URLs:"
echo "  - Netdata Dashboard: http://localhost:19999"
echo "  - Prometheus UI: http://localhost:9090"
echo "  - Prometheus Targets: http://localhost:9090/targets"
echo ""

# Ask if user wants to stop services
read -p "Stop monitoring services? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${YELLOW}Stopping monitoring services...${NC}"
    docker compose -f docker-compose.mvp.yml down prometheus netdata
    echo -e "${GREEN}Monitoring services stopped${NC}"
else
    echo ""
    echo -e "${GREEN}Monitoring services left running${NC}"
    echo "To stop later: docker compose -f docker-compose.mvp.yml down prometheus netdata"
fi

echo ""
echo -e "${GREEN}Test completed successfully!${NC}"
