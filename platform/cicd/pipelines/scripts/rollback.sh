#!/bin/bash
set -euo pipefail

# Project Chimera - Rollback Script
# Usage: ./rollback.sh <environment> [release]

ENVIRONMENT=${1:-preprod}
TARGET_RELEASE=${2:-}
NAMESPACE="chimera-${ENVIRONMENT}"
RELEASE_NAME="chimera"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# List available releases
list_releases() {
    log_info "Available releases:"
    helm history -n "$NAMESPACE" "$RELEASE_NAME" -o table
}

# Confirm rollback
confirm_rollback() {
    local current_revision=$(helm list -n "$NAMESPACE" -f "^${RELEASE_NAME}$" -o json | jq -r '.[0].revision // "unknown"')
    local target_revision=${1}
    
    log_warn "You are about to rollback the $RELEASE_NAME release in $NAMESPACE"
    log_warn "Current revision: $current_revision"
    log_warn "Target revision: $target_revision"
    
    read -p "Are you sure you want to proceed? (yes/no): " confirmation
    if [ "$confirmation" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi
}

# Perform rollback
do_rollback() {
    local target=$1
    
    log_info "Rolling back to $target..."
    
    if [ -z "$target" ]; then
        # Rollback to previous release
        helm rollback -n "$NAMESPACE" "$RELEASE_NAME"
    else
        # Rollback to specific release
        helm rollback -n "$NAMESPACE" "$RELEASE_NAME" "$target"
    fi
    
    log_info "Rollback initiated"
}

# Verify rollback
verify_rollback() {
    log_info "Waiting for rollback to complete..."
    
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance="$RELEASE_NAME" -n "$NAMESPACE" --timeout=300s
    
    log_info "Rollback completed successfully"
    log_info "Current pod status:"
    kubectl get pods -n "$NAMESPACE"
}

# Main rollback flow
main() {
    log_info "Starting rollback for $ENVIRONMENT..."
    
    # Check if release exists
    if ! helm list -n "$NAMESPACE" -f "^${RELEASE_NAME}$" -q &> /dev/null; then
        log_error "Release $RELEASE_NAME not found in namespace $NAMESPACE"
        exit 1
    fi
    
    list_releases
    
    if [ -z "$TARGET_RELEASE" ]; then
        # Interactive mode
        read -p "Enter target revision (or press Enter for previous): " target
    else
        target="$TARGET_RELEASE"
    fi
    
    confirm_rollback "$target"
    do_rollback "$target"
    verify_rollback
    
    log_info "Rollback completed successfully!"
}

main "$@"
