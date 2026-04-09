#!/bin/bash
# Project Chimera Phase 2 - Run Tests Script
#
# This script runs all tests for Phase 2 services.
#
# Usage:
#   chmod +x scripts/run-tests.sh
#   ./scripts/run-tests.sh

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo ""
    echo "=================================="
    echo "$1"
    echo "=================================="
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_error "Virtual environment not activated"
    print_info "Activate with: source venv/bin/activate"
    exit 1
fi

print_header "Project Chimera Phase 2 - Running Tests"

# Test counters
TOTAL=0
PASSED=0
FAILED=0

# Function to run tests for a service
run_service_tests() {
    local service=$1
    local service_path="services/$service"

    print_header "Testing $service"

    if [ -d "$service_path/tests" ]; then
        print_info "Running tests for $service..."

        cd "$service_path"

        if python -m pytest tests/ -v --tb=short; then
            print_success "$service tests passed"
            ((PASSED++))
        else
            print_error "$service tests failed"
            ((FAILED++))
        fi

        cd - > /dev/null
        ((TOTAL++))
    else
        print_info "No tests found for $service"
    fi
}

# Run tests for each service
run_service_tests "dmx-controller"
run_service_tests "audio-controller"
run_service_tests "bsl-avatar-service"

# Print summary
print_header "Test Summary"

echo "Total services tested: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
fi
