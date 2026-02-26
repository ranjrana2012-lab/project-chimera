#!/bin/bash
set -e

echo "⏳ [2/7] Setting up local container registry..."

# Deploy local registry
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

kubectl wait --for=condition=available -n registry deployment/registry --timeout=60s
echo "✅ Local registry ready at localhost:30500"

sudo mkdir -p /etc/rancher/k3s
cat <<EOF | sudo tee /etc/rancher/k3s/registries.yaml
mirrors:
  "localhost:30500":
    endpoint:
      - "http://localhost:30500"
EOF

echo "⏳ Restarting k3s..."
sudo systemctl restart k3s
until kubectl get nodes &> /dev/null; do sleep 2; done
echo "✅ Local registry configured"
echo "✅ [2/7] Registry setup complete"
