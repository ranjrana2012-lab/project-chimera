#!/bin/bash
# Wait for all Project Chimera services to be healthy
# This script polls health endpoints for all 9 services and returns success when all are ready

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service configuration: PORT:SERVICE_NAME
# Updated to match docker-compose.mvp.yml (8 MVP services)
SERVICES=(
  "8000:openclaw-orchestrator"
  "8001:scenespeak-agent"
  "8002:translation-agent"
  "8004:sentiment-agent"
  "8006:safety-filter"
  "8007:operator-console"
  "8008:hardware-bridge"
  "6379:redis"
)

# Configuration
TIMEOUT=60  # seconds (reduced for faster ready check)
INTERVAL=2   # seconds

# Function to check service readiness (container running, not necessarily models loaded)
check_service() {
  local port=$1
  local name=$2

  if [ "$name" = "redis" ]; then
    # Redis uses docker exec for health check
    if docker exec chimera-redis redis-cli ping > /dev/null 2>&1; then
      return 0
    else
      return 1
    fi
  fi

  if curl -sf "http://localhost:${port}/health/ready" > /dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

# Function to wait for a single service
wait_for_service() {
  local port=$1
  local name=$2
  local elapsed=0

  while [ $elapsed -lt $TIMEOUT ]; do
    if check_service "$port" "$name"; then
      echo -e "${GREEN}✓${NC} $name is ready"
      return 0
    fi

    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))

    # Only print waiting message every 10 seconds to reduce noise
    if [ $((elapsed % 10)) -eq 0 ]; then
      echo -e "${YELLOW}⏳${NC} Waiting for $name... (${elapsed}/${TIMEOUT}s)"
    fi
  done

  echo -e "${RED}✗${NC} $name failed to start within ${TIMEOUT}s" >&2
  return 1
}

# Function to wait for model loading (only for ML services)
wait_for_models() {
  local ml_services=("8001:scenespeak" "8002:captioning" "8003:bsl" "8004:sentiment" "8011:music")

  echo ""
  echo "Waiting for ML models to load..."

  for service in "${ml_services[@]}"; do
    IFS=':' read -r PORT NAME <<< "$service"
    echo -n "  $NAME models... "

    local elapsed=0
    while [ $elapsed -lt 180 ]; do
      if curl -sf "http://localhost:${PORT}/health/live" > /dev/null 2>&1; then
        echo -e "${GREEN}loaded${NC}"
        break
      fi
      sleep 5
      elapsed=$((elapsed + 5))
    done
  done
}

# Main execution
main() {
  echo "====================================================================="
  echo "Project Chimera - Service Health Check"
  echo "====================================================================="
  echo ""
  echo "Waiting for services to be healthy..."
  echo "Timeout: ${TIMEOUT}s | Check interval: ${INTERVAL}s"
  echo ""

  local failed_services=()

  for service in "${SERVICES[@]}"; do
    IFS=':' read -r PORT NAME <<< "$service"

    if ! wait_for_service "$PORT" "$NAME"; then
      failed_services+=("$NAME")
    fi
  done

  # Wait for ML models to load (only if all containers are ready)
  if [ ${#failed_services[@]} -eq 0 ]; then
    wait_for_models
  fi

  echo ""
  echo "====================================================================="

  if [ ${#failed_services[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All services ready!${NC}"
    echo "====================================================================="
    return 0
  else
    echo -e "${RED}✗ Failed services: ${failed_services[*]}${NC}"
    echo "====================================================================="
    return 1
  fi
}

# Run main function
main "$@"
