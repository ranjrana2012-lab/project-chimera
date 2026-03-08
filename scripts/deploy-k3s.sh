#!/bin/bash
# K3s Deployment Script for Project Chimera
# This script deploys all Kubernetes manifests in the correct order

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="project-chimera"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
K8S_DIR="${PROJECT_ROOT}/infrastructure/kubernetes"
SERVICES_DIR="${PROJECT_ROOT}/services"

# Functions
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

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    log_success "kubectl found: $(kubectl version --client --short 2>&1 | head -1)"
}

check_context() {
    local current_context=$(kubectl config current-context 2>/dev/null || echo "")
    if [[ -z "$current_context" ]]; then
        log_error "No kubectl context is set. Please set a context first."
        exit 1
    fi
    log_info "Current context: $current_context"

    read -p "Is this the correct K3s context? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Please set the correct kubectl context and try again."
        exit 1
    fi
}

dry_run() {
    local manifest=$1
    log_info "Validating manifest: $manifest"
    if kubectl apply --dry-run=client -f "$manifest"; then
        log_success "Validation passed for: $manifest"
        return 0
    else
        log_error "Validation failed for: $manifest"
        return 1
    fi
}

apply_manifest() {
    local manifest=$1
    local description=${2:-"Applying manifest"}

    log_info "$description: $manifest"
    if kubectl apply -f "$manifest"; then
        log_success "Applied: $manifest"
        return 0
    else
        log_error "Failed to apply: $manifest"
        return 1
    fi
}

wait_for_deployment() {
    local deployment=$1
    local timeout=${2:-300}

    log_info "Waiting for deployment: $deployment (timeout: ${timeout}s)"
    if kubectl rollout status deployment "$deployment" -n "$NAMESPACE" --timeout="${timeout}s"; then
        log_success "Deployment ready: $deployment"
        return 0
    else
        log_error "Deployment failed or timed out: $deployment"
        return 1
    fi
}

wait_for_statefulset() {
    local sts=$1
    local timeout=${2:-300}

    log_info "Waiting for statefulset: $sts (timeout: ${timeout}s)"
    local end=$((SECONDS + timeout))
    while [ $SECONDS -lt $end ]; do
        local ready=$(kubectl get sts "$sts" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local replicas=$(kubectl get sts "$sts" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
        if [ "$ready" = "$replicas" ] && [ "$ready" != "0" ]; then
            log_success "StatefulSet ready: $sts"
            return 0
        fi
        sleep 5
    done
    log_error "StatefulSet timed out: $sts"
    return 1
}

# Main deployment function
deploy_cluster_resources() {
    log_info "=== Phase 1: Deploying Cluster-Level Resources ==="

    local cluster_dir="${K8S_DIR}/cluster"

    # Namespace first
    apply_manifest "${cluster_dir}/namespace.yaml" "Creating namespace"

    # Storage class (may fail if already exists, that's OK)
    log_info "Applying storage class (may already exist)"
    kubectl apply -f "${cluster_dir}/storage-class.yaml" 2>/dev/null || log_warning "Storage class may already exist"

    # Network policy
    apply_manifest "${cluster_dir}/network-policy.yaml" "Creating network policy"

    # Resource quotas
    apply_manifest "${cluster_dir}/resource-quota.yaml" "Creating resource quotas"

    log_success "=== Phase 1 Complete ==="
    echo
}

deploy_infrastructure() {
    log_info "=== Phase 2: Deploying Infrastructure Services ==="

    # Redis
    log_info "Deploying Redis..."
    apply_manifest "${K8S_DIR}/redis/k8s.yaml" "Deploying Redis"
    wait_for_statefulset "redis" 300

    # Kafka
    log_info "Deploying Kafka..."
    apply_manifest "${K8S_DIR}/kafka/k8s.yaml" "Deploying Kafka"
    wait_for_statefulset "kafka" 600

    # Milvus
    log_info "Deploying Milvus..."
    apply_manifest "${K8S_DIR}/milvus/k8s.yaml" "Deploying Milvus"
    # Milvus is a Deployment, not StatefulSet
    kubectl wait --for=condition=available --timeout=600s \
        -n "$NAMESPACE" deployment/milvus 2>/dev/null || log_warning "Milvus deployment check timed out"

    log_success "=== Phase 2 Complete ==="
    echo
}

deploy_services() {
    log_info "=== Phase 3: Deploying Application Services ==="

    # Services in dependency order
    local services=(
        "openclaw-orchestrator:8000"
        "scenespeak-agent:8001"
        "captioning-agent:8002"
        "bsl-agent:8003"
        "sentiment-agent:8004"
        "lighting-sound-music:8005"
        "safety-filter:8006"
        "operator-console:8007"
        "music-generation:8011"
    )

    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port <<< "$service_info"
        local manifest="${SERVICES_DIR}/${service_name}/manifests/k8s.yaml"

        if [[ ! -f "$manifest" ]]; then
            log_warning "Manifest not found: $manifest (skipping)"
            continue
        fi

        log_info "Deploying ${service_name}..."
        apply_manifest "$manifest" "Deploying ${service_name}"

        # Wait for deployment (if applicable)
        if [[ "$service_name" != "lighting-sound-music" ]]; then
            wait_for_deployment "$service_name" 600 || log_warning "Deployment check for ${service_name} timed out"
        fi

        echo
    done

    log_success "=== Phase 3 Complete ==="
    echo
}

deploy_monitoring() {
    log_info "=== Phase 4: Deploying Monitoring Stack ==="

    # Note: Monitoring stack deployment manifests should be created separately
    log_warning "Monitoring stack manifests not yet implemented in this script"
    log_info "Please deploy Prometheus, Grafana, and AlertManager manually"

    log_success "=== Phase 4 Complete (Manual) ==="
    echo
}

verify_deployment() {
    log_info "=== Phase 5: Verifying Deployment ==="

    log_info "Checking all pods in namespace: $NAMESPACE"
    kubectl get pods -n "$NAMESPACE"

    log_info "Checking all services in namespace: $NAMESPACE"
    kubectl get svc -n "$NAMESPACE"

    log_info "Checking all deployments in namespace: $NAMESPACE"
    kubectl get deployments -n "$NAMESPACE"

    log_info "Checking PVCs in namespace: $NAMESPACE"
    kubectl get pvc -n "$NAMESPACE"

    log_success "=== Phase 5 Complete ==="
    echo
}

# Cleanup function
cleanup() {
    log_info "Cleanup function called"
    # Add any cleanup logic here
}

trap cleanup EXIT

# Main execution
main() {
    log_info "=== Project Chimera K3s Deployment ==="
    log_info "Target namespace: $NAMESPACE"
    log_info "Project root: $PROJECT_ROOT"
    echo

    # Pre-flight checks
    check_kubectl
    check_context

    # Parse command line arguments
    DRY_RUN=false
    SKIP_INFRA=false
    SKIP_SERVICES=false
    DEPLOY_MONITORING=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-infra)
                SKIP_INFRA=true
                shift
                ;;
            --skip-services)
                SKIP_SERVICES=true
                shift
                ;;
            --with-monitoring)
                DEPLOY_MONITORING=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --dry-run          Validate all manifests without applying"
                echo "  --skip-infra       Skip infrastructure deployment"
                echo "  --skip-services    Skip service deployment"
                echo "  --with-monitoring  Include monitoring stack deployment"
                echo "  --help             Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    if [[ "$DRY_RUN" == true ]]; then
        log_info "=== DRY RUN MODE - Validating All Manifests ==="
        local all_manifests=(
            "${K8S_DIR}/cluster/namespace.yaml"
            "${K8S_DIR}/cluster/storage-class.yaml"
            "${K8S_DIR}/cluster/network-policy.yaml"
            "${K8S_DIR}/cluster/resource-quota.yaml"
            "${K8S_DIR}/redis/k8s.yaml"
            "${K8S_DIR}/kafka/k8s.yaml"
            "${K8S_DIR}/milvus/k8s.yaml"
        )

        local all_valid=true
        for manifest in "${all_manifests[@]}"; do
            if [[ -f "$manifest" ]]; then
                dry_run "$manifest" || all_valid=false
            else
                log_warning "Manifest not found: $manifest"
            fi
        done

        # Validate service manifests
        for service_dir in "${SERVICES_DIR}"/*/; do
            local manifest="${service_dir}manifests/k8s.yaml"
            if [[ -f "$manifest" ]]; then
                dry_run "$manifest" || all_valid=false
            fi
        done

        if [[ "$all_valid" == true ]]; then
            log_success "=== All manifests validated successfully ==="
            exit 0
        else
            log_error "=== Some manifests failed validation ==="
            exit 1
        fi
    fi

    # Actual deployment
    deploy_cluster_resources

    if [[ "$SKIP_INFRA" == false ]]; then
        deploy_infrastructure
    else
        log_warning "Skipping infrastructure deployment"
    fi

    if [[ "$SKIP_SERVICES" == false ]]; then
        deploy_services
    else
        log_warning "Skipping service deployment"
    fi

    if [[ "$DEPLOY_MONITORING" == true ]]; then
        deploy_monitoring
    fi

    verify_deployment

    log_success "=== Deployment Complete ==="
    log_info "To check pod status: kubectl get pods -n $NAMESPACE"
    log_info "To check logs: kubectl logs -n $NAMESPACE <deployment-name>"
}

main "$@"
