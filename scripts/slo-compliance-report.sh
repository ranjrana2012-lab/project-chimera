#!/bin/bash
# SLO Compliance Report Generator
# Generates weekly SLO compliance reports for all Project Chimera services

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}/reports/slo"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

# SLO Targets (must match slo-recording-rules.yaml)
declare -A SLO_TARGETS=(
    ["openclaw-orchestrator"]="99.9%"
    ["scenespeak-agent"]="99.5%"
    ["captioning-agent"]="99.5%"
    ["bsl-agent"]="99.0%"
    ["safety-filter"]="99.9%"
    ["operator-console"]="99.5%"
)

# Prometheus query names (mapping from service to metric name)
declare -A PROMETHEUS_QUERIES=(
    ["openclaw-orchestrator"]="slo:orchestration_success_rate:30d"
    ["scenespeak-agent"]="slo:generation_success_rate:30d"
    ["captioning-agent"]="slo:captioning_delivery_rate:30d"
    ["bsl-agent"]="slo:bsl_translation_rate:30d"
    ["safety-filter"]="slo:safety_availability:30d"
    ["operator-console"]="slo:sentiment_success_rate:30d"
)

# Colors for output
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly GREEN='\033[0;32m'
readonly NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if prometheus is accessible
check_prometheus() {
    if ! curl -s -f "${PROMETHEUS_URL}/api/v1/status/config" > /dev/null 2>&1; then
        log_error "Cannot connect to Prometheus at ${PROMETHEUS_URL}"
        log_error "Please ensure Prometheus is running or set PROMETHEUS_URL environment variable"
        return 1
    fi
    return 0
}

# Query Prometheus for a metric
query_prometheus() {
    local query="$1"
    local result

    result=$(curl -s -G "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=${query}" 2>/dev/null)

    if echo "$result" | jq -e '.data.result[0].value[1]' > /dev/null 2>&1; then
        echo "$result" | jq -r '.data.result[0].value[1]'
    else
        echo "N/A"
    fi
}

# Get error budget remaining
get_error_budget() {
    local service="$1"
    local slo_target_decimal
    local actual_success_rate
    local error_budget

    # Convert SLO target percentage to decimal
    slo_target_decimal=$(echo "${SLO_TARGETS[$service]}" | sed 's/%//')
    slo_target_decimal=$(awk "BEGIN {print $slo_target_decimal / 100}")

    # Get actual success rate
    actual_success_rate=$(query_prometheus "${PROMETHEUS_QUERIES[$service]}")

    if [[ "$actual_success_rate" == "N/A" ]]; then
        echo "N/A"
        return
    fi

    # Calculate error budget remaining: (target - actual) / target
    error_budget=$(awk "BEGIN {
        target = $slo_target_decimal
        actual = $actual_success_rate
        if (target > 0) {
            budget = (target - actual) / target
            if (budget < 0) budget = 0
            printf \"%.4f\", budget
        } else {
            print \"N/A\"
        }
    }")

    echo "$error_budget"
}

# Get burn rate
get_burn_rate() {
    local service="$1"
    local slo_target_decimal
    local actual_success_rate
    local allowed_error_rate
    local current_error_rate
    local burn_rate

    # Convert SLO target percentage to decimal
    slo_target_decimal=$(echo "${SLO_TARGETS[$service]}" | sed 's/%//')
    slo_target_decimal=$(awk "BEGIN {print $slo_target_decimal / 100}")

    # Get actual success rate
    actual_success_rate=$(query_prometheus "${PROMETHEUS_QUERIES[$service]}")

    if [[ "$actual_success_rate" == "N/A" ]]; then
        echo "N/A"
        return
    fi

    # Calculate burn rate: current_error_rate / allowed_error_rate
    burn_rate=$(awk "BEGIN {
        target = $slo_target_decimal
        actual = $actual_success_rate
        allowed_error = 1 - target
        current_error = 1 - actual
        if (allowed_error > 0) {
            burn = current_error / allowed_error
            printf \"%.2f\", burn
        } else {
            print \"N/A\"
        }
    }")

    echo "$burn_rate"
}

# Determine service status
get_status() {
    local error_budget="$1"
    local status

    if [[ "$error_budget" == "N/A" ]]; then
        echo "unknown"
        return
    fi

    status=$(awk "BEGIN {
        budget = $error_budget
        if (budget >= 0.10) {
            print \"healthy\"
        } else if (budget >= 0.05) {
            print \"warning\"
        } else {
            print \"critical\"
        }
    }")

    echo "$status"
}

# Generate compliance report
generate_report() {
    local report_date="$1"
    local report_file="$2"

    log_info "Generating SLO compliance report for ${report_date}"

    # Create report header
    cat > "$report_file" << EOF
# SLO Compliance Report

**Report Date:** ${report_date}
**Reporting Period:** Last 30 days (rolling window)
**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Executive Summary

This report provides Service Level Objective (SLO) compliance status for all Project Chimera services. SLOs are measured over a 30-day rolling window to provide stable, long-term reliability metrics.

### Overall Status

EOF

    # Generate per-service sections
    local total_services=0
    local healthy_services=0
    local warning_services=0
    local critical_services=0
    local unknown_services=0

    for service in "${!SLO_TARGETS[@]}"; do
        ((total_services++)) || true

        local slo_target="${SLO_TARGETS[$service]}"
        local actual_rate=$(query_prometheus "${PROMETHEUS_QUERIES[$service]}")
        local error_budget=$(get_error_budget "$service")
        local burn_rate=$(get_burn_rate "$service")
        local status=$(get_status "$error_budget")

        # Count services by status
        case "$status" in
            healthy) ((healthy_services++)) || true ;;
            warning) ((warning_services++)) || true ;;
            critical) ((critical_services++)) || true ;;
            *) ((unknown_services++)) || true ;;
        esac

        # Format the actual rate as percentage
        local actual_percent="N/A"
        if [[ "$actual_rate" != "N/A" ]]; then
            actual_percent=$(awk "BEGIN {printf \"%.2f%%\", $actual_rate * 100}")
        fi

        # Format error budget as percentage
        local budget_percent="N/A"
        if [[ "$error_budget" != "N/A" ]]; then
            budget_percent=$(awk "BEGIN {printf \"%.2f%%\", $error_budget * 100}")
        fi

        # Add service section to report
        cat >> "$report_file" << EOF
### ${service}

| Metric | Value |
|--------|-------|
| **SLO Target** | ${slo_target} |
| **Actual Success Rate** | ${actual_percent} |
| **Error Budget Remaining** | ${budget_percent} |
| **Burn Rate** | ${burn_rate}x |
| **Status** | ${status} |

**Prometheus Query:** \`${PROMETHEUS_QUERIES[$service]}\`

EOF

    done

    # Add summary section
    cat >> "$report_file" << EOF

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Total Services** | ${total_services} |
| **Healthy** | ${healthy_services} |
| **Warning** | ${warning_services} |
| **Critical** | ${critical_services} |
| **Unknown** | ${unknown_services} |

## Recommendations

EOF

    # Add recommendations based on status
    if [[ $critical_services -gt 0 ]]; then
        cat >> "$report_file" << EOF
### 🚨 Critical Actions Required

- **Immediate attention needed for ${critical_services} service(s)**
- Error budget is depleted (< 5% remaining)
- Consider pausing non-critical deployments
- Page on-call engineer for immediate investigation

EOF
    fi

    if [[ $warning_services -gt 0 ]]; then
        cat >> "$report_file" << EOF
### ⚠️ Warning - Monitor Closely

- **${warning_services} service(s) approaching error budget depletion**
- Review recent changes and performance trends
- Consider reducing deployment frequency
- Prepare incident response if degradation continues

EOF
    fi

    if [[ $critical_services -eq 0 && $warning_services -eq 0 ]]; then
        cat >> "$report_file" << EOF
### ✅ All Systems Healthy

- All services are meeting SLO targets
- Error budgets are healthy
- Continue normal deployment cadence
- Maintain current monitoring practices

EOF
    fi

    cat >> "$report_file" << EOF
## Next Steps

1. **Review trends:** Check Grafana dashboards for 30-day trends
2. **Validate alerts:** Ensure SLO alerts are properly configured
3. **Plan capacity:** Address any resource constraints identified
4. **Update documentation:** Record any SLO changes or incidents

---

## Appendix

### SLO Definitions

- **OpenClaw Orchestrator:** 99.9% success rate for orchestration requests
- **SceneSpeak Agent:** 99.5% success rate for dialogue generation
- **Captioning Agent:** 99.5% delivery rate for caption delivery
- **BSL Agent:** 99.0% success rate for BSL translation
- **Safety Filter:** 99.9% availability for safety checks
- **Operator Console:** 99.5% success rate for sentiment analysis

### Error Budget Calculation

Error budget represents the allowable error margin within the SLO target:

\[
\text{Error Budget} = \frac{\text{SLO Target} - \text{Actual Rate}}{\text{SLO Target}}
\]

### Burn Rate

Burn rate indicates how quickly the error budget is being consumed:

\[
\text{Burn Rate} = \frac{\text{Current Error Rate}}{\text{Allowed Error Rate}}
\]

- Burn rate < 1x: Consuming budget slower than allowed
- Burn rate = 1x: Consuming budget at expected rate
- Burn rate > 1x: Consuming budget faster than allowed

---

*Report generated by: \`$(basename "$0")\`*
*Project Chimera Observability*
EOF

    log_info "Report generated successfully: $report_file"
}

# Main execution
main() {
    local report_date
    local report_file
    local use_date="${1:-$(date +%Y-%m-%d)}"

    # Validate date format
    if ! date -d "$use_date" +%Y-%m-%d >/dev/null 2>&1; then
        log_error "Invalid date format: $use_date"
        log_error "Use YYYY-MM-DD format or leave empty for today"
        exit 1
    fi

    report_date=$(date -d "$use_date" +%Y-%m-%d)

    # Create output directory
    mkdir -p "$OUTPUT_DIR"

    # Set report file path
    report_file="${OUTPUT_DIR}/slo-compliance-${report_date}.md"

    # Check Prometheus connectivity
    if ! check_prometheus; then
        log_warn "Continuing without Prometheus data - report will show N/A values"
    fi

    # Generate report
    generate_report "$report_date" "$report_file"

    # Output summary
    echo ""
    echo "=========================================="
    echo "SLO Compliance Report Generated"
    echo "=========================================="
    echo "Date:         $report_date"
    echo "Report File:  $report_file"
    echo "Prometheus:   $PROMETHEUS_URL"
    echo ""
    echo "View report:"
    echo "  cat $report_file"
    echo ""
    echo "Open in markdown viewer:"
    echo "  glow $report_file  # if glow is installed"
    echo ""

    # Display brief preview
    if command -v glow >/dev/null 2>&1; then
        glow "$report_file" 2>/dev/null || true
    else
        echo "Preview (first 20 lines):"
        echo "---"
        head -n 20 "$report_file"
        echo "---"
        echo "(Install 'glow' for better markdown viewing)"
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
