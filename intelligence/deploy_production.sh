#!/bin/bash

# Aeon Nimbus Intelligence - Production Deployment Script
# Starts complete system with all features

set -e

echo "🚀 Starting Aeon Nimbus Intelligence Platform..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
cd "$(dirname "$0")"

# Database path
DB_PATH="$HOME/.aeon/intelligence.db"
mkdir -p "$(dirname "$DB_PATH")"

echo -e "${BLUE}📊 Step 1: Database Initialization${NC}"
echo "Database: $DB_PATH"

# Initialize all databases
python3 -c "
import sqlite3
from pathlib import Path

db_path = Path.home() / '.aeon' / 'intelligence.db'
conn = sqlite3.connect(str(db_path))
c = conn.cursor()

# Events
c.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        event_type TEXT,
        phase TEXT,
        affected_tickers TEXT,
        recommendation TEXT,
        impact_score REAL
    )
''')

# News feed
c.execute('''
    CREATE TABLE IF NOT EXISTS news_feed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        source TEXT,
        url TEXT,
        timestamp TEXT NOT NULL,
        affected_tickers TEXT,
        sentiment TEXT
    )
''')

# Portfolio
c.execute('''
    CREATE TABLE IF NOT EXISTS portfolio_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL UNIQUE,
        quantity REAL NOT NULL,
        entry_price REAL NOT NULL,
        current_price REAL,
        added_at TEXT
    )
''')

# Alerts
c.execute('''
    CREATE TABLE IF NOT EXISTS alert_configurations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL,
        ticker TEXT,
        days_before INTEGER,
        enabled INTEGER DEFAULT 1,
        channels TEXT,
        created_at TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS alert_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT,
        message TEXT,
        channel TEXT,
        triggered_at TEXT,
        acknowledged INTEGER DEFAULT 0
    )
''')

# Patterns
c.execute('''
    CREATE TABLE IF NOT EXISTS historical_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        event_type TEXT,
        avg_pre_event_move REAL,
        avg_event_move REAL,
        avg_post_event_move REAL,
        win_rate REAL,
        sample_size INTEGER,
        last_updated TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS pattern_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        ticker TEXT,
        predicted_move REAL,
        confidence REAL,
        factors TEXT,
        created_at TEXT
    )
''')

# Bot features
c.execute('''
    CREATE TABLE IF NOT EXISTS user_watchlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        added_at TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS daily_briefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        content TEXT,
        major_events TEXT,
        market_sentiment TEXT
    )
''')

conn.commit()
conn.close()
print('✅ Database tables initialized')
"

echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

echo -e "${BLUE}📅 Step 2: Loading Calendar Data${NC}"
python3 calendar_sync.py
echo -e "${GREEN}✓ Calendar events loaded${NC}"
echo ""

echo -e "${BLUE}💼 Step 3: Setting Up Demo Portfolio${NC}"
python3 -c "
from portfolio_tracker import PortfolioTracker

tracker = PortfolioTracker()

# Add demo positions
positions = [
    ('AAPL', 100, 175.50),
    ('MSFT', 50, 380.25),
    ('NVDA', 75, 450.00),
    ('TSLA', 25, 245.75),
    ('SPY', 200, 485.30),
    ('QQQ', 150, 420.15)
]

for ticker, qty, price in positions:
    try:
        tracker.add_position(ticker, qty, price)
        print(f'Added {ticker}: {qty} @ \${price}')
    except:
        pass

print('✅ Demo portfolio created')
"
echo -e "${GREEN}✓ Portfolio initialized${NC}"
echo ""

echo -e "${BLUE}🔔 Step 4: Configuring Default Alerts${NC}"
python3 -c "
from alert_manager import AlertManager

manager = AlertManager()

# Default alert configurations
alerts = [
    ('countdown', None, 7, ['desktop']),
    ('countdown', None, 3, ['desktop']),
    ('countdown', None, 1, ['desktop']),
    ('phase_change', None, None, ['desktop']),
]

for alert_type, ticker, days, channels in alerts:
    try:
        manager.create_alert_config(alert_type, ticker, days, channels)
        print(f'Created alert: {alert_type} (D-{days if days else \"N/A\"})')
    except:
        pass

print('✅ Default alerts configured')
"
echo -e "${GREEN}✓ Alerts configured${NC}"
echo ""

echo -e "${BLUE}📊 Step 5: Seeding Sample News${NC}"
python3 -c "
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

db_path = Path.home() / '.aeon' / 'intelligence.db'
conn = sqlite3.connect(str(db_path))
c = conn.cursor()

# Add sample news items
sample_news = [
    ('Federal Reserve signals potential rate pause', 'The Federal Reserve indicated it may pause rate hikes in upcoming meetings, citing cooling inflation data.', 'Financial News', 'SPY,QQQ', 'neutral'),
    ('Tech stocks rally on AI optimism', 'Major technology stocks surged as investors bet on AI-driven growth potential.', 'Market Watch', 'AAPL,MSFT,NVDA,GOOGL', 'positive'),
    ('Tesla announces new production milestone', 'Tesla reported reaching a new quarterly production record, beating analyst expectations.', 'Auto News', 'TSLA', 'positive'),
    ('Oil prices steady ahead of OPEC meeting', 'Crude oil prices remain stable as traders await OPEC+ production decision.', 'Energy Report', 'USO,XLE', 'neutral'),
    ('Chip sector sees strong demand signals', 'Semiconductor companies report robust order books for coming quarters.', 'Tech Insider', 'NVDA,AMD,INTC', 'positive'),
]

for title, content, source, tickers, sentiment in sample_news:
    timestamp = datetime.now() - timedelta(minutes=30)
    c.execute('''
        INSERT INTO news_feed (title, content, source, affected_tickers, sentiment, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, content, source, tickers, sentiment, timestamp.isoformat()))

conn.commit()
conn.close()
print('✅ Sample news added')
"
echo -e "${GREEN}✓ Sample news loaded${NC}"
echo ""

echo -e "${BLUE}🤖 Step 6: Starting Backend API (v3.0)${NC}"

# Kill existing instance if running
if [ -f /tmp/intelligence_v3.pid ]; then
    OLD_PID=$(cat /tmp/intelligence_v3.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing API (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
fi

# Start new instance
nohup python3 intelligence_service_v3.py > /tmp/intelligence_api.log 2>&1 &
API_PID=$!
echo $API_PID > /tmp/intelligence_v3.pid
echo -e "${GREEN}✓ API started (PID: $API_PID)${NC}"

# Wait for API to be ready
echo "Waiting for API to start..."
for i in {1..10}; do
    if curl -s http://localhost:8003/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready${NC}"
        break
    fi
    sleep 1
done
echo ""

echo -e "${BLUE}🎨 Step 7: Starting Frontend Dashboard${NC}"

# Kill existing instance if running
EXISTING_PID=$(lsof -ti:5175 || true)
if [ ! -z "$EXISTING_PID" ]; then
    echo "Stopping existing frontend (PID: $EXISTING_PID)..."
    kill $EXISTING_PID
    sleep 2
fi

cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
nohup npm run dev > /tmp/intelligence_frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/intelligence_frontend.pid
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to be ready
echo "Waiting for frontend to start..."
sleep 5
echo ""

cd ../backend

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ AEON NIMBUS INTELLIGENCE - FULLY OPERATIONAL${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo "   Dashboard:  http://localhost:5175"
echo "   API:        http://localhost:8003"
echo "   API Docs:   http://localhost:8003/docs"
echo ""
echo -e "${BLUE}📊 System Status:${NC}"

# Get system stats
STATS=$(curl -s http://localhost:8003/api/system/info)
echo "$STATS" | python3 -m json.tool

echo ""
echo -e "${BLUE}📝 Process IDs:${NC}"
echo "   API:        $API_PID (log: /tmp/intelligence_api.log)"
echo "   Frontend:   $FRONTEND_PID (log: /tmp/intelligence_frontend.log)"
echo ""
echo -e "${BLUE}🛑 To Stop:${NC}"
echo "   kill $API_PID $FRONTEND_PID"
echo ""
echo -e "${BLUE}🔧 Optional Background Services:${NC}"
echo "   News Aggregator:  python3 news_aggregator.py &"
echo "   Celery Worker:    celery -A celery_tasks worker -l info &"
echo "   Celery Beat:      celery -A celery_tasks beat -l info &"
echo ""
echo -e "${GREEN}🚀 System is ready! Open http://localhost:5175${NC}"
echo ""
