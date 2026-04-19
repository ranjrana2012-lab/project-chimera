#!/bin/bash
# Project Chimera - MVP Health Validation Script
# Validates health status of all 8 MVP services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service definitions
declare -A services=(
    ["openclaw-orchestrator"]="8000"
    ["scenespeak-agent"]="8001"
    ["translation-agent"]="8002"
    ["sentiment-agent"]="8004"
    ["safety-filter"]="8006"
    ["operator-console"]="8007"
    ["hardware-bridge"]="8008"
    ["redis"]="6379"
)

# Health endpoints for each service
declare -A health_endpoints=(
    ["openclaw-orchestrator"]="/health"
    ["scenespeak-agent"]="/health"
    ["translation-agent"]="/health"
    ["sentiment-agent"]="/health"
    ["safety-filter"]="/health/live"
    ["operator-console"]="/health"
    ["hardware-bridge"]="/health"
    ["redis"]="/ping"  # Redis uses PING command
)

echo "=========================================="
echo "🎭 Project Chimera - MVP Health Check"
echo "=========================================="
echo ""

# Check if docker compose is running
echo "📋 Checking Docker Compose status..."
if ! docker compose -f docker-compose.mvp.yml ps &>/dev/null; then
    echo -e "${RED}✗ Docker Compose is not running${NC}"
    echo "Please start services with: docker compose -f docker-compose.mvp.yml up -d"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is running${NC}"
echo ""

# Check each service
failed_services=()
total_services=${#services[@]}

for service in "${!services[@]}"; do
    port=${services[$service]}
    endpoint=${health_endpoints[$service]}

    echo -n "Checking $service (port $port)... "

    # Try to reach the health endpoint
    if [ "$service" == "redis" ]; then
        # Redis uses redis-cli for health check
        if docker exec chimera-redis redis-cli ping &>/dev/null; then
            echo -e "${GREEN}✓ HEALTHY${NC}"
        else
            echo -e "${RED}✗ UNHEALTHY${NC}"
            failed_services+=("$service")
        fi
    else
        # HTTP services use curl
        if curl -sf "http://localhost:$port$endpoint" &>/dev/null; then
            echo -e "${GREEN}✓ HEALTHY${NC}"
        else
            echo -e "${RED}✗ UNHEALTHY${NC}"
            failed_services+=("$service")
        fi
    fi
done

echo ""
echo "=========================================="
echo "Summary: $((total_services - ${#failed_services[@]}))/$total_services services healthy"
echo "=========================================="

# Exit with error code if any services failed
if [ ${#failed_services[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed services:${NC}"
    for service in "${failed_services[@]}"; do
        echo "  - $service"
    done
    exit 1
fi

echo ""
echo -e "${GREEN}✓ All MVP services are healthy!${NC}"
exit 0
