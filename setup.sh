#!/bin/bash

# MCP Server Setup Script
# This script sets up the MCP Research + News Newspaper Generator

set -e  # Exit on error

echo "=================================="
echo "MCP Server Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/newspapers
mkdir -p data/cache
mkdir -p data/pdfs
mkdir -p logs

echo "✓ Directories created"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo "   Required: OPENAI_API_KEY, GEMINI_API_KEY"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Download spaCy model (optional, for NLP)
echo ""
echo "Downloading spaCy English model (optional)..."
python -m spacy download en_core_web_sm || echo "⚠️  spaCy model download failed (optional)"

echo ""
echo "=================================="
echo "Setup Complete! 🎉"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Edit config/config.yaml to set your topics"
echo "3. Run: python mcp_orchestrator.py --topics 'your topic' --max-items 20"
echo ""
echo "For help: python mcp_orchestrator.py --help"
echo ""
