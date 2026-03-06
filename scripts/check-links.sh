#!/bin/bash

###############################################################################
# Documentation Link Validation Script
# Purpose: Find broken internal markdown links
# Usage: ./scripts/check-links.sh [--verbose] [--fix]
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
VERBOSE=false
FIX=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        *)
            echo "Usage: $0 [--verbose|--v] [--fix]"
            exit 1
            ;;
    esac
done

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

log_debug() {
    if [[ "${VERBOSE}" == true ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

print_header() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
}

# Normalize a path (resolve .. and .)
normalize_path() {
    local path="$1"
    # Remove markdown anchor (#section)
    path="${path%%#*}"
    echo "${path}"
}

# Check if a relative link is valid
check_relative_link() {
    local source_file="$1"
    local link="$2"
    local link_path

    # Normalize the link
    link_path=$(normalize_path "${link}")

    # Get directory of source file
    local source_dir
    source_dir=$(dirname "${source_file}")

    # Resolve the target path
    local target_path
    if [[ "${link_path}" == /* ]]; then
        # Absolute path (relative to project root)
        target_path="${PROJECT_ROOT}${link_path}"
    else
        # Relative path
        target_path="${source_dir}/${link_path}"
    fi

    # Resolve .. and .
    target_path=$(cd "$(dirname "${target_path}")" 2>/dev/null && pwd)/$(basename "${target_path}")

    # Check if file exists
    if [[ -f "${target_path}" ]]; then
        echo "valid"
        return 0
    else
        echo "invalid|${target_path}"
        return 1
    fi
}

# Extract markdown links from a file
extract_links() {
    local file="$1"

    # Extract markdown links: [text](url)
    grep -o -E '\[[^\]]*\]\([^\)]+\)' "$file" 2>/dev/null | \
        sed -E 's/.*\(([^\)]+)\).*/\1/' | \
        sort -u
}

# Check if a link is internal (markdown file)
is_internal_link() {
    local link="$1"

    # Remove anchor
    local link_path="${link%%#*}"

    # Check if it's a markdown file (internal link)
    if [[ "${link_path}" == *.md ]] || [[ "${link_path}" == *.md#* ]]; then
        return 0
    fi

    # Check if it's a relative link without extension (might be a directory)
    if [[ "${link_path}" != http* ]] && [[ "${link_path}" != //* ]]; then
        return 0
    fi

    return 1
}

###############################################################################
# Validation Functions
###############################################################################

validate_internal_links() {
    print_header "Validating Internal Markdown Links"

    local total_links=0
    local valid_links=0
    local invalid_links=()
    local files_processed=0

    # Find all markdown files
    while IFS= read -r -d '' file; do
        files_processed=$((files_processed + 1))
        log_debug "Processing: ${file#"${PROJECT_ROOT}/"}"

        # Extract links from file
        local links
        links=$(extract_links "${file}")

        if [[ -z "${links}" ]]; then
            continue
        fi

        # Check each link
        while IFS= read -r link; do
            if [[ -z "${link}" ]]; then
                continue
            fi

            total_links=$((total_links + 1))

            # Skip external links
            if ! is_internal_link "${link}"; then
                log_debug "Skipping external link: ${link}"
                continue
            fi

            # Check relative link
            local result
            result=$(check_relative_link "${file}" "${link}")

            if [[ "${result}" == "valid" ]]; then
                valid_links=$((valid_links + 1))
                log_debug "  ✓ ${link}"
            else
                IFS='|' read -r status target_path <<< "${result}"
                invalid_links+=("${file#"${PROJECT_ROOT}/"}|${link}|${target_path}")
                log_debug "  ✗ ${link} -> ${target_path}"
            fi
        done <<< "${links}"

    done < <(find "${DOCS_DIR}" -name "*.md" -type f -print0)

    # Report results
    log_info "Processed ${files_processed} documentation files"
    log_info "Found ${total_links} total links, ${valid_links} valid, ${#invalid_links[@]} invalid"

    if [[ ${#invalid_links[@]} -gt 0 ]]; then
        log_error "Found ${#invalid_links[@]} broken internal links:"
        for entry in "${invalid_links[@]}"; do
            IFS='|' read -r source link target <<< "${entry}"
            echo ""
            echo "  Source: ${source}"
            echo "  Link: ${link}"
            echo "  Target: ${target}"
        done

        # Optionally fix links
        if [[ "${FIX}" == true ]]; then
            log_info "Attempting to fix broken links..."
            # Fix implementation would go here
            log_warning "Auto-fix not implemented yet. Please fix manually."
        fi

        return 1
    else
        log_success "All internal links are valid!"
        return 0
    fi
}

validate_section_anchors() {
    print_header "Validating Section Anchors"

    local anchor_issues=()
    local files_checked=0

    while IFS= read -r -d '' file; do
        files_checked=$((files_checked + 1))

        # Extract links with anchors
        local links
        links=$(grep -o -E '\[[^\]]*\]\([^)]*#[^)]+\)' "$file" 2>/dev/null | \
                sed -E 's/.*\(([^)]+)\)/\1/')

        if [[ -z "${links}" ]]; then
            continue
        fi

        # Check each anchor
        while IFS= read -r link; do
            if [[ -z "${link}" ]]; then
                continue
            fi

            # Extract file path and anchor
            local link_file="${link%%#*}"
            local anchor="${link#*#}"

            # Resolve target file
            local target_file
            if [[ -z "${link_file}" ]] || [[ "${link_file}" == "${link}" ]]; then
                # Same file reference
                target_file="${file}"
            else
                # Different file
                local source_dir
                source_dir=$(dirname "${file}")
                target_file="${source_dir}/${link_file}"
                target_file=$(normalize_path "${target_file}")
            fi

            # Check if target file exists
            if [[ ! -f "${target_file}" ]]; then
                continue
            fi

            # Check if anchor exists in target file
            local anchor_pattern
            anchor_pattern=$(echo "${anchor}" | sed 's/-/ /g' | sed 's/\.md$//')

            if ! grep -q -i "^##* ${anchor_pattern}" "${target_file}" 2>/dev/null; then
                anchor_issues+=("${file#"${PROJECT_ROOT}/"}|${link}|${target_file#"${PROJECT_ROOT}/"}")
            fi
        done <<< "${links}"

    done < <(find "${DOCS_DIR}" -name "*.md" -type f -print0)

    log_info "Checked ${files_checked} files for section anchors"

    if [[ ${#anchor_issues[@]} -gt 0 ]]; then
        log_warning "Found ${#anchor_issues[@]} invalid section anchors:"
        for entry in "${anchor_issues[@]}"; do
            IFS='|' read -r source link target <<< "${entry}"
            echo "  ${source} -> ${link} (in ${target})"
        done
        return 1
    else
        log_success "All section anchors are valid!"
        return 0
    fi
}

check_image_references() {
    print_header "Checking Image References"

    local missing_images=()
    local total_images=0

    while IFS= read -r -d '' file; do
        # Extract image references: ![alt](path)
        local images
        images=$(grep -o -E '!\[[^\]]*\]\([^\)]+\)' "$file" 2>/dev/null | \
                 sed -E 's/.*\(([^\)]+)\).*/\1/')

        if [[ -z "${images}" ]]; then
            continue
        fi

        while IFS= read -r img; do
            if [[ -z "${img}" ]]; then
                continue
            fi

            total_images=$((total_images + 1))

            # Resolve image path
            local source_dir
            source_dir=$(dirname "${file}")
            local img_path="${source_dir}/${img}"

            # Check if image exists
            if [[ ! -f "${img_path}" ]]; then
                missing_images+=("${file#"${PROJECT_ROOT}/"}|${img}")
            fi
        done <<< "${images}"

    done < <(find "${DOCS_DIR}" -name "*.md" -type f -print0)

    log_info "Found ${total_images} image references"

    if [[ ${#missing_images[@]} -gt 0 ]]; then
        log_warning "Found ${#missing_images[@]} missing image files:"
        for entry in "${missing_images[@]}"; do
            IFS='|' read -r source img <<< "${entry}"
            echo "  ${source} -> ${img}"
        done
        return 1
    else
        log_success "All image references are valid!"
        return 0
    fi
}

generate_link_report() {
    print_header "Generating Link Validation Report"

    local report_file="${PROJECT_ROOT}/docs/link-validation-report.md"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "${report_file}" << EOF
# Link Validation Report

**Generated:** ${timestamp}
**Project:** Project Chimera
**Branch:** $(git -C "${PROJECT_ROOT}" branch --show-current)

## Summary

This report validates all internal markdown links, section anchors, and image references in the documentation.

## Validation Checks

### 1. Internal Markdown Links
- Status: $(validate_internal_links >/dev/null 2>&1 && echo "✓ PASSED" || echo "✗ FAILED")
- Description: All relative links between documentation files resolve correctly

### 2. Section Anchors
- Status: $(validate_section_anchors >/dev/null 2>&1 && echo "✓ PASSED" || echo "✗ FAILED")
- Description: All section anchors (\#section-name) exist in their target files

### 3. Image References
- Status: $(check_image_references >/dev/null 2>&1 && echo "✓ PASSED" || echo "✗ FAILED")
- Description: All referenced images exist in the repository

## Recommendations

1. Run this script regularly to catch broken links early
2. Use relative paths for internal links (not absolute paths)
3. Use descriptive section names that work well as anchors
4. Keep images in the same directory as the documentation that references them

## Automation

Consider adding this script to your CI/CD pipeline:

\`\`\`yaml
- name: Validate Documentation Links
  run: ./scripts/check-links.sh
\`\`\`

EOF

    log_success "Report generated: ${report_file}"
}

###############################################################################
# Main Execution
###############################################################################

main() {
    local exit_code=0
    local start_time
    start_time=$(date +%s)

    log_info "Starting link validation at $(date)"
    log_info "Project root: ${PROJECT_ROOT}"
    log_info "Docs directory: ${DOCS_DIR}"
    echo ""

    # Run all validations
    validate_internal_links || exit_code=1
    validate_section_anchors || exit_code=1
    check_image_references || exit_code=1

    # Generate report
    generate_link_report

    # Calculate duration
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Final summary
    print_header "Validation Summary"

    if [[ ${exit_code} -eq 0 ]]; then
        log_success "All link validation checks passed!"
        echo ""
        log_info "Duration: ${duration} seconds"
        return 0
    else
        log_error "Some validation checks failed. Please review the issues above."
        echo ""
        log_info "Duration: ${duration} seconds"
        return 1
    fi
}

# Run main function
main "$@"
