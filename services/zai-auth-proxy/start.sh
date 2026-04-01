#!/bin/bash
# Z.ai Authentication Proxy Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔐 Z.ai Authentication Proxy"
echo "============================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🚀 Starting authentication proxy..."
echo ""
echo "Open your browser and navigate to:"
echo "  📟 http://127.0.0.1:8899"
echo ""
echo "Follow the instructions to authenticate with your Z.ai account."
echo ""

# Start the service
python3 main.py
