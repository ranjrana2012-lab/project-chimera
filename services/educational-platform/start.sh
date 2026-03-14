#!/bin/bash
# Educational Platform Service Startup Script

set -e

echo "================================"
echo "Educational Platform Service"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if .env exists, if not copy example
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "✓ .env file created. Please review and update if needed."
fi

# Check if dependencies are available
echo ""
echo "Checking service dependencies..."

# Check BSL Agent
if curl -s http://localhost:8003/health/live > /dev/null 2>&1; then
    echo "✓ BSL Agent (port 8003) - Available"
else
    echo "⚠ BSL Agent (port 8003) - Not available (optional)"
fi

# Check Captioning Agent
if curl -s http://localhost:8002/health/live > /dev/null 2>&1; then
    echo "✓ Captioning Agent (port 8002) - Available"
else
    echo "⚠ Captioning Agent (port 8002) - Not available (optional)"
fi

# Check Sentiment Agent
if curl -s http://localhost:8004/health/live > /dev/null 2>&1; then
    echo "✓ Sentiment Agent (port 8004) - Available"
else
    echo "⚠ Sentiment Agent (port 8004) - Not available (optional)"
fi

echo ""
echo "Starting Educational Platform Service on port 8012..."
echo ""

# Start the service
python main.py
