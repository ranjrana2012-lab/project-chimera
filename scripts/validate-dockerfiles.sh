#!/bin/bash
# Validate all service Dockerfiles for CI consistency
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ERRORS=0

echo "Validating Dockerfiles..."

for dockerfile in services/*/Dockerfile; do
  service=$(basename $(dirname "$dockerfile"))
  echo -n "Checking $service... "

  # Check for curl installation (simple check: curl must appear somewhere)
  if ! grep -q "curl" "$dockerfile"; then
    echo -e "${RED}FAIL${NC} (missing curl)"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Check for consistent base image (python:3.11-slim or 3.12-slim)
  if ! grep -q "FROM python:3.1[12]-slim" "$dockerfile"; then
    # Non-Python services are OK (e.g., Node.js)
    if ! grep -q "FROM python:" "$dockerfile"; then
      echo -e "${GREEN}OK${NC} (non-Python service)"
      continue
    fi
    echo -e "${RED}FAIL${NC} (inconsistent base image)"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  echo -e "${GREEN}OK${NC}"
done

if [ $ERRORS -gt 0 ]; then
  echo -e "${RED}$ERRORS validation errors found${NC}"
  exit 1
fi

echo -e "${GREEN}All Dockerfiles validated!${NC}"
exit 0
