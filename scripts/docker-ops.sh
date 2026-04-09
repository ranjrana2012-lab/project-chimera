#!/bin/bash
# Project Chimera Phase 2 - Docker Operations Script
#
# This script manages Docker operations for Phase 2 services.
#
# Usage:
#   chmod +x scripts/docker-ops.sh
#   ./scripts/docker-ops.sh [command]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo ""
    echo "=================================="
    echo "$1"
    echo "=================================="
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Show usage
show_usage() {
    cat << EOF
Project Chimera Phase 2 - Docker Operations

Usage: ./scripts/docker-ops.sh [command]

Commands:
  build       Build all Docker images
  up          Start all services
  down        Stop all services
  restart     Restart all services
  logs        Show logs from all services
  status      Show status of all services
  clean       Remove all containers, volumes, and images
  help        Show this help message

Examples:
  ./scripts/docker-ops.sh build
  ./scripts/docker-ops.sh up
  ./scripts/docker-ops.sh logs dmx-controller
EOF
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found"
        print_info "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not found"
        print_info "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Build Docker images
build_images() {
    print_header "Building Docker Images"

    print_info "Building Phase 2 services..."
    docker-compose -f services/docker-compose.phase2.yml build

    print_success "Docker images built"
}

# Start services
start_services() {
    print_header "Starting Phase 2 Services"

    print_info "Starting services..."
    docker-compose -f services/docker-compose.phase2.yml up -d

    print_success "Services started"

    print_info "Service URLs:"
    echo "  DMX Controller:    http://localhost:8001"
    echo "  Audio Controller:  http://localhost:8002"
    echo "  BSL Avatar:        http://localhost:8003"
    echo "  Prometheus:        http://localhost:9090"
    echo "  Grafana:           http://localhost:3000"
}

# Stop services
stop_services() {
    print_header "Stopping Phase 2 Services"

    print_info "Stopping services..."
    docker-compose -f services/docker-compose.phase2.yml down

    print_success "Services stopped"
}

# Restart services
restart_services() {
    print_header "Restarting Phase 2 Services"

    stop_services
    sleep 2
    start_services
}

# Show logs
show_logs() {
    local service=$1

    if [ -z "$service" ]; then
        print_info "Showing logs from all services (Ctrl+C to exit)..."
        docker-compose -f services/docker-compose.phase2.yml logs -f
    else
        print_info "Showing logs from $service (Ctrl+C to exit)..."
        docker-compose -f services/docker-compose.phase2.yml logs -f "$service"
    fi
}

# Show status
show_status() {
    print_header "Phase 2 Services Status"

    docker-compose -f services/docker-compose.phase2.yml ps
}

# Clean up
clean_up() {
    print_header "Cleaning Up Docker Resources"

    print_info "Stopping and removing containers..."
    docker-compose -f services/docker-compose.phase2.yml down -v

    print_info "Removing volumes..."
    docker volume rm project-chimera_prometheus-data 2>/dev/null || true
    docker volume rm project-chimera_grafana-data 2>/dev/null || true

    print_info "Removing images..."
    docker rmi chimera-dmx-controller chimera-audio-controller chimera-bsl-avatar 2>/dev/null || true

    print_success "Cleanup complete"
}

# Main function
main() {
    check_docker

    case "${1:-help}" in
        build)
            build_images
            ;;
        up)
            start_services
            ;;
        down)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs "$2"
            ;;
        status)
            show_status
            ;;
        clean)
            clean_up
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
