#!/bin/bash

# Project Chimera Demo Preparation Script
# Prepares the environment for the Monday demo

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================"
echo "Project Chimera Demo Preparation"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

echo ""

# Step 2: Clean up previous demo environment
echo "Step 2: Cleaning up previous environment..."

# Stop any running containers
docker-compose down 2>/dev/null || true

# Remove old demo data
rm -f /tmp/chimera-demo-*.log

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 3: Check system resources
echo "Step 3: Checking system resources..."

# Available memory
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$MEMORY_GB" -lt 8 ]; then
    echo -e "${YELLOW}WARNING: Less than 8GB RAM available (current: ${MEMORY_GB}GB)${NC}"
    echo "Demo may run slowly. Consider closing other applications."
else
    echo -e "${GREEN}✓ Sufficient memory (${MEMORY_GB}GB)${NC}"
fi

# Disk space
DISK_GB=$(df -BG . | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$DISK_GB" -lt 5 ]; then
    echo -e "${RED}ERROR: Less than 5GB disk space available (current: ${DISK_GB}GB)${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Sufficient disk space (${DISK_GB}GB)${NC}"
fi

echo ""

# Step 4: Create necessary directories
echo "Step 4: Creating directories..."

mkdir -p logs/demo
mkdir -p data/demo
mkdir -p tmp/demo

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 5: Check configuration files
echo "Step 5: Checking configuration..."

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}ERROR: docker-compose.yml not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose.yml found${NC}"

# Check for demo configuration
if [ -f "docker-compose.demo.yml" ]; then
    echo -e "${GREEN}✓ Demo docker-compose configuration found${NC}"
else
    echo -e "${YELLOW}NOTE: No docker-compose.demo.yml, using default${NC}"
fi

echo ""

# Step 6: Prepare demo data
echo "Step 6: Preparing demo data..."

# Check if demo scenario exists
if [ -f "examples/demo-scenario.json" ]; then
    echo -e "${GREEN}✓ Demo scenario data found${NC}"
else
    echo -e "${YELLOW}WARNING: demo-scenario.json not found in examples/${NC}"
fi

# Create demo log file
LOG_FILE="logs/demo/prep-$(date +%Y%m%d-%H%M%S).log"
touch "$LOG_FILE"
echo -e "${GREEN}✓ Demo log file created: $LOG_FILE${NC}"

echo ""

# Step 7: Build Docker images
echo "Step 7: Building Docker images (this may take a few minutes)..."

if docker-compose build --quiet 2>&1 | tee -a "$LOG_FILE"; then
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
else
    echo -e "${RED}ERROR: Failed to build Docker images${NC}"
    echo "Check log file: $LOG_FILE"
    exit 1
fi

echo ""

# Step 8: Pre-pull common images
echo "Step 8: Pre-pulling infrastructure images..."

docker pull nats:latest-alpine 2>&1 | grep -q "Status:" && echo -e "${GREEN}✓ NATS image ready${NC}"
docker pull prom/prometheus:latest 2>&1 | grep -q "Status:" && echo -e "${GREEN}✓ Prometheus image ready${NC}"
docker pull grafana/grafana:latest 2>&1 | grep -q "Status:" && echo -e "${GREEN}✓ Grafana image ready${NC}"
docker pull jaegertracing/all-in-one:latest 2>&1 | grep -q "Status:" && echo -e "${GREEN}✓ Jaeger image ready${NC}"

echo ""

# Step 9: Check port availability
echo "Step 9: Checking port availability..."

PORTS=(8000 8001 8002 8003 8004 8005 8006 8007 3000 9090 16686 4222 8222)
PORTS_OCCUPIED=()

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        PORTS_OCCUPIED+=($port)
    fi
done

if [ ${#PORTS_OCCUPIED[@]} -gt 0 ]; then
    echo -e "${YELLOW}WARNING: The following ports are already in use:${NC}"
    for port in "${PORTS_OCCUPIED[@]}"; do
        echo "  - Port $port"
    done
    echo ""
    echo "These ports will be used by Project Chimera services."
    echo "Please stop the conflicting services or free up these ports."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ All required ports are available${NC}"
fi

echo ""

# Step 10: Prepare sample requests
echo "Step 10: Preparing sample requests..."

if [ -f "examples/sample-request.py" ]; then
    chmod +x examples/sample-request.py
    echo -e "${GREEN}✓ Sample request script ready${NC}"
fi

echo ""

# Step 11: Generate demo preparation report
echo "Step 11: Generating preparation report..."

REPORT_FILE="logs/demo/prep-report-$(date +%Y%m%d-%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
Project Chimera Demo Preparation Report
========================================
Date: $(date)
Host: $(hostname)
User: $(whoami)

System Information:
-------------------
OS: $(uname -s) $(uname -r)
Memory: ${MEMORY_GB}GB
Disk Space: ${DISK_GB}GB free

Docker Information:
-------------------
Docker Version: $(docker --version)
Docker Compose Version: $(docker-compose --version)

Services Status:
----------------
$(docker-compose ps 2>/dev/null || echo "Services not yet started")

Port Availability:
------------------
$(for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Port $port: OCCUPIED"
    else
        echo "Port $port: Available"
    fi
  done)

Next Steps:
-----------
1. Run: ./scripts/demo-start.sh
2. Verify: ./scripts/demo-status.sh
3. Access Operator Console: http://localhost:8007
4. Access Grafana: http://localhost:3000 (admin/admin)
5. Access Jaeger: http://localhost:16686

Demo Checklist:
---------------
- [ ] All services running
- [ ] Health checks passing
- [ ] Operator Console accessible
- [ ] Grafana dashboards loaded
- [ ] Jaeger tracing working
- [ ] Sample requests tested
- [ ] Demo script reviewed

Files Generated:
----------------
- Log file: $LOG_FILE
- Report file: $REPORT_FILE
EOF

echo -e "${GREEN}✓ Report generated: $REPORT_FILE${NC}"

echo ""
echo "================================"
echo "Demo Preparation Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Start services:  ./scripts/demo-start.sh"
echo "  2. Check status:    ./scripts/demo-status.sh"
echo "  3. View report:     cat $REPORT_FILE"
echo ""
echo "Demo access URLs:"
echo "  - Operator Console: http://localhost:8007"
echo "  - Grafana:          http://localhost:3000"
echo "  - Jaeger:           http://localhost:16686"
echo ""
