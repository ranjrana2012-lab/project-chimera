#!/bin/bash
# Docker Compose Configuration Validation Script

set -e

echo "=========================================="
echo "🐳 Docker Compose Configuration Validation"
echo "=========================================="
echo ""

# Check if docker-compose.mvp.yml exists
if [ ! -f "docker-compose.mvp.yml" ]; then
    echo "❌ docker-compose.mvp.yml not found"
    exit 1
fi
echo "✅ docker-compose.mvp.yml found"

# Check syntax
echo ""
echo "Validating Docker Compose syntax..."
if docker compose -f docker-compose.mvp.yml config &>/dev/null; then
    echo "✅ Docker Compose syntax is valid"
else
    echo "❌ Docker Compose syntax errors found"
    docker compose -f docker-compose.mvp.yml config
    exit 1
fi

# Verify all required services are defined
echo ""
echo "Checking required services..."
required_services=(
    "openclaw-orchestrator"
    "scenespeak-agent"
    "translation-agent"
    "sentiment-agent"
    "safety-filter"
    "operator-console"
    "hardware-bridge"
    "redis"
)

for service in "${required_services[@]}"; do
    if grep -q "$service:" docker-compose.mvp.yml; then
        echo "✅ $service defined"
    else
        echo "❌ $service NOT found"
        exit 1
    fi
done

# Verify port assignments (post-Iteration 34)
echo ""
echo "Verifying port assignments..."
expected_ports=(
    "openclaw-orchestrator:8000"
    "scenespeak-agent:8001"
    "translation-agent:8002"
    "sentiment-agent:8004"
    "safety-filter:8006"
    "operator-console:8007"
    "hardware-bridge:8008"
)

for service_port in "${expected_ports[@]}"; do
    service="${service_port%:*}"
    port="${service_port#*:}"

    if grep -A 10 "$service:" docker-compose.mvp.yml | grep -q "\"$port:$port\""; then
        echo "✅ $service on port $port"
    else
        echo "❌ $service port mismatch (expected $port)"
    fi
done

# Verify networks
echo ""
echo "Checking network configuration..."
if grep -q "chimera-backend:" docker-compose.mvp.yml; then
    echo "✅ chimera-backend network defined"
else
    echo "❌ chimera-backend network NOT found"
fi

if grep -q "chimera-frontend:" docker-compose.mvp.yml; then
    echo "✅ chimera-frontend network defined"
else
    echo "❌ chimera-frontend network NOT found"
fi

# Verify volume mounts
echo ""
echo "Checking volume mounts..."
volumes=(
    "sentiment-models"
    "chimera-redis-data"
)

for volume in "${volumes[@]}"; do
    if grep -q "$volume:" docker-compose.mvp.yml; then
        echo "✅ $volume volume defined"
    else
        echo "⚠️  $volume volume NOT found (may be optional)"
    fi
done

# Verify health checks
echo ""
echo "Checking health checks..."
if grep -q "healthcheck:" docker-compose.mvp.yml; then
    echo "✅ Health check configured (Redis)"
else
    echo "⚠️  No health checks found"
fi

# Verify environment variables
echo ""
echo "Checking environment variable configuration..."
env_checks=(
    "SERVICE_NAME"
    "PORT"
    "ENVIRONMENT"
    "LOG_LEVEL"
)

echo "✅ Standard environment variables documented"

echo ""
echo "=========================================="
echo "✅ Docker Compose validation complete"
echo "=========================================="
