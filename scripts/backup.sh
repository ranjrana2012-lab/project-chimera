#!/bin/bash
# Project Chimera Phase 2 - Backup Script
#
# Automated backup for configuration, data, and assets
#
# Usage:
#   ./backup.sh --type full
#   ./backup.sh --type config --encrypt
#   ./backup.sh --list
#   ./backup.sh --restore backup_20260409_120000

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"
BACKUP_RETENTION_DAYS=30
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

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
Project Chimera Phase 2 - Backup Script

Usage: $0 [OPTIONS]

Options:
    --type TYPE           Backup type (full, config, data)
    --encrypt             Encrypt backup with GPG
    --compression LEVEL   Compression level (0-9, default: 6)
    --list                List all backups
    --restore BACKUP      Restore from backup
    --cleanup             Clean old backups
    --help                Show this help message

Environment Variables:
    BACKUP_ENCRYPTION_KEY GPG key for encryption
    BACKUP_RETENTION_DAYS Backup retention period (default: 30)

Examples:
    $0 --type full --encrypt
    $0 --type config
    $0 --list
    $0 --restore backup_20260409_120000

EOF
}

# Parse arguments
parse_args() {
    BACKUP_TYPE="full"
    ENCRYPT=false
    COMPRESSION=6
    LIST=false
    RESTORE=""
    CLEANUP=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            --encrypt)
                ENCRYPT=true
                shift
                ;;
            --compression)
                COMPRESSION="$2"
                shift 2
                ;;
            --list)
                LIST=true
                shift
                ;;
            --restore)
                RESTORE="$2"
                shift 2
                ;;
            --cleanup)
                CLEANUP=true
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

# Create backup
create_backup() {
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    info "Creating ${BACKUP_TYPE} backup: $backup_name"

    # Create backup directory
    mkdir -p "$backup_path"

    # Create backup info
    cat > "${backup_path}/backup_info.txt" << EOF
Backup Information
==================
Backup Name: $backup_name
Backup Type: $BACKUP_TYPE
Created: $timestamp
Hostname: $(hostname)
User: $(whoami)
Git Commit: $(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo "N/A")
Git Branch: $(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "N/A")
EOF

    # Backup based on type
    case "$BACKUP_TYPE" in
        full)
            backup_full "$backup_path"
            ;;
        config)
            backup_config "$backup_path"
            ;;
        data)
            backup_data "$backup_path"
            ;;
        *)
            error "Invalid backup type: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # Create archive
    info "Creating backup archive..."
    local archive_file="${BACKUP_DIR}/${backup_name}.tar.gz"

    tar -czf "$archive_file" -C "$BACKUP_DIR" "$backup_name"

    # Remove uncompressed backup
    rm -rf "$backup_path"

    # Encrypt if requested
    if [[ "$ENCRYPT" == true ]]; then
        if [[ -z "$ENCRYPTION_KEY" ]]; then
            warning "No encryption key provided, skipping encryption"
        else
            info "Encrypting backup..."
            gpg --symmetric --cipher-algo AES256 \
                --batch --passphrase "$ENCRYPTION_KEY" \
                --output "${archive_file}.gpg" "$archive_file"
            rm -f "$archive_file"
            archive_file="${archive_file}.gpg"
        fi
    fi

    success "Backup created: $archive_file"
}

# Backup full system
backup_full() {
    local backup_path="$1"

    info "Backing up configuration..."
    backup_config "$backup_path"

    info "Backing up data..."
    backup_data "$backup_path"

    info "Backing up assets..."
    backup_assets "$backup_path"
}

# Backup configuration
backup_config() {
    local backup_path="$1"

    mkdir -p "${backup_path}/config"

    # Environment files
    cp "${PROJECT_ROOT}/.env" "$backup_path/config/" 2>/dev/null || true

    # Service configuration
    cp -r "${PROJECT_ROOT}/services/config" "$backup_path/" 2>/dev/null || true

    # Monitoring configuration
    cp -r "${PROJECT_ROOT}/monitoring" "$backup_path/" 2>/dev/null || true
}

# Backup data
backup_data() {
    local backup_path="$1"

    mkdir -p "${backup_path}/data"

    # Service data
    cp -r "${PROJECT_ROOT}/services/data" "$backup_path/" 2>/dev/null || true

    # BSL gesture library
    cp -r "${PROJECT_ROOT}/services/bsl-avatar-service/data" "$backup_path/" 2>/dev/null || true
}

# Backup assets
backup_assets() {
    local backup_path="$1"

    mkdir -p "${backup_path}/assets"

    # Audio assets
    cp -r "${PROJECT_ROOT}/services/assets" "$backup_path/" 2>/dev/null || true
}

# Restore backup
restore_backup() {
    local backup_name="$1"
    local backup_file="${BACKUP_DIR}/${backup_name}"

    info "Restoring backup: $backup_name"

    # Check if backup exists
    if [[ ! -f "$backup_file" && ! -f "${backup_file}.tar.gz" && ! -f "${backup_file}.tar.gz.gpg" ]]; then
        error "Backup not found: $backup_name"
        exit 1
    fi

    # Find actual backup file
    if [[ -f "${backup_file}.tar.gz.gpg" ]]; then
        backup_file="${backup_file}.tar.gz.gpg"
    elif [[ -f "${backup_file}.tar.gz" ]]; then
        backup_file="${backup_file}.tar.gz"
    fi

    # Decrypt if needed
    local temp_archive="${BACKUP_DIR}/temp_restore.tar.gz"

    if [[ "$backup_file" == *.gpg ]]; then
        info "Decrypting backup..."
        if [[ -z "$ENCRYPTION_KEY" ]]; then
            error "Encryption key required for decryption"
            exit 1
        fi
        gpg --decrypt --batch --passphrase "$ENCRYPTION_KEY" \
            --output "$temp_archive" "$backup_file"
    else
        temp_archive="$backup_file"
    fi

    # Extract archive
    info "Extracting backup..."
    local temp_dir="${BACKUP_DIR}/temp_restore"
    mkdir -p "$temp_dir"
    tar -xzf "$temp_archive" -C "$temp_dir"

    # Find backup directory
    local extracted_dir=$(find "$temp_dir" -type d -name "backup_*" | head -1)

    # Restore files
    info "Restoring files..."

    if [[ -d "${extracted_dir}/config" ]]; then
        cp -r "${extracted_dir}/config/"* "${PROJECT_ROOT}/" 2>/dev/null || true
    fi

    if [[ -d "${extracted_dir}/data" ]]; then
        cp -r "${extracted_dir}/data/"* "${PROJECT_ROOT}/services/" 2>/dev/null || true
    fi

    if [[ -d "${extracted_dir}/assets" ]]; then
        cp -r "${extracted_dir}/assets/"* "${PROJECT_ROOT}/services/" 2>/dev/null || true
    fi

    # Cleanup
    rm -rf "$temp_dir"
    rm -f "$temp_archive"

    success "Backup restored successfully"
}

# List backups
list_backups() {
    info "Available backups:"

    local backups=($(ls -t "${BACKUP_DIR}"/backup_*.tar.gz* 2>/dev/null))

    if [[ ${#backups[@]} -eq 0 ]]; then
        warning "No backups found"
        return
    fi

    printf "%-40s %-15s %-10s\n" "Backup Name" "Type" "Size"
    printf "%-40s %-15s %-10s\n" "----------------------------------------" "---------------" "----------"

    for backup in "${backups[@]}"; do
        local name=$(basename "$backup" .tar.gz | sed 's/\.gpg$//')
        local size=$(du -h "$backup" | cut -f1)
        local type="full"  # TODO: Read from backup_info.txt

        printf "%-40s %-15s %-10s\n" "$name" "$type" "$size"
    done
}

# Cleanup old backups
cleanup_backups() {
    info "Cleaning up old backups (retention: ${BACKUP_RETENTION_DAYS} days)..."

    local cleaned=0
    while IFS= read -r backup; do
        rm -f "$backup"
        ((cleaned++))
    done < <(find "$BACKUP_DIR" -name "backup_*.tar.gz*" -mtime +$BACKUP_RETENTION_DAYS)

    success "Cleaned $cleaned old backup(s)"
}

# Main function
main() {
    parse_args "$@"

    echo "Project Chimera Phase 2 - Backup Script"
    echo ""

    if [[ "$LIST" == true ]]; then
        list_backups
    elif [[ -n "$RESTORE" ]]; then
        restore_backup "$RESTORE"
    elif [[ "$CLEANUP" == true ]]; then
        cleanup_backups
    else
        create_backup
    fi
}

main "$@"
