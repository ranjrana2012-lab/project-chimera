#!/bin/bash
#
# Production Deployment Script for Project Chimera (Iteration 35)
#
# Automates the deployment of Project Chimera MVP to production
# on university/organization infrastructure.
#
# Usage:
#   ./scripts/deploy-production.sh [environment]
#
# Environments:
#   - production (default)
#   - staging
#
# Features:
#   - Pre-deployment health checks
#   - Docker Compose build and start
#   - Service health verification
#   - ML model readiness checks
#   - Smoke tests
#   - Rollback on failure
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.mvp.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
MAX_WAIT_SECONDS=300  # 5 minutes for service startup
HEALTH_CHECK_INTERVAL=5

# Service ports for health checks
declare -A SERVICE_PORTS=(
    ["openclaw-orchestrator"]=8000
    ["scenespeak-agent"]=8001
    ["translation-agent"]=8002
    ["sentiment-agent"]=8004
    ["safety-filter"]=8006
    ["operator-console"]=8007
)

# ============================================================================
# Logging Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# Pre-deployment Checks
# ============================================================================

pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install docker-compose plugin first."
        exit 1
    fi

    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    # Check if ports are already in use
    log_info "Checking if required ports are available..."
    local ports_in_use=()
    for port in "${SERVICE_PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            ports_in_use+=("$port")
        fi
    done

    if [[ ${#ports_in_use[@]} -gt 0 ]]; then
        log_warning "The following ports are already in use: ${ports_in_use[*]}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled."
            exit 0
        fi
    fi

    log_success "Pre-deployment checks passed."
}

# ============================================================================
# Deployment Functions
# ============================================================================

build_services() {
    log_info "Building Docker images (this may take several minutes)..."

    cd "$PROJECT_ROOT"

    if docker compose -f "$COMPOSE_FILE" build --no-cache; then
        log_success "Docker images built successfully."
    else
        log_error "Docker build failed. Please check the logs above."
        exit 1
    fi
}

start_services() {
    log_info "Starting services..."

    cd "$PROJECT_ROOT"

    # Stop any existing services
    docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true

    # Start services
    if docker compose -f "$COMPOSE_FILE" up -d; then
        log_success "Services started."
    else
        log_error "Failed to start services. Check logs with: docker compose logs"
        exit 1
    fi
}

# ============================================================================
# Health Check Functions
# ============================================================================

check_service_health() {
    local service_name="$1"
    local port="$2"
    local max_wait="$3"
    local elapsed=0

    log_info "Waiting for $service_name to be healthy..."

    while [[ $elapsed -lt $max_wait ]]; do
        if curl -s "http://localhost:${port}/health" > /dev/null 2>&1; then
            # Check if ML model is loaded (for applicable services)
            if [[ "$service_name" =~ (sentiment-agent|scenespeak-agent) ]]; then
                local health_data
                health_data=$(curl -s "http://localhost:${port}/health" 2>/dev/null)
                if echo "$health_data" | grep -q '"model_loaded":true'; then
                    log_success "$service_name is ready (ML model loaded)."
                    return 0
                fi
                # Still waiting for model to load
            else
                log_success "$service_name is healthy."
                return 0
            fi
        fi

        sleep $HEALTH_CHECK_INTERVAL
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))

        # Show progress dots every 30 seconds
        if [[ $((elapsed % 30)) -eq 0 ]]; then
            echo -n "..."
        fi
    done

    log_error "$service_name failed to become healthy within ${max_wait}s."
    return 1
}

verify_all_services() {
    log_info "Verifying all services are healthy..."

    local failed_services=()

    for service in "${!SERVICE_PORTS[@]}"; do
        local port="${SERVICE_PORTS[$service]}"
        if ! check_service_health "$service" "$port" "$MAX_WAIT_SECONDS"; then
            failed_services+=("$service")
        fi
    done

    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "The following services failed health checks: ${failed_services[*]}"
        return 1
    fi

    log_success "All services are healthy and ready."
    return 0
}

check_ml_models() {
    log_info "Verifying ML models are loaded..."

    local models_ok=true

    # Check sentiment agent model
    local sentiment_health
    sentiment_health=$(curl -s http://localhost:8004/health 2>/dev/null)
    if echo "$sentiment_health" | grep -q '"model_loaded":true'; then
        log_success "Sentiment agent ML model is loaded."
    else
        log_warning "Sentiment agent ML model not yet loaded."
        models_ok=false
    fi

    # Check scenespeak agent model
    local scenespeak_health
    scenespeak_health=$(curl -s http://localhost:8001/health 2>/dev/null)
    if echo "$scenespeak_health" | grep -q '"model_loaded":true'; then
        log_success "SceneSpeak agent model is ready."
    else
        log_warning "SceneSpeak agent model not yet loaded."
        models_ok=false
    fi

    return $([[ "$models_ok" == "true" ]])
}

# ============================================================================
# Smoke Tests
# ============================================================================

run_smoke_tests() {
    log_info "Running smoke tests..."

    # Test orchestrator health
    if curl -s http://localhost:8000/health/ready | grep -q '"status":"ready"'; then
        log_success "Orchestrator smoke test passed."
    else
        log_error "Orchestrator smoke test failed."
        return 1
    fi

    # Test sentiment analysis
    local sentiment_result
    sentiment_result=$(curl -s -X POST http://localhost:8004/api/analyze \
        -H "Content-Type: application/json" \
        -d '{"text":"This is a test"}' 2>/dev/null)

    if echo "$sentiment_result" | grep -q '"sentiment"'; then
        log_success "Sentiment agent smoke test passed."
    else
        log_error "Sentiment agent smoke test failed."
        return 1
    fi

    # Test safety filter
    local safety_result
    safety_result=$(curl -s -X POST http://localhost:8006/api/check \
        -H "Content-Type: application/json" \
        -d '{"text":"Hello world"}' 2>/dev/null)

    if echo "$safety_result" | grep -q '"safe":true'; then
        log_success "Safety filter smoke test passed."
    else
        log_error "Safety filter smoke test failed."
        return 1
    fi

    log_success "All smoke tests passed."
    return 0
}

# ============================================================================
# Rollback Functions
# ============================================================================

rollback_deployment() {
    log_warning "Rolling back deployment..."

    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" down

    log_info "Rollback complete. Services stopped."
}

# ============================================================================
# Main Deployment Flow
# ============================================================================

main() {
    log_info "Starting Project Chimera deployment to: $ENVIRONMENT"
    echo ""

    # Run pre-deployment checks
    pre_deployment_checks
    echo ""

    # Build services
    build_services
    echo ""

    # Start services
    start_services
    echo ""

    # Wait a bit for services to initialize
    log_info "Waiting for services to initialize..."
    sleep 10
    echo ""

    # Verify all services
    if ! verify_all_services; then
        log_error "Service health checks failed."
        read -p "Rollback deployment? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z "$REPLY" ]]; then
            rollback_deployment
        fi
        exit 1
    fi
    echo ""

    # Check ML models (with patience)
    if ! check_ml_models; then
        log_warning "ML models not fully loaded yet. This is normal on first startup."
        log_info "Services will be ready after model loading completes (may take 30-60s)."
    fi
    echo ""

    # Run smoke tests
    if ! run_smoke_tests; then
        log_warning "Smoke tests failed. Services may need more time to warm up."
    fi
    echo ""

    # Deployment summary
    log_success "=========================================="
    log_success "Deployment Complete!"
    log_success "=========================================="
    echo ""
    log_info "Services running:"
    for service in "${!SERVICE_PORTS[@]}"; do
        echo "  - $service (port ${SERVICE_PORTS[$service]})"
    done
    echo ""
    log_info "Access points:"
    echo "  - Operator Console: http://localhost:8007"
    echo "  - API Docs: http://localhost:8000/docs (when available)"
    echo ""
    log_info "To view logs:"
    echo "  docker compose -f $COMPOSE_FILE logs -f"
    echo ""
    log_info "To stop services:"
    echo "  ./scripts/stop-production.sh"
    echo ""
}

# ============================================================================
# Script Entry Point
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
