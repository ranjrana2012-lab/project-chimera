#!/bin/bash
#
# docker-start.sh - Start all Project Chimera services
#
# This script starts all Docker Compose services for local development or demo.
# Usage: ./scripts/docker-start.sh [dev|prod]
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

# Default environment
ENV=${1:-dev}

# Print banner
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Project Chimera - Docker Start${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    echo -e "${RED}Invalid environment: $ENV${NC}"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo -e "${GREEN}Starting Project Chimera in $ENV mode...${NC}"
echo ""

# Load environment variables
if [[ -f .env.docker ]]; then
    export $(cat .env.docker | grep -v '^#' | grep -v '^$' | xargs)
    echo -e "${GREEN}Loaded environment variables from .env.docker${NC}"
else
    echo -e "${YELLOW}Warning: .env.docker not found, using defaults${NC}"
fi

# Stop any running containers first
echo -e "${YELLOW}Stopping any existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Build images
echo -e "${YELLOW}Building Docker images...${NC}"
if [[ "$ENV" == "dev" ]]; then
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
else
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"
if [[ "$ENV" == "dev" ]]; then
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
else
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
fi

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Show service status
echo ""
echo -e "${GREEN}Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Project Chimera services started successfully!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${GREEN}Available Services:${NC}"
echo -e "  • OpenClaw Orchestrator:    ${BLUE}http://localhost:8000${NC}"
echo -e "  • SceneSpeak Agent:         ${BLUE}http://localhost:8001${NC}"
echo -e "  • Captioning Agent:         ${BLUE}http://localhost:8002${NC}"
echo -e "  • BSL Agent:                ${BLUE}http://localhost:8003${NC}"
echo -e "  • Sentiment Agent:          ${BLUE}http://localhost:8004${NC}"
echo -e "  • Lighting-Sound-Music:     ${BLUE}http://localhost:8005${NC}"
echo -e "  • Safety Filter:            ${BLUE}http://localhost:8006${NC}"
echo -e "  • Operator Console:         ${BLUE}http://localhost:8007${NC}"
echo ""
echo -e "${GREEN}Infrastructure Services:${NC}"
echo -e "  • Prometheus (Metrics):     ${BLUE}http://localhost:9090${NC}"
echo -e "  • Jaeger (Tracing):         ${BLUE}http://localhost:16686${NC}"
echo -e "  • Grafana (Dashboards):     ${BLUE}http://localhost:3000${NC} (admin/chimera)"
echo -e "  • Redis:                    ${BLUE}localhost:6379${NC}"
echo -e "  • Kafka:                    ${BLUE}localhost:9092${NC}"
echo ""
echo -e "${YELLOW}Use './scripts/docker-status.sh' to check service health${NC}"
echo -e "${YELLOW}Use './scripts/docker-stop.sh' to stop all services${NC}"
echo -e "${YELLOW}Use 'docker-compose logs -f [service]' to view logs${NC}"
echo ""

# Show recent logs
echo -e "${YELLOW}Recent logs (use 'docker-compose logs -f' for live logs):${NC}"
echo ""
docker-compose logs --tail=5
