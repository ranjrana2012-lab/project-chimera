#!/bin/bash
# Nemo Claw Orchestrator Deployment Script
# Run this script on your DGX Spark GB0 ARM64 system

set -e

echo "🚀 Nemo Claw Orchestrator Deployment"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're on the right system
echo "🔍 Checking system compatibility..."
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    echo -e "${YELLOW}Warning: This service is optimized for ARM64 (DGX Spark GB0). Current architecture: $ARCH${NC}"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker environment OK${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your DGX and API settings before continuing!${NC}"
    echo ""
    echo "Required settings to configure:"
    echo "  - ANTHROPIC_API_KEY (for cloud fallback)"
    echo "  - DGX_ENDPOINT (your Nemotron service URL)"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

echo ""
echo "🐳 Building and starting Nemo Claw Orchestrator..."
echo ""

# Build and start with Docker Compose
if docker compose version &> /dev/null; then
    # Use newer docker compose (v2)
    docker compose up -d --build
else
    # Use older docker-compose
    docker-compose up -d --build
fi

echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""
echo "🔍 Checking service health..."
sleep 5

# Health check
MAX_ATTEMPTS=10
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health/live > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Nemo Claw Orchestrator is healthy!${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "Waiting for service to start... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}✗ Service failed to start. Check logs with: docker compose logs${NC}"
    exit 1
fi

echo ""
echo "📊 Service Status:"
echo "  Service: http://localhost:8000"
echo "  Health:  http://localhost:8000/health/live"
echo "  Ready:   http://localhost:8000/health/ready"
echo ""
echo "📋 Available Endpoints:"
echo "  POST /v1/orchestrate        - Agent orchestration with policy"
echo "  GET  /health/live            - Liveness check"
echo "  GET  /health/ready           - Readiness check with component status"
echo "  GET  /skills                 - List available skills"
echo "  POST /api/show/start         - Start a show"
echo "  POST /api/show/end           - End a show"
echo "  GET  /api/show/state         - Get current show state"
echo "  WebSocket /ws/show           - Real-time updates"
echo ""
echo "📚 Documentation:"
echo "  API Docs:     docs/api/nemoclaw-orchestrator.md"
echo "  Migration:    docs/migration-guide.md"
echo "  README:       services/nemoclaw-orchestrator/README.md"
echo ""
echo "🔧 Useful Commands:"
echo "  View logs:     docker compose logs -f nemoclaw-orchestrator"
echo "  Stop service:  docker compose down"
echo "  Restart:       docker compose restart"
echo "  Run tests:     pytest tests/"
echo ""
echo -e "${GREEN}🎉 Nemo Claw Orchestrator is running!${NC}"
