#!/bin/bash
# Start all Project Chimera services
# This script handles Docker permissions and ensures all services are running

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}=== Project Chimera Service Startup ===${NC}"
echo ""

# Check if user can access docker
if ! docker ps > /dev/null 2>&1; then
    echo -e "${YELLOW}Docker permission detected. Fixing...${NC}"

    # Check if user is in docker group
    if groups | grep -q "\bdocker\b"; then
        echo "User is in docker group. Using newgrp to refresh permissions..."
        # We'll use newgrp for docker commands
        DOCKER_CMD="newgrp docker"
    else
        echo -e "${RED}User is not in docker group. Adding user...${NC}"
        sudo usermod -aG docker "$USER"
        echo -e "${YELLOW}Please log out and log back in for group changes to take effect.${NC}"
        echo -e "${YELLOW}Or run: newgrp docker${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Docker is accessible"
    DOCKER_CMD=""
fi

# Function to run docker commands with proper permissions
docker_cmd() {
    if [ -n "$DOCKER_CMD" ]; then
        echo "$@" | $DOCKER_CMD
    else
        "$@"
    fi
}

# Check current service status
echo ""
echo "Checking current service status..."
echo ""

# Define services
declare -A SERVICES=(
    ["openclaw-orchestrator"]="8000"
    ["scenespeak-agent"]="8001"
    ["captioning-agent"]="8002"
    ["bsl-agent"]="8003"
    ["sentiment-agent"]="8004"
    ["lighting-sound-music"]="8005"
    ["safety-filter"]="8006"
    ["operator-console"]="8007"
    ["music-generation"]="8011"
)

# Check which services are running
running_services=()
stopped_services=()
missing_services=()

for service in "${!SERVICES[@]}"; do
    port=${SERVICES[$service]}
    container_name="chimera-${service}"

    # Map service names to container names
    case $service in
        "openclaw-orchestrator") container_name="chimera-orchestrator" ;;
        "scenespeak-agent") container_name="chimera-scenespeak" ;;
        "captioning-agent") container_name="chimera-captioning" ;;
        "bsl-agent") container_name="chimera-bsl" ;;
        "sentiment-agent") container_name="chimera-sentiment" ;;
        "lighting-sound-music") container_name="chimera-lighting-sound-music" ;;
        "safety-filter") container_name="chimera-safety-filter" ;;
        "operator-console") container_name="chimera-operator-console" ;;
        "music-generation") container_name="chimera-music-generation" ;;
    esac

    # Check if container exists
    if docker_cmd docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        # Check if running
        if docker_cmd docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            # Check health
            if curl -sf "http://localhost:${port}/health/live" > /dev/null 2>&1 || \
               curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} $service (port $port): Healthy"
                running_services+=("$service")
            else
                echo -e "${YELLOW}⚠${NC} $service (port $port): Running but unhealthy"
                stopped_services+=("$service")
            fi
        else
            echo -e "${RED}✗${NC} $service (port $port): Stopped"
            stopped_services+=("$service")
        fi
    else
        echo -e "${RED}✗${NC} $service (port $port): Not built"
        missing_services+=("$service")
    fi
done

echo ""
echo "Summary:"
echo "  Running: ${#running_services[@]}/${#SERVICES[@]}"
echo "  Stopped: ${#stopped_services[@]}"
echo "  Not built: ${#missing_services[@]}"

# Start stopped services
if [ ${#stopped_services[@]} -gt 0 ]; then
    echo ""
    echo -e "${BLUE}Starting stopped services...${NC}"
    for service in "${stopped_services[@]}"; do
        echo "Starting $service..."
        docker_cmd docker compose up -d "$service"
    done
fi

# Build missing services
if [ ${#missing_services[@]} -gt 0 ]; then
    echo ""
    echo -e "${BLUE}Building missing services...${NC}"
    for service in "${missing_services[@]}"; do
        echo "Building $service..."
        docker_cmd docker compose build "$service"
        echo "Starting $service..."
        docker_cmd docker compose up -d "$service"
    done
fi

# Wait for services to be healthy
echo ""
echo -e "${BLUE}Waiting for services to be healthy...${NC}"

# Define health check endpoints
declare -A HEALTH_ENDPOINTS=(
    ["openclaw-orchestrator"]="/health/live"
    ["scenespeak-agent"]="/health/live"
    ["captioning-agent"]="/health/live"
    ["bsl-agent"]="/health/live"
    ["sentiment-agent"]="/health/live"
    ["lighting-sound-music"]="/health/live"
    ["safety-filter"]="/health"
    ["operator-console"]="/health/live"
    ["music-generation"]="/health/live"
)

# Check each service
all_healthy=true
for service in "${!SERVICES[@]}"; do
    port=${SERVICES[$service]}
    endpoint=${HEALTH_ENDPOINTS[$service]:="/health/live"}

    echo -n "Checking $service (port $port)... "

    # Try up to 30 times with 2 second intervals
    for i in {1..30}; do
        if curl -sf "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
            break
        fi

        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Timeout${NC}"
            all_healthy=false
        fi

        sleep 2
    done
done

echo ""
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}=== All services are healthy! ===${NC}"
    echo ""
    echo "Service URLs:"
    for service in "${!SERVICES[@]}"; do
        port=${SERVICES[$service]}
        echo "  - $service: http://localhost:$port"
    done
    exit 0
else
    echo -e "${RED}=== Some services are not healthy ===${NC}"
    echo ""
    echo "Check logs with:"
    for service in "${!SERVICES[@]}"; do
        case $service in
            "openclaw-orchestrator") echo "  docker logs chimera-orchestrator" ;;
            "scenespeak-agent") echo "  docker logs chimera-scenespeak" ;;
            "captioning-agent") echo "  docker logs chimera-captioning" ;;
            "bsl-agent") echo "  docker logs chimera-bsl" ;;
            "sentiment-agent") echo "  docker logs chimera-sentiment" ;;
            "lighting-sound-music") echo "  docker logs chimera-lighting-sound-music" ;;
            "safety-filter") echo "  docker logs chimera-safety-filter" ;;
            "operator-console") echo "  docker logs chimera-operator-console" ;;
            "music-generation") echo "  docker logs chimera-music-generation" ;;
        esac
    done
    exit 1
fi
