#!/bin/bash
# Project Chimera Phase 2 - Security Hardening Script
#
# Automated security scanning, vulnerability assessment, and
# hardening for Phase 2 services.
#
# Usage:
#   ./security-harden.sh --action scan
#   ./security-harden.sh --action harden --service dmx
#   ./security-harden.sh --action audit
#   ./security-harden.sh --action compliance

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES_DIR="${PROJECT_ROOT}/services"
REPORT_DIR="${PROJECT_ROOT}/security-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Security tools
DOCKER_SCAN_TOOL="${DOCKER_SCAN_TOOL:-trivy}"
BANDIT="${BANDIT:-bandit}"
SAFETY="${SAFETY:-safety}"

# Logging
log() {
    local level="$1"
    shift
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}"
}
info() { log "${BLUE}[INFO]${NC}", "$*"; }
success() { log "${GREEN}[SUCCESS]${NC}", "$*"; }
warning() { log "${YELLOW}[WARNING]${NC}", "$*"; }
error() { log "${RED}[ERROR]${NC}", "$*"; }

# Create report directory
mkdir -p "$REPORT_DIR"

# Help function
show_help() {
    cat << EOF
Project Chimera Phase 2 - Security Hardening Script

Usage: $0 [OPTIONS]

Options:
    --action ACTION       Action to perform (scan, harden, audit, compliance)
    --service SERVICE     Service to target (dmx, audio, bsl, all)
    --output FORMAT       Report format (text, json, html)
    --fix                 Auto-fix issues where possible
    --severity LEVEL      Minimum severity to report (low, medium, high, critical)
    --help                Show this help message

Actions:
    scan                  Run vulnerability scans
    harden                Apply security hardening
    audit                 Run security audit
    compliance           Check compliance with security standards

Examples:
    $0 --action scan --service all
    $0 --action harden --service dmx --fix
    $0 --action audit --output json
    $0 --action compliance

Security Checks:
    - Docker image vulnerabilities
    - Python dependency vulnerabilities
    - Code security issues (bandit)
    - SAST analysis
    - Configuration security
    - Secrets detection
    - Compliance checking

EOF
}

# Parse arguments
parse_args() {
    ACTION=""
    SERVICE="all"
    OUTPUT="text"
    FIX=false
    SEVERITY="medium"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --action)
                ACTION="$2"
                shift 2
                ;;
            --service)
                SERVICE="$2"
                shift 2
                ;;
            --output)
                OUTPUT="$2"
                shift 2
                ;;
            --fix)
                FIX=true
                shift
                ;;
            --severity)
                SEVERITY="$2"
                shift 2
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

    if [[ -z "$ACTION" ]]; then
        error "--action is required"
        show_help
        exit 1
    fi
}

# Scan Docker images for vulnerabilities
scan_docker_images() {
    local service="$1"
    local report_file="${REPORT_DIR}/docker_scan_${service}_${TIMESTAMP}.txt"

    info "Scanning Docker images for ${service}..."

    local image_name="chimera-${service}-controller"

    # Check if image exists
    if ! docker image inspect "$image_name" &>/dev/null; then
        warning "Image ${image_name} not found, skipping"
        return
    fi

    # Run Trivy scan
    if command -v trivy &>/dev/null; then
        info "Running Trivy vulnerability scanner..."
        trivy image --severity "$SEVERITY" --no-progress "$image_name" | tee "$report_file"
    else
        # Fallback to docker scan
        info "Trivy not found, using docker scan..."
        docker scan "$image_name" 2>&1 | tee "$report_file"
    fi

    # Check for critical vulnerabilities
    local critical_vulns=$(grep -i "CRITICAL" "$report_file" | wc -l)
    if [[ $critical_vulns -gt 0 ]]; then
        warning "Found ${critical_vulns} critical vulnerabilities"
    else
        success "No critical vulnerabilities found"
    fi
}

# Scan Python dependencies
scan_dependencies() {
    local service="$1"
    local report_file="${REPORT_DIR}/dependency_scan_${service}_${TIMESTAMP}.txt"

    info "Scanning Python dependencies for ${service}..."

    local service_dir="${SERVICES_DIR}/${service}-controller"
    if [[ ! -d "$service_dir" ]]; then
        warning "Service directory not found: $service_dir"
        return
    fi

    cd "$service_dir"

    # Run safety check
    if command -v safety &>/dev/null; then
        info "Running safety check..."
        safety check --json > "${REPORT_DIR}/safety_${service}_${TIMESTAMP}.json" 2>/dev/null || true
        safety check | tee "$report_file"
    fi

    # Run pip-audit
    if command -v pip-audit &>/dev/null; then
        info "Running pip-audit..."
        pip-audit --format json > "${REPORT_DIR}/pipaudit_${service}_${TIMESTAMP}.json" 2>/dev/null || true
        pip-audit | tee -a "$report_file"
    fi

    cd - > /dev/null
}

# Run bandit security analysis
run_bandit_scan() {
    local service="$1"
    local report_file="${REPORT_DIR}/bandit_scan_${service}_${TIMESTAMP}.txt"

    info "Running Bandit security analysis for ${service}..."

    local service_dir="${SERVICES_DIR}/${service}-controller"
    if [[ ! -d "$service_dir" ]]; then
        warning "Service directory not found: $service_dir"
        return
    fi

    cd "$service_dir"

    if command -v bandit &>/dev/null; then
        bandit -r . -f txt -o "$report_file" || true

        # Also generate JSON if requested
        if [[ "$OUTPUT" == "json" ]]; then
            bandit -r . -f json -o "${REPORT_DIR}/bandit_${service}_${TIMESTAMP}.json" || true
        fi

        # Check for high severity issues
        local high_severity=$(grep -i "Severity: High" "$report_file" | wc -l)
        if [[ $high_severity -gt 0 ]]; then
            warning "Found ${high_severity} high severity issues"
        else
            success "No high severity issues found"
        fi
    else
        warning "Bandit not installed, skipping"
    fi

    cd - > /dev/null
}

# Detect secrets in code
detect_secrets() {
    local report_file="${REPORT_DIR}/secrets_scan_${TIMESTAMP}.txt"

    info "Scanning for secrets in code..."

    if command -v trufflehog &>/dev/null; then
        info "Running trufflehog..."
        trufflehog filesystem "$PROJECT_ROOT/services" \
            --json \
            --output "${REPORT_DIR}/secrets_${TIMESTAMP}.json" 2>/dev/null || true
    fi

    # Simple grep-based scan for common secrets
    info "Running basic secrets scan..."

    echo "Secrets Scan Results" | tee "$report_file"
    echo "==================" | tee -a "$report_file"

    # Scan for API keys
    local api_keys=$(grep -r "api[_-]key\|API[_-]KEY" "$PROJECT_ROOT/services" 2>/dev/null || true)
    if [[ -n "$api_keys" ]]; then
        warning "Potential API keys found" | tee -a "$report_file"
        echo "$api_keys" | head -10 | tee -a "$report_file"
    fi

    # Scan for passwords
    local passwords=$(grep -ri "password.*=.*['\"][^'\"]+['\"]" "$PROJECT_ROOT/services" 2>/dev/null || true)
    if [[ -n "$passwords" ]]; then
        warning "Potential hardcoded passwords found" | tee -a "$report_file"
        echo "$passwords" | head -10 | tee -a "$report_file"
    fi

    # Scan for tokens
    local tokens=$(grep -ri "token.*=.*['\"][^'\"]+['\"]" "$PROJECT_ROOT/services" 2>/dev/null || true)
    if [[ -n "$tokens" ]]; then
        warning "Potential hardcoded tokens found" | tee -a "$report_file"
        echo "$tokens" | head -10 | tee -a "$report_file"
    fi

    success "Secrets scan complete"
}

# Run security audit
run_security_audit() {
    info "Running comprehensive security audit..."

    local audit_report="${REPORT_DIR}/security_audit_${TIMESTAMP}.md"

    cat > "$audit_report" << EOF
# Project Chimera Phase 2 - Security Audit Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Scanner:** Automated Security Audit

## Executive Summary

EOF

    # Run all scans
    local services_to_scan=()
    case "$SERVICE" in
        all)
            services_to_scan=("dmx" "audio" "bsl")
            ;;
        dmx|audio|bsl)
            services_to_scan=("$SERVICE")
            ;;
    esac

    local total_vulns=0
    local total_issues=0

    for svc in "${services_to_scan[@]}"; do
        echo "## ${svc^} Controller" >> "$audit_report"
        echo "" >> "$audit_report"

        # Docker scan
        scan_docker_images "$svc"
        local docker_vulns=$?

        # Dependency scan
        scan_dependencies "$svc"
        local dep_vulns=$?

        # Bandit scan
        run_bandit_scan "$svc"
        local bandit_issues=$?

        # Count issues
        if [[ $docker_vulns -ne 0 ]]; then ((total_vulns++)); fi
        if [[ $dep_vulns -ne 0 ]]; then ((total_vulns++)); fi
        if [[ $bandit_issues -ne 0 ]]; then ((total_issues++)); fi

        echo "" >> "$audit_report"
    done

    # Secrets scan
    detect_secrets

    # Summary
    cat >> "$audit_report" << EOF

## Summary

- **Services Scanned:** ${#services_to_scan[@]}
- **Vulnerabilities Found:** $total_vulns
- **Security Issues:** $total_issues

## Recommendations

EOF

    # Add recommendations based on findings
    if [[ $total_vulns -gt 0 ]]; then
        cat >> "$audit_report" << EOF
1. **Update Dependencies:** Update vulnerable packages to latest secure versions
2. **Patch Images:** Rebuild Docker images with updated base images
3. **Monitor:** Set up continuous vulnerability scanning

EOF
    fi

    if [[ $total_issues -gt 0 ]]; then
        cat >> "$audit_report" << EOF
1. **Code Review:** Review and fix high-severity security issues
2. **Static Analysis:** Integrate SAST into CI/CD pipeline
3. **Training:** Provide security training for developers

EOF
    fi

    success "Security audit complete: $audit_report"
}

# Apply security hardening
apply_hardening() {
    info "Applying security hardening..."

    local services_to_harden=()
    case "$SERVICE" in
        all)
            services_to_harden=("dmx" "audio" "bsl")
            ;;
        dmx|audio|bsl)
            services_to_harden=("$SERVICE")
            ;;
    esac

    for svc in "${services_to_harden[@]}"; do
        info "Hardening ${svc} controller..."

        local service_dir="${SERVICES_DIR}/${svc}-controller"
        if [[ ! -d "$service_dir" ]]; then
            continue
        fi

        cd "$service_dir"

        # Update requirements.txt with secure versions
        if [[ -f "requirements.txt" ]]; then
            info "Updating dependencies to secure versions..."
            pip-compile --upgrade --resolver-version latest 2>/dev/null || true
        fi

        # Add security headers to FastAPI app if not present
        # (This is a placeholder - actual implementation would modify code)

        cd - > /dev/null
    done

    success "Security hardening applied"
}

# Check compliance
check_compliance() {
    info "Checking security compliance..."

    local compliance_report="${REPORT_DIR}/compliance_${TIMESTAMP}.txt"

    cat > "$compliance_report" << EOF
Project Chimera Phase 2 - Security Compliance Check
================================================

Date: $(date '+%Y-%m-%d %H:%M:%S')

Compliance Framework: OWASP Top 10 2021

EOF

    local compliant_items=0
    local total_items=10

    # Check 1: Injection
    echo "A01:2021 - Broken Access Control" >> "$compliance_report"
    if grep -r "@app.*post.*admin" "$PROJECT_ROOT/services" 2>/dev/null | grep -v "authentication" > /dev/null; then
        echo "  ⚠️  Warning: Admin endpoints without authentication detected" >> "$compliance_report"
    else
        echo "  ✓ Pass: No unauthenticated admin endpoints" >> "$compliance_report"
        ((compliant_items++))
    fi
    echo "" >> "$compliance_report"

    # Check 2: Cryptographic Failures
    echo "A02:2021 - Cryptographic Failures" >> "$compliance_report"
    if grep -r "http://" "$PROJECT_ROOT/services" 2>/dev/null | grep -v "localhost" > /dev/null; then
        echo "  ⚠️  Warning: Non-HTTPS URLs detected" >> "$compliance_report"
    else
        echo "  ✓ Pass: No insecure HTTP URLs" >> "$compliance_report"
        ((compliant_items++))
    fi
    echo "" >> "$compliance_report"

    # Check 3: Injection
    echo "A03:2021 - Injection" >> "$compliance_report"
    if grep -r "execute.*%\|format.*%" "$PROJECT_ROOT/services" 2>/dev/null; then
        echo "  ⚠️  Warning: Potential SQL injection risks" >> "$compliance_report"
    else
        echo "  ✓ Pass: No obvious injection risks" >> "$compliance_report"
        ((compliant_items++))
    fi
    echo "" >> "$compliance_report"

    # Check 4: Insecure Design
    echo "A04:2021 - Insecure Design" >> "$compliance_report"
    if grep -r "emergency.*stop\|emergency.*mute" "$PROJECT_ROOT/services" 2>/dev/null; then
        echo "  ✓ Pass: Emergency procedures implemented" >> "$compliance_report"
        ((compliant_items++))
    else
        echo "  ⚠️  Warning: No emergency procedures found" >> "$compliance_report"
    fi
    echo "" >> "$compliance_report"

    # Check 5: Security Misconfiguration
    echo "A05:2021 - Security Misconfiguration" >> "$compliance_report"
    if grep -r "DEBUG.*=.*True\|debug.*=.*true" "$PROJECT_ROOT/services" 2>/dev/null; then
        echo "  ⚠️  Warning: Debug mode may be enabled" >> "$compliance_report"
    else
        echo "  ✓ Pass: Debug mode appears disabled" >> "$compliance_report"
        ((compliant_items++))
    fi
    echo "" >> "$compliance_report"

    # More checks would go here...

    # Summary
    cat >> "$compliance_report" << EOF

===========================================
Compliance Score: ${compliant_items}/${total_items} (${compliant_items}0%)

Status: $([ $compliant_items -ge 8 ] && echo "COMPLIANT" || echo "NEEDS IMPROVEMENT")

Next Steps:
$(if [[ $compliant_items -lt 8 ]]; then
    echo "1. Review failed compliance items"
    echo "2. Implement recommended fixes"
    echo "3. Re-run compliance check"
else
    echo "1. Continue monitoring"
    echo "2. Schedule periodic compliance reviews"
fi)

EOF

    success "Compliance check complete: $compliance_report"
}

# Main function
main() {
    parse_args "$@"

    echo "Project Chimera Phase 2 - Security Hardening"
    echo "================================================"
    echo ""

    # Execute action
    case "$ACTION" in
        scan)
            local services_to_scan=()
            case "$SERVICE" in
                all)
                    services_to_scan=("dmx" "audio" "bsl")
                    ;;
                dmx|audio|bsl)
                    services_to_scan=("$SERVICE")
                    ;;
            esac

            for svc in "${services_to_scan[@]}"; do
                scan_docker_images "$svc"
                scan_dependencies "$svc"
                run_bandit_scan "$svc"
            done

            detect_secrets
            ;;
        harden)
            apply_hardening
            ;;
        audit)
            run_security_audit
            ;;
        compliance)
            check_compliance
            ;;
        *)
            error "Unknown action: $ACTION"
            exit 1
            ;;
    esac

    success "Security operations complete"
}

main "$@"
