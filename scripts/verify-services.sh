#!/bin/bash
# Quick health verification script for Project Chimera services

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Project Chimera Service Health Verification ==="
echo ""

# Services with their health endpoints
declare -A SERVICES=(
    ["openclaw-orchestrator:8000"]="/health/live"
    ["scenespeak-agent:8001"]="/health/live"
    ["captioning-agent:8002"]="/health/live"
    ["bsl-agent:8003"]="/health/live"
    ["sentiment-agent:8004"]="/health/live"
    ["lighting-sound-music:8005"]="/health/live"
    ["safety-filter:8006"]="/health"
    ["operator-console:8007"]="/health/live"
    ["music-generation:8011"]="/health/live"
)

healthy_count=0
unhealthy_count=0
optional_count=0

for service_endpoint in "${!SERVICES[@]}"; do
    IFS=':' read -r service port <<< "$service_endpoint"
    health_endpoint="${SERVICES[$service_endpoint]}"

    echo -n "Checking $service (port $port)... "

    # Check if service is responding
    if curl -sf "http://localhost:${port}${health_endpoint}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        ((healthy_count++))
    else
        # Mark music-generation as optional (still building)
        if [ "$service" = "music-generation" ]; then
            echo -e "${YELLOW}⚠ Not available (optional - still building)${NC}"
            ((optional_count++))
        else
            echo -e "${RED}✗ Unhealthy${NC}"
            ((unhealthy_count++))
        fi
    fi
done

echo ""
echo "=== Summary ==="
echo "Healthy: $healthy_count"
echo "Unhealthy: $unhealthy_count"
echo "Optional (not available): $optional_count"
echo ""

if [ $unhealthy_count -eq 0 ]; then
    echo -e "${GREEN}✓ All required services are healthy!${NC}"
    echo ""
    echo "Services are ready for E2E testing."
    exit 0
else
    echo -e "${RED}✗ Some required services are unhealthy${NC}"
    echo ""
    echo "Check logs with: docker logs chimera-<service>"
    exit 1
fi
