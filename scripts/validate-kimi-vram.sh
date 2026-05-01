#!/bin/bash
# Validate Kimi K2.6 VRAM usage stays within bounds

set -e

THRESHOLD_GB=${KIMI_VRAM_THRESHOLD_GB:-85}  # Warn if using >85GB
CRITICAL_GB=${KIMI_VRAM_CRITICAL_GB:-100}   # Error if using >100GB

echo "================================================"
echo "Kimi K2.6 VRAM Validation"
echo "================================================"
echo "Warning threshold: ${THRESHOLD_GB}GB"
echo "Critical threshold: ${CRITICAL_GB}GB"
echo ""

# Get VRAM usage in MB
vram_mb=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
vram_gb=$((vram_mb / 1024))

echo "Current VRAM usage: ${vram_gb}GB"
echo ""

# Check against thresholds
if [ $vram_gb -gt $CRITICAL_GB ]; then
    echo "✗ CRITICAL: VRAM usage (${vram_gb}GB) exceeds critical threshold (${CRITICAL_GB}GB)"
    echo ""
    echo "Action required:"
    echo "1. Check if Kimi vLLM is running with correct GPU memory fraction"
    echo "2. Verify no other processes are using GPU memory"
    echo "3. Consider reducing KIMI_GPU_MEMORY_FRACTION"
    exit 1
elif [ $vram_gb -gt $THRESHOLD_GB ]; then
    echo "⚠️  WARNING: VRAM usage (${vram_gb}GB) exceeds warning threshold (${THRESHOLD_GB}GB)"
    echo ""
    echo "Recommendation: Monitor usage closely"
    exit 0
else
    echo "✓ VRAM usage (${vram_gb}GB) within acceptable bounds"
    echo ""
    echo "Headroom available: $((128 - vram_gb))GB"
    exit 0
fi
