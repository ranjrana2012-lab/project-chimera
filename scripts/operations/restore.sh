#!/bin/bash
# Project Chimera - Restore Script
# Restores from a backup

set -e

BACKUP_DIR=${1:-""}

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup-directory>"
    echo ""
    echo "Available backups:"
    ls -lt backups/ | grep "^d" | head -10
    exit 1
fi

echo "Restoring from $BACKUP_DIR..."

# Restore configs
if [ -d "$BACKUP_DIR/configs" ]; then
    echo "Restoring configurations..."
    cp -r "$BACKUP_DIR/configs/"* configs/
fi

# Restore Kubernetes configs
if [ -f "$BACKUP_DIR/configmaps-live.yaml" ]; then
    echo "Restoring Kubernetes ConfigMaps..."
    kubectl apply -f "$BACKUP_DIR/configmaps-live.yaml"
fi

# Restore Redis data
if [ -f "$BACKUP_DIR/redis-dump.rdb" ]; then
    echo "Restoring Redis data..."
    kubectl cp "$BACKUP_DIR/redis-dump.rdb" shared/redis-0:/data/dump.rdb
    kubectl exec -n shared redis-0 -- redis-cli SHUTDOWN SAVE NOSAVE || true
fi

echo "Restore complete!"
