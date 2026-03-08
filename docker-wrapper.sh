#!/bin/bash
# Docker wrapper script that handles group membership issues
# This script ensures Docker commands run with proper permissions

# Check if user is in docker group
if groups | grep -q docker; then
    # User is in docker group, but current session may not have updated groups
    # Use newgrp to execute docker commands with proper group membership
    echo "$@" | newgrp docker
else
    # User is not in docker group, try with sudo
    sudo "$@"
fi
