#!/bin/bash
# integration-test.sh - Run integration tests for Project Chimera
#
# This script handles starting services, running integration tests,
# and cleaning up afterward.
#
# Usage:
#   ./scripts/integration-test.sh [options]
#
# Options:
#   --no-docker      Run tests without docker-compose (services must be running)
#   --quick          Skip slow tests
#   --verbose        Enable verbose output
#   --keep-running   Keep services running after tests
#   --coverage       Generate coverage report
#   -h, --help       Show this help message

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default values
USE_DOCKER=true
SKIP_SLOW=false
VERBOSE=false
KEEP_RUNNING=false
COVERAGE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
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

show_help() {
    grep '^#' "$SCRIPT_DIR/integration-test.sh" | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-docker)
            USE_DOCKER=false
            shift
            ;;
        --quick)
            SKIP_SLOW=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --keep-running)
            KEEP_RUNNING=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Export environment variables
export USE_DOCKER="$USE_DOCKER"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Build pytest arguments
PYTEST_ARGS=()
PYTEST_ARGS+=("tests/integration/")
PYTEST_ARGS+=("-v")

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS+=("-vv")
    PYTEST_ARGS+=("-s")
fi

if [ "$SKIP_SLOW" = true ]; then
    PYTEST_ARGS+=("-m" "not slow")
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS+=("--cov=services")
    PYTEST_ARGS+=("--cov-report=html")
    PYTEST_ARGS+=("--cov-report=term")
fi

# Start services if using docker
if [ "$USE_DOCKER" = true ]; then
    log_info "Starting services with docker-compose..."

    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found. Please install docker-compose."
        exit 1
    fi

    # Start services
    docker-compose up -d

    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check service health
    log_info "Checking service health..."
    unhealthy_services=()

    # Check each service
    for service in orchestrator scenespeak-agent captioning-agent bsl-agent sentiment-agent safety-filter operator-console; do
        if ! docker-compose ps "$service" | grep -q "Up"; then
            unhealthy_services+=("$service")
        fi
    done

    if [ ${#unhealthy_services[@]} -gt 0 ]; then
        log_warning "Some services may not be fully started: ${unhealthy_services[*]}"
        log_info "Waiting additional time..."
        sleep 10
    fi

    log_success "Services started"
fi

# Run tests
log_info "Running integration tests..."
log_info "Command: pytest ${PYTEST_ARGS[*]}"

# Set exit trap for cleanup
cleanup() {
    exit_code=$?

    if [ "$USE_DOCKER" = true ] && [ "$KEEP_RUNNING" = false ]; then
        log_info "Stopping services..."
        docker-compose down
        log_success "Services stopped"
    elif [ "$KEEP_RUNNING" = true ]; then
        log_info "Services are still running. Stop with: docker-compose down"
    fi

    exit $exit_code
}

trap cleanup EXIT INT TERM

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    log_error "pytest not found. Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov httpx websockets
fi

# Run pytest
if pytest "${PYTEST_ARGS[@]}"; then
    log_success "All integration tests passed!"

    if [ "$COVERAGE" = true ]; then
        log_info "Coverage report generated in htmlcov/"
    fi

    exit 0
else
    log_error "Some integration tests failed"
    exit 1
fi
