#!/bin/bash
#
# docker-status.sh - Check Project Chimera service status
#
# This script checks the health and status of all running services.
# Usage: ./scripts/docker-status.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Print banner
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Project Chimera - Service Status${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Service definitions
declare -A SERVICES=(
    ["openclaw-orchestrator"]="8000"
    ["scenespeak-agent"]="8001"
    ["captioning-agent"]="8002"
    ["bsl-agent"]="8003"
    ["sentiment-agent"]="8004"
    ["lighting-sound-music"]="8005"
    ["safety-filter"]="8006"
    ["operator-console"]="8007"
)

declare -A INFRA=(
    ["redis"]="6379"
    ["kafka"]="9092"
    ["prometheus"]="9090"
    ["jaeger"]="16686"
    ["grafana"]="3000"
)

# Function to check service health
check_service_health() {
    local service_name=$1
    local port=$2

    # Try different health endpoints
    for endpoint in "/health/live" "/health" "/healthz" "/"; do
        if curl -s "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} ${service_name}"
            return 0
        fi
    done

    return 1
}

# Function to get container status
get_container_status() {
    local container_name=$1
    docker ps --filter "name=${container_name}" --format "{{.Status}}" 2>/dev/null || echo "Not found"
}

# Check Core Services
echo -e "${CYAN}Core Services:${NC}"
CORE_COUNT=0
CORE_UP=0

for service in "${!SERVICES[@]}"; do
    CORE_COUNT=$((CORE_COUNT + 1))
    port=${SERVICES[$service]}
    container_name="chimera-${service//_/-}"

    # Check if container is running
    container_status=$(get_container_status "$container_name")

    if [[ "$container_status" != "Not found" ]] && [[ "$container_status" == *"Up"* ]]; then
        # Check service health
        if check_service_health "$service" "$port"; then
            CORE_UP=$((CORE_UP + 1))
        else
            echo -e "${YELLOW}⚠${NC} ${service} (running but health check failed)"
        fi
    else
        echo -e "${RED}✗${NC} ${service} (not running)"
    fi
done

echo ""

# Check Infrastructure Services
echo -e "${CYAN}Infrastructure Services:${NC}"
INFRA_COUNT=0
INFRA_UP=0

for service in "${!INFRA[@]}"; do
    INFRA_COUNT=$((INFRA_COUNT + 1))
    port=${INFRA[$service]}
    container_name="chimera-${service}"

    # Check if container is running
    container_status=$(get_container_status "$container_name")

    if [[ "$container_status" != "Not found" ]] && [[ "$container_status" == *"Up"* ]]; then
        # Check if port is accessible
        if timeout 1 bash -c "cat < /dev/null > /dev/tcp/localhost/${port}" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} ${service}"
            INFRA_UP=$((INFRA_UP + 1))
        else
            echo -e "${YELLOW}⚠${NC} ${service} (running but port ${port} not accessible)"
        fi
    else
        echo -e "${RED}✗${NC} ${service} (not running)"
    fi
done

echo ""

# Summary
TOTAL_COUNT=$((CORE_COUNT + INFRA_COUNT))
TOTAL_UP=$((CORE_UP + INFRA_UP))

echo -e "${BLUE}================================================${NC}"
echo -e "${CYAN}Summary:${NC}"
echo -e "  Core Services:       ${CORE_UP}/${CORE_COUNT} up"
echo -e "  Infrastructure:      ${INFRA_UP}/${INFRA_COUNT} up"
echo -e "  Total:               ${TOTAL_UP}/${TOTAL_COUNT} up"
echo ""

if [[ $TOTAL_UP -eq $TOTAL_COUNT ]]; then
    echo -e "${GREEN}✓ All services are running!${NC}"
else
    echo -e "${YELLOW}⚠ Some services are not running${NC}"
fi

echo ""
echo -e "${CYAN}Recent Logs:${NC}"
docker-compose logs --tail=3 2>/dev/null | head -20 || echo "No logs available"
echo ""

echo -e "${CYAN}Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
    $(docker ps --filter "name=chimera" --format "{{.Names}}") 2>/dev/null || echo "No containers running"
echo ""

echo -e "${YELLOW}Use 'docker-compose logs -f [service]' to view logs${NC}"
echo -e "${YELLOW}Use 'docker-compose ps' for detailed status${NC}"
echo ""
