#!/bin/bash
# Rebuild and Test E2E Services Script
#
# This script rebuilds the services with E2E API compatibility changes
# and runs the relevant E2E tests to verify the implementations.
#
# Usage: sudo ./scripts/rebuild-and-test-services.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script requires sudo privileges to rebuild Docker containers"
    log_info "Please run: sudo $0"
    exit 1
fi

log_info "Starting E2E services rebuild and test..."
echo ""

# Array of services to rebuild (in order)
SERVICES=(
    "bsl-agent"
    "captioning-agent"
    "openclaw-orchestrator"
)

# Array of test suites to run (matches services)
TEST_SUITES=(
    "api/bsl.spec.ts"
    "api/captioning.spec.ts"
    "websocket/sentiment-updates.spec.ts"
)

# Rebuild each service
for i in "${!SERVICES[@]}"; do
    SERVICE="${SERVICES[$i]}"
    log_info "Rebuilding $SERVICE..."

    # Build service
    docker compose build "$SERVICE"

    if [ $? -eq 0 ]; then
        log_success "$SERVICE built successfully"
    else
        log_error "$SERVICE build failed"
        exit 1
    fi

    echo ""
done

# Restart services
log_info "Restarting services..."
docker compose up -d "${SERVICES[@]}"

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

# Check health
for SERVICE in "${SERVICES[@]}"; do
    case $SERVICE in
        "bsl-agent")
            PORT=8003
            ;;
        "captioning-agent")
            PORT=8002
            ;;
        "openclaw-orchestrator")
            PORT=8000
            ;;
        *)
            log_warning "Unknown health check port for $SERVICE"
            continue
            ;;
    esac

    if curl -sf "http://localhost:$PORT/health/live" > /dev/null; then
        log_success "$SERVICE is healthy"
    else
        log_error "$SERVICE health check failed"
        exit 1
    fi
done

echo ""
log_success "All services rebuilt and running!"

# Run E2E tests
log_info "Running E2E tests..."
cd tests/e2e

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Run each test suite
for TEST_SUITE in "${TEST_SUITES[@]}"; do
    log_info "Testing $TEST_SUITE..."

    # Run tests and capture results
    TEST_OUTPUT=$(npm test -- "$TEST_SUITE" 2>&1 || true)

    # Count tests from output
    SUITE_TOTAL=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= passed)' | awk '{s+=$1} END {print s}')
    SUITE_PASSED=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= passed)' | tail -1)
    SUITE_FAILED=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= failed)' | tail -1)

    # Add to totals (using default values if not found)
    TOTAL_TESTS=$((TOTAL_TESTS + ${SUITE_TOTAL:-0}))
    PASSED_TESTS=$((PASSED_TESTS + ${SUITE_PASSED:-0}))
    FAILED_TESTS=$((FAILED_TESTS + ${SUITE_FAILED:-0}))

    if [ -n "$SUITE_PASSED" ] && [ "$SUITE_FAILED" -eq 0 ]; then
        log_success "$TEST_SUITE: $SUITE_PASSED/$SUITE_TOTAL tests passed"
    else
        log_warning "$TEST_SUITE: Some tests failed or skipped"
    fi

    echo ""
done

# Print summary
echo ""
log_info "========================================="
log_info "E2E Test Summary"
log_info "========================================="
log_info "Total Tests: $TOTAL_TESTS"
log_success "Passed: $PASSED_TESTS"
if [ $FAILED_TESTS -gt 0 ]; then
    log_error "Failed: $FAILED_TESTS"
else
    log_info "Failed: $FAILED_TESTS"
fi
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    log_success "All E2E tests passed!"
    exit 0
else
    log_warning "Some tests failed. Check the output above for details."
    exit 1
fi
