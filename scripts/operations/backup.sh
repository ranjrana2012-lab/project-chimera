#!/bin/bash
# Project Chimera - Backup Script
# Creates backups of configuration and data

set -e

BACKUP_DIR="backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR..."

# Backup Kubernetes configs
echo "Backing up Kubernetes configurations..."
kubectl get configmap -n live -o yaml > "$BACKUP_DIR/configmaps-live.yaml"
kubectl get secrets -n live -o yaml > "$BACKUP_DIR/secrets-live.yaml"
kubectl get configmap -n shared -o yaml > "$BACKUP_DIR/configmaps-shared.yaml"

# Backup Redis (if accessible)
echo "Backing up Redis data..."
kubectl exec -n shared redis-0 -- redis-cli SAVE || true
kubectl cp shared/redis-0:/data/dump.rdb "$BACKUP_DIR/redis-dump.rdb" || true

# Backup policies and configs
echo "Backing up configuration..."
cp -r configs "$BACKUP_DIR/"
cp -r infrastructure "$BACKUP_DIR/"

echo "Backup complete: $BACKUP_DIR"
