#!/bin/bash
# Docker Pre-Flight Check
# Run this before any Docker build operation

set -e

echo "🔍 Docker Pre-Flight Check"
echo "=========================="
echo ""

# Check 1: .dockerignore files
echo "📋 Check 1: .dockerignore files"
echo "-------------------------------"
MISSING=0
for service in services/*/; do
    if [ -f "$service/Dockerfile" ]; then
        if [ -f "$service/.dockerignore" ]; then
            echo "✅ $service: .dockerignore found"
        else
            echo "❌ $service: .dockerignore MISSING!"
            MISSING=1
        fi
    fi
done
if [ $MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  WARNING: Missing .dockerignore files can cause bloat!"
    echo "   Consider adding them before building."
fi
echo ""

# Check 2: Current disk usage
echo "💾 Check 2: Current Docker Disk Usage"
echo "-------------------------------------"
docker system df
echo ""

# Check 3: Port conflicts
echo "🔌 Check 3: Port Conflicts"
echo "--------------------------"
PORTS=(8000 8001 8002 8004 8006 8007 8008 6379)
CONFLICTS=0
for port in "${PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo "⚠️  Port $port is IN USE"
        CONFLICTS=1
    else
        echo "✅ Port $port is free"
    fi
done
echo ""

# Summary
echo "=========================="
if [ $MISSING -eq 0 ] && [ $CONFLICTS -eq 0 ]; then
    echo "✅ Pre-flight check PASSED"
    echo ""
    echo "Ready to proceed with Docker operations."
    exit 0
else
    echo "⚠️  Pre-flight check had WARNINGS"
    echo ""
    echo "Please review above before proceeding."
    exit 1
fi
