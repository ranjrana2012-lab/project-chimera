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

# Check 3: Port conflicts (with portable fallback)
echo "🔌 Check 3: Port Conflicts"
echo "--------------------------"
PORTS=(8000 8001 8002 8004 8006 8007 8008 6379)
CONFLICTS=0

# Try multiple commands for portability
if command -v ss >/dev/null 2>&1; then
    # Use ss (modern Linux)
    for port in "${PORTS[@]}"; do
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            echo "⚠️  Port $port is IN USE"
            CONFLICTS=1
        else
            echo "✅ Port $port is free"
        fi
    done
elif command -v lsof >/dev/null 2>&1; then
    # Fallback to lsof (macOS/Linux)
    for port in "${PORTS[@]}"; do
        if lsof -iTCP -sTCP:LISTEN -n -P 2>/dev/null | grep -q ":$port "; then
            echo "⚠️  Port $port is IN USE"
            CONFLICTS=1
        else
            echo "✅ Port $port is free"
        fi
    done
else
    # Last resort: netstat (deprecated but widely available)
    for port in "${PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo "⚠️  Port $port is IN USE"
            CONFLICTS=1
        else
            echo "✅ Port $port is free"
        fi
    done
fi
echo ""

# Check 4: Root .dockerignore file
echo "📋 Check 4: Root .dockerignore File"
echo "-----------------------------------"

check_dockerignore() {
    local dockerignore_path=".dockerignore"

    if [ ! -f "$dockerignore_path" ]; then
        echo "⚠️  WARNING: Root .dockerignore not found!"
        echo "   Build context will include ALL files (~84GB)"
        echo "   Run: touch .dockerignore (and populate it)"
        return 1
    fi

    # Verify key exclusions are present
    local required_exclusions=("models/" ".git/" "venv/")
    local missing=0

    for exclusion in "${required_exclusions[@]}"; do
        if ! grep -q "^$exclusion" "$dockerignore_path"; then
            echo "⚠️  WARNING: .dockerignore missing '$exclusion' exclusion"
            missing=1
        fi
    done

    if [ $missing -eq 0 ]; then
        echo "✓ Root .dockerignore exists with key exclusions"
        return 0
    else
        return 1
    fi
}

check_dockerignore
DOCKERIGNORE_STATUS=$?

echo ""

# Summary
echo "=========================="
if [ $MISSING -eq 0 ] && [ $CONFLICTS -eq 0 ] && [ $DOCKERIGNORE_STATUS -eq 0 ]; then
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
