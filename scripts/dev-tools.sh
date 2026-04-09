#!/bin/bash
# Project Chimera Phase 2 - Developer Tools Script
#
# Convenient utilities for developers working on Phase 2 services
#
# Usage:
#   ./dev-tools.sh --action build --service dmx
#   ./dev-tools.sh --action test --coverage
#   ./dev-tools.sh --action logs --service audio --follow
#   ./dev-tools.sh --action shell --service bsl

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES_DIR="${PROJECT_ROOT}/services"
COMPOSE_FILE="${SERVICES_DIR}/docker-compose.phase2.yml"

# Services
declare -A SERVICE_PATHS
SERVICE_PATHS[dmx]="${SERVICES_DIR}/dmx-controller"
SERVICE_PATHS[audio]="${SERVICES_DIR}/audio-controller"
SERVICE_PATHS[bsl]="${SERVICES_DIR}/bsl-avatar-service"

# Help function
show_help() {
    cat << EOF
Project Chimera Phase 2 - Developer Tools

Usage: $0 --action ACTION [OPTIONS]

Actions:
    build           Build service Docker images
    start           Start services
    stop            Stop services
    restart         Restart services
    logs            Show service logs
    test            Run tests
    lint            Run linting
    format          Format code
    shell           Open shell in service container
    clean           Remove containers and images
    status          Show service status
    health          Run health checks
    metrics         Show service metrics

Options:
    --service SERVICE    Service to operate on (dmx, audio, bsl, all)
    --follow             Follow log output
    --coverage           Generate coverage report
    --verbose            Show detailed output
    --help               Show this help message

Examples:
    $0 --action build --service dmx
    $0 --action logs --service audio --follow
    $0 --action test --coverage
    $0 --action shell --service bsl

EOF
}

# Parse arguments
parse_args() {
    ACTION=""
    SERVICE="all"
    FOLLOW=false
    COVERAGE=false
    VERBOSE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --action)
                ACTION="$2"
                shift 2
                ;;
            --service)
                SERVICE="$2"
                shift 2
                ;;
            --follow)
                FOLLOW=true
                shift
                ;;
            --coverage)
                COVERAGE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    if [[ -z "$ACTION" ]]; then
        error "--action is required"
        show_help
        exit 1
    fi
}

# Build service images
build_service() {
    local service="$1"

    echo "Building ${service} service..."

    cd "${SERVICE_PATHS[$service]}"

    if [[ "$VERBOSE" == true ]]; then
        docker-compose -f docker-compose.yml build
    else
        docker-compose -f docker-compose.yml build --quiet
    fi
}

# Start services
start_service() {
    local service="$1"

    echo "Starting ${service} service..."

    if [[ "$service" == "all" ]]; then
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        docker-compose -f "$COMPOSE_FILE" up -d "${service}-controller"
    fi
}

# Stop services
stop_service() {
    local service="$1"

    echo "Stopping ${service} service..."

    if [[ "$service" == "all" ]]; then
        docker-compose -f "$COMPOSE_FILE" down
    else
        docker-compose -f "$COMPOSE_FILE" stop "${service}-controller"
    fi
}

# Restart services
restart_service() {
    local service="$1"

    echo "Restarting ${service} service..."
    stop_service "$service"
    start_service "$service"
}

# Show logs
show_logs() {
    local service="$1"

    if [[ "$FOLLOW" == true ]]; then
        if [[ "$service" == "all" ]]; then
            docker-compose -f "$COMPOSE_FILE" logs -f
        else
            docker-compose -f "$COMPOSE_FILE" logs -f "${service}-controller"
        fi
    else
        if [[ "$service" == "all" ]]; then
            docker-compose -f "$COMPOSE_FILE" logs --tail=100
        else
            docker-compose -f "$COMPOSE_FILE" logs --tail=100 "${service}-controller"
        fi
    fi
}

# Run tests
run_tests() {
    local service="$1"

    if [[ "$service" == "all" ]]; then
        echo "Running all tests..."
        cd "$PROJECT_ROOT"
        if [[ "$COVERAGE" == true ]]; then
            pytest tests/ -v --cov=services --cov-report=html --cov-report=term
        else
            pytest tests/ -v
        fi
    else
        echo "Running ${service} tests..."
        cd "${SERVICE_PATHS[$service]}"
        if [[ "$COVERAGE" == true ]]; then
            pytest tests/ -v --cov=. --cov-report=html --cov-report=term
        else
            pytest tests/ -v
        fi
    fi
}

# Run linting
run_lint() {
    local service="$1"

    if [[ "$service" == "all" ]]; then
        echo "Linting all services..."
        cd "$PROJECT_ROOT"
        ruff check services/
    else
        echo "Linting ${service} service..."
        cd "${SERVICE_PATHS[$service]}"
        ruff check . --exclude tests/
    fi
}

# Format code
format_code() {
    local service="$1"

    if [[ "$service" == "all" ]]; then
        echo "Formatting all services..."
        cd "$PROJECT_ROOT"
        black services/
        isort services/
    else
        echo "Formatting ${service} service..."
        cd "${SERVICE_PATHS[$service]}"
        black .
        isort .
    fi
}

# Open shell
open_shell() {
    local service="$1"
    local container_name="chimera-${service}-controller"

    echo "Opening shell in ${container_name}..."
    docker exec -it "$container_name" /bin/bash
}

# Clean up
cleanup() {
    echo "Cleaning up..."

    # Stop and remove containers
    docker-compose -f "$COMPOSE_FILE" down -v

    # Remove dangling images
    docker image prune -f

    echo "Cleanup complete"
}

# Show status
show_status() {
    echo "Service Status:"
    echo "================"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Run health checks
run_health_checks() {
    echo "Running health checks..."

    local services_to_check=()
    case "$SERVICE" in
        all)
            services_to_check=("dmx" "audio" "bsl")
            ;;
        dmx|audio|bsl)
            services_to_check=("$SERVICE")
            ;;
    esac

    declare -A ports
    ports[dmx]=8001
    ports[audio]=8002
    ports[bsl]=8003

    for service in "${services_to_check[@]}"; do
        local port=${ports[$service]}
        local url="http://localhost:${port}/health"

        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${service} (${port}): ${GREEN}✓ Healthy${NC}"
        else
            echo -e "${service} (${port}): ${RED}✗ Unhealthy${NC}"
        fi
    done
}

# Show metrics
show_metrics() {
    local service="$1"

    declare -A ports
    ports[dmx]=8001
    ports[audio]=8002
    ports[bsl]=8003

    if [[ "$service" == "all" ]]; then
        for svc in dmx audio bsl; do
            show_metrics "$svc"
        done
        return
    fi

    local port=${ports[$service]}
    local url="http://localhost:${port}/metrics"

    echo "Metrics for ${service} (port ${port}):"
    curl -s "$url" | grep -v "^#" | head -20
}

# Logging functions
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Main function
main() {
    parse_args "$@"

    echo "Project Chimera Phase 2 - Developer Tools"
    echo ""

    # Execute action
    case "$ACTION" in
        build)
            if [[ "$SERVICE" == "all" ]]; then
                for svc in dmx audio bsl; do
                    build_service "$svc"
                done
            else
                build_service "$SERVICE"
            fi
            success "Build complete"
            ;;
        start)
            start_service "$SERVICE"
            success "Services started"
            ;;
        stop)
            stop_service "$SERVICE"
            success "Services stopped"
            ;;
        restart)
            restart_service "$SERVICE"
            success "Services restarted"
            ;;
        logs)
            show_logs "$SERVICE"
            ;;
        test)
            run_tests "$SERVICE"
            ;;
        lint)
            run_lint "$SERVICE"
            ;;
        format)
            format_code "$SERVICE"
            success "Code formatted"
            ;;
        shell)
            open_shell "$SERVICE"
            ;;
        clean)
            cleanup
            ;;
        status)
            show_status
            ;;
        health)
            run_health_checks
            ;;
        metrics)
            show_metrics "$SERVICE"
            ;;
        *)
            error "Unknown action: $ACTION"
            exit 1
            ;;
    esac
}

main "$@"
