#!/bin/bash
set -e

echo "⏳ [1/7] Installing k3s..."

# Check if k3s is already installed
if command -v k3s &> /dev/null; then
    echo "✅ k3s already installed"
    k3s --version
else
    echo "⏳ Installing k3s..."
    curl -sfL https://get.k3s.io | sh -
    echo "✅ k3s installed"
fi

# Wait for k3s to be ready
echo "⏳ Waiting for k3s to be ready..."
until kubectl get nodes &> /dev/null; do
    sleep 2
done

# Verify node is Ready
NODE_STATUS=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
if [ "$NODE_STATUS" != "True" ]; then
    echo "❌ k3s node not ready"
    exit 1
fi

echo "✅ k3s node ready"

# Export kubeconfig for current user
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config

# Create namespaces
echo "⏳ Creating namespaces..."
kubectl create namespace live --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace preprod --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace shared --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace registry --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Namespaces created: live, preprod, shared, registry"

# Install Kustomize if not present
if ! command -v kustomize &> /dev/null; then
    echo "⏳ Installing Kustomize..."
    curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
    sudo mv kustomize /usr/local/bin/
fi

echo "✅ Kustomize installed"
echo "✅ [1/7] k3s installation complete"
