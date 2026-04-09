#!/bin/bash
# Visual Core Service - Build and Deploy Script
# This script helps build and deploy the visual-core service to k3s

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_DIR="$PROJECT_ROOT/services/visual-core"

echo "🔨 Visual Core Service - Build and Deploy Script"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "$SERVICE_DIR/Dockerfile" ]; then
    echo "❌ Dockerfile not found at $SERVICE_DIR/Dockerfile"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to build with Docker
build_with_docker() {
    echo "🐳 Building Docker image with docker..."
    cd "$SERVICE_DIR"
    docker build -t visual-core:latest .

    # Check if build was successful
    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully"
        return 0
    else
        echo "❌ Docker build failed"
        return 1
    fi
}

# Function to build with sudo docker
build_with_sudo_docker() {
    echo "🐳 Building Docker image with sudo docker..."
    cd "$SERVICE_DIR"
    sudo docker build -t visual-core:latest .

    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully with sudo"

        # Import to k3s containerd
        echo "📦 Importing image to k3s containerd..."
        sudo docker save visual-core:latest | sudo ctr -n k8s.io image import -
        if [ $? -eq 0 ]; then
            echo "✅ Image imported to k3s successfully"
            return 0
        else
            echo "⚠️  Image built but failed to import to k3s"
            echo "   You may need to restart the pods manually:"
            echo "   kubectl rollout restart deployment/visual-core -n project-chimera"
            return 1
        fi
    else
        echo "❌ Docker build with sudo failed"
        return 1
    fi
}

# Function to check kubectl access
check_kubectl() {
    if ! command_exists kubectl; then
        echo "❌ kubectl not found. Please install kubectl."
        exit 1
    fi

    # Try to access the cluster
    if kubectl get nodes >/dev/null 2>&1; then
        echo "✅ kubectl is configured and can access the cluster"
        return 0
    else
        echo "⚠️  kubectl cannot access the cluster. Trying with user kubeconfig..."
        export KUBECONFIG=~/.kube/config
        if kubectl get nodes >/dev/null 2>&1; then
            echo "✅ kubectl is configured with user kubeconfig"
            return 0
        else
            echo "❌ kubectl cannot access the cluster"
            exit 1
        fi
    fi
}

# Function to restart deployment
restart_deployment() {
    echo "🔄 Restarting visual-core deployment..."
    export KUBECONFIG=~/.kube/config
    kubectl rollout restart deployment/visual-core -n project-chimera

    if [ $? -eq 0 ]; then
        echo "✅ Deployment restarted successfully"
        echo "⏳ Waiting for pods to be ready..."
        kubectl wait --for=condition=ready pod -l app=visual-core -n project-chimera --timeout=120s
        if [ $? -eq 0 ]; then
            echo "✅ Pods are ready!"
            return 0
        else
            echo "⚠️  Pods are taking longer than expected to become ready"
            echo "   Check status with: kubectl get pods -n project-chimera -l app=visual-core"
            return 1
        fi
    else
        echo "❌ Failed to restart deployment"
        return 1
    fi
}

# Main execution flow
main() {
    echo "Step 1: Checking kubectl access..."
    check_kubectl
    echo ""

    echo "Step 2: Attempting to build Docker image..."
    echo ""

    # Try regular docker first
    if command_exists docker; then
        if docker ps >/dev/null 2>&1; then
            if build_with_docker; then
                echo "✅ Image built with regular docker"
                restart_deployment
                exit $?
            fi
        else
            echo "⚠️  Docker daemon not accessible, trying with sudo..."
        fi
    fi

    # Try sudo docker
    if command_exists docker; then
        if build_with_sudo_docker; then
            restart_deployment
            exit $?
        fi
    fi

    echo ""
    echo "❌ All build methods failed. Please ensure:"
    echo "   1. Docker is installed and running"
    echo "   2. You have permissions to access Docker (or use sudo)"
    echo "   3. The Dockerfile is present and valid"
    echo ""
    echo "Alternative: Build and push to a registry, then update the deployment:"
    echo "   kubectl set image deployment/visual-core visual-core=<registry>/visual-core:latest -n project-chimera"
    exit 1
}

# Run main function
main
