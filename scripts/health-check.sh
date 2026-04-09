#!/bin/bash
# Project Chimera Phase 2 - Health Check Script
#
# Comprehensive health checking for all Phase 2 services
#
# Usage:
#   ./health-check.sh --service all
#   ./health-check.sh --service dmx --verbose
#   ./health-check.sh --watch

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-5}
INTERVAL=${HEALTH_CHECK_INTERVAL:-10}
WATCH=false
VERBOSE=false

# Services configuration
declare -A SERVICES
SERVICES[dmx]="DMX Controller|8001|/health"
SERVICES[audio]="Audio Controller|8002|/health"
SERVICES[bsl]="BSL Avatar Service|8003|/health"

# Help function
show_help() {
    cat << EOF
Project Chimera Phase 2 - Health Check Script

Usage: $0 [OPTIONS]

Options:
    --service SERVICE     Service to check (dmx, audio, bsl, all)
    --timeout SECONDS     Request timeout (default: 5)
    --interval SECONDS    Interval between checks (default: 10)
    --watch               Continuous monitoring mode
    --verbose             Show detailed health information
    --help                Show this help message

Examples:
    $0 --service all
    $0 --service dmx --verbose
    $0 --watch

EOF
}

# Parse arguments
parse_args() {
    SERVICE="all"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --service)
                SERVICE="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --interval)
                INTERVAL="$2"
                shift 2
                ;;
            --watch)
                WATCH=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check single service
check_service() {
    local service_key="$1"
    local service_info="${SERVICES[$service_key]}"
    local service_name=$(echo "$service_info" | cut -d'|' -f1)
    local port=$(echo "$service_info" | cut -d'|' -f2)
    local endpoint=$(echo "$service_info" | cut -d'|' -f3)
    local url="http://localhost:${port}${endpoint}"

    # Print service name
    echo -n "  ${service_name} (${port}): "

    # Make health check request
    local response
    local status_code
    local response_time

    if response=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" \
        --max-time "$TIMEOUT" "$url" 2>/dev/null); then
        status_code=$(echo "$response" | cut -d'|' -f1)
        response_time=$(echo "$response" | cut -d'|' -f2)

        if [[ "$status_code" == "200" ]]; then
            echo -e "${GREEN}✓ Healthy${NC} (${response_time}s)"
            if [[ "$VERBOSE" == true ]]; then
                show_service_details "$service_key"
            fi
            return 0
        else
            echo -e "${RED}✗ Unhealthy (HTTP ${status_code})${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    fi
}

# Show detailed service information
show_service_details() {
    local service_key="$1"
    local service_info="${SERVICES[$service_key]}"
    local port=$(echo "$service_info" | cut -d'|' -f2)

    # Get detailed status
    local status_url="http://localhost:${port}/api/status"
    local details

    if details=$(curl -s --max-time "$TIMEOUT" "$status_url" 2>/dev/null); then
        echo "    Details:"
        echo "$details" | jq -r 'to_entries | .[] | "      \(.key): \(.value)"' 2>/dev/null || echo "      $details"
    fi
}

# Check all services
check_all_services() {
    local services_to_check=()

    case "$SERVICE" in
        all)
            services_to_check=("dmx" "audio" "bsl")
            ;;
        dmx|audio|bsl)
            services_to_check=("$SERVICE")
            ;;
        *)
            echo "Invalid service: $SERVICE"
            exit 1
            ;;
    esac

    local healthy=0
    local total=${#services_to_check[@]}

    for service_key in "${services_to_check[@]}"; do
        if check_service "$service_key"; then
            ((healthy++))
        fi
    done

    echo ""
    echo "Summary: ${healthy}/${total} services healthy"

    if [[ $healthy -eq $total ]]; then
        return 0
    else
        return 1
    fi
}

# Watch mode
watch_mode() {
    echo "Watching service health (Ctrl+C to stop)..."
    echo ""

    while true; do
        clear
        echo "Project Chimera Phase 2 - Service Health"
        echo "Last check: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""

        check_all_services

        echo ""
        echo "Next check in ${INTERVAL}s..."
        sleep "$INTERVAL"
    done
}

# Main function
main() {
    parse_args "$@"

    if [[ "$WATCH" == true ]]; then
        watch_mode
    else
        echo "Project Chimera Phase 2 - Service Health Check"
        echo ""
        check_all_services
    fi
}

main "$@"
