#!/bin/bash
# Quick start script for the entire agent governance system

set -e

echo "=========================================="
echo "Agent Governance Platform - Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✓ Python version: $(python3 --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
make install

echo ""
echo "✓ Dependencies installed successfully!"
echo ""

# Create logs directory
mkdir -p logs
mkdir -p tmp/pids

echo "🚀 Starting services..."
echo ""
echo "Services to start:"
echo "  - Primary Backend (Port 8000)"
echo "  - Customer Service Backend (Port 8001)"
echo "  - Frontend (Port 5173)"
echo "  - LangGraph Agent (Port 9001)"
echo ""

make dev

echo ""
echo "✓ All services started!"
echo ""
echo "📋 Service URLs:"
echo "  - Frontend: http://localhost:5173"
echo "  - Primary Backend: http://localhost:8000"
echo "  - Customer Service Backend: http://localhost:8001"
echo "  - LangGraph Agent: http://localhost:9001"
echo ""
echo "📖 Check logs with: make status"
echo "🛑 Stop services with: make stop"
echo ""
