#!/bin/bash
# Project Chimera - Student First-Run Setup Script
# ==================================================
# Automated setup for first-time students getting started with Project Chimera
#
# This script will:
#   - Verify repository exists (or clone it)
#   - Check prerequisites (Docker, Docker Compose, git, curl)
#   - Create .env file from template
#   - Pull Docker images
#   - Start all 8 MVP services
#   - Run health checks
#   - Display success message with next steps
#
# Usage:
#   ./scripts/student-first-run.sh
#   ./scripts/student-first-run.sh --skip-prereqs
#   ./scripts/student-first-run.sh --help

set -euo pipefail

# ============================================================================
# COLORS AND FORMATTING
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================================
# CONFIGURATION
# ============================================================================
SKIP_PREREQS=false
SKIP_IMAGES=false
PROJECT_NAME="Project_Chimera"
REPO_URL="https://github.com/your-org/Project_Chimera.git"
DOCKER_COMPOSE_FILE="docker-compose.mvp.yml"
ENV_TEMPLATE=".env.example"
ENV_FILE=".env"
TOTAL_SERVICES=8

# Service ports for health checks
declare -A SERVICE_PORTS=(
    ["openclaw-orchestrator"]="8000"
    ["scenespeak-agent"]="8001"
    ["translation-agent"]="8002"
    ["sentiment-agent"]="8004"
    ["safety-filter"]="8006"
    ["operator-console"]="8007"
    ["hardware-bridge"]="8008"
    ["redis"]="6379"
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
}

print_info() {
    echo -e "${BOLD}  $1${NC}"
}

show_help() {
    cat << EOF
${BOLD}Project Chimera - Student First-Run Setup${NC}

${BOLD}Usage:${NC}
    $0 [OPTIONS]

${BOLD}Options:${NC}
    --skip-prereqs    Skip prerequisite checks (for troubleshooting)
    --skip-images     Skip Docker image pulling
    --help            Show this help message

${BOLD}Description:${NC}
    This script automates the initial setup for students working with
    Project Chimera. It performs the following steps:

    1. Verifies repository exists (or clones it)
    2. Checks prerequisites (Docker, Docker Compose, git, curl)
    3. Creates .env file from .env.example template
    4. Pulls all required Docker images
    5. Starts all 8 MVP services
    6. Runs health checks on all services
    7. Displays success message with next steps

${BOLD}Services Started:${NC}
    - openclaw-orchestrator (port 8000)
    - scenespeak-agent (port 8001)
    - translation-agent (port 8002)
    - sentiment-agent (port 8004)
    - safety-filter (port 8006)
    - operator-console (port 8007)
    - hardware-bridge (port 8008)
    - redis (port 6379)

${BOLD}Examples:${NC}
    $0                          # Full setup with all checks
    $0 --skip-prereqs          # Skip prerequisite checks
    $0 --skip-images           # Skip pulling images

EOF
    exit 0
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

error_exit() {
    print_error "$1"
    echo ""
    print_warning "Setup failed. Please fix the error above and run again."
    echo "For help, visit: https://github.com/your-org/Project_Chimera/docs"
    exit 1
}

trap 'error_exit "Script interrupted by user"' INT

# ============================================================================
# REPOSITORY CHECKS
# ============================================================================

check_repository() {
    print_step "Checking repository..."

    # Check if we're in the Project Chimera directory
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        print_warning "Docker Compose file not found in current directory"

        # Check if we're in a subdirectory
        if [[ -f "../$DOCKER_COMPOSE_FILE" ]]; then
            print_info "Found repository in parent directory"
            cd ..
            print_success "Changed to repository directory: $(pwd)"
            return 0
        fi

        # Ask if user wants to clone
        echo ""
        print_warning "Repository not found locally."
        echo -n "Would you like to clone $REPO_URL? (y/n): "
        read -r response

        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_info "Cloning repository..."
            if git clone "$REPO_URL"; then
                cd "$PROJECT_NAME"
                print_success "Repository cloned successfully"
            else
                error_exit "Failed to clone repository"
            fi
        else
            error_exit "Cannot proceed without repository"
        fi
    else
        print_success "Repository found: $(pwd)"
    fi

    # Verify it's actually the Project Chimera repo
    if [[ ! -f "README.md" ]] || ! grep -q "Project Chimera" README.md 2>/dev/null; then
        error_exit "This doesn't appear to be a Project Chimera repository"
    fi
}

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

check_prerequisites() {
    if [[ "$SKIP_PREREQS" == true ]]; then
        print_warning "Skipping prerequisite checks (--skip-prereqs flag)"
        return 0
    fi

    print_step "Checking prerequisites..."

    local missing_prereqs=()

    # Check Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker installed: $docker_version"

        # Check if Docker is running
        if docker info &> /dev/null; then
            print_success "Docker daemon is running"
        else
            error_exit "Docker daemon is not running. Please start Docker."
        fi
    else
        missing_prereqs+=("Docker")
    fi

    # Check Docker Compose
    if docker compose version &> /dev/null; then
        local compose_version=$(docker compose version --short)
        print_success "Docker Compose installed: $compose_version"
    elif command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker Compose installed: $compose_version"
        print_warning "Consider upgrading to 'docker compose' (plugin version)"
    else
        missing_prereqs+=("Docker Compose")
    fi

    # Check git
    if command -v git &> /dev/null; then
        local git_version=$(git --version | awk '{print $3}')
        print_success "Git installed: $git_version"
    else
        missing_prereqs+=("git")
    fi

    # Check curl
    if command -v curl &> /dev/null; then
        print_success "curl installed"
    else
        missing_prereqs+=("curl")
    fi

    # Check disk space (need at least 5GB free)
    local free_space_gb=$(df . | tail -1 | awk '{print int($4/1024/1024)}')
    if [[ $free_space_gb -ge 5 ]]; then
        print_success "Disk space available: ${free_space_gb}GB"
    else
        print_warning "Low disk space: ${free_space_gb}GB free (recommend 5GB+)"
    fi

    # Report missing prerequisites
    if [[ ${#missing_prereqs[@]} -gt 0 ]]; then
        echo ""
        print_error "Missing prerequisites:"
        for prereq in "${missing_prereqs[@]}"; do
            echo "  • $prereq"
        done
        echo ""
        print_info "Please install missing prerequisites and run again."
        echo ""
        echo "Installation guides:"
        echo "  • Docker: https://docs.docker.com/get-docker/"
        echo "  • Docker Compose: https://docs.docker.com/compose/install/"
        echo "  • Git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git"
        echo ""
        error_exit "Prerequisites check failed"
    fi

    print_success "All prerequisites installed"
}

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

setup_environment() {
    print_step "Setting up environment..."

    # Check if .env already exists
    if [[ -f "$ENV_FILE" ]]; then
        print_warning ".env file already exists"
        echo -n "Backup existing .env and create new one? (y/n): "
        read -r response

        if [[ "$response" =~ ^[Yy]$ ]]; then
            mv "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
            print_success "Backed up existing .env file"
        else
            print_info "Using existing .env file"
            return 0
        fi
    fi

    # Check if template exists
    if [[ ! -f "$ENV_TEMPLATE" ]]; then
        error_exit "Environment template not found: $ENV_TEMPLATE"
    fi

    # Copy template to .env
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    print_success "Created .env from template"

    # Set default values for critical variables
    print_info "Configuring default values..."

    # Set environment to development
    sed -i.bak 's/^ENVIRONMENT=.*/ENVIRONMENT=development/' "$ENV_FILE"
    sed -i.bak 's/^LOG_LEVEL=.*/LOG_LEVEL=INFO/' "$ENV_FILE"

    # Remove backup file
    rm -f "${ENV_FILE}.bak"

    print_success "Environment configured for development"

    # Show what variables need attention
    echo ""
    print_warning "Note: Some environment variables may need your attention:"
    echo "  • GLM_API_KEY - Required for SceneSpeak LLM features"
    echo "  • CORS_ORIGINS - Adjust for your development setup"
    echo ""
    print_info "Edit .env file to customize: nano .env"
}

# ============================================================================
# DOCKER OPERATIONS
# ============================================================================

pull_docker_images() {
    if [[ "$SKIP_IMAGES" == true ]]; then
        print_warning "Skipping Docker image pull (--skip-images flag)"
        return 0
    fi

    print_step "Pulling Docker images..."

    print_info "This may take several minutes on first run..."

    if docker compose -f "$DOCKER_COMPOSE_FILE" pull 2>&1 | while IFS= read -r line; do
        echo "  $line"
    done; then
        print_success "Docker images pulled successfully"
    else
        print_warning "Some images failed to pull (will build instead)"
    fi
}

start_services() {
    print_step "Starting services..."

    print_info "Starting $TOTAL_SERVICES services..."

    if docker compose -f "$DOCKER_COMPOSE_FILE" up -d 2>&1 | while IFS= read -r line; do
        echo "  $line"
    done; then
        print_success "Services started successfully"
    else
        error_exit "Failed to start services"
    fi
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

wait_for_service() {
    local service_name=$1
    local port=$2
    local max_wait=60
    local wait_time=0

    echo -n "  Waiting for $service_name (port $port)..."

    while [[ $wait_time -lt $max_wait ]]; do
        if curl -sf "http://localhost:$port/" &>/dev/null || \
           curl -sf "http://localhost:$port/health" &>/dev/null || \
           curl -sf "http://localhost:$port/health/live" &>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi

        # Special check for Redis
        if [[ "$service_name" == "redis" ]]; then
            if docker exec chimera-redis redis-cli ping &>/dev/null; then
                echo -e " ${GREEN}✓${NC}"
                return 0
            fi
        fi

        echo -n "."
        sleep 2
        ((wait_time += 2))
    done

    echo -e " ${RED}✗ TIMEOUT${NC}"
    return 1
}

run_health_checks() {
    print_step "Running health checks..."

    local healthy=0
    local total=${#SERVICE_PORTS[@]}

    echo ""
    for service in "${!SERVICE_PORTS[@]}"; do
        port=${SERVICE_PORTS[$service]}

        if wait_for_service "$service" "$port"; then
            ((healthy++))
        fi
    done

    echo ""
    print_info "Health check results: $healthy/$total services responsive"

    if [[ $healthy -eq $total ]]; then
        print_success "All services are healthy!"
        return 0
    elif [[ $healthy -gt 0 ]]; then
        print_warning "Some services are still starting..."
        print_info "Run './scripts/validate-mvp-health.sh' to check again"
        return 0
    else
        print_error "No services are responding"
        return 1
    fi
}

# ============================================================================
# SUCCESS MESSAGE
# ============================================================================

show_success_message() {
    print_header "Setup Complete!"

    cat << EOF
${GREEN}✓ Project Chimera is now running!${NC}

${BOLD}Services Access:${NC}
  • Orchestrator:     http://localhost:8000
  • SceneSpeak:       http://localhost:8001
  • Translation:      http://localhost:8002
  • Sentiment:        http://localhost:8004
  • Safety Filter:    http://localhost:8006
  • Operator Console: http://localhost:8007
  • Hardware Bridge:  http://localhost:8008
  • Redis:            localhost:6379

${BOLD}Next Steps:${NC}
  1. Explore the documentation:
     ${CYAN}cat README.md${NC}
     ${CYAN}cat STUDENT_GUIDE.md${NC}

  2. Run the student quick start:
     ${CYAN}cat Student_Quick_Start.md${NC}

  3. Test the system:
     ${CYAN}./scripts/validate-mvp-health.sh${NC}

  4. View service logs:
     ${CYAN}docker compose -f $DOCKER_COMPOSE_FILE logs -f${NC}

  5. Stop services when done:
     ${CYAN}docker compose -f $DOCKER_COMPOSE_FILE down${NC}

${BOLD}Getting Help:${NC}
  • Documentation: ./docs/
  • Troubleshooting: ./docs/student-preparation/troubleshooting.md
  • Issues: https://github.com/your-org/Project_Chimera/issues

${YELLOW}Note:${NC} This is your first setup. Consider:
  • Reviewing .env configuration for your environment
  • Setting up any required API keys (GLM_API_KEY for SceneSpeak)
  • Exploring the test suite: ./tests/

EOF
}

# ============================================================================
# MAIN FUNCTION
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-prereqs)
                SKIP_PREREQS=true
                shift
                ;;
            --skip-images)
                SKIP_IMAGES=true
                shift
                ;;
            --help|-h)
                show_help
                ;;
            *)
                error_exit "Unknown option: $1 (use --help for usage)"
                ;;
        esac
    done

    # Print welcome banner
    print_header "Project Chimera - Student First-Run Setup"

    cat << EOF
Welcome to Project Chimera! This script will guide you through
the initial setup process to get all services running.

This should take 5-10 minutes depending on your network speed.

EOF

    # Run setup steps
    check_repository
    check_prerequisites
    setup_environment
    pull_docker_images
    start_services
    run_health_checks

    # Show success message
    show_success_message

    exit 0
}

# Run main function
main "$@"
