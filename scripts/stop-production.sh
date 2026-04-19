#!/bin/bash
#
# Production Stop Script for Project Chimera (Iteration 35)
#
# Gracefully stops all Project Chimera MVP services.
#
# Usage:
#   ./scripts/stop-production.sh [--force]
#
# Options:
#   --force  Force stop without waiting for graceful shutdown
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

# Parse arguments
FORCE_STOP=false
if [[ "${1:-}" == "--force" ]]; then
    FORCE_STOP=true
fi

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
# Pre-stop Checks
# ============================================================================

pre_stop_checks() {
    log_info "Running pre-stop checks..."

    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker compose file not found: $COMPOSE_FILE"
        log_info "Services may not be running."
        exit 0
    fi

    # Check if services are actually running
    cd "$PROJECT_ROOT"
    if ! docker compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log_warning "No services are currently running."
        exit 0
    fi
}

# ============================================================================
# Stop Functions
# ============================================================================

stop_services() {
    log_info "Stopping Project Chimera services..."

    cd "$PROJECT_ROOT"

    if [[ "$FORCE_STOP" == "true" ]]; then
        log_warning "Force stopping services (no graceful shutdown)..."
        docker compose -f "$COMPOSE_FILE" down --remove-orphans
    else
        # Graceful shutdown with timeout
        log_info "Attempting graceful shutdown (30 second timeout)..."
        if timeout 30 docker compose -f "$COMPOSE_FILE" down; then
            log_success "Services stopped gracefully."
        else
            log_warning "Graceful shutdown timed out. Force stopping..."
            docker compose -f "$COMPOSE_FILE" down --remove-orphans
        fi
    fi

    # Clean up any orphaned containers
    log_info "Cleaning up orphaned containers..."
    docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
}

# ============================================================================
# Verification Functions
# ============================================================================

verify_stopped() {
    log_info "Verifying all services are stopped..."

    local running_containers
    running_containers=$(docker ps -q --filter "name=chimera" 2>/dev/null || true)

    if [[ -n "$running_containers" ]]; then
        log_warning "Some chimera containers are still running:"
        docker ps --filter "name=chimera" --format "table {{.Names}}\t{{.Status}}"
        echo ""
        read -p "Force kill remaining containers? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker kill $running_containers 2>/dev/null || true
            docker rm $running_containers 2>/dev/null || true
            log_success "Remaining containers removed."
        fi
    else
        log_success "All chimera containers stopped."
    fi
}

# ============================================================================
# Main Stop Flow
# ============================================================================

main() {
    log_info "Stopping Project Chimera services..."
    echo ""

    # Run pre-stop checks
    pre_stop_checks
    echo ""

    # Stop services
    stop_services
    echo ""

    # Verify stopped
    verify_stopped
    echo ""

    log_success "=========================================="
    log_success "Stop Complete!"
    log_success "=========================================="
    echo ""
    log_info "All Project Chimera services have been stopped."
    echo ""
    log_info "To restart services:"
    echo "  ./scripts/deploy-production.sh"
    echo ""
}

# ============================================================================
# Script Entry Point
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
