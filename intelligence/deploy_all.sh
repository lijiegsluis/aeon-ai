#!/bin/bash
# Aeon Nimbus Intelligence - Complete System Deployment
# All features: Events, Portfolio, Alerts, Patterns, News Aggregation

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 AEON NIMBUS INTELLIGENCE - COMPLETE DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$(dirname "$0")"

# ═══════════════════════════════════════════════════════════
# STEP 1: Database Initialization
# ═══════════════════════════════════════════════════════════

echo "📊 Step 1: Initializing Databases..."

python3 -c "
from intelligence_service_enhanced import get_db
from portfolio_tracker import PortfolioTracker
from alert_manager import AlertManager
from pattern_analyzer import PatternAnalyzer

# Initialize all tables
with get_db() as conn:
    conn.execute('SELECT 1')

PortfolioTracker()
AlertManager()
PatternAnalyzer()
print('✓ All database tables initialized')
"

# ═══════════════════════════════════════════════════════════
# STEP 2: Seed Data
# ═══════════════════════════════════════════════════════════

echo ""
echo "🌱 Step 2: Seeding Data..."

# Economic calendar
python3 calendar_sync.py

# Demo portfolio (optional)
echo ""
echo "Would you like to add demo portfolio? (y/n)"
read -t 5 -n 1 ADD_PORTFOLIO || ADD_PORTFOLIO="n"
echo ""

if [ "$ADD_PORTFOLIO" = "y" ]; then
    python3 portfolio_tracker.py
fi

# Default alerts
echo ""
echo "Setting up default alerts..."
python3 alert_manager.py

# ═══════════════════════════════════════════════════════════
# STEP 3: Start Enhanced API
# ═══════════════════════════════════════════════════════════

echo ""
echo "🚀 Step 3: Starting Enhanced Intelligence API..."

# Stop old service
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 2

# Start enhanced service
python3 intelligence_service_enhanced.py > /tmp/intelligence_enhanced.log 2>&1 &
INTEL_PID=$!
echo $INTEL_PID > /tmp/intelligence_enhanced.pid
sleep 4

# Verify API
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✓ Enhanced API running (PID: $INTEL_PID)"
else
    echo "✗ Enhanced API failed to start"
    tail -20 /tmp/intelligence_enhanced.log
    exit 1
fi

# ═══════════════════════════════════════════════════════════
# STEP 4: Frontend
# ═══════════════════════════════════════════════════════════

echo ""
echo "🎨 Step 4: Starting Intelligence Dashboard..."

cd ../frontend

# Check dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Stop old frontend
lsof -ti:5175 | xargs kill -9 2>/dev/null || true
sleep 2

# Start frontend
npm run dev > /tmp/intelligence_frontend_enhanced.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/intelligence_frontend_enhanced.pid
sleep 4

if lsof -ti:5175 > /dev/null; then
    echo "✓ Intelligence Dashboard running (PID: $FRONTEND_PID)"
else
    echo "✗ Dashboard failed to start"
    tail -20 /tmp/intelligence_frontend_enhanced.log
    exit 1
fi

# ═══════════════════════════════════════════════════════════
# STEP 5: Optional - Start News Aggregator
# ═══════════════════════════════════════════════════════════

echo ""
echo "📡 Step 5: News Aggregator..."
echo ""
echo "Would you like to start multi-source news aggregator? (y/n)"
read -t 5 -n 1 START_NEWS || START_NEWS="n"
echo ""

if [ "$START_NEWS" = "y" ]; then
    cd ../backend
    python3 news_aggregator.py > /tmp/news_aggregator.log 2>&1 &
    NEWS_PID=$!
    echo $NEWS_PID > /tmp/news_aggregator.pid
    echo "✓ News aggregator started (PID: $NEWS_PID)"
    echo "  Monitoring: Telegram (8 channels), RSS feeds, Twitter"
fi

# ═══════════════════════════════════════════════════════════
# SYSTEM STATUS
# ═══════════════════════════════════════════════════════════

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SYSTEM READY - ENHANCED VERSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access Points:"
echo "   Intelligence Dashboard:  http://localhost:5175"
echo "   Enhanced API:            http://localhost:8001"
echo "   API Documentation:       http://localhost:8001/docs"
echo ""
echo "📊 Features Available:"
echo "   ✓ Market Events & D-X Countdown System"
echo "   ✓ Portfolio Tracking & Event Exposure"
echo "   ✓ Smart Alert System (Desktop, Push, Email)"
echo "   ✓ Pattern Recognition & Historical Analysis"
echo "   ✓ Backtesting Engine"
echo "   ✓ Multi-Source News Aggregation"
echo "   ✓ Predictive Analytics"
echo ""
echo "📁 Logs:"
echo "   API:        /tmp/intelligence_enhanced.log"
echo "   Frontend:   /tmp/intelligence_frontend_enhanced.log"
if [ "$START_NEWS" = "y" ]; then
    echo "   News Feed:  /tmp/news_aggregator.log"
fi
echo ""
echo "⚡ Quick Stats:"
curl -s http://localhost:8001/api/system/info | python3 -m json.tool 2>/dev/null || echo "API warming up..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Open http://localhost:5175 in your browser"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Pro Tips:"
echo "   • Visit /api/portfolio/summary for portfolio exposure"
echo "   • Use /api/alerts/check to trigger smart alerts"
echo "   • Explore /api/patterns for historical analysis"
echo "   • Check /api/predictions/{event_id} for AI predictions"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait
