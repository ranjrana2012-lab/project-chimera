#!/bin/bash
# Project Chimera Phase 2 - Monitoring Setup
#
# This script sets up the monitoring stack including Prometheus,
# Grafana, and alerting for Phase 2 services.

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MONITORING_DIR="${PROJECT_ROOT}/monitoring"
COMPOSE_FILE="${MONITORING_DIR}/docker-compose.monitoring.yml"

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
Project Chimera Phase 2 - Monitoring Setup

Usage: $0 [OPTIONS]

Options:
    --action ACTION     Action to perform (install, start, stop, status)
    --help              Show this help message

Actions:
    install      Install monitoring stack
    start        Start monitoring services
    stop         Stop monitoring services
    status       Show monitoring status

Services:
    Prometheus    http://localhost:9090
    Grafana       http://localhost:3000 (admin/chimera)
    AlertManager  http://localhost:9093

Examples:
    $0 --action install
    $0 --action start
    $0 --action status

EOF
}

# Parse arguments
parse_args() {
    ACTION=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --action)
                ACTION="$2"
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

# Create Grafana provisioning
setup_grafana_provisioning() {
    info "Setting up Grafana provisioning..."

    mkdir -p "${MONITORING_DIR}/grafana/provisioning/datasources"
    mkdir -p "${MONITORING_DIR}/grafana/provisioning/dashboards"

    # Create datasource config
    cat > "${MONITORING_DIR}/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Create dashboard provider config
    cat > "${MONITORING_DIR}/grafana/provisioning/dashboards/dashboards.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'Chimera Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    success "Grafana provisioning configured"
}

# Create AlertManager config
setup_alertmanager() {
    info "Setting up AlertManager..."

    mkdir -p "${MONITORING_DIR}/alertmanager"

    cat > "${MONITORING_DIR}/alertmanager/alertmanager.yml" << 'EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'

receivers:
  - name: 'default'
    # webhook_configs:
    #   - url: 'http://localhost:5001/alerts'
EOF

    success "AlertManager configured"
}

# Install monitoring stack
install_monitoring() {
    info "Installing monitoring stack..."

    # Create directories
    mkdir -p "${MONITORING_DIR}/prometheus/rules"
    mkdir -p "${MONITORING_DIR}/grafana/dashboards"
    mkdir -p "${MONITORING_DIR}/alertmanager"

    # Setup configurations
    setup_grafana_provisioning
    setup_alertmanager

    # Create network if it doesn't exist
    if ! docker network inspect chimera-network &>/dev/null; then
        docker network create chimera-network
        info "Created chimera-network"
    fi

    success "Monitoring stack installation complete"
}

# Start monitoring services
start_monitoring() {
    info "Starting monitoring stack..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Monitoring not installed. Run: $0 --action install"
        exit 1
    fi

    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be ready
    info "Waiting for services to start..."
    sleep 5

    # Check services
    check_services

    success "Monitoring stack started"
    info ""
    info "Access dashboards:"
    info "  Prometheus: http://localhost:9090"
    info "  Grafana:    http://localhost:3000 (admin/chimera)"
    info "  AlertManager: http://localhost:9093"
}

# Stop monitoring services
stop_monitoring() {
    info "Stopping monitoring stack..."

    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose -f "$COMPOSE_FILE" down
    fi

    success "Monitoring stack stopped"
}

# Check service health
check_services() {
    info "Checking service health..."

    local services=(
        "Prometheus:9090"
        "Grafana:3000"
        "AlertManager:9093"
    )

    for service in "${services[@]}"; do
        local name="${service%:*}"
        local port="${service#*:}"

        if curl -sf "http://localhost:$port" &>/dev/null; then
            success "✓ $name is running"
        else
            error "✗ $name is not accessible"
        fi
    done
}

# Show monitoring status
show_status() {
    info "Monitoring stack status..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        echo "Status: Not installed"
        return
    fi

    # Show running containers
    echo ""
    echo "Running containers:"
    docker-compose -f "$COMPOSE_FILE" ps

    # Check service health
    echo ""
    check_services
}

# Main function
main() {
    parse_args "$@"

    echo "Project Chimera Phase 2 - Monitoring Setup"
    echo "=========================================="
    echo ""

    case "$ACTION" in
        install)
            install_monitoring
            ;;
        start)
            start_monitoring
            ;;
        stop)
            stop_monitoring
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
