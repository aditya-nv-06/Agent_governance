#!/bin/bash
# 🚀 Quick Setup - Run Everything (No LangGraph)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Agent Governance Platform - Quick Start"
echo "=========================================="
echo ""
echo "Services to start:"
echo "  ✓ Frontend (Port 5173)"
echo "  ✓ Primary Backend (Port 8000)"
echo "  ✓ Customer Service Backend (Port 8001)"
echo ""

# Step 1: Install dependencies
echo "📦 Installing dependencies..."
make install > /dev/null 2>&1 || true

# Step 2: Create directories
mkdir -p logs tmp/pids

# Step 3: Start services
echo "🚀 Starting services..."
echo ""

make dev

echo ""
echo "=========================================="
echo "✓ Services Started!"
echo "=========================================="
echo ""
echo "📍 Service URLs:"
echo "  • Frontend:           http://localhost:5173"
echo "  • Primary Backend:    http://localhost:8000"
echo "  • Customer Service:   http://localhost:8001"
echo ""
echo "📊 View Logs:"
echo "  make status"
echo ""
echo "🛑 Stop Services:"
echo "  make stop"
echo ""
