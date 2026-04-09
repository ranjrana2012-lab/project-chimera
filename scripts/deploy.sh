#!/bin/bash
# Project Chimera Phase 2 - Automated Deployment Script
#
# This script handles production deployment of Phase 2 services
# with health checks, rolling updates, and rollback capabilities.
#
# Usage:
#   ./deploy.sh --env production --service all
#   ./deploy.sh --env staging --service dmx --dry-run
#   ./deploy.sh --rollback

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/deploy_$(date +%Y%m%d_%H%M%S).log"

# Deployment configuration
DEPLOYMENT_USER="${DEPLOYMENT_USER:-chimera}"
DEPLOYMENT_HOST="${DEPLOYMENT_HOST:-localhost}"
DEPLOYMENT_PORT="${DEPLOYMENT_PORT:-22}"
DEPLOYMENT_PATH="${DEPLOYMENT_PATH:-/opt/chimera}"
COMPOSE_FILE="${PROJECT_ROOT}/services/docker-compose.phase2.yml"

# Health check configuration
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-5}"

# Backup configuration
BACKUP_DIR="${PROJECT_ROOT}/backups"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() { log "INFO", "${BLUE}$*${NC}"; }
success() { log "SUCCESS", "${GREEN}$*${NC}"; }
warning() { log "WARNING", "${YELLOW}$*${NC}"; }
error() { log "ERROR", "${RED}$*${NC}"; }

# Error handling
trap 'error "Script failed at line $LINENO"' ERR

# Help function
show_help() {
    cat << EOF
Project Chimera Phase 2 - Deployment Script

Usage: $0 [OPTIONS]

Options:
    --env ENVIRONMENT         Deployment environment (production, staging, development)
    --service SERVICE         Service to deploy (dmx, audio, bsl, all)
    --dry-run                Show what would be done without making changes
    --rollback               Rollback to previous deployment
    --skip-backup            Skip backup before deployment
    --skip-health-check      Skip post-deployment health check
    --force                  Force deployment even if health check fails
    --help                   Show this help message

Examples:
    $0 --env production --service all
    $0 --env staging --service dmx --dry-run
    $0 --rollback

Environment Variables:
    DEPLOYMENT_USER          User for deployment (default: chimera)
    DEPLOYMENT_HOST          Target host (default: localhost)
    DEPLOYMENT_PORT          SSH port (default: 22)
    DEPLOYMENT_PATH          Deployment path (default: /opt/chimera)
    HEALTH_CHECK_TIMEOUT     Health check timeout in seconds (default: 300)
    HEALTH_CHECK_INTERVAL    Health check interval in seconds (default: 5)

EOF
}

# Parse command line arguments
parse_args() {
    ENVIRONMENT=""
    SERVICE=""
    DRY_RUN=false
    ROLLBACK=false
    SKIP_BACKUP=false
    SKIP_HEALTH_CHECK=false
    FORCE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --service)
                SERVICE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-health-check)
                SKIP_HEALTH_CHECK=true
                shift
                ;;
            --force)
                FORCE=true
                shift
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

    # Validate arguments
    if [[ "$ROLLBACK" == false ]]; then
        if [[ -z "$ENVIRONMENT" ]]; then
            error "--env is required"
            show_help
            exit 1
        fi
        if [[ ! "$ENVIRONMENT" =~ ^(production|staging|development)$ ]]; then
            error "Invalid environment: $ENVIRONMENT"
            exit 1
        fi
        if [[ -z "$SERVICE" ]]; then
            error "--service is required"
            show_help
            exit 1
        fi
        if [[ ! "$SERVICE" =~ ^(dmx|audio|bsl|all)$ ]]; then
            error "Invalid service: $SERVICE"
            exit 1
        fi
    fi
}

# Pre-flight checks
preflight_checks() {
    info "Running pre-flight checks..."

    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root is not recommended"
    fi

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi

    # Check if .env file exists
    if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
        error ".env file not found"
        exit 1
    fi

    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    # Check disk space
    local available_space=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')
    if [[ $available_space -lt 5 ]]; then
        error "Insufficient disk space: ${available_space}G available, 5G required"
        exit 1
    fi

    # Create log directory
    mkdir -p "$LOG_DIR"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    success "Pre-flight checks passed"
}

# Backup current deployment
backup_deployment() {
    if [[ "$SKIP_BACKUP" == true ]]; then
        warning "Skipping backup"
        return
    fi

    info "Creating deployment backup..."

    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="${BACKUP_DIR}/${backup_name}"

    mkdir -p "$backup_path"

    # Backup configuration
    cp -r "${PROJECT_ROOT}/.env" "$backup_path/" 2>/dev/null || true
    cp -r "${PROJECT_ROOT}/services/config" "$backup_path/" 2>/dev/null || true

    # Backup data
    cp -r "${PROJECT_ROOT}/services/data" "$backup_path/" 2>/dev/null || true

    # Create backup info
    cat > "$backup_path/backup_info.txt" << EOF
Backup Date: $(date)
Environment: $ENVIRONMENT
Service: $SERVICE
Git Commit: $(git rev-parse HEAD) 2>/dev/null || echo "N/A"
Git Branch: $(git rev-parse --abbrev-ref HEAD) 2>/dev/null || echo "N/A"
EOF

    success "Backup created: $backup_path"

    # Clean old backups
    info "Cleaning old backups (retention: ${BACKUP_RETENTION_DAYS} days)..."
    find "$BACKUP_DIR" -type d -name "backup_*" -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} +
}

# Build Docker images
build_images() {
    info "Building Docker images..."

    local services_to_build=()

    case "$SERVICE" in
        dmx)
            services_to_build=("dmx-controller")
            ;;
        audio)
            services_to_build=("audio-controller")
            ;;
        bsl)
            services_to_build=("bsl-avatar-service")
            ;;
        all)
            services_to_build=("dmx-controller" "audio-controller" "bsl-avatar-service")
            ;;
    esac

    for service in "${services_to_build[@]}"; do
        info "Building $service..."
        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY RUN] Would build: $service"
        else
            docker-compose -f "$COMPOSE_FILE" build "$service"
        fi
    done

    success "Docker images built successfully"
}

# Stop current services
stop_services() {
    info "Stopping current services..."

    local services_to_stop=()

    case "$SERVICE" in
        dmx)
            services_to_stop=("dmx-controller")
            ;;
        audio)
            services_to_stop=("audio-controller")
            ;;
        bsl)
            services_to_stop=("bsl-avatar-service")
            ;;
        all)
            services_to_stop=("dmx-controller" "audio-controller" "bsl-avatar-service")
            ;;
    esac

    for service in "${services_to_stop[@]}"; do
        info "Stopping $service..."
        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY RUN] Would stop: $service"
        else
            docker-compose -f "$COMPOSE_FILE" stop "$service"
        fi
    done

    success "Services stopped"
}

# Start new services
start_services() {
    info "Starting new services..."

    local services_to_start=()

    case "$SERVICE" in
        dmx)
            services_to_start=("dmx-controller")
            ;;
        audio)
            services_to_start=("audio-controller")
            ;;
        bsl)
            services_to_start=("bsl-avatar-service")
            ;;
        all)
            services_to_start=("dmx-controller" "audio-controller" "bsl-avatar-service")
            ;;
    esac

    for service in "${services_to_start[@]}"; do
        info "Starting $service..."
        if [[ "$DRY_RUN" == true ]]; then
            echo "[DRY RUN] Would start: $service"
        else
            docker-compose -f "$COMPOSE_FILE" up -d "$service"
        fi
    done

    success "Services started"
}

# Health check
health_check() {
    if [[ "$SKIP_HEALTH_CHECK" == true ]]; then
        warning "Skipping health check"
        return
    fi

    info "Running health checks..."

    local services_to_check=()
    local ports=()

    case "$SERVICE" in
        dmx)
            services_to_check=("DMX Controller")
            ports=("8001")
            ;;
        audio)
            services_to_check=("Audio Controller")
            ports=("8002")
            ;;
        bsl)
            services_to_check=("BSL Avatar Service")
            ports=("8003")
            ;;
        all)
            services_to_check=("DMX Controller" "Audio Controller" "BSL Avatar Service")
            ports=("8001" "8002" "8003")
            ;;
    esac

    local start_time=$(date +%s)
    local all_healthy=false

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [[ $elapsed -gt $HEALTH_CHECK_TIMEOUT ]]; then
            if [[ "$FORCE" == true ]]; then
                warning "Health check timeout exceeded, but continuing due to --force"
                break
            else
                error "Health check timeout exceeded"
                error "Deployment failed health check"
                exit 1
            fi
        fi

        local healthy_count=0
        local total_count=${#services_to_check[@]}

        for i in "${!services_to_check[@]}"; do
            local service="${services_to_check[$i]}"
            local port="${ports[$i]}"

            if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
                ((healthy_count++))
                echo -n "."
            else
                echo -n "X"
            fi
        done

        echo ""  # New line

        if [[ $healthy_count -eq $total_count ]]; then
            success "All services are healthy"
            all_healthy=true
            break
        else
            info "Waiting for services... (${healthy_count}/${total_count} healthy)"
            sleep $HEALTH_CHECK_INTERVAL
        fi
    done
}

# Rollback deployment
rollback_deployment() {
    info "Rolling back deployment..."

    # Find latest backup
    local latest_backup=$(ls -t "${BACKUP_DIR}/backup_"* 2>/dev/null | head -1)

    if [[ -z "$latest_backup" ]]; then
        error "No backup found for rollback"
        exit 1
    fi

    info "Rolling back to: $latest_backup"

    # Stop current services
    info "Stopping current services..."
    docker-compose -f "$COMPOSE_FILE" down

    # Restore backup
    info "Restoring backup..."
    cp -r "${latest_backup}/.env" "${PROJECT_ROOT}/" 2>/dev/null || true
    cp -r "${latest_backup}/config" "${PROJECT_ROOT}/services/" 2>/dev/null || true
    cp -r "${latest_backup}/data" "${PROJECT_ROOT}/services/" 2>/dev/null || true

    # Restart services
    info "Restarting services..."
    docker-compose -f "$COMPOSE_FILE" up -d

    success "Rollback completed"
}

# Cleanup old images
cleanup_images() {
    info "Cleaning up old Docker images..."

    if [[ "$DRY_RUN" == true ]]; then
        echo "[DRY RUN] Would clean up old images"
    else
        docker image prune -af --filter "until=72h"
    fi

    success "Cleanup completed"
}

# Generate deployment report
generate_report() {
    local report_file="${LOG_DIR}/deploy_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Project Chimera Phase 2 - Deployment Report
===========================================

Deployment Date: $(date)
Environment: $ENVIRONMENT
Service: $SERVICE
Dry Run: $DRY_RUN
Rollback: $ROLLBACK

Deployment Details:
-------------------
EOF

    if [[ "$ROLLBACK" == true ]]; then
        cat >> "$report_file" << EOF
Action: Rollback
Status: Completed
EOF
    else
        cat >> "$report_file" << EOF
Action: Deploy
Services Deployed: $SERVICE
Backup Created: $(if [[ "$SKIP_BACKUP" == false ]]; then echo "Yes"; else echo "No"; fi)
Health Check: $(if [[ "$SKIP_HEALTH_CHECK" == false ]]; then echo "Passed"; else echo "Skipped"; fi)

Current Service Status:
--------------------
EOF

        # Add service status
        case "$SERVICE" in
            dmx|all)
                echo "DMX Controller (8001): $(curl -s http://localhost:8001/health 2>/dev/null && echo "Healthy" || echo "Unhealthy")" >> "$report_file"
                ;;
        esac
        case "$SERVICE" in
            audio|all)
                echo "Audio Controller (8002): $(curl -s http://localhost:8002/health 2>/dev/null && echo "Healthy" || echo "Unhealthy")" >> "$report_file"
                ;;
        esac
        case "$SERVICE" in
            bsl|all)
                echo "BSL Avatar Service (8003): $(curl -s http://localhost:8003/health 2>/dev/null && echo "Healthy" || echo "Unhealthy")" >> "$report_file"
                ;;
        esac
    fi

    cat >> "$report_file" << EOF

Logs:
-----
Full deployment log: $LOG_FILE

EOF

    success "Deployment report generated: $report_file"
}

# Main deployment function
deploy() {
    info "Starting deployment..."
    info "Environment: $ENVIRONMENT"
    info "Service: $SERVICE"
    info "Dry Run: $DRY_RUN"

    # Pre-flight checks
    preflight_checks

    # Handle rollback
    if [[ "$ROLLBACK" == true ]]; then
        rollback_deployment
        generate_report
        return
    fi

    # Deployment steps
    backup_deployment
    build_images
    stop_services
    start_services
    health_check
    cleanup_images
    generate_report

    success "Deployment completed successfully!"
}

# Main script execution
main() {
    # Parse arguments
    parse_args "$@"

    # Display banner
    cat << EOF
╔══════════════════════════════════════════════════════════╗
║   Project Chimera Phase 2 - Automated Deployment        ║
║   Version: 1.0.0                                         ║
╚══════════════════════════════════════════════════════════╝
EOF

    # Run deployment
    deploy
}

# Run main function
main "$@"
