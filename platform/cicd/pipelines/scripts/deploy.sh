#!/bin/bash
set -euo pipefail

# Project Chimera - Automated Deployment Script
# Usage: ./deploy.sh <environment> <version>

ENVIRONMENT=${1:-preprod}
VERSION=${2:-latest}
HELM_CHART="./platform/deployment/helm/project-chimera"
NAMESPACE="chimera-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
pre_deploy_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check Helm
    if ! command -v helm &> /dev/null; then
        log_error "Helm not installed"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "Namespace $NAMESPACE does not exist, creating..."
        kubectl create namespace "$NAMESPACE"
    fi
    
    log_info "Pre-deployment checks passed"
}

# Get current release info
get_current_release() {
    helm list -n "$NAMESPACE" -f "^chimera$" -q || echo ""
}

# Deploy function
deploy() {
    local release_name="chimera"
    
    log_info "Deploying version $VERSION to $ENVIRONMENT..."
    
    # Helm upgrade with atomic (rollback on failure)
    helm upgrade "$release_name" "$HELM_CHART" \
        --namespace "$NAMESPACE" \
        --install \
        --values "$HELM_CHART/values.yaml" \
        --set images.tag="$VERSION" \
        --wait \
        --timeout 15m \
        --atomic \
        --cleanup-on-fail
    
    log_info "Deployment completed successfully"
}

# Post-deployment verification
post_deploy_checks() {
    log_info "Running post-deployment checks..."
    
    # Wait for deployments to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=chimera -n "$NAMESPACE" --timeout=300s
    
    log_info "Pod status:"
    kubectl get pods -n "$NAMESPACE"
    
    log_info "Service status:"
    kubectl get svc -n "$NAMESPACE"
    
    log_info "Post-deployment checks passed"
}

# Main deployment flow
main() {
    log_info "Starting deployment to $ENVIRONMENT..."
    log_info "Version: $VERSION"
    
    pre_deploy_checks
    deploy
    post_deploy_checks
    
    log_info "Deployment completed successfully!"
}

# Trap errors
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"
