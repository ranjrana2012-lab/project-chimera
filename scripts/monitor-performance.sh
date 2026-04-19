#!/bin/bash
#
# Performance Monitoring Script for Project Chimera (Iteration 35)
#
# Continuously monitors response times and alerts on degradation.
#
# Usage:
#   ./scripts/monitor-performance.sh [--duration SECONDS] [--interval SECONDS]
#
# Options:
#   --duration  How long to monitor (default: 3600s = 1 hour)
#   --interval  How often to check (default: 30s)
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
DURATION="${2:-3600}"  # 1 hour default
INTERVAL="${3:-30}"     # 30 seconds default

# Performance thresholds (in milliseconds)
ORCHESTRATION_P95_THRESHOLD=5000
FIRST_REQUEST_THRESHOLD=1000
CACHE_HIT_THRESHOLD=100

# Service endpoints
ORCHESTRATOR_URL="http://localhost:8000"
SENTIMENT_URL="http://localhost:8004"
SCENESPEAK_URL="http://localhost:8001"
SAFETY_URL="http://localhost:8006"
TRANSLATION_URL="http://localhost:8006"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Alert tracking
declare -i alert_count=0
declare -i warning_count=0

# ============================================================================
# Logging Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ✓ $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} ⚠ $1"
    ((warning_count++))
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} ✗ $1"
    ((alert_count++))
}

log_metric() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} 📊 $1"
}

# ============================================================================
# Performance Check Functions
# ============================================================================

measure_orchestration_latency() {
    local url="$ORCHESTRATOR_URL/api/orchestrate"

    # First request (may include cold start)
    local start_time
    start_time=$(date +%s%3N)

    local response
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "Performance test prompt",
            "show_id": "monitoring_test",
            "context": {}
        }' 2>/dev/null)

    local end_time
    end_time=$(date +%s%3N)

    local duration_ms=$((end_time - start_time))
    local http_code="${response##*$'\n'}"

    if [[ "$http_code" == "200" ]]; then
        log_metric "Orchestration: ${duration_ms}ms"
        echo "$duration_ms"
    else
        log_error "Orchestration request failed (HTTP $http_code)"
        echo "-1"
    fi
}

measure_cache_hit() {
    local url="$ORCHESTRATOR_URL/api/orchestrate"
    local test_prompt="Cache performance test prompt"

    # First request to populate cache
    curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"$test_prompt\", \"show_id\": \"cache_test\", \"context\": {}}" > /dev/null

    # Second request should hit cache
    local start_time
    start_time=$(date +%s%3N)

    local response
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"$test_prompt\", \"show_id\": \"cache_test\", \"context\": {}}")

    local end_time
    end_time=$(date +%s%3N)

    local duration_ms=$((end_time - start_time))
    local http_code="${response##*$'\n'}"

    if [[ "$http_code" == "200" ]]; then
        log_metric "Cache hit: ${duration_ms}ms"
        echo "$duration_ms"
    else
        log_warning "Cache hit measurement failed"
        echo "-1"
    fi
}

check_service_health() {
    local service_name="$1"
    local url="$2"

    local response
    response=$(curl -s -w "\n%{http_code}" "$url/health" 2>/dev/null)
    local http_code="${response##*$'\n'}"
    local body="${response%$'\n'*}"

    if [[ "$http_code" == "200" ]] && echo "$body" | grep -q '"status":"healthy"'; then
        echo "up"
    else
        echo "down"
    fi
}

# ============================================================================
# Alert Functions
# ============================================================================

check_thresholds() {
    local metric_name="$1"
    local value="$2"
    local threshold="$3"

    if [[ "$value" == "-1" ]]; then
        return
    fi

    if [[ "$value" -gt "$threshold" ]]; then
        log_error "$metric_name: ${value}ms exceeds threshold of ${threshold}ms"
    fi
}

# ============================================================================
# Monitoring Loop
# ============================================================================

monitor_loop() {
    local end_time
    end_time=$(($(date +%s) + DURATION))

    log_info "Starting performance monitoring for ${DURATION}s..."
    log_info "Checking every ${INTERVAL}s"
    log_info "Alert thresholds:"
    log_info "  - Orchestration P95: ${ORCHESTRATION_P95_THRESHOLD}ms"
    log_info "  - Cache hit: ${CACHE_HIT_THRESHOLD}ms"
    echo ""

    local iteration=0

    while [[ $(date +%s) -lt $end_time ]]; do
        ((iteration++))

        # Create separator line
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

        # Check service health
        log_info "Checking service health..."
        local orchestrator_status sentiment_status scenespeak_status

        orchestrator_status=$(check_service_health "Orchestrator" "$ORCHESTRATOR_URL")
        sentiment_status=$(check_service_health "Sentiment" "$SENTIMENT_URL")
        scenespeak_status=$(check_service_health "SceneSpeak" "$SCENESPEAK_URL")

        if [[ "$orchestrator_status" == "up" ]]; then
            log_success "Orchestrator: UP"
        else
            log_error "Orchestrator: DOWN"
        fi

        if [[ "$sentiment_status" == "up" ]]; then
            log_success "Sentiment: UP"
        else
            log_warning "Sentiment: DOWN"
        fi

        if [[ "$scenespeak_status" == "up" ]]; then
            log_success "SceneSpeak: UP"
        else
            log_warning "SceneSpeak: DOWN"
        fi

        echo ""

        # Measure orchestration latency
        if [[ "$orchestrator_status" == "up" ]]; then
            log_info "Measuring orchestration latency..."
            local latency
            latency=$(measure_orchestration_latency)

            if [[ "$latency" != "-1" ]]; then
                check_thresholds "Orchestration" "$latency" "$ORCHESTRATION_P95_THRESHOLD"
            fi
            echo ""
        fi

        # Measure cache hit performance
        if [[ "$orchestrator_status" == "up" ]]; then
            log_info "Measuring cache hit performance..."
            local cache_time
            cache_time=$(measure_cache_hit)

            if [[ "$cache_time" != "-1" ]]; then
                check_thresholds "Cache Hit" "$cache_time" "$CACHE_HIT_THRESHOLD"
            fi
            echo ""
        fi

        # Summary for this iteration
        log_info "Iteration $iteration complete. Warnings: $warning_count, Alerts: $alert_count"
        echo ""

        # Wait before next iteration
        if [[ $(date +%s) -lt $end_time ]]; then
            sleep $INTERVAL
        fi
    done
}

# ============================================================================
# Main
# ============================================================================

main() {
    log_info "Project Chimera Performance Monitor"
    log_info "========================================="
    echo ""

    monitor_loop

    echo ""
    log_info "Monitoring complete."
    log_info "Total alerts: $alert_count"
    log_info "Total warnings: $warning_count"

    if [[ $alert_count -gt 0 ]]; then
        log_error "Performance issues detected during monitoring period."
        exit 1
    else
        log_success "No performance issues detected."
        exit 0
    fi
}

# ============================================================================
# Script Entry Point
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
