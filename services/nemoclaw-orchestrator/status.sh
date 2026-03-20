#!/bin/bash
# Nemo Claw Orchestrator Status Check Script

set -e

echo "🔍 Nemo Claw Orchestrator Status Check"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if service is running
if ! curl -s http://localhost:8000/health/live > /dev/null 2>&1; then
    echo -e "${RED}✗ Nemo Claw Orchestrator is not running${NC}"
    echo ""
    echo "Start it with:"
    echo "  cd services/nemoclaw-orchestrator"
    echo "  ./deploy.sh"
    exit 1
fi

echo -e "${GREEN}✓ Service is running${NC}"
echo ""

# Health check details
echo "📊 Health Checks:"
echo ""

# Liveness
echo -n "  Liveness: "
if curl -s http://localhost:8000/health/live | grep -q "alive"; then
    echo -e "${GREEN}OK${NC} (http://localhost:8000/health/live)"
else
    echo -e "${RED}FAILED${NC}"
fi

# Readiness with components
echo -n "  Readiness: "
READY_OUTPUT=$(curl -s http://localhost:8000/health/ready 2>/dev/null || echo "{}")
if echo "$READY_OUTPUT" | grep -q '"status":"ready"'; then
    echo -e "${GREEN}OK${NC} (http://localhost:8000/health/ready)"

    # Show component status if available
    if echo "$READY_OUTPUT" | grep -q '"components"'; then
        echo ""
        echo "  Components:"
        echo "$READY_OUTPUT" | python3 -m json.tool 2>/dev/null | grep -A 10 '"components"' | grep -E '^\s*"[^"]+":' | sed 's/^[[:space:]]*//' | sed 's/: */: /' | sed 's/"//g' | while read line; do
            echo "    $line"
        done
    fi
else
    echo -e "${RED}FAILED${NC}"
fi

echo ""
echo "🔗 Service Endpoints:"
echo "  Orchestration:  POST http://localhost:8000/v1/orchestrate"
echo "  Skills:         GET  http://localhost:8000/skills"
echo "  Show Start:      POST http://localhost:8000/api/show/start"
echo "  Show End:        POST http://localhost:8000/api/show/end"
echo "  Show State:      GET  http://localhost:8000/api/show/state"
echo "  WebSocket:       WS   http://localhost:8000/ws/show"
echo ""

echo "🤖 LLM Backends:"
ZAI_STATUS=$(curl -s http://localhost:8000/llm/zai/status 2>/dev/null || echo '{"available":false}')
if echo "$ZAI_STATUS" | grep -q '"available".*true'; then
    echo -e "  ${GREEN}✓ Z.AI Available${NC}"
else
    echo -e "  ${YELLOW}⚠️  Z.AI Unavailable (credits exhausted or not configured)${NC}"
fi
echo ""
echo "  Backend Status:"
curl -s http://localhost:8000/llm/backends | python3 -m json.tool 2>/dev/null | grep -E '"name"|"model"|"available"' | sed 's/^[[:space:]]*//' | sed 's/"//g' | sed 's/: */: /' | while read line; do
    echo "    $line"
done
echo ""

# Test orchestration endpoint
echo "🧪 Quick Test:"
echo "  Testing orchestration endpoint..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/orchestrate \
    -H "Content-Type: application/json" \
    -d '{"skill": "sentiment_analysis", "input": {"text": "test"}}' 2>/dev/null || echo "{}")

if echo "$TEST_RESPONSE" | grep -q "result\|error"; then
    echo -e "  ${GREEN}✓ Orchestration endpoint responding${NC}"
    echo "  Response: $(echo "$TEST_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('error', d.get('result', 'OK')))" 2>/dev/null || echo "OK")"
else
    echo -e "  ${YELLOW}⚠️  Unexpected response${NC}"
fi

echo ""
echo "📊 Docker Status:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
elif docker compose version &> /dev/null; then
    docker compose ps
else
    echo "  Docker Compose not found"
fi

echo ""
echo "📋 Available Commands:"
echo "  View logs:     docker compose logs -f nemoclaw-orchestrator"
echo "  Restart:       docker compose restart"
echo "  Stop:          docker compose down"
echo "  Run tests:     pytest tests/"
echo "  Check status:  ./status.sh"
echo ""
