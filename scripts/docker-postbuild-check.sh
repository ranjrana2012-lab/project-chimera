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

# Parse and show reclaimable space warning
echo "📊 Reclaimable Space Analysis:"
echo "----------------------------"
TOTAL_RECLAIMABLE=0
for type in Images Containers Local Volumes Build\ Cache; do
    # Get reclaimable space for each type
    value=$(docker system df --format "{{.Type}}: {{.Reclaimable}}" | grep "^${type}:" | cut -d: -f2 | xargs)
    if [ -n "$value" ]; then
        echo "$type: $value reclaimable"
    fi
done | head -5

# Check if total reclaimable is significant
RECLAIMABLE=$(docker system df --format "{{.Reclaimable}}" | grep -E "[0-9]+GB|[0-9]+MB" | head -1)
echo ""
if [ -n "$RECLAIMABLE" ]; then
    echo "⚠️  Total Reclaimable: $RECLAIMABLE"
    if echo "$RECLAIMABLE" | grep -qE "[0-9]+GB"; then
        echo "   Consider running: docker system prune -a"
    fi
else
    echo "✅ No significant reclaimable space"
fi
echo ""

echo "=========================="
echo "✅ Post-build check complete"
echo ""
echo "💡 Tips:"
echo "   - Run 'docker image prune -f' to clean dangling images"
echo "   - Run 'docker builder prune -f' to clean build cache"
echo "   - Run 'docker system df' anytime to check usage"
