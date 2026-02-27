#!/bin/bash
#
# Project Chimera Deployment Verification Script
#
# This script verifies that all Project Chimera services are running correctly.
# It performs health checks on all deployed services.
#
# Usage: sudo ./scripts/verify-deployment.sh [NAMESPACE]
#
# Arguments:
#   NAMESPACE - Kubernetes namespace to verify (default: live)
#
# This script will:
#   1. Check for sudo privileges
#   2. Verify k3s/kubectl access
#   3. Check pod status
#   4. Check service endpoints
#   5. Perform health checks on services
#   6. Display monitoring dashboard URLs
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Services to verify
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

# Infrastructure services
INFRA_SERVICES=(
    "redis"
    "kafka"
    "milvus"
)

# Monitoring services
MONITORING_SERVICES=(
    "prometheus"
    "grafana"
    "jaeger"
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
    if [ "$EUID" -eq 0 ]; then
        print_info "Running with sudo privileges"
    else
        print_info "Running without sudo"
    fi
}

# Verify kubectl access
verify_kubectl() {
    print_info "Verifying kubectl access..."

    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        return 1
    fi

    if ! kubectl get nodes &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        return 1
    fi

    print_success "kubectl access verified"
    return 0
}

# Get pod status
get_pod_status() {
    local namespace=$1
    local app_label=$2

    kubectl get pods -n $namespace -l app=$app_label -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound"
}

# Get pod ready status
get_pod_ready() {
    local namespace=$1
    local app_label=$2

    kubectl get pods -n $namespace -l app=$app_label -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False"
}

# Get pod restart count
get_pod_restarts() {
    local namespace=$1
    local app_label=$2

    kubectl get pods -n $namespace -l app=$app_label -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}' 2>/dev/null || echo "N/A"
}

# Wait for pod to be ready
wait_for_pod() {
    local namespace=$1
    local app_label=$2
    local timeout=${3:-60}

    print_info "Waiting for $app_label to be ready (timeout: ${timeout}s)..."

    local max_attempts=$((timeout / 5))
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        local status=$(get_pod_status "$namespace" "$app_label")
        local ready=$(get_pod_ready "$namespace" "$app_label")

        if [ "$status" = "Running" ] && [ "$ready" = "True" ]; then
            print_success "$app_label is ready"
            return 0
        fi

        sleep 5
        attempt=$((attempt + 1))
    done

    print_warning "$app_label is not ready after ${timeout}s"
    return 1
}

# Check service endpoint
check_service_endpoint() {
    local namespace=$1
    local service_name=$2

    kubectl get svc "$service_name" -n $namespace &> /dev/null
}

################################################################################
# Step 1: Check Cluster Status
################################################################################

check_cluster_status() {
    print_header "1" "7" "Checking cluster status"

    # Check k3s/node status
    print_info "Checking k3s node status..."
    kubectl get nodes

    local node_status=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
    if [ "$node_status" = "True" ]; then
        print_success "Cluster node is Ready"
    else
        print_error "Cluster node is not Ready"
        return 1
    fi

    # Check cluster info
    print_info "Cluster info:"
    kubectl cluster-info

    # Check version
    print_info "kubectl version:"
    kubectl version --client 2>/dev/null | head -3 || true
}

################################################################################
# Step 2: Check Namespace Status
################################################################################

check_namespaces() {
    print_header "2" "7" "Checking namespaces"

    local namespaces=("live" "preprod" "shared" "registry")

    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &> /dev/null; then
            print_success "Namespace '$ns' exists"

            # Show pod count
            local pod_count=$(kubectl get pods -n "$ns" --no-headers 2>/dev/null | wc -l)
            print_info "  Pods in $ns: $pod_count"
        else
            print_warning "Namespace '$ns' does not exist"
        fi
    done
}

################################################################################
# Step 3: Check Infrastructure Services
################################################################################

check_infrastructure() {
    print_header "3" "7" "Checking infrastructure services"

    local namespace="shared"

    for service in "${INFRA_SERVICES[@]}"; do
        local status=$(get_pod_status "$namespace" "$service")
        local ready=$(get_pod_ready "$namespace" "$service")
        local restarts=$(get_pod_restarts "$namespace" "$service")

        if [ "$status" = "Running" ] && [ "$ready" = "True" ]; then
            print_success "$service: Running (Restarts: $restarts)"
        elif [ "$status" = "NotFound" ]; then
            print_warning "$service: Not deployed"
        else
            print_warning "$service: $status (Ready: $ready, Restarts: $restarts)"
        fi

        # Show more details if not running
        if [ "$status" != "Running" ]; then
            kubectl get pods -n "$namespace" -l app="$service" 2>/dev/null || true
        fi
    done

    # Show all shared namespace pods
    echo ""
    print_info "All pods in shared namespace:"
    kubectl get pods -n "$namespace" || true
}

################################################################################
# Step 4: Check Monitoring Services
################################################################################

check_monitoring() {
    print_header "4" "7" "Checking monitoring services"

    local namespace="shared"

    for service in "${MONITORING_SERVICES[@]}"; do
        local status=$(get_pod_status "$namespace" "$service")
        local ready=$(get_pod_ready "$namespace" "$service")
        local restarts=$(get_pod_restarts "$namespace" "$service")

        if [ "$status" = "Running" ] && [ "$ready" = "True" ]; then
            print_success "$service: Running (Restarts: $restarts)"
        elif [ "$status" = "NotFound" ]; then
            print_warning "$service: Not deployed"
        else
            print_warning "$service: $status (Ready: $ready, Restarts: $restarts)"
        fi
    done

    # Check port forwards
    echo ""
    print_info "Checking monitoring port forwards..."

    if netstat -tuln 2>/dev/null | grep -q ":9090 "; then
        print_success "Prometheus port forward active (localhost:9090)"
    else
        print_warning "Prometheus port forward not active"
        print_info "  Run: kubectl port-forward -n shared svc/prometheus 9090:9090"
    fi

    if netstat -tuln 2>/dev/null | grep -q ":3000 "; then
        print_success "Grafana port forward active (localhost:3000)"
    else
        print_warning "Grafana port forward not active"
        print_info "  Run: kubectl port-forward -n shared svc/grafana 3000:3000"
    fi

    if netstat -tuln 2>/dev/null | grep -q ":16686 "; then
        print_success "Jaeger port forward active (localhost:16686)"
    else
        print_warning "Jaeger port forward not active"
        print_info "  Run: kubectl port-forward -n shared svc/jaeger 16686:16686"
    fi
}

################################################################################
# Step 5: Check AI Services
################################################################################

check_ai_services() {
    print_header "5" "7" "Checking AI services in '$NAMESPACE' namespace"

    local running_count=0
    local failed_count=0
    local pending_count=0
    local not_deployed_count=0

    for service in "${SERVICES[@]}"; do
        local status=$(get_pod_status "$NAMESPACE" "$service")
        local ready=$(get_pod_ready "$NAMESPACE" "$service")
        local restarts=$(get_pod_restarts "$NAMESPACE" "$service")

        if [ "$status" = "Running" ] && [ "$ready" = "True" ]; then
            print_success "$service: Running (Restarts: $restarts)"
            running_count=$((running_count + 1))
        elif [ "$status" = "NotFound" ]; then
            print_warning "$service: Not deployed"
            not_deployed_count=$((not_deployed_count + 1))
        elif [ "$status" = "Pending" ] || [ "$status" = "ContainerCreating" ]; then
            print_warning "$service: $status (starting...)"
            pending_count=$((pending_count + 1))
        else
            print_error "$service: $status (Ready: $ready, Restarts: $restarts)"
            failed_count=$((failed_count + 1))

            # Show pod details for failed services
            kubectl get pods -n "$NAMESPACE" -l app="$service" 2>/dev/null || true
        fi
    done

    echo ""
    print_info "AI Services Summary:"
    echo "  Running: $running_count"
    echo "  Pending: $pending_count"
    echo "  Failed: $failed_count"
    echo "  Not Deployed: $not_deployed_count"

    # Show all pods in namespace
    echo ""
    print_info "All pods in '$NAMESPACE' namespace:"
    kubectl get pods -n "$NAMESPACE" || true
}

################################################################################
# Step 6: Check Services and Endpoints
################################################################################

check_service_endpoints() {
    print_header "6" "7" "Checking service endpoints"

    print_info "Services in '$NAMESPACE' namespace:"
    kubectl get svc -n "$NAMESPACE" || true

    echo ""
    print_info "Services in 'shared' namespace:"
    kubectl get svc -n "shared" || true

    # Check for any NodePort or LoadBalancer services
    echo ""
    print_info "External access endpoints:"

    local nodeport_services=$(kubectl get svc -A -o jsonpath='{range .items[?(@.spec.type=="NodePort")]}{.metadata.namespace}/{.metadata.name}{"\n"}{end}' 2>/dev/null)

    if [ -n "$nodeport_services" ]; then
        echo "$nodeport_services" | while read -r service; do
            local ns=$(echo "$service" | cut -d'/' -f1)
            local name=$(echo "$service" | cut -d'/' -f2)
            local port=$(kubectl get svc "$name" -n "$ns" -o jsonpath='{.spec.ports[0].nodePort}')
            print_info "  $ns/$name: localhost:$port"
        done
    else
        print_info "  No NodePort services found"
    fi
}

################################################################################
# Step 7: Display Dashboard URLs and Next Steps
################################################################################

display_summary() {
    print_header "7" "7" "Deployment summary"

    echo ""
    print_info "Monitoring Dashboards:"
    echo "  Grafana:     http://localhost:3000 (admin/admin)"
    echo "  Prometheus:  http://localhost:9090"
    echo "  Jaeger:      http://localhost:16686"
    echo ""

    # Get pod counts
    local live_pods=$(kubectl get pods -n live --no-headers 2>/dev/null | wc -l)
    local live_running=$(kubectl get pods -n live --no-headers 2>/dev/null | grep -c "Running" || echo "0")
    local shared_pods=$(kubectl get pods -n shared --no-headers 2>/dev/null | wc -l)
    local shared_running=$(kubectl get pods -n shared --no-headers 2>/dev/null | grep -c "Running" || echo "0")

    print_info "Pod Status Summary:"
    echo "  Live namespace:   $live_running/$live_pods running"
    echo "  Shared namespace: $shared_running/$shared_pods running"
    echo ""

    # Display useful commands
    print_info "Useful Commands:"
    echo "  # View all pods:"
    echo "  kubectl get pods -A"
    echo ""
    echo "  # View logs for a service:"
    echo "  kubectl logs -f deployment/<service-name> -n $NAMESPACE"
    echo ""
    echo "  # Get shell access to a pod:"
    echo "  kubectl exec -it <pod-name> -n $NAMESPACE -- /bin/bash"
    echo ""
    echo "  # Describe a pod for troubleshooting:"
    echo "  kubectl describe pod <pod-name> -n $NAMESPACE"
    echo ""
    echo "  # Restart a deployment:"
    echo "  kubectl rollout restart deployment/<service-name> -n $NAMESPACE"
    echo ""

    # Next steps
    print_info "Next Steps:"
    if [ "$live_running" -eq "$live_pods" ] && [ "$live_pods" -gt 0 ]; then
        print_success "All services are running!"
        echo "  1. Run the demo: ./scripts/run-demo.sh"
        echo "  2. Open Grafana: http://localhost:3000"
        echo "  3. Test the API endpoints"
    else
        print_warning "Some services are not running yet"
        echo "  1. Check pod status: kubectl get pods -n $NAMESPACE"
        echo "  2. Check pod logs: kubectl logs <pod-name> -n $NAMESPACE"
        echo "  3. Run this script again in a few minutes"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Project Chimera Deployment Verification${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Target namespace: $NAMESPACE"
    echo ""

    # Pre-flight checks
    check_sudo
    verify_kubectl || exit 1

    # Run verification steps
    check_cluster_status
    check_namespaces
    check_infrastructure
    check_monitoring
    check_ai_services
    check_service_endpoints
    display_summary

    echo ""
    print_success "Verification complete!"
    echo ""
}

# Change to project root
cd "$PROJECT_ROOT"

# Run main function
main "$@"
