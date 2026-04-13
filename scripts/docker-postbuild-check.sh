#!/bin/bash
# Docker Post-Build Check
# Run this after any Docker build operation

set -e

echo "🧹 Docker Post-Build Check"
echo "=========================="
echo ""

# Check current disk usage
echo "💾 Current Docker Disk Usage:"
echo "----------------------------"
docker system df
echo ""

# Parse and warn about reclaimable space
RECLAIMABLE=$(docker system df --format "{{.Reclaimable}}" | grep -E "[0-9]+GB|[0-9]+MB" | head -1)

echo "=========================="
echo "✅ Post-build check complete"
echo ""
echo "💡 Tips:"
echo "   - Run 'docker image prune -f' to clean dangling images"
echo "   - Run 'docker builder prune -f' to clean build cache"
echo "   - Run 'docker system df' anytime to check usage"
