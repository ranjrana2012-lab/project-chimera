#!/bin/bash

# Live Show Automation - Quick Start Script
# This script helps you quickly set up and run a demonstration of the automation system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DIRECTOR_PORT=8013
SHOW_ID="welcome_show"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Project Chimera Live Show Automation${NC}"
echo -e "${BLUE}Quick Start Script${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to check if a service is running
check_service() {
    local url=$1
    local name=$2

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not running"
        return 1
    fi
}

# Function to start a service
start_service() {
    local service_dir=$1
    local service_name=$2
    local port=$3

    echo -e "${YELLOW}Starting $service_name (port $port)...${NC}"

    # Check if service directory exists
    if [ ! -d "$service_dir" ]; then
        echo -e "${RED}Error: Service directory not found: $service_dir${NC}"
        return 1
    fi

    # Start service in background
    cd "$service_dir"
    python main.py > /dev/null 2>&1 &
    SERVICE_PID=$!

    # Wait for service to start
    sleep 3

    # Check if service started successfully
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $service_name started successfully (PID: $SERVICE_PID)"
        echo "$SERVICE_PID" > "/tmp/${service_name}.pid"
        cd - > /dev/null
        return 0
    else
        echo -e "${RED}✗${NC} $service_name failed to start"
        cd - > /dev/null
        return 1
    fi
}

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}Project root: $PROJECT_ROOT${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Prerequisites check passed"
echo ""

# Step 2: Check if services are already running
echo -e "${BLUE}Step 2: Checking existing services...${NC}"

SERVICES_RUNNING=0

if check_service "http://localhost:8001/health" "SceneSpeak Agent"; then
    SERVICES_RUNNING=$((SERVICES_RUNNING + 1))
fi

if check_service "http://localhost:8002/health" "Captioning Agent"; then
    SERVICES_RUNNING=$((SERVICES_RUNNING + 1))
fi

if check_service "http://localhost:8003/health" "BSL Agent"; then
    SERVICES_RUNNING=$((SERVICES_RUNNING + 1))
fi

if check_service "http://localhost:8004/health" "Sentiment Agent"; then
    SERVICES_RUNNING=$((SERVICES_RUNNING + 1))
fi

if check_service "http://localhost:8005/health" "Lighting-Sound-Music"; then
    SERVICES_RUNNING=$((SERVICES_RUNNING + 1))
fi

if check_service "http://localhost:8013/health" "Director Agent"; then
    DIRECTOR_RUNNING=true
else
    DIRECTOR_RUNNING=false
fi

echo ""

if [ $SERVICES_RUNNING -gt 0 ]; then
    echo -e "${YELLOW}Found $SERVICES_RUNNING services already running${NC}"
    echo -e "${YELLOW}Skipping agent startup${NC}"
    echo ""
fi

# Step 3: Start Director Agent (if not running)
if [ "$DIRECTOR_RUNNING" = false ]; then
    echo -e "${BLUE}Step 3: Starting Director Agent...${NC}"

    DIRECTOR_DIR="$PROJECT_ROOT/services/director-agent"

    if [ ! -d "$DIRECTOR_DIR" ]; then
        echo -e "${RED}Error: Director Agent directory not found${NC}"
        exit 1
    fi

    # Install dependencies if needed
    if [ ! -d "$DIRECTOR_DIR/venv" ]; then
        echo -e "${YELLOW}Installing Director Agent dependencies...${NC}"
        cd "$DIRECTOR_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -q -r requirements.txt
        deactivate
    fi

    # Start Director Agent
    cd "$DIRECTOR_DIR"
    source venv/bin/activate
    python main.py > /dev/null 2>&1 &
    DIRECTOR_PID=$!
    deactivate

    # Wait for Director Agent to start
    sleep 3

    if check_service "http://localhost:8013/health" "Director Agent"; then
        echo "$DIRECTOR_PID" > "/tmp/director-agent.pid"
        echo -e "${GREEN}✓${NC} Director Agent started successfully (PID: $DIRECTOR_PID)"
    else
        echo -e "${RED}✗${NC} Director Agent failed to start"
        exit 1
    fi

    echo ""
else
    echo -e "${BLUE}Step 3: Director Agent already running${NC}"
    echo ""
fi

# Step 4: List available shows
echo -e "${BLUE}Step 4: Loading shows...${NC}"

SHOWS_RESPONSE=$(curl -s http://localhost:8013/api/shows)
SHOW_COUNT=$(echo "$SHOWS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('shows', [])))")

if [ "$SHOW_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Found $SHOW_COUNT available shows:"
    echo "$SHOWS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for show in data.get('shows', []):
    print(f\"  - {show['show_id']}: {show['title']}\")
"
else
    echo -e "${YELLOW}⚠${NC} No shows found. Loading example shows...${NC}"

    # Load example shows
    WELCOME_SHOW="$PROJECT_ROOT/services/director-agent/shows/welcome_show.yaml"
    if [ -f "$WELCOME_SHOW" ]; then
        curl -s -X POST http://localhost:8013/api/shows/load \
            -H "Content-Type: application/json" \
            -d "{\"show_id\": \"welcome_show\", \"file_path\": \"$WELCOME_SHOW\"}" > /dev/null

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Loaded welcome_show"
        fi
    fi
fi

echo ""

# Step 5: Start the show
echo -e "${BLUE}Step 5: Starting show...${NC}"

echo -e "${YELLOW}Starting show: $SHOW_ID${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

START_RESPONSE=$(curl -s -X POST "http://localhost:8013/api/shows/$SHOW_ID/start" \
    -H "Content-Type: application/json" \
    -d '{"require_approval": false}')

START_STATUS=$(echo "$START_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('status', 'unknown'))")

if [ "$START_STATUS" = "started" ]; then
    echo -e "${GREEN}✓${NC} Show started successfully!"
    echo ""
    echo -e "${BLUE}Monitoring show execution...${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop monitoring${NC}"
    echo ""

    # Monitor show state
    while true; do
        STATE_RESPONSE=$(curl -s "http://localhost:8013/api/shows/$SHOW_ID/state")
        STATE=$(echo "$STATE_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('state', 'unknown'))")
        SCENE_INDEX=$(echo "$STATE_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('current_scene_index', 0))")

        echo -ne "\r${BLUE}State: $STATE | Scene: $SCENE_INDEX |$(NC} "

        sleep 1

        # Check if show completed or failed
        if [ "$STATE" = "completed" ] || [ "$STATE" = "failed" ] || [ "$STATE" = "stopped" ]; then
            echo ""
            echo -e "${GREEN}✓${NC} Show finished with state: $STATE"
            break
        fi
    done

    # Get final state
    FINAL_STATE=$(curl -s "http://localhost:8013/api/shows/$SHOW_ID/state")
    echo ""
    echo -e "${BLUE}Final show state:${NC}"
    echo "$FINAL_STATE" | python3 -m json.tool | head -20

else
    echo -e "${RED}✗${NC} Failed to start show"
    echo "$START_RESPONSE"
fi

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Quick Start Complete!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "To stop all services, run:"
echo -e "  kill \$(cat /tmp/director-agent.pid)"
echo ""
echo -e "For more information, see:"
echo -e "  - LIVE_SHOW_AUTOMATION_GUIDE.md"
echo -e "  - services/director-agent/README.md"
echo ""
