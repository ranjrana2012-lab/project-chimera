#!/bin/bash
#
# Immutable Evaluator for Autonomous Codebase Refactoring
#
# This is the "prepare.py" equivalent from AutoResearch methodology.
# It evaluates code changes against ungameable quality metrics.
#
# Exit Code Mapping:
#   0 - All checks passed (commit should be kept)
#   1 - Functional test failure (pytest exit != 0)
#   2 - Reward hacking detected (assertions deleted, coverage dropped)
#   3 - Coverage below threshold
#   4 - Deprecation warnings found
#   5 - Evaluation error
#
# Usage:
#   ./evaluate.sh [--test-path PATH] [--coverage-target PATH] [--baseline FILE]
#
# Environment Variables:
#   CHIMERA_TEST_PATH       - Path to test directory (default: tests/)
#   CHIMERA_COVERAGE_TARGET - Path to module for coverage (default: auto-detect)
#   CHIMERA_BASELINE_FILE   - Path to baseline metrics JSON (default: baseline_metrics.json)
#   CHIMERA_MIN_COVERAGE    - Minimum coverage threshold (default: 80.0)
#   CHIMERA_MUTATION_TESTS  - Enable mutation testing (default: false)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEST_PATH="${CHIMERA_TEST_PATH:-${PROJECT_ROOT}/tests}"
COVERAGE_TARGET="${CHIMERA_COVERAGE_TARGET:-}"
BASELINE_FILE="${CHIMERA_BASELINE_FILE:-${PROJECT_ROOT}/baseline_metrics.json}"
MIN_COVERAGE="${CHIMERA_MIN_COVERAGE:-80.0}"
ENABLE_MUTATION="${CHIMERA_MUTATION_TESTS:-false}"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test-path)
            TEST_PATH="$2"
            shift 2
            ;;
        --coverage-target)
            COVERAGE_TARGET="$2"
            shift 2
            ;;
        --baseline)
            BASELINE_FILE="$2"
            shift 2
            ;;
        --min-coverage)
            MIN_COVERAGE="$2"
            shift 2
            ;;
        --enable-mutation)
            ENABLE_MUTATION=true
            shift
            ;;
        --help)
            cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --test-path PATH          Path to test directory
  --coverage-target PATH    Path to module for coverage measurement
  --baseline FILE           Path to baseline metrics JSON file
  --min-coverage FLOAT      Minimum coverage threshold (default: 80.0)
  --enable-mutation         Enable mutation testing with mutmut
  --help                    Show this help message

Environment Variables:
  CHIMERA_TEST_PATH       - Same as --test-path
  CHIMERA_COVERAGE_TARGET - Same as --coverage-target
  CHIMERA_BASELINE_FILE   - Same as --baseline
  CHIMERA_MIN_COVERAGE    - Same as --min-coverage
  CHIMERA_MUTATION_TESTS  - Same as --enable-mutation

Exit Codes:
  0 - All checks passed
  1 - Functional test failure
  2 - Reward hacking detected
  3 - Coverage below threshold
  4 - Deprecation warnings found
  5 - Evaluation error
EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 5
            ;;
    esac
done

# Validate paths
if [[ ! -d "$TEST_PATH" ]]; then
    log_error "Test path does not exist: $TEST_PATH"
    exit 5
fi

# Auto-detect coverage target if not specified
if [[ -z "$COVERAGE_TARGET" ]]; then
    # Look for common service directories
    for service_dir in "${PROJECT_ROOT}"/services/*; do
        if [[ -d "$service_dir" && -d "${service_dir}/src" ]]; then
            COVERAGE_TARGET="${service_dir}/src"
            break
        fi
    done
fi

log_info "=== Immutable Evaluator: Autonomous Codebase Refactoring ==="
log_info "Project Root: ${PROJECT_ROOT}"
log_info "Test Path: ${TEST_PATH}"
log_info "Coverage Target: ${COVERAGE_TARGET:-<auto-detect>}"
log_info "Baseline File: ${BASELINE_FILE}"
log_info "Minimum Coverage: ${MIN_COVERAGE}%"
log_info ""

# Change to project root
cd "$PROJECT_ROOT"

# Create Python evaluator script
EVALUATOR_PY="${SCRIPT_DIR}/run_evaluation.py"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found in PATH"
    exit 5
fi

# Run the Python evaluator
log_info "Running anti-gaming evaluation..."

# Build Python command arguments
PYTHON_ARGS=(
    "$EVALUATOR_PY"
    "--test-path" "$TEST_PATH"
    "--baseline" "$BASELINE_FILE"
    "--min-coverage" "$MIN_COVERAGE"
)

if [[ -n "$COVERAGE_TARGET" ]]; then
    PYTHON_ARGS+=("--coverage-target" "$COVERAGE_TARGET")
fi

if [[ "$ENABLE_MUTATION" == "true" ]]; then
    PYTHON_ARGS+=("--enable-mutation")
fi

# Run the evaluator and capture output
if ! python3 "${PYTHON_ARGS[@]}" 2>&1; then
    exit_code=$?
    log_error "Evaluation failed with exit code $exit_code"
    exit 5
fi

# Check results file
RESULTS_FILE="${PROJECT_ROOT}/evaluation_results.json"
if [[ ! -f "$RESULTS_FILE" ]]; then
    log_error "Evaluation results not found: $RESULTS_FILE"
    exit 5
fi

# Parse and display results
log_info "=== Evaluation Results ==="

# Use jq if available, otherwise use Python
if command -v jq &> /dev/null; then
    jq -r '.' "$RESULTS_FILE" >&2
else
    python3 -m json.tool "$RESULTS_FILE" >&2
fi

# Determine outcome
OUTCOME=$(python3 -c "import json; d=json.load(open('$RESULTS_FILE')); print(d['outcome'])")

case "$OUTCOME" in
    passed)
        log_info "✓ Evaluation PASSED - All quality gates satisfied"
        exit 0
        ;;
    failed_functional)
        log_error "✗ Evaluation FAILED - Functional tests failed"
        exit 1
        ;;
    failed_reward_hacking)
        log_error "✗ Evaluation FAILED - Reward hacking detected (assertions deleted or coverage dropped)"
        exit 2
        ;;
    failed_coverage)
        log_error "✗ Evaluation FAILED - Coverage below threshold"
        exit 3
        ;;
    failed_deprecations)
        log_error "✗ Evaluation FAILED - PyTorch deprecation warnings found"
        exit 4
        ;;
    *)
        log_error "✗ Unknown outcome: $OUTCOME"
        exit 5
        ;;
esac
