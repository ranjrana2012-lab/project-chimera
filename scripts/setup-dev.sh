#!/bin/bash
# Project Chimera Phase 2 - Development Setup Script
#
# This script sets up the development environment for Phase 2 services.
#
# Usage:
#   chmod +x scripts/setup-dev.sh
#   ./scripts/setup-dev.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=================================="
    echo "$1"
    echo "=================================="
}

# Check Python version
check_python() {
    print_header "Checking Python Version"

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        print_info "Found Python $PYTHON_VERSION"

        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
            print_error "Python 3.12+ is required"
            print_info "Install Python 3.12 or higher"
            exit 1
        fi

        print_info "Python version OK"
    else
        print_error "Python 3 not found"
        print_info "Install Python 3.12 or higher"
        exit 1
    fi
}

# Check if pip is available
check_pip() {
    print_header "Checking pip"

    if command -v pip3 &> /dev/null; then
        print_info "pip3 found"
    elif command -v pip &> /dev/null; then
        print_info "pip found"
    else
        print_error "pip not found"
        print_info "Install pip:"
        print_info "  python3 -m ensurepip --upgrade"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_header "Creating Virtual Environment"

    if [ -d "venv" ]; then
        print_warn "Virtual environment already exists"
        read -p "Recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing virtual environment"
            rm -rf venv
            python3 -m venv venv
            print_info "Virtual environment created"
        else
            print_info "Using existing virtual environment"
        fi
    else
        python3 -m venv venv
        print_info "Virtual environment created"
    fi
}

# Activate virtual environment
activate_venv() {
    print_header "Activating Virtual Environment"

    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_info "Virtual environment activated"
    else
        print_error "Virtual environment not found"
        exit 1
    fi
}

# Upgrade pip
upgrade_pip() {
    print_header "Upgrading pip"

    pip install --upgrade pip setuptools wheel
    print_info "pip upgraded"
}

# Install Phase 2 dependencies
install_dependencies() {
    print_header "Installing Phase 2 Dependencies"

    print_info "Installing base dependencies..."
    pip install pydantic pydantic-settings python-dotenv

    print_info "Installing development dependencies..."
    pip install pytest pytest-asyncio pytest-cov black ruff mypy

    print_info "Installing DMX dependencies..."
    pip install dmx485 || print_warn "DMX dependencies not available (optional)"

    print_info "Installing Audio dependencies..."
    pip install sounddevice || print_warn "Audio dependencies not available (optional)"

    print_info "Installing BSL dependencies..."
    pip install mediapipe opencv-python numpy || print_warn "BSL dependencies not available (optional)"

    print_info "Dependencies installed"
}

# Create requirements files
create_requirements() {
    print_header "Creating Requirements Files"

    # Base requirements
    cat > services/requirements.txt << EOF
# Project Chimera Phase 2 - Base Requirements
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
EOF

    # Development requirements
    cat > services/requirements-dev.txt << EOF
# Project Chimera Phase 2 - Development Requirements
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.5.0
pre-commit>=3.3.0
EOF

    # DMX requirements
    cat > services/dmx-controller/requirements.txt << EOF
# DMX Controller Requirements
pydantic>=2.0.0
python-dotenv>=1.0.0
dmx485>=0.1.0
EOF

    # Audio requirements
    cat > services/audio-controller/requirements.txt << EOF
# Audio Controller Requirements
pydantic>=2.0.0
python-dotenv>=1.0.0
sounddevice>=0.4.6
pyaudio>=0.2.13
EOF

    # BSL requirements
    cat > services/bsl-avatar-service/requirements.txt << EOF
# BSL Avatar Service Requirements
pydantic>=2.0.0
python-dotenv>=1.0.0
mediapipe>=0.10.0
opencv-python>=4.8.0
numpy>=1.24.0
EOF

    print_info "Requirements files created"
}

# Create .env.example file
create_env_example() {
    print_header "Creating Environment Example"

    cat > .env.example << EOF
# Project Chimera Phase 2 - Environment Variables

# DMX Controller
DMX_UNIVERSE=1
DMX_REFRESH_RATE=44
DMX_INTERFACE=/dev/ttyUSB0

# Audio Controller
AUDIO_SAMPLE_RATE=48000
AUDIO_BIT_DEPTH=24
AUDIO_OUTPUT_DEVICE=default

# BSL Avatar Service
GESTURE_LIBRARY_PATH=services/bsl-avatar-service/data/gestures.json
AVATAR_RENDERER_URL=http://localhost:8080

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Development
DEBUG=false
RELOAD=true
EOF

    if [ ! -f .env ]; then
        cp .env.example .env
        print_info "Created .env from .env.example"
    else
        print_info ".env already exists, skipping"
    fi
}

# Create data directories
create_directories() {
    print_header "Creating Data Directories"

    mkdir -p services/bsl-avatar-service/data
    mkdir -p assets/audio
    mkdir -p logs

    print_info "Directories created"
}

# Run tests
run_tests() {
    print_header "Running Tests"

    print_info "Running DMX Controller tests..."
    cd services/dmx-controller
    python -m pytest tests/test_dmx_controller.py -v || print_warn "Some DMX tests failed"
    cd ../..

    print_info "Running Audio Controller tests..."
    cd services/audio-controller
    python -m pytest tests/test_audio_controller.py -v || print_warn "Some Audio tests failed"
    cd ../..

    print_info "Running BSL Avatar Service tests..."
    cd services/bsl-avatar-service
    python -m pytest tests/test_bsl_avatar_service.py -v || print_warn "Some BSL tests failed"
    cd ../..

    print_info "Tests complete"
}

# Setup git hooks
setup_git_hooks() {
    print_header "Setting Up Git Hooks"

    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Project Chimera - Pre-commit Hook

echo "Running pre-commit checks..."

# Format with black
echo "Formatting with black..."
black services/dmx-controller/*.py
black services/audio-controller/*.py
black services/bsl-avatar-service/*.py

# Check with ruff
echo "Checking with ruff..."
ruff check services/dmx-controller/*.py
ruff check services/audio-controller/*.py
ruff check services/bsl-avatar-service/*.py

echo "Pre-commit checks complete"
EOF

    chmod +x .git/hooks/pre-commit
    print_info "Git hooks configured"
}

# Print summary
print_summary() {
    print_header "Setup Complete"

    echo ""
    echo "Development environment is ready!"
    echo ""
    echo "Next steps:"
    echo "  1. Activate virtual environment:"
    echo "     source venv/bin/activate"
    echo ""
    echo "  2. Run tests:"
    echo "     cd services/dmx-controller && python -m pytest tests/"
    echo "     cd services/audio-controller && python -m pytest tests/"
    echo "     cd services/bsl-avatar-service && python -m pytest tests/"
    echo ""
    echo "  3. Run examples:"
    echo "     cd services/dmx-controller && python examples/dmx_example.py"
    echo "     cd services/audio-controller && python examples/audio_example.py"
    echo "     cd services/bsl-avatar-service && python examples/bsl_avatar_example.py"
    echo ""
    echo "  4. Start services (with Docker):"
    echo "     docker-compose -f services/docker-compose.phase2.yml up -d"
    echo ""
    echo "For more information, see:"
    echo "  - README.md in each service directory"
    echo "  - docs/PHASE_2_IMPLEMENTATION_PLAN.md"
    echo ""
}

# Main setup flow
main() {
    print_header "Project Chimera Phase 2 - Development Setup"

    check_python
    check_pip
    create_venv
    activate_venv
    upgrade_pip
    create_requirements
    create_env_example
    create_directories
    setup_git_hooks

    read -p "Run tests now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    fi

    print_summary
}

# Run main function
main "$@"
