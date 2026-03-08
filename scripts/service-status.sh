#!/bin/bash
# Service health check and startup script for Project Chimera
# This script checks all 9 services and starts any that are missing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service ports mapping
declare -A SERVICES=(
    ["orchestrator"]="8000"
    ["scenespeak"]="8001"
    ["captioning"]="8002"
    ["bsl"]="8003"
    ["sentiment"]="8004"
    ["lighting"]="8005"
    ["safety"]="8006"
    ["console"]="8007"
    ["music"]="8011"
)

# Function to check service health
check_service_health() {
    local port=$1
    local service_name=$2

    # Try /health/live first, then /health, then root
    for endpoint in "/health/live" "/health" "/"; do
        if curl -sf "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $service_name (port $port): Healthy via $endpoint"
            return 0
        fi
    done

    echo -e "${RED}✗${NC} $service_name (port $port): Not responding"
    return 1
}

# Function to check if service container is running
check_container_running() {
    local service_name=$1
    if docker ps --format '{{.Names}}' | grep -q "chimera-${service_name}"; then
        return 0
    fi
    return 1
}

# Main function
main() {
    echo "=== Project Chimera Service Status ==="
    echo ""

    # Change to project directory
    cd "$(dirname "$0")/.." || exit 1

    # Check each service
    local unhealthy_services=()
    local missing_services=()

    for service in "${!SERVICES[@]}"; do
        port=${SERVICES[$service]}
        service_container=$(get_container_name "$service")

        echo -n "Checking $service (port $port)... "

        if check_container_running "$service_container"; then
            if check_service_health "$port" "$service"; then
                continue
            else
                unhealthy_services+=("$service")
            fi
        else
            echo -e "${YELLOW}⚠${NC} Container not running"
            missing_services+=("$service")
        fi
    done

    echo ""
    echo "=== Summary ==="
    echo "Total services: ${#SERVICES[@]}"
    echo "Running: $((${#SERVICES[@]} - ${#unhealthy_services[@]} - ${#missing_services[@]}))"
    echo "Unhealthy: ${#unhealthy_services[@]}"
    echo "Missing: ${#missing_services[@]}"

    if [ ${#missing_services[@]} -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Missing services:${NC} ${missing_services[*]}"
        echo ""
        read -p "Start missing services? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Starting missing services..."
            for service in "${missing_services[@]}"; do
                echo "Starting $service..."
                docker compose up -d "$service" || echo "Failed to start $service"
            fi
        fi
    fi

    if [ ${#unhealthy_services[@]} -gt 0 ]; then
        echo ""
        echo -e "${RED}Unhealthy services:${NC} ${unhealthy_services[*]}"
        echo "Check logs with: docker logs chimera-<service>"
    fi
}

get_container_name() {
    local service=$1
    case $service in
        "orchestrator") echo "orchestrator" ;;
        "scenespeak") echo "scenespeak" ;;
        "captioning") echo "captioning" ;;
        "bsl") echo "bsl" ;;
        "sentiment") echo "sentiment" ;;
        "lighting") echo "lighting-sound-music" ;;
        "safety") echo "safety-filter" ;;
        "console") echo "operator-console" ;;
        "music") echo "music-generation" ;;
    esac
}

main "$@"
