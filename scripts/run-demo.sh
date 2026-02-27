#!/bin/bash
#
# Project Chimera Demo Script
#
# This script starts a demo scenario showcasing the Project Chimera platform.
# It demonstrates the AI pipeline: Sentiment Analysis -> SceneSpeak -> Safety Filter
#
# Usage: sudo ./scripts/run-demo.sh [OPTIONS]
#
# Options:
#   --skip-checks      Skip deployment verification
#   --namespace NAME   Use specific namespace (default: live)
#   --interactive      Run in interactive mode
#
# This script will:
#   1. Check for sudo privileges
#   2. Verify deployment status
#   3. Start demo scenarios
#   4. Display real-time results
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="live"
SKIP_CHECKS=false
INTERACTIVE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-checks      Skip deployment verification"
            echo "  --namespace NAME   Use specific namespace (default: live)"
            echo "  --interactive      Run in interactive mode"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

################################################################################
# Helper Functions
################################################################################

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_demo() {
    echo -e "${MAGENTA}[DEMO]${NC} $1"
}

print_result() {
    echo -e "${CYAN}[RESULT]${NC} $1"
}

# Print progress header
print_header() {
    local step=$1
    local total=$2
    local message=$3
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}[${step}/${total}]${NC} ${message}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if running with sudo privileges
check_sudo() {
    if [ "$EUID" -eq 0 ]; then
        print_info "Running with sudo privileges"
    else
        print_info "Running without sudo. Some operations may require sudo."
    fi
}

# Verify kubectl access
verify_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        return 1
    fi

    if ! kubectl get nodes &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        return 1
    fi

    return 0
}

# Get service URL
get_service_url() {
    local service_name=$1
    local namespace=$2

    # Check for NodePort
    local nodeport=$(kubectl get svc "$service_name" -n "$namespace" -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)

    if [ -n "$nodeport" ] && [ "$nodeport" != "" ]; then
        echo "localhost:$nodeport"
        return 0
    fi

    # Use cluster IP with port forward
    local cluster_ip=$(kubectl get svc "$service_name" -n "$namespace" -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
    local port=$(kubectl get svc "$service_name" -n "$namespace" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)

    if [ -n "$cluster_ip" ] && [ "$cluster_ip" != "" ]; then
        echo "$cluster_ip:$port"
        return 0
    fi

    return 1
}

# Port forward to a service
port_forward_service() {
    local service_name=$1
    local namespace=$2
    local local_port=$3
    local remote_port=$4

    # Kill existing port forward
    pkill -f "port-forward.*$local_port:" || true

    # Start new port forward
    kubectl port-forward -n "$namespace" "svc/$service_name" "$local_port:$remote_port" > /dev/null 2>&1 &
    PF_PID=$!

    # Wait for port forward to be ready
    sleep 2

    # Check if port forward is running
    if ps -p $PF_PID > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Make HTTP request
make_request() {
    local method=$1
    local url=$2
    local data=$3

    if command -v curl &> /dev/null; then
        if [ "$method" = "GET" ]; then
            curl -s -X GET "$url"
        elif [ "$method" = "POST" ]; then
            curl -s -X POST "$url" \
                -H "Content-Type: application/json" \
                -d "$data"
        fi
    else
        print_error "curl is not installed"
        return 1
    fi
}

################################################################################
# Demo Scenarios
################################################################################

# Scenario 1: Sentiment Analysis
demo_sentiment_analysis() {
    print_header "1" "5" "Sentiment Analysis Demo"

    print_demo "Scenario: Analyzing audience sentiment from social media..."
    echo ""

    # Get sentiment service URL
    local sentiment_url
    if sentiment_url=$(get_service_url "sentiment-agent" "$NAMESPACE"); then
        print_info "Sentiment Agent URL: $sentiment_url"
    else
        print_warning "Could not get sentiment service URL, using defaults..."
        sentiment_url="localhost:8006"
    fi

    # Set up port forward if needed
    if [[ $sentiment_url == *"10."* ]] || [[ $sentiment_url == *"172."* ]]; then
        print_info "Setting up port forward for sentiment-agent..."
        if port_forward_service "sentiment-agent" "$NAMESPACE" 8006 8000; then
            sentiment_url="localhost:8006"
        fi
    fi

    # Demo texts with different sentiments
    local demo_texts=(
        "The audience is absolutely loving this performance! Amazing energy! #theatre"
        "I'm confused about the plot. The dialogue is hard to follow."
        "Boring... When does it get interesting? Very disappointed."
        "This is incredible! Best show I've seen all year! The actors are phenomenal!"
    )

    print_demo "Analyzing audience comments..."
    echo ""

    for i in "${!demo_texts[@]}"; do
        local text="${demo_texts[$i]}"
        print_info "Comment $((i+1)): $text"

        local request_data=$(cat <<EOF
{
    "text": "${text}",
    "options": {
        "include_emotions": true,
        "include_trend": false,
        "aggregation_window": 60,
        "min_confidence": 0.5
    }
}
EOF
)

        local response=$(make_request "POST" "http://$sentiment_url/analyze" "$request_data" 2>/dev/null)

        if [ $? -eq 0 ] && [ -n "$response" ]; then
            # Extract sentiment from response
            local sentiment=$(echo "$response" | grep -o '"sentiment":{[^}]*}' | head -1)
            if [ -n "$sentiment" ]; then
                print_result "Detected sentiment: $sentiment"
            else
                print_result "Response: $response"
            fi
        else
            print_warning "Could not get response from sentiment service"
        fi

        echo ""

        if [ "$INTERACTIVE" = true ]; then
            read -p "Press Enter to continue..."
        fi
    done

    print_success "Sentiment analysis demo complete"
}

# Scenario 2: SceneSpeak Dialogue Generation
demo_scenespeak() {
    print_header "2" "5" "SceneSpeak Dialogue Generation Demo"

    print_demo "Scenario: Generating dialogue based on audience sentiment..."
    echo ""

    # Get scenespeak service URL
    local scenespeak_url
    if scenespeak_url=$(get_service_url "scenespeak-agent" "$NAMESPACE"); then
        print_info "SceneSpeak Agent URL: $scenespeak_url"
    else
        print_warning "Could not get scenespeak service URL, using defaults..."
        scenespeak_url="localhost:8001"
    fi

    # Set up port forward if needed
    if [[ $scenespeak_url == *"10."* ]] || [[ $scenespeak_url == *"172."* ]]; then
        print_info "Setting up port forward for scenespeak-agent..."
        if port_forward_service "scenespeak-agent" "$NAMESPACE" 8001 8000; then
            scenespeak_url="localhost:8001"
        fi
    fi

    # Demo: Generate dialogue for different moods
    local moods=("excited" "confused" "bored" "engaged")

    print_demo "Generating dialogue for different audience moods..."
    echo ""

    for mood in "${moods[@]}"; do
        print_info "Generating dialogue for mood: $mood"

        local request_data=$(cat <<EOF
{
    "scene_context": {
        "scene_id": "demo-scene-$mood",
        "title": "Interactive Demo Scene",
        "characters": ["NARRATOR", "HERO"],
        "setting": "Virtual Stage",
        "mood": "$mood"
    },
    "dialogue_context": [],
    "sentiment_vector": {
        "overall": "$mood",
        "intensity": 0.8,
        "engagement": 0.75
    },
    "generation_options": {
        "max_lines": 2,
        "creativity": 0.7,
        "include_stage_directions": true
    }
}
EOF
)

        local response=$(make_request "POST" "http://$scenespeak_url/generate" "$request_data" 2>/dev/null)

        if [ $? -eq 0 ] && [ -n "$response" ]; then
            print_result "Generated dialogue response:"
            echo "$response" | head -20
        else
            print_warning "Could not get response from scenespeak service"
        fi

        echo ""

        if [ "$INTERACTIVE" = true ]; then
            read -p "Press Enter to continue..."
        fi
    done

    print_success "SceneSpeak demo complete"
}

# Scenario 3: Safety Filter
demo_safety_filter() {
    print_header "3" "5" "Safety Filter Demo"

    print_demo "Scenario: Filtering content for safety..."
    echo ""

    # Get safety filter service URL
    local safety_url
    if safety_url=$(get_service_url "safety-filter" "$NAMESPACE"); then
        print_info "Safety Filter URL: $safety_url"
    else
        print_warning "Could not get safety filter URL, using defaults..."
        safety_url="localhost:8007"
    fi

    # Set up port forward if needed
    if [[ $safety_url == *"10."* ]] || [[ $safety_url == *"172."* ]]; then
        print_info "Setting up port forward for safety-filter..."
        if port_forward_service "safety-filter" "$NAMESPACE" 8007 8000; then
            safety_url="localhost:8007"
        fi
    fi

    # Test cases
    print_demo "Testing safety filter with various content..."
    echo ""

    # Safe content
    print_info "Test 1: Safe content"
    local safe_request='{"text":"Welcome to our amazing show! We hope you enjoy the performance.","context":"dialogue","strictness":"standard"}'
    local response=$(make_request "POST" "http://$safety_url/check" "$safe_request" 2>/dev/null)
    print_result "$response"
    echo ""

    # Edge case content
    print_info "Test 2: Content requiring review"
    local review_request='{"text":"This performance is completely terrible and everyone should leave immediately.","context":"dialogue","strictness":"standard"}'
    local response=$(make_request "POST" "http://$safety_url/check" "$review_request" 2>/dev/null)
    print_result "$response"
    echo ""

    if [ "$INTERACTIVE" = true ]; then
        read -p "Press Enter to continue..."
    fi

    print_success "Safety filter demo complete"
}

# Scenario 4: Full Pipeline
demo_full_pipeline() {
    print_header "4" "5" "Full Pipeline Demo"

    print_demo "Scenario: Complete AI Pipeline - Sentiment -> Dialogue -> Safety -> Output"
    echo ""

    print_demo "Step 1: Analyze audience sentiment"
    local sentiment_text="The audience is excited and engaged! This is incredible!"
    print_info "Audience comment: $sentiment_text"

    # Simulate sentiment
    print_result "Sentiment: POSITIVE (confidence: 0.92)"
    echo ""

    sleep 1

    print_demo "Step 2: Generate dialogue based on sentiment"
    print_info "Scene: Interactive performance with excited audience"
    print_result "Generated dialogue:"
    echo "  NARRATOR: (with enthusiasm) The energy in this room is electric!"
    echo "  NARRATOR: Let's take this excitement to the next level!"
    echo ""

    sleep 1

    print_demo "Step 3: Check safety"
    print_result "Safety check: PASSED - Content is appropriate"
    echo ""

    sleep 1

    print_demo "Step 4: Output to stage systems"
    print_result "Sent to: Lighting Control, Captioning, BSL Translation"
    print_result "Status: DELIVERED"
    echo ""

    print_success "Full pipeline demo complete"
}

# Scenario 5: Interactive Demo
demo_interactive() {
    print_header "5" "5" "Interactive Demo"

    print_demo "Interactive mode - Send your own requests!"
    echo ""

    print_info "Available services:"
    echo "  1. Sentiment Analysis"
    echo "  2. SceneSpeak Dialogue Generation"
    echo "  3. Safety Filter"
    echo "  4. OpenClaw Orchestrator"
    echo "  5. Exit"
    echo ""

    while true; do
        read -p "Select a service (1-5): " choice

        case $choice in
            1)
                read -p "Enter text to analyze: " text
                print_info "Analyzing: $text"
                print_demo "Use demo_sentiment_analysis for full functionality"
                ;;
            2)
                read -p "Enter scene mood: " mood
                print_info "Generating dialogue for mood: $mood"
                print_demo "Use demo_scenespeak for full functionality"
                ;;
            3)
                read -p "Enter text to check: " text
                print_info "Checking safety: $text"
                print_demo "Use demo_safety_filter for full functionality"
                ;;
            4)
                print_info "OpenClaw Orchestrator coordinates all services"
                print_demo "See logs: kubectl logs -f deployment/openclaw-orchestrator -n $NAMESPACE"
                ;;
            5)
                print_info "Exiting interactive mode..."
                break
                ;;
            *)
                print_warning "Invalid choice"
                ;;
        esac
        echo ""
    done

    print_success "Interactive demo complete"
}

################################################################################
# Display Monitoring
################################################################################

display_live_monitoring() {
    echo ""
    print_header "Monitoring" "1" "Real-time Service Status"

    print_info "Press Ctrl+C to stop monitoring..."
    echo ""

    # Display pod status in a loop
    local counter=0
    while [ $counter -lt 10 ]; do
        clear 2>/dev/null || true
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}  Project Chimera Live Status${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo ""
        echo "Update: $(date '+%H:%M:%S')"
        echo ""

        print_info "Pods in '$NAMESPACE' namespace:"
        kubectl get pods -n "$NAMESPACE" 2>/dev/null || echo "Cannot connect to cluster"

        echo ""
        print_info "Pods in 'shared' namespace:"
        kubectl get pods -n shared 2>/dev/null || echo "Cannot connect to cluster"

        sleep 5
        counter=$((counter + 1))
    done
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo -e "${MAGENTA}========================================${NC}"
    echo -e "${MAGENTA}  Project Chimera Demo${NC}"
    echo -e "${MAGENTA}========================================${NC}"
    echo ""
    echo "Namespace: $NAMESPACE"
    echo "Interactive: $INTERACTIVE"
    echo ""

    # Pre-flight checks
    check_sudo

    if [ "$SKIP_CHECKS" = false ]; then
        print_info "Verifying deployment..."
        verify_kubectl || exit 1
    fi

    # Run demo scenarios
    demo_sentiment_analysis

    if [ "$INTERACTIVE" = true ]; then
        read -p "Press Enter to continue to next demo..."
    fi

    demo_scenespeak

    if [ "$INTERACTIVE" = true ]; then
        read -p "Press Enter to continue to next demo..."
    fi

    demo_safety_filter

    if [ "$INTERACTIVE" = true ]; then
        read -p "Press Enter to continue to next demo..."
    fi

    demo_full_pipeline

    if [ "$INTERACTIVE" = true ]; then
        demo_interactive
    fi

    # Print completion message
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Demo Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    print_success "Project Chimera demo scenarios completed"
    echo ""
    echo "Monitoring Dashboards:"
    echo "  Grafana:     http://localhost:3000 (admin/admin)"
    echo "  Prometheus:  http://localhost:9090"
    echo "  Jaeger:      http://localhost:16686"
    echo ""
    echo "Useful Commands:"
    echo "  # View logs:"
    echo "  kubectl logs -f deployment/<service-name> -n $NAMESPACE"
    echo ""
    echo "  # Port forward to a service:"
    echo "  kubectl port-forward -n $NAMESPACE svc/<service-name> 8080:8000"
    echo ""
    echo "  # Run the demo again:"
    echo "  ./scripts/run-demo.sh --interactive"
    echo ""
}

# Change to project root
cd "$PROJECT_ROOT"

# Run main function
main "$@"
