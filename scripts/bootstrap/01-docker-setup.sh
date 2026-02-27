#!/bin/bash
# Bootstrap Step 1: Fix Docker Permissions
# This script adds the current user to the docker group

set -e

echo "==> Step 1: Fix Docker Permissions"

# Check if docker group exists
if ! getent group docker > /dev/null 2>&1; then
    echo "Creating docker group..."
    sudo groupadd docker 2>/dev/null || true
fi

# Add current user to docker group
USER=$(whoami)
echo "Adding user $USER to docker group..."
sudo usermod -aG docker "$USER"

echo "==> Docker permissions configured"
echo "NOTE: You need to log out and back in for group changes to take effect"
echo "Or run: newgrp docker"
