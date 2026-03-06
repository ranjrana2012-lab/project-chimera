#!/bin/bash
#
# docker-stop.sh - Stop all Project Chimera services
#
# This script gracefully stops all Docker Compose services.
# Usage: ./scripts/docker-stop.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Print banner
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Project Chimera - Docker Stop${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${YELLOW}Stopping Project Chimera services...${NC}"
echo ""

# Show current status
echo -e "${YELLOW}Current service status:${NC}"
docker-compose ps
echo ""

# Stop services
echo -e "${YELLOW}Stopping containers...${NC}"
docker-compose down

echo ""
echo -e "${GREEN}All services stopped successfully!${NC}"
echo ""

# Optional: Clean up volumes
if [[ "${1}" == "--clean" ]]; then
    echo -e "${YELLOW}Cleaning up volumes...${NC}"
    docker-compose down -v
    echo -e "${GREEN}Volumes cleaned!${NC}"
    echo ""
fi

# Optional: Clean up images
if [[ "${1}" == "--prune" ]]; then
    echo -e "${YELLOW}Pruning Docker resources...${NC}"
    docker system prune -f
    echo -e "${GREEN}Docker resources pruned!${NC}"
    echo ""
fi

echo -e "${BLUE}================================================${NC}"
echo ""

# Show remaining containers
REMAINING=$(docker ps -a --filter "name=chimera" --format "{{.Names}}" | wc -l)
if [[ $REMAINING -gt 0 ]]; then
    echo -e "${YELLOW}Note: $REMAINING Project Chimera containers still exist${NC}"
    echo -e "Use 'docker rm -f \$(docker ps -a -q --filter \"name=chimera\")' to remove them"
else
    echo -e "${GREEN}All Project Chimera containers removed${NC}"
fi
echo ""

echo -e "${YELLOW}Usage:${NC}"
echo -e "  $0              - Stop all services"
echo -e "  $0 --clean      - Stop services and remove volumes"
echo -e "  $0 --prune      - Stop services and prune Docker resources"
echo ""
