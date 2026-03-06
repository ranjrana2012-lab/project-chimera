#!/bin/bash

###############################################################################
# Documentation Audit Script
# Purpose: Detect stale documentation, version inconsistencies, and placeholders
# Usage: ./scripts/audit-docs.sh [--verbose]
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
EXPECTED_VERSION="v0.4.0"
VERBOSE=false

# Parse arguments
if [[ "${1:-}" == "--verbose" ]]; then
    VERBOSE=true
fi

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_header() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
}

###############################################################################
# Audit Functions
###############################################################################

check_version_consistency() {
    print_header "Checking Version Consistency (Expected: ${EXPECTED_VERSION})"

    local version_files=()
    local inconsistent_files=()
    local total_files=0

    # Find all markdown files
    while IFS= read -r -d '' file; do
        total_files=$((total_files + 1))

        # Check for version mentions
        if grep -q -E "v[0-9]+\.[0-9]+\.[0-9]+" "$file"; then
            version_files+=("$file")

            # Check if expected version is present
            if ! grep -q "${EXPECTED_VERSION}" "$file"; then
                inconsistent_files+=("$file")
            fi
        fi
    done < <(find "${DOCS_DIR}" -name "*.md" -type f -print0)

    log_info "Scanned ${total_files} documentation files"
    log_info "Found ${#version_files[@]} files with version references"

    if [[ ${#inconsistent_files[@]} -gt 0 ]]; then
        log_warning "Found ${#inconsistent_files[@]} files with inconsistent versions:"
        for file in "${inconsistent_files[@]}"; do
            local versions
            versions=$(grep -o -E "v[0-9]+\.[0-9]+\.[0-9]+" "$file" | sort -u | tr '\n' ', ')
            echo "  - ${file#"${PROJECT_ROOT}/"}: ${versions%,}"
        done
        return 1
    else
        log_success "All version references are consistent with ${EXPECTED_VERSION}"
        return 0
    fi
}

check_placeholders() {
    print_header "Checking for Placeholder Text"

    local placeholder_files=()
    local total_issues=0

    # Define placeholder patterns
    local patterns=("TODO" "FIXME" "XXX" "PLACEHOLDER" "TBD" "COMING SOON")

    while IFS= read -r -d '' file; do
        local file_issues=()

        for pattern in "${patterns[@]}"; do
            if grep -q -i "${pattern}" "$file"; then
                local count
                count=$(grep -c -i "${pattern}" "$file" || true)
                file_issues+=("${pattern}: ${count}")
                total_issues=$((total_issues + count))
            fi
        done

        if [[ ${#file_issues[@]} -gt 0 ]]; then
            placeholder_files+=("$file|${file_issues[*]}")
        fi
    done < <(find "${DOCS_DIR}" -name "*.md" -type f -print0)

    if [[ ${#placeholder_files[@]} -gt 0 ]]; then
        log_warning "Found ${#placeholder_files[@]} files with placeholder text (${total_issues} total issues):"
        for entry in "${placeholder_files[@]}"; do
            IFS='|' read -r file issues <<< "$entry"
            echo "  - ${file#"${PROJECT_ROOT}/"}: ${issues}"
        done
        return 1
    else
        log_success "No placeholder text found"
        return 0
    fi
}

check_service_documentation() {
    print_header "Checking Service Documentation"

    local services_dir="${PROJECT_ROOT}/services"
    local docs_services_dir="${DOCS_DIR}/services"
    local missing_docs=()
    local missing_api_sections=()

    # Get list of actual services
    if [[ ! -d "${services_dir}" ]]; then
        log_warning "Services directory not found: ${services_dir}"
        return 1
    fi

    local service_count=0
    local documented_count=0

    for service_dir in "${services_dir}"/*; do
        if [[ -d "${service_dir}" ]]; then
            local service_name
            service_name=$(basename "${service_dir}")
            service_count=$((service_count + 1))

            # Skip shared and test directories
            if [[ "${service_name}" == "shared" ]] || [[ "${service_name}" == "test" ]]; then
                continue
            fi

            # Check if documentation exists
            local doc_file
            doc_file=$(find "${docs_services_dir}" -name "*${service_name}*.md" -type f 2>/dev/null | head -n 1)

            if [[ -z "${doc_file}" ]]; then
                missing_docs+=("${service_name}")
            else
                documented_count=$((documented_count + 1))

                # Check for required sections
                if ! grep -q "## Endpoints" "${doc_file}" 2>/dev/null; then
                    missing_api_sections+=("${service_name}: missing ## Endpoints section")
                fi

                if ! grep -q "## Configuration" "${doc_file}" 2>/dev/null; then
                    missing_api_sections+=("${service_name}: missing ## Configuration section")
                fi
            fi
        fi
    done

    log_info "Found ${service_count} services, ${documented_count} documented"

    if [[ ${#missing_docs[@]} -gt 0 ]]; then
        log_warning "Services missing documentation:"
        for service in "${missing_docs[@]}"; do
            echo "  - ${service}"
        done
    fi

    if [[ ${#missing_api_sections[@]} -gt 0 ]]; then
        log_warning "Services missing required API sections:"
        for issue in "${missing_api_sections[@]}"; do
            echo "  - ${issue}"
        done
    fi

    if [[ ${#missing_docs[@]} -eq 0 ]] && [[ ${#missing_api_sections[@]} -eq 0 ]]; then
        log_success "All services have complete documentation"
        return 0
    else
        return 1
    fi
}

check_demo_documentation() {
    print_header "Checking Demo Documentation"

    local demo_dir="${DOCS_DIR}/demo"
    local issues=()

    if [[ ! -d "${demo_dir}" ]]; then
        log_error "Demo documentation directory not found: ${demo_dir}"
        return 1
    fi

    # Check for required files
    local required_files=("README.md" "demo-script.md" "service-status.md" "troubleshooting.md")

    for file in "${required_files[@]}"; do
        if [[ ! -f "${demo_dir}/${file}" ]]; then
            issues+=("Missing required file: ${file}")
        fi
    done

    # Check demo-script.md for sections
    if [[ -f "${demo_dir}/demo-script.md" ]]; then
        local section_count
        section_count=$(grep -c "^## " "${demo_dir}/demo-script.md" || true)

        if [[ ${section_count} -lt 5 ]]; then
            issues+=("demo-script.md has only ${section_count} sections (expected 5+)")
        else
            log_info "demo-script.md has ${section_count} sections"
        fi
    fi

    if [[ ${#issues[@]} -gt 0 ]]; then
        log_error "Demo documentation issues:"
        for issue in "${issues[@]}"; do
            echo "  - ${issue}"
        done
        return 1
    else
        log_success "Demo documentation is complete"
        return 0
    fi
}

check_documentation_age() {
    print_header "Checking Documentation Age"

    local stale_threshold_days=30
    local today
    today=$(date +%s)
    local stale_files=()

    while IFS= read -r -d '' file; do
        local file_mtime
        file_mtime=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)

        if [[ -n "${file_mtime}" ]]; then
            local age_days
            age_days=$(( (today - file_mtime) / 86400 ))

            if [[ ${age_days} -gt ${stale_threshold_days} ]]; then
                stale_files+=("${file#"${PROJECT_ROOT}/"} (${age_days} days)")
            fi
        fi
    done < <(find "${DOCS_DIR}" -name "*.md" -type f -print0)

    if [[ ${#stale_files[@]} -gt 0 ]]; then
        log_warning "Found ${#stale_files[@]} files not updated in > ${stale_threshold_days} days:"
        for file in "${stale_files[@]}"; do
            echo "  - ${file}"
        done
        return 1
    else
        log_success "All documentation has been updated recently"
        return 0
    fi
}

###############################################################################
# Main Execution
###############################################################################

main() {
    local exit_code=0
    local start_time
    start_time=$(date +%s)

    log_info "Starting documentation audit at $(date)"
    log_info "Project root: ${PROJECT_ROOT}"
    log_info "Docs directory: ${DOCS_DIR}"
    echo ""

    # Run all checks
    check_version_consistency || exit_code=1
    check_placeholders || exit_code=1
    check_service_documentation || exit_code=1
    check_demo_documentation || exit_code=1
    check_documentation_age || exit_code=1

    # Calculate duration
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Final summary
    print_header "Audit Summary"

    if [[ ${exit_code} -eq 0 ]]; then
        log_success "All checks passed! Documentation is healthy."
        echo ""
        log_info "Duration: ${duration} seconds"
        return 0
    else
        log_error "Some checks failed. Please review the issues above."
        echo ""
        log_info "Duration: ${duration} seconds"
        return 1
    fi
}

# Run main function
main "$@"
