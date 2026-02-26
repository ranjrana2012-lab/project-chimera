#!/bin/bash
# Project Chimera Installation Script
# This script sets up the development environment for Project Chimera

set -e

echo "=========================================="
echo "Project Chimera - Installation"
echo "=========================================="

# Check Python version
PYTHON_VERSION_REQUIRED="3.10"
PYTHON_VERSION=$(python3 --version | awk '{print $2}')

echo "Checking Python version..."
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "Error: Python 3.10 or higher is required"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements-dev.txt

# Install service dependencies
for service in services/*; do
    if [ -f "$service/requirements.txt" ]; then
        echo "Installing dependencies for $service..."
        pip install -r "$service/requirements.txt" || true
    fi
done

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p models/prompts
mkdir -p models/lora-adapters
mkdir -p logs

# Pre-commit hooks
echo ""
echo "Setting up pre-commit hooks..."
pre-commit install || true

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run tests: make test"
echo "  4. Start local development: make dev"
