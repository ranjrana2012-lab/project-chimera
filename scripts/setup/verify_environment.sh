#!/bin/bash
# Project Chimera - Environment Verification Script
# Verifies that all dependencies are correctly installed

set -e

echo "=========================================="
echo "Project Chimera - Environment Check"
echo "=========================================="

# Check Python
echo -n "Python 3.10+: "
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "✓ $(python3 --version)"
else
    echo "✗ Not found or wrong version"
    exit 1
fi

# Check Docker
echo -n "Docker: "
if command -v docker &> /dev/null; then
    echo "✓ $(docker --version | awk '{print $3}')"
else
    echo "✗ Not found"
fi

# Check kubectl
echo -n "kubectl: "
if command -v kubectl &> /dev/null; then
    echo "✓ $(kubectl version --client | grep Client | cut -d: -f2 | cut -d, -f1 | xargs)"
else
    echo "✗ Not found"
fi

# Check GPU (optional)
echo -n "NVIDIA GPU: "
if command -v nvidia-smi &> /dev/null; then
    GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
    echo "✓ $GPU_COUNT GPU(s) detected"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | head -1
else
    echo "⊘ Not detected (optional for development)"
fi

# Check Redis connection
echo -n "Redis connection: "
if timeout 2 bash -c "cat < /dev/tcp/127.0.0.1/6379" 2>/dev/null; then
    echo "✓ Available on localhost:6379"
else
    echo "⊘ Not available (will use containerized Redis)"
fi

echo ""
echo "=========================================="
echo "Environment check complete!"
echo "=========================================="
