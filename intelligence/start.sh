#!/bin/bash
# Aeon Nimbus Intelligence - Complete System Startup

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 AEON NIMBUS INTELLIGENCE - System Startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Change to project root
cd "$(dirname "$0")"

# Step 1: Sync Economic Calendar
echo "📅 Step 1: Syncing Economic Calendar..."
python3 backend/calendar_sync.py
echo ""

# Step 2: Start Intelligence API (Port 8003)
echo "🚀 Step 2: Starting Intelligence API (Port 8003)..."
lsof -ti:8003 | xargs kill -9 2>/dev/null
python3 backend/intelligence_service.py > /tmp/intelligence_api.log 2>&1 &
INTEL_PID=$!
echo $INTEL_PID > /tmp/intelligence_api.pid
sleep 3

# Check if API started
if curl -s http://localhost:8003/health > /dev/null; then
    echo "✓ Intelligence API running (PID: $INTEL_PID)"
else
    echo "✗ Intelligence API failed to start"
    tail -20 /tmp/intelligence_api.log
    exit 1
fi
echo ""

# Step 3: Start Telegram Monitor (if not already running)
echo "📡 Step 3: Checking Telegram Monitor..."
if ps aux | grep "telegram_integration.py" | grep -v grep > /dev/null; then
    echo "✓ Telegram Monitor already running"
else
    echo "⚠️  Telegram Monitor not running"
    echo "   Start manually: cd ../analytics && python3 telegram_integration.py API_ID API_HASH"
fi
echo ""

# Step 4: Install Frontend Dependencies (if needed)
echo "📦 Step 4: Setting up Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Step 5: Start Frontend Dashboard (Port 5175)
echo "🎨 Step 5: Starting Intelligence Dashboard (Port 5175)..."
lsof -ti:5175 | xargs kill -9 2>/dev/null
npm run dev > /tmp/intelligence_frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/intelligence_frontend.pid
sleep 4

if lsof -ti:5175 > /dev/null; then
    echo "✓ Intelligence Dashboard running (PID: $FRONTEND_PID)"
else
    echo "✗ Dashboard failed to start"
    tail -20 /tmp/intelligence_frontend.log
    exit 1
fi
echo ""

# System Status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SYSTEM READY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Services:"
echo "   Intelligence API:    http://localhost:8003"
echo "   Intelligence App:    http://localhost:5175"
echo ""
echo "📊 Features:"
echo "   ✓ Real-time event countdowns (D-X system)"
echo "   ✓ Economic calendar (90 days ahead)"
echo "   ✓ Live news feed (Telegram integration)"
echo "   ✓ Phase-based trading signals"
echo "   ✓ Multi-asset impact analysis"
echo ""
echo "📁 Logs:"
echo "   API:       /tmp/intelligence_api.log"
echo "   Frontend:  /tmp/intelligence_frontend.log"
echo ""
echo "⚡ Quick Stats:"
curl -s http://localhost:8003/api/stats | python3 -m json.tool
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Open http://localhost:5175 to access Intelligence"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
