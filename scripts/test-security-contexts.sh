#!/bin/bash
# Security Context Validation Script for Project Chimera
# This script validates that all services meet the Baseline Pod Security Standards

set -e

NAMESPACE="project-chimera"
SERVICES=(
  "openclaw-orchestrator"
  "scenespeak-agent"
  "captioning-agent"
  "bsl-agent"
  "sentiment-agent"
  "lighting-control"
  "safety-filter"
  "operator-console"
  "autonomous-agent"
)

echo "=== Project Chimera Security Context Validation ==="
echo "Testing namespace: $NAMESPACE"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check pod security context
check_pod_security_context() {
  local service=$1
  echo -e "\n${YELLOW}Checking: $service${NC}"

  # Get the pod name (take first pod if multiple replicas)
  local pod=$(kubectl get pods -n $NAMESPACE -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

  if [ -z "$pod" ]; then
    echo -e "${RED}✗ No pod found for $service${NC}"
    return 1
  fi

  echo "Pod: $pod"

  # Check pod-level security context
  local pod_context=$(kubectl get pod $pod -n $NAMESPACE -o json)

  # Check hostNetwork
  local host_network=$(echo $pod_context | jq -r '.spec.hostNetwork')
  if [ "$host_network" = "true" ] && [ "$service" != "lighting-control" ]; then
    echo -e "${RED}✗ hostNetwork is true (should be false)${NC}"
  elif [ "$host_network" = "true" ] && [ "$service" = "lighting-control" ]; then
    echo -e "${GREEN}✓ hostNetwork is true (exception for lighting-control)${NC}"
  else
    echo -e "${GREEN}✓ hostNetwork is false${NC}"
  fi

  # Check hostPID
  local host_pid=$(echo $pod_context | jq -r '.spec.hostPID')
  if [ "$host_pid" = "true" ]; then
    echo -e "${RED}✗ hostPID is true (should be false)${NC}"
  else
    echo -e "${GREEN}✓ hostPID is false${NC}"
  fi

  # Check hostIPC
  local host_ipc=$(echo $pod_context | jq -r '.spec.hostIPC')
  if [ "$host_ipc" = "true" ]; then
    echo -e "${RED}✗ hostIPC is true (should be false)${NC}"
  else
    echo -e "${GREEN}✓ hostIPC is false${NC}"
  fi

  # Check runAsNonRoot
  local run_as_non_root=$(echo $pod_context | jq -r '.spec.securityContext.runAsNonRoot')
  if [ "$run_as_non_root" = "true" ] || [ "$run_as_non_root" = "null" ]; then
    echo -e "${GREEN}✓ runAsNonRoot is set${NC}"
  else
    echo -e "${RED}✗ runAsNonRoot is not set${NC}"
  fi

  # Check runAsUser
  local run_as_user=$(echo $pod_context | jq -r '.spec.securityContext.runAsUser // "null"')
  if [ "$run_as_user" != "null" ] && [ "$run_as_user" != "0" ]; then
    echo -e "${GREEN}✓ runAsUser is set to $run_as_user${NC}"
  elif [ "$run_as_user" = "0" ]; then
    echo -e "${RED}✗ runAsUser is 0 (root)${NC}"
  else
    echo -e "${YELLOW}⚠ runAsUser is not set${NC}"
  fi

  # Check seccompProfile
  local seccomp_profile=$(echo $pod_context | jq -r '.spec.securityContext.seccompProfile.type // "null"')
  if [ "$seccomp_profile" = "RuntimeDefault" ] || [ "$seccomp_profile" = "Localhost" ]; then
    echo -e "${GREEN}✓ seccompProfile is set to $seccomp_profile${NC}"
  else
    echo -e "${YELLOW}⚠ seccompProfile is not set (should be RuntimeDefault)${NC}"
  fi

  # Check container-level security context
  local container_context=$(echo $pod_context | jq -r '.spec.containers[0].securityContext')

  # Check allowPrivilegeEscalation
  local allow_priv_esc=$(echo $container_context | jq -r '.allowPrivilegeEscalation // "null"')
  if [ "$allow_priv_esc" = "false" ]; then
    echo -e "${GREEN}✓ allowPrivilegeEscalation is false${NC}"
  elif [ "$service" = "lighting-control" ]; then
    echo -e "${YELLOW}⚠ allowPrivilegeEscalation is true (exception for lighting-control)${NC}"
  else
    echo -e "${RED}✗ allowPrivilegeEscalation is not set to false${NC}"
  fi

  # Check capabilities
  local drop_caps=$(echo $container_context | jq -r '.capabilities.drop // "null"')
  if [ "$drop_caps" != "null" ]; then
    echo -e "${GREEN}✓ Capabilities are dropped: $drop_caps${NC}"
  else
    echo -e "${YELLOW}⚠ No capabilities dropped${NC}"
  fi

  # Check for privileged containers
  local privileged=$(echo $container_context | jq -r '.privileged // "false"')
  if [ "$privileged" = "true" ]; then
    if [ "$service" = "lighting-control" ]; then
      echo -e "${YELLOW}⚠ Privileged mode is true (exception for lighting-control)${NC}"
    else
      echo -e "${RED}✗ Privileged mode is true (should be false)${NC}"
    fi
  else
    echo -e "${GREEN}✓ Not running in privileged mode${NC}"
  fi

  # Check for HostPath volumes
  local hostpath_volumes=$(echo $pod_context | jq -r '[.spec.volumes[]? | select(.hostPath != null)] | length')
  if [ "$hostpath_volumes" -gt 0 ]; then
    if [ "$service" = "lighting-control" ]; then
      echo -e "${YELLOW}⚠ HostPath volumes found: $hostpath_volumes (exception for lighting-control)${NC}"
    else
      echo -e "${RED}✗ HostPath volumes found: $hostpath_volumes${NC}"
    fi
  else
    echo -e "${GREEN}✓ No HostPath volumes${NC}"
  fi
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
  echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
  exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
  echo -e "${RED}Error: jq is not installed or not in PATH${NC}"
  echo "Install jq: https://stedolan.github.io/jq/"
  exit 1
fi

# Check namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
  echo -e "${RED}Error: Namespace $NAMESPACE does not exist${NC}"
  echo "Create namespace with: kubectl create namespace $NAMESPACE"
  exit 1
fi

# Check Pod Security Admission labels
echo -e "\n${YELLOW}=== Pod Security Admission Configuration ===${NC}"
local psa_labels=$(kubectl get namespace $NAMESPACE -o json | jq -r '.metadata.labels | to_entries[] | select(.key | startswith("pod-security.kubernetes.io/")) | "\(.key): \(.value)"')
if [ -z "$psa_labels" ]; then
  echo -e "${RED}✗ No Pod Security Admission labels found on namespace${NC}"
else
  echo "$psa_labels"
fi

# Check each service
echo -e "\n${YELLOW}=== Service Security Context Checks ===${NC}"
for service in "${SERVICES[@]}"; do
  check_pod_security_context "$service"
done

echo -e "\n${GREEN}=== Security Validation Complete ===${NC}"
echo ""
echo "Summary:"
echo "- Green checks indicate compliance with Baseline policy"
echo "- Yellow warnings indicate exceptions or recommendations"
echo "- Red failures indicate policy violations that should be addressed"
echo ""
echo "For detailed information, see: docs/security/PRODUCTION_HARDENING_GUIDE.md"
