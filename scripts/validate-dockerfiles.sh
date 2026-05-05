#!/bin/bash
# Validate all service Dockerfiles for CI consistency
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ERRORS=0

echo "Validating Dockerfiles..."

for dockerfile in services/*/Dockerfile; do
  service=$(basename "$(dirname "$dockerfile")")
  echo -n "Checking $service... "

  # Check for consistent base image on Python services.
  if grep -q "^FROM python:" "$dockerfile" && ! grep -q "^FROM python:3.1[12]-slim" "$dockerfile"; then
    echo -e "${RED}FAIL${NC} (inconsistent base image)"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Health checks may use curl, wget, or Python HTTP clients depending on image.
  if grep -q "^HEALTHCHECK" "$dockerfile" && ! grep -Eq "CMD +(curl|wget|python)" "$dockerfile"; then
    echo -e "${RED}FAIL${NC} (unsupported healthcheck command)"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  if ! grep -q "^FROM python:" "$dockerfile"; then
    echo -e "${GREEN}OK${NC} (non-Python service)"
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
