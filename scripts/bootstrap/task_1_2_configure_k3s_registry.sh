#!/bin/bash
# Task 1.2: Configure k3s Registry
# This script must be run with sudo privileges

set -e

echo "Configuring k3s registry..."

# Create k3s registries configuration
sudo mkdir -p /etc/rancher/k3s/

cat <<EOF | sudo tee /etc/rancher/k3s/registries.yaml
mirrors:
  "localhost:30500":
    endpoint:
      - "http://localhost:30500"
EOF

echo "Registry configuration created at /etc/rancher/k3s/registries.yaml"

# Restart k3s
echo "Restarting k3s..."
sudo systemctl restart k3s

# Wait for k3s to be ready
echo "Waiting for k3s to be ready..."
until kubectl get nodes &> /dev/null; do
    echo "Waiting for k3s..."
    sleep 2
done

echo "k3s restarted successfully"
echo ""
echo "Verifying k3s node status..."
export KUBECONFIG=/home/ranj/.kube/config
kubectl get nodes

echo ""
echo "Task 1.2 completed successfully!"
