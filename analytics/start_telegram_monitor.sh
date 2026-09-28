#!/bin/bash
# Aeon Nimbus - Telegram News Monitor Startup Script

cd "$(dirname "$0")"

# Check if session exists
if [ ! -f "aeon_terminal_session.session" ]; then
    echo "⚠️  No Telegram session found. Please authenticate first:"
    echo "   python3 telegram_integration.py 37634302 d3657dff2652c4251b3d3ff2f1d10f04"
    exit 1
fi

echo "🚀 Starting Telegram news monitor for @Tradeul_Breaking_News..."
python3 telegram_integration.py 37634302 d3657dff2652c4251b3d3ff2f1d10f04 &

MONITOR_PID=$!
echo "✓ Monitor running (PID: $MONITOR_PID)"
echo "✓ Watching channel for breaking news"
echo "✓ Events will appear in Terminal Rumor/News tab"
echo ""
echo "To stop: kill $MONITOR_PID"
