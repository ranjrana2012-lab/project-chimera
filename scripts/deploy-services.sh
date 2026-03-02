#!/bin/bash
#
# Project Chimera Services Deployment Script
#
# This script deploys all Project Chimera services to the k3s cluster.
# It requires kubectl to be configured with access to the cluster.
#
# Usage: sudo ./scripts/deploy-services.sh [NAMESPACE]
#
# Arguments:
#   NAMESPACE - Kubernetes namespace to deploy to (default: live)
#
# This script will:
#   1. Check for sudo privileges
#   2. Verify k3s/kubectl access
#   3. Deploy infrastructure services
#   4. Deploy monitoring stack
#   5. Deploy AI services
#   6. Configure networking
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${1:-live}"
REGISTRY="localhost:30500"
VERSION="latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Services to deploy
SERVICES=(
    "openclaw-orchestrator"
    "scenespeak-agent"
    "captioning-agent"
    "bsl-text2gloss-agent"
    "sentiment-agent"
    "lighting-control"
    "safety-filter"
    "operator-console"
)

################################################################################
# Helper Functions
################################################################################

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print progress header
print_header() {
    local step=$1
    local total=$2
    local message=$3
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}[${step}/${total}]${NC} ${message}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if running with sudo privileges
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        print_warning "Running without sudo. Some operations may fail."
        print_info "For full functionality, run: sudo $0 $NAMESPACE"
    else
        print_info "Running with sudo privileges"
    fi
}

# Verify kubectl access
verify_kubectl() {
    print_info "Verifying kubectl access..."

    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        print_info "Install with: sudo apt-get install kubectl"
        exit 1
    fi

    if ! kubectl get nodes &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_info "Make sure k3s is installed and running"
        exit 1
    fi

    print_success "kubectl access verified"
}

# Verify namespace exists
verify_namespace() {
    print_info "Verifying namespace '$NAMESPACE' exists..."

    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_warning "Namespace '$NAMESPACE' does not exist. Creating..."
        kubectl create namespace "$NAMESPACE"
        print_success "Namespace '$NAMESPACE' created"
    else
        print_success "Namespace '$NAMESPACE' exists"
    fi
}

# Verify shared namespace exists
verify_shared_namespace() {
    print_info "Verifying shared namespace exists..."

    if ! kubectl get namespace shared &> /dev/null; then
        print_warning "Shared namespace does not exist. Creating..."
        kubectl create namespace shared
        print_success "Shared namespace created"
    else
        print_success "Shared namespace exists"
    fi
}

################################################################################
# Step 1: Deploy Infrastructure Services
################################################################################

deploy_infrastructure() {
    print_header "1" "5" "Deploying infrastructure services"

    local namespace="shared"

    # Check if registry namespace exists
    if ! kubectl get namespace registry &> /dev/null; then
        print_info "Creating registry namespace..."
        kubectl create namespace registry
    fi

    # Deploy Redis
    print_info "Deploying Redis..."
    if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/base/redis/kustomization.yaml" ]; then
        kubectl apply -k "$PROJECT_ROOT/infrastructure/kubernetes/base/redis/" -n $namespace

        # Wait for Redis to be ready
        print_info "Waiting for Redis to be ready..."
        local max_attempts=60
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if kubectl get pods -n $namespace -l app=redis 2>/dev/null | grep -q "Running"; then
                break
            fi
            sleep 2
            attempt=$((attempt + 1))
        done
        print_success "Redis deployed"
    else
        print_warning "Redis configuration not found, skipping..."
    fi

    # Deploy Kafka
    print_info "Deploying Kafka..."
    if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/base/kafka/kustomization.yaml" ]; then
        kubectl apply -k "$PROJECT_ROOT/infrastructure/kubernetes/base/kafka/" -n $namespace

        # Wait for Kafka to be ready
        print_info "Waiting for Kafka to be ready..."
        local max_attempts=90
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if kubectl get pods -n $namespace -l app=kafka 2>/dev/null | grep -q "Running"; then
                break
            fi
            sleep 2
            attempt=$((attempt + 1))
        done
        print_success "Kafka deployed"
    else
        print_warning "Kafka configuration not found, skipping..."
    fi

    # Deploy Vector DB (Milvus)
    print_info "Deploying Milvus (Vector DB)..."
    if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/base/vector-db/kustomization.yaml" ]; then
        kubectl apply -k "$PROJECT_ROOT/infrastructure/kubernetes/base/vector-db/" -n $namespace

        # Wait for Milvus to be ready
        print_info "Waiting for Milvus to be ready..."
        local max_attempts=90
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if kubectl get pods -n $namespace -l app=milvus 2>/dev/null | grep -q "Running"; then
                break
            fi
            sleep 2
            attempt=$((attempt + 1))
        done
        print_success "Milvus deployed"
    else
        print_warning "Vector DB configuration not found, skipping..."
    fi

    print_success "Infrastructure services deployed"
    kubectl get svc -n $namespace || true
}

################################################################################
# Step 2: Deploy Monitoring Stack
################################################################################

deploy_monitoring() {
    print_header "2" "5" "Deploying monitoring stack"

    local namespace="shared"

    # Deploy Prometheus
    print_info "Deploying Prometheus..."
    if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/base/monitoring/prometheus/kustomization.yaml" ]; then
        kubectl apply -k "$PROJECT_ROOT/infrastructure/kubernetes/base/monitoring/prometheus/" -n $namespace
        print_success "Prometheus deployed"
    else
        print_warning "Prometheus configuration not found, skipping..."
    fi

    # Deploy Grafana
    print_info "Deploying Grafana..."
    if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/base/monitoring/grafana/kustomization.yaml" ]; then
        kubectl apply -k "$PROJECT_ROOT/infrastructure/kubernetes/base/monitoring/grafana/" -n $namespace
        print_success "Grafana deployed"
    else
        print_warning "Grafana configuration not found, skipping..."
    fi

    # Deploy Jaeger
    print_info "Deploying Jaeger..."
    if [ -f "$PROJECT_ROOT/infrastructure/kubernetes/base/monitoring/jaeger/kustomization.yaml" ]; then
        kubectl apply -k "$PROJECT_ROOT/infrastructure/kubernetes/base/monitoring/jaeger/" -n $namespace
        print_success "Jaeger deployed"
    else
        print_warning "Jaeger configuration not found, skipping..."
    fi

    # Wait for monitoring services
    print_info "Waiting for monitoring services to be ready..."
    kubectl wait --for=condition=ready -n $namespace pod -l app=prometheus --timeout=180s 2>/dev/null || print_warning "Prometheus not ready"
    kubectl wait --for=condition=ready -n $namespace pod -l app=grafana --timeout=180s 2>/dev/null || print_warning "Grafana not ready"
    kubectl wait --for=condition=ready -n $namespace pod -l app=jaeger --timeout=180s 2>/dev/null || print_warning "Jaeger not ready"

    # Kill existing port forwards
    pkill -f "port-forward.*prometheus" || true
    pkill -f "port-forward.*grafana" || true
    pkill -f "port-forward.*jaeger" || true

    # Start port forwards for monitoring services
    print_info "Setting up port forwards..."
    nohup kubectl port-forward -n $namespace svc/prometheus 9090:9090 > /dev/null 2>&1 &
    nohup kubectl port-forward -n $namespace svc/grafana 3000:3000 > /dev/null 2>&1 &
    nohup kubectl port-forward -n $namespace svc/jaeger 16686:16686 > /dev/null 2>&1 &

    sleep 3

    print_success "Monitoring stack deployed"
    print_info "Grafana: http://localhost:3000 (admin/admin)"
    print_info "Prometheus: http://localhost:9090"
    print_info "Jaeger: http://localhost:16686"
}

################################################################################
# Step 3: Deploy AI Services
################################################################################

deploy_ai_services() {
    print_header "3" "5" "Deploying AI services"

    local deployed_count=0
    local failed_count=0

    for service in "${SERVICES[@]}"; do
        local service_dir="$PROJECT_ROOT/infrastructure/kubernetes/base/$service"
        local deployment_file="$service_dir/deployment.yaml"
        local service_file="$service_dir/service.yaml"

        if [ ! -f "$deployment_file" ]; then
            print_warning "Deployment file not found for $service"
            failed_count=$((failed_count + 1))
            continue
        fi

        print_info "Deploying $service..."

        # Apply deployment
        if kubectl apply -f "$deployment_file" -n $NAMESPACE 2>&1; then
            # Apply service if exists
            if [ -f "$service_file" ]; then
                kubectl apply -f "$service_file" -n $NAMESPACE 2>/dev/null || true
            fi

            # Wait for rollout (with timeout)
            if kubectl rollout status deployment/$service -n $NAMESPACE --timeout=300s 2>/dev/null; then
                print_success "$service deployed"
                deployed_count=$((deployed_count + 1))
            else
                print_warning "$service deployment timed out"
                failed_count=$((failed_count + 1))
            fi
        else
            print_error "Failed to deploy $service"
            failed_count=$((failed_count + 1))
        fi
    done

    print_success "AI services deployment complete"
    echo "  Deployed: $deployed_count"
    echo "  Failed/Warnings: $failed_count"

    # Show pods
    kubectl get pods -n $NAMESPACE || true
}

################################################################################
# Step 4: Configure Network Policies
################################################################################

configure_networking() {
    print_header "4" "5" "Configuring network policies"

    local network_dir="$PROJECT_ROOT/infrastructure/kubernetes/base/network-policies"

    if [ -d "$network_dir" ]; then
        print_info "Applying network policies..."
        for policy_file in "$network_dir"/*.yaml; do
            if [ -f "$policy_file" ]; then
                print_info "Applying $(basename "$policy_file")..."
                kubectl apply -f "$policy_file" || print_warning "Failed to apply $(basename "$policy_file")"
            fi
        done
        print_success "Network policies configured"
    else
        print_info "No network policies found, skipping..."
    fi

    # Apply priority classes if they exist
    local priority_dir="$PROJECT_ROOT/infrastructure/kubernetes/base/priority-classes"
    if [ -d "$priority_dir" ]; then
        print_info "Applying priority classes..."
        kubectl apply -f "$priority_dir/" || print_warning "Failed to apply priority classes"
    fi
}

################################################################################
# Step 5: Display Service Status
################################################################################

display_status() {
    print_header "5" "5" "Service status"

    echo ""
    print_info "Services in '$NAMESPACE' namespace:"
    kubectl get pods -n $NAMESPACE

    echo ""
    print_info "Services in 'shared' namespace:"
    kubectl get pods -n shared

    echo ""
    print_info "Services status:"
    kubectl get svc -n $NAMESPACE

    echo ""
    print_info "To view logs for a service:"
    echo "  kubectl logs -f deployment/<service-name> -n $NAMESPACE"
    echo ""
    print_info "To get shell access to a pod:"
    echo "  kubectl exec -it <pod-name> -n $NAMESPACE -- /bin/bash"
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Project Chimera Services Deployment${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Target namespace: $NAMESPACE"
    echo ""

    # Pre-flight checks
    check_sudo
    verify_kubectl
    verify_namespace
    verify_shared_namespace

    # Deploy components
    deploy_infrastructure
    deploy_monitoring
    deploy_ai_services
    configure_networking
    display_status

    # Print completion message
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Services Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    print_success "All services deployed to namespace '$NAMESPACE'"
    echo ""
    echo "Next Steps:"
    echo "  1. Run: ./scripts/verify-deployment.sh"
    echo "  2. Check pod status: kubectl get pods -n $NAMESPACE"
    echo "  3. View logs: kubectl logs -f deployment/openclaw-orchestrator -n $NAMESPACE"
    echo ""
}

# Change to project root
cd "$PROJECT_ROOT"

# Run main function
main "$@"
