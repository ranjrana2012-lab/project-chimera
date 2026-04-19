#!/bin/bash
# Project Chimera - Comprehensive Stack Health Verification
# Validates all 8 MVP services are running and healthy after reboot
# This script is the primary health check for CI/CD and manual verification

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# MVP Services - must match docker-compose.mvp.yml
declare -A SERVICES=(
    ["openclaw-orchestrator"]="8000:8000:/health"
    ["scenespeak-agent"]="8001:8001:/health"
    ["translation-agent"]="8002:8002:/health"
    ["sentiment-agent"]="8004:8004:/health"
    ["safety-filter"]="8006:8006:/health/live"
    ["operator-console"]="8007:8007:/health"
    ["hardware-bridge"]="8008:8008:/health"
    ["redis"]="6379:6379:ping"
)

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.mvp.yml}"
TIMEOUT="${TIMEOUT:-120}"  # seconds
MAX_RETRIES="${MAX_RETRIES:-3}"

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check Docker daemon
check_docker() {
    log_info "Checking Docker daemon..."
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
    log_success "Docker daemon is running"
    return 0
}

# Check Docker Compose services
check_compose_running() {
    log_info "Checking Docker Compose services..."
    if ! docker compose -f "$COMPOSE_FILE" ps &>/dev/null; then
        log_error "Docker Compose is not running for $COMPOSE_FILE"
        log_info "Start services with: docker compose -f $COMPOSE_FILE up -d"
        return 1
    fi

    # Check if containers are actually running
    local running=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | wc -l)
    local expected=${#SERVICES[@]}

    if [ "$running" -lt "$expected" ]; then
        log_warning "Only $running/$expected services are running"
        docker compose -f "$COMPOSE_FILE" ps
        return 1
    fi

    log_success "All $expected containers are running"
    return 0
}

# Check individual service health
check_service_health() {
    local service=$1
    local config=(${SERVICES[$service]})
    local internal_port=${config[0]}
    local external_port=${config[1]}
    local endpoint=${config[2]}

    echo -n "  $service ... "

    if [ "$service" = "redis" ]; then
        # Redis uses docker exec for ping
        if docker exec chimera-redis redis-cli ping &>/dev/null; then
            echo -e "${GREEN}✓ HEALTHY${NC}"
            return 0
        else
            echo -e "${RED}✗ UNHEALTHY${NC}"
            return 1
        fi
    fi

    # HTTP services
    local url="http://localhost:$external_port$endpoint"
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")

    if [ "$response" = "200" ] || [ "$response" = "204" ]; then
        echo -e "${GREEN}✓ HEALTHY${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ UNHEALTHY${NC} (HTTP $response)"
        return 1
    fi
}

# Main health check
main() {
    echo "=========================================="
    echo "🎭 Project Chimera - Stack Health Check"
    echo "=========================================="
    echo "Compose File: $COMPOSE_FILE"
    echo "Timeout: ${TIMEOUT}s"
    echo ""

    local exit_code=0

    # Phase 1: Docker checks
    if ! check_docker; then
        exit 1
    fi

    if ! check_compose_running; then
        exit 1
    fi

    echo ""

    # Phase 2: Service health checks
    log_info "Checking service health endpoints..."
    echo ""

    local healthy=0
    local failed=0

    for service in "${!SERVICES[@]}"; do
        if check_service_health "$service"; then
            ((healthy++))
        else
            ((failed++))
            exit_code=1
        fi
    done

    echo ""
    echo "=========================================="
    echo "Summary: $healthy/${#SERVICES[@]} services healthy"
    echo "=========================================="

    if [ $exit_code -ne 0 ]; then
        echo ""
        log_error "Some services are unhealthy. Check logs with:"
        echo "  docker compose -f $COMPOSE_FILE logs [service-name]"
        echo ""
        echo "Restart services with:"
        echo "  docker compose -f $COMPOSE_FILE restart"
    else
        echo ""
        log_success "✓ All MVP services are healthy!"
        echo ""
        echo "Access endpoints:"
        echo "  - Orchestrator API: http://localhost:8000"
        echo "  - Operator Console: http://localhost:8007"
        echo "  - API Docs: http://localhost:8000/docs"
    fi

    return $exit_code
}

# Run main function
main "$@"
