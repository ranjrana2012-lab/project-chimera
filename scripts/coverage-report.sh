#!/bin/bash
# Project Chimera Phase 2 - Test Coverage Report Script
#
# This script generates comprehensive test coverage reports for
# Phase 2 services and enforces coverage thresholds.

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COVERAGE_THRESHOLD=80
REPORT_DIR="${PROJECT_ROOT}/coverage"

# Logging
log() {
    local level="$1"
    shift
    echo -e "${level} $*"
}
info() { log "${BLUE}[INFO]${NC}", "$*"; }
success() { log "${GREEN}[SUCCESS]${NC}", "$*"; }
warning() { log "${YELLOW}[WARNING]${NC}", "$*"; }
error() { log "${RED}[ERROR]${NC}", "$*"; }

# Help function
show_help() {
    cat << EOF
Project Chimera Phase 2 - Test Coverage Report

Usage: $0 [OPTIONS]

Options:
    --threshold PERCENT   Minimum coverage threshold (default: 80)
    --format FORMAT       Report format (html, json, xml, term)
    --service SERVICE     Specific service to test
    --watch              Watch mode for development
    --help               Show this help message

Services:
    dmx                  DMX Controller service
    audio                Audio Controller service
    bsl                  BSL Avatar Service
    orchestration        Service orchestration
    all                  All services (default)

Formats:
    html                 HTML report (default)
    json                 JSON report
    xml                  XML report for CI
    term                 Terminal report

Examples:
    $0 --service all --format html
    $0 --service dmx --threshold 90
    $0 --watch

EOF
}

# Parse arguments
parse_args() {
    SERVICE="all"
    FORMAT="html"
    THRESHOLD=80
    WATCH=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --threshold)
                THRESHOLD="$2"
                shift 2
                ;;
            --format)
                FORMAT="$2"
                shift 2
                ;;
            --service)
                SERVICE="$2"
                shift 2
                ;;
            --watch)
                WATCH=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Install dependencies
install_deps() {
    info "Checking test dependencies..."

    cd "$PROJECT_ROOT"

    if ! pip show pytest-cov &>/dev/null; then
        info "Installing pytest-cov..."
        pip install pytest-cov
    fi

    if ! pip show pytest-asyncio &>/dev/null; then
        info "Installing pytest-asyncio..."
        pip install pytest-asyncio
    fi
}

# Run coverage for specific service
run_coverage_service() {
    local service=$1
    local format=$2
    local threshold=$3

    info "Running coverage for $service..."

    cd "$PROJECT_ROOT"

    # Determine test directory and module
    case "$service" in
        dmx)
            test_dir="tests/dmx-controller"
            module="services/dmx_controller"
            ;;
        audio)
            test_dir="tests/audio-controller"
            module="services/audio_controller"
            ;;
        bsl)
            test_dir="tests/bsl-avatar-service"
            module="services/bsl_avatar_service"
            ;;
        orchestration)
            test_dir="tests/orchestration"
            module="services/orchestration"
            ;;
        *)
            error "Unknown service: $service"
            return 1
            ;;
    esac

    # Create report directory
    mkdir -p "$REPORT_DIR"

    # Build pytest arguments
    pytest_args=(
        "$test_dir"
        "--cov=$module"
        "--cov-append"
        "--cov-fail-under=$threshold"
    )

    # Add format-specific arguments
    case "$format" in
        html)
            pytest_args+=("--cov-report=html:$REPORT_DIR/html")
            ;;
        json)
            pytest_args+=("--cov-report=json:$REPORT_DIR/coverage.json")
            ;;
        xml)
            pytest_args+=("--cov-report=xml:$REPORT_DIR/coverage.xml")
            ;;
        term)
            pytest_args+=("--cov-report=term-missing")
            ;;
    esac

    # Run tests
    info "Running pytest with coverage..."
    pytest "${pytest_args[@]}" || return 1

    success "Coverage report generated for $service"
}

# Run coverage for all services
run_coverage_all() {
    local format=$1
    local threshold=$2

    info "Running coverage for all services..."

    # Run coverage for each service
    for service in dmx audio bsl orchestration; do
        if [ -d "$PROJECT_ROOT/tests/$service" ]; then
            run_coverage_service "$service" "$format" "$threshold" || return 1
        fi
    done

    # Generate combined report
    info "Generating combined coverage report..."

    case "$format" in
        html)
            info "HTML report: $REPORT_DIR/html/index.html"
            ;;
        json)
            info "JSON report: $REPORT_DIR/coverage.json"
            ;;
        xml)
            info "XML report: $REPORT_DIR/coverage.xml"
            ;;
        term)
            # Already displayed
            ;;
    esac
}

# Generate summary report
generate_summary() {
    info "Generating coverage summary..."

    cd "$PROJECT_ROOT"

    # Check if coverage report exists
    if [ ! -f "$REPORT_DIR/coverage.json" ]; then
        warning "No coverage report found. Run with --format json first."
        return
    fi

    # Parse coverage data
    python3 << 'EOF'
import json
import sys

try:
    with open('coverage/coverage.json') as f:
        data = json.load(f)

    files = data.get('files', {})
    total_lines = 0
    covered_lines = 0

    for filename, file_data in files.items():
        summary = file_data.get('summary', {})
        total_lines += summary.get('num_statements', 0)
        covered_lines += summary.get('covered_lines', 0)

    if total_lines > 0:
        coverage_pct = (covered_lines / total_lines) * 100
        print(f"\nTotal Coverage: {coverage_pct:.1f}%")
        print(f"Total Lines: {total_lines}")
        print(f"Covered Lines: {covered_lines}")

        if coverage_pct < 80:
            print("\n⚠️  Coverage below 80% threshold")
            sys.exit(1)
        else:
            print("\n✅ Coverage meets 80% threshold")
            sys.exit(0)

except Exception as e:
    print(f"Error parsing coverage: {e}")
    sys.exit(1)
EOF
}

# Watch mode for development
watch_mode() {
    info "Starting watch mode (Ctrl+C to exit)..."

    while true; do
        clear
        echo "=========================================="
        echo "Coverage Watch - $(date)"
        echo "=========================================="
        echo ""

        run_coverage_all "term" "$THRESHOLD" || true

        echo ""
        info "Waiting for changes... (Press Ctrl+C to exit)"
        sleep 5
    done
}

# Main function
main() {
    parse_args "$@"

    echo "Project Chimera Phase 2 - Test Coverage Report"
    echo "============================================="
    echo ""
    echo "Configuration:"
    echo "  Service: $SERVICE"
    echo "  Format: $FORMAT"
    echo "  Threshold: $THRESHOLD%"
    echo ""

    # Install dependencies
    install_deps

    # Run coverage
    if [ "$WATCH" = true ]; then
        watch_mode
    else
        if [ "$SERVICE" = "all" ]; then
            run_coverage_all "$FORMAT" "$THRESHOLD"
            generate_summary
        else
            run_coverage_service "$SERVICE" "$FORMAT" "$THRESHOLD"
        fi

        success "Coverage report complete!"
    fi
}

main "$@"
