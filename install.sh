#!/bin/bash

# AetherSignal Installation Script
# Supports: macOS, Linux, Windows WSL

set -e

echo "🚀 Installing AetherSignal..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p storage
mkdir -p data/cache
mkdir -p data/processed
mkdir -p config
mkdir -p docs

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env and add your API keys (optional)"
    else
        echo "⚠️  .env.example not found, creating basic .env..."
        cat > .env << EOF
# AetherSignal Configuration
STREAMLIT_SERVER_PORT=8501
LOG_LEVEL=INFO
DEV_MODE=false
EOF
    fi
fi

# Run startup health checks
echo "🔍 Running startup health checks..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.system.startup_checks import startup_health_check
    startup_health_check()
    print('✅ Health checks passed')
except Exception as e:
    print(f'⚠️  Health check warning: {e}')
"

echo ""
echo "✨ Installation complete!"
echo ""
echo "To run AetherSignal:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: streamlit run app.py"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
echo ""

