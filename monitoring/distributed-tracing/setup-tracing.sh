#!/bin/bash
# Project Chimera Phase 2 - Distributed Tracing Setup
#
# This script sets up distributed tracing using Jaeger for Phase 2 services
# to provide end-to-end observability and request tracking.
#
# Usage:
#   ./setup-tracing.sh --action install
#   ./setup-tracing.sh --action start
#   ./setup-tracing.sh --action stop

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/monitoring/distributed-tracing/docker-compose.tracing.yml"
JAEGER_PORT=16686
JAEGER_UI_PORT=16686

# Logging
log() {
    local level="$1"
    shift
    echo -e "${level} $*"
}
info() { log "${BLUE}[INFO]${NC}", "$*"; }
success() { log "${GREEN}[SUCCESS]${NC}", "$*"; }
warning() { log "${YELLOW}[WARNING]${NC}", "$*"; }
error() { log "${RED}[ERROR]${NC}", "$*"; }

# Help function
show_help() {
    cat << EOF
Project Chimera Phase 2 - Distributed Tracing Setup

Usage: $0 [OPTIONS]

Options:
    --action ACTION     Action to perform (install, start, stop, status)
    --format FORMAT     Trace format (json, protobuf)
    --sample-rate RATE   Sampling rate (default: 1.0 = 100%)
    --help              Show this help message

Actions:
    install      Install Jaeger and related components
    start        Start distributed tracing system
    stop         Stop distributed tracing system
    status       Show tracing system status

Environment Variables:
    JAEGER_PORT          Jaeger port (default: 16686)
    JAEGER_UI_PORT        Jaeger UI port (default: 16686)
    TRACE_SAMPLE_RATE     Sampling rate (default: 1.0)

Examples:
    $0 --action install
    $0 --action start
    $0 --action status

EOF
}

# Parse arguments
parse_args() {
    ACTION=""
    FORMAT="json"
    SAMPLE_RATE="1.0"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --action)
                ACTION="$2"
                shift 2
                ;;
            --format)
                FORMAT="$2"
                shift 2
                ;;
            --sample-rate)
                SAMPLE_RATE="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
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

# Install Jaeger
install_jaeger() {
    info "Installing Jaeger distributed tracing system..."

    # Create monitoring directory
    mkdir -p "${PROJECT_ROOT}/monitoring/distributed-tracing"

    # Create docker-compose file for tracing
    cat > "$COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  # Jaeger Collector
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: chimera-jaeger
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
    ports:
      - "5775:5775/udp"       # accept zipkin.thrift over compact thrift
      - "6831:6831/udp"       # accept jaeger.thrift over compact thrift
      - "6832:6832"           # accept jaeger.thrift over binary thrift
      - "9411:9411"           # Collector
      - "16686:16686"         # Jaeger UI
      - "14250:14250"         # HTTP model access
    restart: unless-stopped
    networks:
      - chimera-network

networks:
  chimera-network:
    external: true
    name: chimera-network
EOF

    success "Jaeger installation complete"
}

# Start tracing system
start_tracing() {
    info "Starting distributed tracing system..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Tracing not installed. Run: $0 --action install"
    fi

    # Start Jaeger
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for Jaeger to be ready
    info "Waiting for Jaeger to start..."
    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf http://localhost:$JAEGER_PORT/api/metrics &>/dev/null; then
            success "Jaeger is running"
            break
        fi
        ((attempt++))
        sleep 2
    done

    if [[ $attempt -eq $max_attempts ]]; then
        error "Jaeger failed to start"
        exit 1
    fi

    info "Jaeger UI available at: http://localhost:$JAEGER_UI_PORT"
    info "Distributed tracing ready"
}

# Stop tracing system
stop_tracing() {
    info "Stopping distributed tracing system..."

    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose -f "$COMPOSE_FILE" down
    fi

    success "Distributed tracing stopped"
}

# Show tracing status
show_status() {
    info "Distributed tracing system status..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        echo "Status: Not installed"
        return
    fi

    # Check if Jaeger is running
    if docker ps | grep -q chimera-jaeger; then
        echo "Status: Running"
        echo "Jaeger UI: http://localhost:$JAEGER_UI_PORT"

        # Show trace statistics
        echo ""
        echo "Recent Traces:"
        curl -s http://localhost:$JAEGER_PORT/api/traces?limit=10 2>/dev/null | \
            jq -r '.data[].traceID' 2>/dev/null || echo "No traces yet"
    else
        echo "Status: Stopped"
    fi
}

# Main function
main() {
    parse_args "$@"

    echo "Project Chimera Phase 2 - Distributed Tracing"
    echo "=========================================="
    echo ""

    case "$ACTION" in
        install)
            install_jaeger
            ;;
        start)
            start_tracing
            ;;
        stop)
            stop_tracing
            ;;
        status)
            show_status
            ;;
        *)
            error "Unknown action: $ACTION"
            exit 1
            ;;
    esac
}

main "$@"
