#!/bin/bash
#
# Project Chimera Bootstrap Deployment Script
#
# This script performs the initial bootstrap of the Project Chimera platform.
# It requires sudo privileges for system-level operations.
#
# Usage: sudo ./scripts/deploy-bootstrap.sh
#
# This script will:
#   1. Check for sudo privileges
#   2. Install k3s (lightweight Kubernetes)
#   3. Set up local container registry
#   4. Configure k3s to use the local registry
#   5. Create Kubernetes namespaces
#   6. Build and push all service images
#   7. Deploy infrastructure services (Redis, Kafka, Milvus)
#   8. Deploy monitoring stack (Prometheus, Grafana, Jaeger)
#   9. Deploy AI services
#  10. Verify deployment
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="localhost:30500"
VERSION="latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Services to build and deploy
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
    print_info "Checking for sudo privileges..."
    if [ "$EUID" -ne 0 ]; then
        print_error "This script requires sudo privileges"
        print_info "Please run: sudo $0"
        exit 1
    fi
    print_success "Sudo privileges confirmed"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check for curl
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        print_info "Install with: sudo apt-get install curl"
        exit 1
    fi

    # Check for docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_info "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # Check if docker can be used without sudo
    if ! docker info &> /dev/null; then
        print_warning "Docker requires sudo. Adding current user to docker group..."
        usermod -aG docker $SUDO_USER 2>/dev/null || true
        print_warning "You may need to log out and back in for group changes to take effect"
    fi

    print_success "Prerequisites check passed"
}

################################################################################
# Step 1: Install k3s
################################################################################

install_k3s() {
    print_header "1" "10" "Installing k3s"

    # Check if k3s is already installed
    if command -v k3s &> /dev/null; then
        print_info "k3s already installed"
        k3s --version
    else
        print_info "Installing k3s..."
        curl -sfL https://get.k3s.io | sh -
        print_success "k3s installed"
    fi

    # Wait for k3s to be ready
    print_info "Waiting for k3s to be ready..."
    local max_attempts=60
    local attempt=0
    until kubectl get nodes &> /dev/null; do
        sleep 2
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            print_error "k3s failed to start within ${max_attempts}s"
            exit 1
        fi
    done

    # Verify node is Ready
    NODE_STATUS=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
    if [ "$NODE_STATUS" != "True" ]; then
        print_error "k3s node not ready"
        exit 1
    fi

    print_success "k3s node ready"

    # Export kubeconfig for sudo user
    mkdir -p /root/.kube
    cp /etc/rancher/k3s/k3s.yaml /root/.kube/config
    chmod 600 /root/.kube/config

    # Also export for the original user
    if [ -n "$SUDO_USER" ]; then
        USER_HOME=$(eval echo ~$SUDO_USER)
        mkdir -p "$USER_HOME/.kube"
        cp /etc/rancher/k3s/k3s.yaml "$USER_HOME/.kube/config"
        chown $SUDO_USER:$SUDO_USER "$USER_HOME/.kube/config"
        chmod 600 "$USER_HOME/.kube/config"
    fi
}

################################################################################
# Step 2: Create Namespaces
################################################################################

create_namespaces() {
    print_header "2" "10" "Creating Kubernetes namespaces"

    kubectl create namespace live --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace preprod --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace shared --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace registry --dry-run=client -o yaml | kubectl apply -f -

    print_success "Namespaces created: live, preprod, shared, registry"
}

################################################################################
# Step 3: Install Kustomize
################################################################################

install_kustomize() {
    print_header "3" "10" "Installing Kustomize"

    if ! command -v kustomize &> /dev/null; then
        print_info "Installing Kustomize..."
        cd /tmp
        curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
        sudo mv kustomize /usr/local/bin/
        cd "$PROJECT_ROOT"
        print_success "Kustomize installed"
    else
        print_info "Kustomize already installed"
        kustomize version
    fi
}

################################################################################
# Step 4: Setup Local Container Registry
################################################################################

setup_registry() {
    print_header "4" "10" "Setting up local container registry"

    # Deploy local registry
    print_info "Deploying local registry to k3s..."
    kubectl apply -f - <<EOF_MANIFEST
apiVersion: apps/v1
kind: Deployment
metadata:
  name: registry
  namespace: registry
spec:
  replicas: 1
  selector:
    matchLabels:
      app: registry
  template:
    metadata:
      labels:
        app: registry
    spec:
      containers:
      - name: registry
        image: registry:2
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: data
          mountPath: /var/lib/registry
      volumes:
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: registry
  namespace: registry
spec:
  type: NodePort
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30500
  selector:
    app: registry
EOF_MANIFEST

    # Wait for registry to be ready
    print_info "Waiting for registry to be ready..."
    kubectl wait --for=condition=available -n registry deployment/registry --timeout=60s

    print_success "Local registry deployed at localhost:30500"

    # Configure k3s to use the local registry
    print_info "Configuring k3s to use local registry..."
    mkdir -p /etc/rancher/k3s
    cat > /etc/rancher/k3s/registries.yaml <<EOF
mirrors:
  "localhost:30500":
    endpoint:
      - "http://localhost:30500"
EOF

    print_info "Restarting k3s to apply registry configuration..."
    systemctl restart k3s

    # Wait for k3s to restart
    local max_attempts=60
    local attempt=0
    until kubectl get nodes &> /dev/null; do
        sleep 2
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            print_error "k3s failed to restart within ${max_attempts}s"
            exit 1
        fi
    done

    print_success "Local registry configured"
}

################################################################################
# Step 5: Build Service Images
################################################################################

build_images() {
    print_header "5" "10" "Building service images"

    # Change to project root
    cd "$PROJECT_ROOT"

    for service in "${SERVICES[@]}"; do
        if [ ! -d "services/$service" ]; then
            print_warning "Service directory not found: services/$service"
            continue
        fi

        print_info "Building $service..."
        if docker build -t $REGISTRY/project-chimera/$service:$VERSION "services/$service/" 2>&1; then
            print_success "Built $service"
        else
            print_error "Failed to build $service"
            exit 1
        fi

        print_info "Pushing $service..."
        if docker push $REGISTRY/project-chimera/$service:$VERSION 2>&1; then
            print_success "Pushed $service"
        else
            print_error "Failed to push $service"
            exit 1
        fi
    done

    print_success "All service images built and pushed"
    docker images | grep project-chimera || true
}

################################################################################
# Step 6: Deploy Infrastructure
################################################################################

deploy_infrastructure() {
    print_header "6" "10" "Deploying infrastructure services"

    local namespace="shared"

    # Deploy Redis
    print_info "Deploying Redis..."
    if [ -f "infrastructure/kubernetes/base/redis/kustomization.yaml" ]; then
        kubectl apply -k infrastructure/kubernetes/base/redis/ -n $namespace
        kubectl wait --for=condition=ready -n $namespace pod -l app=redis --timeout=180s || print_warning "Redis not ready"
    else
        print_warning "Redis kustomization not found, skipping..."
    fi

    # Deploy Kafka
    print_info "Deploying Kafka..."
    if [ -f "infrastructure/kubernetes/base/kafka/kustomization.yaml" ]; then
        kubectl apply -k infrastructure/kubernetes/base/kafka/ -n $namespace
        kubectl wait --for=condition=ready -n $namespace pod -l app=kafka --timeout=180s || print_warning "Kafka not ready"
    else
        print_warning "Kafka kustomization not found, skipping..."
    fi

    # Deploy Vector DB (Milvus)
    print_info "Deploying Milvus (Vector DB)..."
    if [ -f "infrastructure/kubernetes/base/vector-db/kustomization.yaml" ]; then
        kubectl apply -k infrastructure/kubernetes/base/vector-db/ -n $namespace
        kubectl wait --for=condition=ready -n $namespace pod -l app=milvus --timeout=180s || print_warning "Milvus not ready"
    else
        print_warning "Vector DB kustomization not found, skipping..."
    fi

    print_success "Infrastructure services deployed"
    kubectl get svc -n $namespace
}

################################################################################
# Step 7: Deploy Monitoring Stack
################################################################################

deploy_monitoring() {
    print_header "7" "10" "Deploying monitoring stack"

    local namespace="shared"

    # Deploy Prometheus
    print_info "Deploying Prometheus..."
    if [ -f "infrastructure/kubernetes/base/monitoring/prometheus/kustomization.yaml" ]; then
        kubectl apply -k infrastructure/kubernetes/base/monitoring/prometheus/ -n $namespace
    fi

    # Deploy Grafana
    print_info "Deploying Grafana..."
    if [ -f "infrastructure/kubernetes/base/monitoring/grafana/kustomization.yaml" ]; then
        kubectl apply -k infrastructure/kubernetes/base/monitoring/grafana/ -n $namespace
    fi

    # Deploy Jaeger
    print_info "Deploying Jaeger..."
    if [ -f "infrastructure/kubernetes/base/monitoring/jaeger/kustomization.yaml" ]; then
        kubectl apply -k infrastructure/kubernetes/base/monitoring/jaeger/ -n $namespace
    fi

    # Wait for monitoring services to be ready
    kubectl wait --for=condition=ready -n $namespace pod -l app=prometheus --timeout=180s || print_warning "Prometheus not ready"
    kubectl wait --for=condition=ready -n $namespace pod -l app=grafana --timeout=180s || print_warning "Grafana not ready"
    kubectl wait --for=condition=ready -n $namespace pod -l app=jaeger --timeout=180s || print_warning "Jaeger not ready"

    # Kill existing port forwards
    pkill -f "port-forward.*prometheus" || true
    pkill -f "port-forward.*grafana" || true
    pkill -f "port-forward.*jaeger" || true

    # Start port forwards for monitoring services
    print_info "Setting up port forwards for monitoring services..."
    kubectl port-forward -n $namespace svc/prometheus 9090:9090 > /dev/null 2>&1 &
    kubectl port-forward -n $namespace svc/grafana 3000:3000 > /dev/null 2>&1 &
    kubectl port-forward -n $namespace svc/jaeger 16686:16686 > /dev/null 2>&1 &

    sleep 3

    print_success "Monitoring stack deployed"
    print_info "Grafana: http://localhost:3000 (admin/admin)"
    print_info "Prometheus: http://localhost:9090"
    print_info "Jaeger: http://localhost:16686"
}

################################################################################
# Step 8: Deploy AI Services
################################################################################

deploy_services() {
    print_header "8" "10" "Deploying AI services"

    local namespace="live"

    for service in "${SERVICES[@]}"; do
        # Convert service name to kubernetes compatible name
        # e.g., openclaw-orchestrator -> openclaw-orchestrator
        k8s_service_name="$service"

        if [ -f "infrastructure/kubernetes/base/$service/deployment.yaml" ]; then
            print_info "Deploying $service..."
            kubectl apply -f infrastructure/kubernetes/base/$service/deployment.yaml -n $namespace
            kubectl apply -f infrastructure/kubernetes/base/$service/service.yaml -n $namespace 2>/dev/null || true

            # Wait for deployment to complete
            if kubectl rollout status deployment/$k8s_service_name -n $namespace --timeout=300s 2>/dev/null; then
                print_success "$service deployed"
            else
                print_warning "$service deployment timed out or failed"
            fi
        else
            print_warning "Deployment not found for $service"
        fi
    done

    print_success "AI services deployment complete"
    kubectl get pods -n $namespace
}

################################################################################
# Step 9: Configure Network Policies
################################################################################

configure_networking() {
    print_header "9" "10" "Configuring network policies"

    # Apply network policies if they exist
    if [ -f "infrastructure/kubernetes/base/network-policies/default-deny.yaml" ]; then
        print_info "Applying network policies..."
        kubectl apply -f infrastructure/kubernetes/base/network-policies/ -R
        print_success "Network policies configured"
    else
        print_info "No network policies found, skipping..."
    fi
}

################################################################################
# Step 10: Verify Deployment
################################################################################

verify_deployment() {
    print_header "10" "10" "Verifying deployment"

    local namespace="live"

    print_info "Waiting for pods to stabilize..."
    sleep 30

    print_info "Checking pod status in live namespace..."
    kubectl get pods -n $namespace

    print_info "Checking pod status in shared namespace..."
    kubectl get pods -n shared

    # Count pods by status
    local running_pods=$(kubectl get pods -n $namespace --no-headers | grep -c "Running" || true)
    local total_pods=$(kubectl get pods -n $namespace --no-headers | wc -l)

    echo ""
    print_success "Deployment Summary"
    echo "  Live namespace: $running_pods/$total_pods pods running"

    # Check for any issues
    local not_ready_pods=$(kubectl get pods -n $namespace --no-headers | grep -v "Running\|Completed" | wc -l)
    if [ "$not_ready_pods" -gt 0 ]; then
        print_warning "Some pods are not ready yet"
        print_info "Run 'kubectl describe pod <pod-name> -n live' for details"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Project Chimera Bootstrap${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Check prerequisites
    check_sudo
    check_prerequisites

    # Run deployment steps
    install_k3s
    create_namespaces
    install_kustomize
    setup_registry
    build_images
    deploy_infrastructure
    deploy_monitoring
    deploy_services
    configure_networking
    verify_deployment

    # Print completion message
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Bootstrap Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Monitoring Dashboards:"
    echo "  Grafana:     http://localhost:3000 (admin/admin)"
    echo "  Prometheus:  http://localhost:9090"
    echo "  Jaeger:      http://localhost:16686"
    echo ""
    echo "Next Steps:"
    echo "  1. Run: ./scripts/verify-deployment.sh"
    echo "  2. Run: ./scripts/run-demo.sh"
    echo "  3. View logs: kubectl logs -f deployment/openclaw-orchestrator -n live"
    echo ""
    print_success "Project Chimera is ready to use!"
}

# Change to project root
cd "$PROJECT_ROOT"

# Run main function
main "$@"
