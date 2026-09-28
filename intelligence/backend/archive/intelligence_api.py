"""
Aeon Nimbus Intelligence - Production API v3.0
Complete market intelligence platform with real-time news and events
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
from datetime import datetime, timedelta
import os
from pathlib import Path

# Initialize FastAPI
app = FastAPI(
    title="Aeon Nimbus Intelligence API",
    description="Complete market intelligence platform with event monitoring and news aggregation",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = str(Path.home() / ".aeon" / "intelligence.db")


# Pydantic Models
class NewsItem(BaseModel):
    title: str
    content: str
    source: str
    url: Optional[str] = None
    affected_tickers: Optional[str] = None

class ChatMessage(BaseModel):
    message: str


# Helper functions
def calculate_days_away(event_date: str) -> int:
    """Calculate days until event"""
    try:
        event_dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
        now = datetime.now()
        delta = event_dt - now
        return max(0, delta.days)
    except:
        return 0


def determine_phase(days_away: int) -> str:
    """Determine D-X phase based on days away"""
    if days_away <= 2:
        return "DANGER ZONE"
    elif days_away <= 9:
        return "EUFORIA"
    elif days_away <= 20:
        return "ACCUMULATION"
    else:
        return "PRE-RUMOR"


def get_recommendation(phase: str) -> str:
    """Get trading recommendation for phase"""
    recommendations = {
        "DANGER ZONE": "High volatility - Consider exit or hedging",
        "EUFORIA": "Peak speculation - Take profits on winners",
        "ACCUMULATION": "Buy the rumor - Accumulate positions",
        "PRE-RUMOR": "Early positioning - Research and monitor"
    }
    return recommendations.get(phase, "Monitor closely")


def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Events table
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

    # News feed table
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

    conn.commit()
    conn.close()


# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "aeon-nimbus-intelligence",
        "version": "3.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "aeon-nimbus-intelligence",
        "version": "3.0.0"
    }


@app.get("/api/events/live")
async def get_live_events():
    """Get all events with real-time D-X countdown"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT id, title, description, date, event_type, affected_tickers, impact_score
        FROM events
        WHERE date >= ?
        ORDER BY date ASC
    ''', (datetime.now().isoformat(),))

    events = []
    for row in c.fetchall():
        days_away = calculate_days_away(row[3])
        phase = determine_phase(days_away)

        events.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "date": row[3],
            "event_type": row[4],
            "affected_tickers": row[5],
            "impact_score": row[6],
            "days_away": days_away,
            "phase": phase,
            "recommendation": get_recommendation(phase)
        })

    conn.close()
    return events


@app.get("/api/news/live")
async def get_live_news():
    """Get live news feed from last 24 hours"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()

    c.execute('''
        SELECT id, title, content, source, url, timestamp, affected_tickers, sentiment
        FROM news_feed
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 100
    ''', (cutoff,))

    news = []
    for row in c.fetchall():
        news.append({
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "source": row[3],
            "url": row[4],
            "timestamp": row[5],
            "affected_tickers": row[6],
            "sentiment": row[7]
        })

    conn.close()
    return news


@app.post("/api/news/feed")
async def add_news(news: NewsItem):
    """Add news item to feed"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        INSERT INTO news_feed (title, content, source, url, timestamp, affected_tickers)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        news.title,
        news.content,
        news.source,
        news.url,
        datetime.now().isoformat(),
        news.affected_tickers
    ))

    conn.commit()
    news_id = c.lastrowid
    conn.close()

    return {"status": "success", "id": news_id}


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Total events
    c.execute('SELECT COUNT(*) FROM events WHERE date >= ?', (datetime.now().isoformat(),))
    total_events = c.fetchone()[0]

    # Events in next 7 days
    cutoff_7d = (datetime.now() + timedelta(days=7)).isoformat()
    c.execute('SELECT COUNT(*) FROM events WHERE date >= ? AND date <= ?',
              (datetime.now().isoformat(), cutoff_7d))
    events_7d = c.fetchone()[0]

    # News in last 24h
    cutoff_24h = (datetime.now() - timedelta(hours=24)).isoformat()
    c.execute('SELECT COUNT(*) FROM news_feed WHERE timestamp >= ?', (cutoff_24h,))
    news_24h = c.fetchone()[0]

    # Portfolio positions
    c.execute('SELECT COUNT(*) FROM portfolio_positions')
    portfolio_count = c.fetchone()[0]

    # Active alerts
    c.execute('SELECT COUNT(*) FROM alert_configurations WHERE enabled = 1')
    alert_count = c.fetchone()[0]

    conn.close()

    return {
        "total_events": total_events,
        "events_next_7_days": events_7d,
        "news_last_24h": news_24h,
        "portfolio_positions": portfolio_count,
        "active_alerts": alert_count
    }


@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Simple chat interface"""
    query = message.message.lower()

    # Simple keyword-based responses
    if "event" in query or "upcoming" in query:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM events WHERE date >= ?', (datetime.now().isoformat(),))
        count = c.fetchone()[0]
        conn.close()
        return {"response": f"There are {count} upcoming events. Check the Events tab for details."}

    elif any(ticker in query.upper() for ticker in ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ"]):
        return {"response": "Check the ticker's event exposure in the Events tab or add it to your portfolio."}

    elif "portfolio" in query:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM portfolio_positions')
        count = c.fetchone()[0]
        conn.close()
        return {"response": f"You have {count} positions in your portfolio."}

    else:
        return {"response": "I can help you with: upcoming events, ticker analysis, portfolio tracking, and market insights. What would you like to know?"}


@app.get("/api/system/info")
async def system_info():
    """Get system information"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM events')
    events_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM news_feed')
    news_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM portfolio_positions')
    portfolio_count = c.fetchone()[0]

    conn.close()

    return {
        "version": "3.0.0",
        "status": "operational",
        "data_counts": {
            "events": events_count,
            "news_feed": news_count,
            "portfolio_positions": portfolio_count
        },
        "database": DB_PATH
    }


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    print(f"✅ Aeon Nimbus Intelligence API v3.0 started on port 8001")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
