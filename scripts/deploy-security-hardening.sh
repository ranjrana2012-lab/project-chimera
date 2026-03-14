#!/bin/bash
# Security Hardening Deployment Script for Project Chimera
# This script applies all security hardening changes to the cluster

set -e

NAMESPACE="project-chimera"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Project Chimera Security Hardening Deployment ==="
echo "Project Root: $PROJECT_ROOT"
echo "Namespace: $NAMESPACE"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
  echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
  exit 1
fi

# Check if we're connected to the cluster
if ! kubectl cluster-info &> /dev/null; then
  echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
  echo "Please configure kubectl to connect to your cluster"
  exit 1
fi

echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"

# Function to apply a YAML file
apply_yaml() {
  local file=$1
  local description=$2

  echo -e "\n${YELLOW}Applying: $description${NC}"
  echo "File: $file"

  if [ -f "$file" ]; then
    kubectl apply -f "$file"
    echo -e "${GREEN}✓ Applied successfully${NC}"
  else
    echo -e "${RED}✗ File not found: $file${NC}"
    return 1
  fi
}

# Function to wait for pods to be ready
wait_for_pods() {
  local timeout=300
  local elapsed=0

  echo -e "\n${YELLOW}Waiting for pods to be ready...${NC}"

  while [ $elapsed -lt $timeout ]; do
    local not_ready=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running -o json | jq -r '.items | length')

    if [ "$not_ready" -eq 0 ]; then
      echo -e "${GREEN}✓ All pods are running${NC}"
      return 0
    fi

    echo "Waiting... ($elapsed/$timeout seconds)"
    sleep 5
    elapsed=$((elapsed + 5))
  done

  echo -e "${YELLOW}⚠ Timeout waiting for pods${NC}"
  return 1
}

# Step 1: Apply Pod Security Admission configuration
echo -e "\n${YELLOW}=== Step 1: Pod Security Admission Configuration ===${NC}"
apply_yaml "$PROJECT_ROOT/infrastructure/kubernetes/cluster/pod-security-policy.yaml" "Pod Security Admission Configuration"

# Step 2: Verify namespace labels
echo -e "\n${YELLOW}=== Step 2: Verify Namespace Labels ===${NC}"
echo "Checking Pod Security Admission labels..."
kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.labels}' | jq .

# Step 3: Apply service manifests
echo -e "\n${YELLOW}=== Step 3: Apply Service Manifests ===${NC}"

SERVICES=(
  "openclaw-orchestrator"
  "scenespeak-agent"
  "captioning-agent"
  "bsl-agent"
  "sentiment-agent"
  "lighting-sound-music"
  "safety-filter"
  "operator-console"
)

for service in "${SERVICES[@]}"; do
  manifest="$PROJECT_ROOT/services/$service/manifests/k8s.yaml"
  if [ -f "$manifest" ]; then
    apply_yaml "$manifest" "Service: $service"
  else
    echo -e "${RED}✗ Manifest not found: $manifest${NC}"
  fi
done

# Apply autonomous-agent separately (has separate files)
echo -e "\n${YELLOW}Applying: autonomous-agent${NC}"
apply_yaml "$PROJECT_ROOT/services/autonomous-agent/k8s-deployment.yaml" "Autonomous Agent Deployment"
apply_yaml "$PROJECT_ROOT/services/autonomous-agent/k8s-service.yaml" "Autonomous Agent Service"

# Step 4: Wait for pods to be ready
wait_for_pods

# Step 5: Show pod status
echo -e "\n${YELLOW}=== Step 4: Pod Status ===${NC}"
kubectl get pods -n $NAMESPACE

# Step 6: Run security validation
echo -e "\n${YELLOW}=== Step 5: Security Validation ===${NC}"
if [ -f "$PROJECT_ROOT/scripts/test-security-contexts.sh" ]; then
  echo "Running security validation script..."
  bash "$PROJECT_ROOT/scripts/test-security-contexts.sh"
else
  echo -e "${YELLOW}⚠ Security validation script not found${NC}"
  echo "Expected location: $PROJECT_ROOT/scripts/test-security-contexts.sh"
fi

# Step 7: Check for policy violations
echo -e "\n${YELLOW}=== Step 6: Check for Policy Violations ===${NC}"
violations=$(kubectl get events -n $NAMESPACE --field-selector reason=Violation --no-headers 2>/dev/null | wc -l)

if [ "$violations" -eq 0 ]; then
  echo -e "${GREEN}✓ No policy violations detected${NC}"
else
  echo -e "${YELLOW}⚠ Found $violations policy violation(s)${NC}"
  echo "Recent violations:"
  kubectl get events -n $NAMESPACE --field-selector reason=Violation --sort-by='.lastTimestamp' | tail -10
fi

# Summary
echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Verify all services are running: kubectl get pods -n $NAMESPACE"
echo "2. Check service logs for any errors: kubectl logs -n $NAMESPACE <pod-name>"
echo "3. Run security validation: ./scripts/test-security-contexts.sh"
echo "4. Monitor for 24 hours to ensure stability"
echo ""
echo "Documentation:"
echo "- Production Hardening Guide: docs/security/PRODUCTION_HARDENING_GUIDE.md"
echo "- Quick Reference: docs/security/SECURITY_QUICK_REFERENCE.md"
echo "- Validation Checklist: docs/security/VALIDATION_CHECKLIST.md"
echo ""
echo "For issues, see: docs/security/PRODUCTION_HARDENING_GUIDE.md#troubleshooting"
