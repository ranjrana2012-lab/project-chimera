#!/bin/bash
set -e
echo "🚀 Setting up Project Chimera Monitoring Stack..."

# Detect runtime profile
RUNTIME_PROFILE=$(python3 scripts/detect_runtime_profile.py 2>/dev/null || echo "student")

if [[ "$RUNTIME_PROFILE" == *"dgx"* ]] || [[ "$RUNTIME_PROFILE" == *"arm64"* ]]; then
    COMPOSE_FILES="-f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml"
else
    COMPOSE_FILES="-f docker-compose.mvp.yml"
fi

mkdir -p config/prometheus logs/monitoring

echo "🔨 Building monitoring containers..."
docker compose $COMPOSE_FILES build prometheus netdata

echo "🚀 Starting monitoring services..."
docker compose $COMPOSE_FILES up -d prometheus netdata

echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🎉 Monitoring stack is ready!"
echo ""
echo "📊 Access points:"
echo "  • Netdata dashboard:  http://localhost:19999"
echo "  • Prometheus UI:      http://localhost:9090"
echo "  • Monitoring dashboard: Start with:"
echo "      cd services/dashboard && python -m uvicorn main:app --port 8013"
echo "    Then visit: http://localhost:8013/monitoring"
