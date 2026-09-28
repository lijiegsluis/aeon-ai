"""
Aeon Nimbus Intelligence - Complete Enhanced API Service
Integrates all features: events, news, portfolio, alerts, patterns, sentiment, chat
Version 3.0 - Production Ready
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
from datetime import datetime, timedelta
import os
from pathlib import Path

# Import all backend modules
from portfolio_tracker import PortfolioTracker
from alert_manager import AlertManager
from pattern_analyzer import PatternAnalyzer
from bot_features import BotFeatures

# Initialize FastAPI
app = FastAPI(
    title="Aeon Nimbus Intelligence API",
    description="Complete market intelligence platform with event monitoring, news aggregation, and AI chat",
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

# Initialize services
portfolio_tracker = PortfolioTracker(DB_PATH)
alert_manager = AlertManager(DB_PATH)
pattern_analyzer = PatternAnalyzer(DB_PATH)
bot_features = BotFeatures(DB_PATH)

# Lazy-load heavy services
sentiment_analyzer = None
langchain_agent = None

def get_sentiment_analyzer():
    global sentiment_analyzer
    if sentiment_analyzer is None:
        try:
            from sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer(DB_PATH)
        except Exception as e:
            print(f"Could not load sentiment analyzer: {e}")
    return sentiment_analyzer

def get_langchain_agent():
    global langchain_agent
    if langchain_agent is None:
        try:
            from langchain_agent import IntelligenceAgent
            langchain_agent = IntelligenceAgent(DB_PATH)
        except Exception as e:
            print(f"Could not load LangChain agent: {e}")
    return langchain_agent


# Pydantic Models
class NewsItem(BaseModel):
    title: str
    content: str
    source: str
    url: Optional[str] = None
    affected_tickers: Optional[str] = None

class PortfolioPosition(BaseModel):
    ticker: str
    quantity: float
    entry_price: float

class AlertConfig(BaseModel):
    alert_type: str
    ticker: Optional[str] = None
    days_before: Optional[int] = None
    channels: List[str] = ["desktop"]

class ChatMessage(BaseModel):
    message: str

class BacktestRequest(BaseModel):
    ticker: str
    event_type: str
    buy_day: int = -10
    sell_day: int = -1


# Database initialization
def init_db():
    """Initialize all database tables"""
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

    # Economic calendar
    c.execute('''
        CREATE TABLE IF NOT EXISTS economic_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            date TEXT NOT NULL,
            importance TEXT,
            actual TEXT,
            forecast TEXT,
            previous TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized")


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


# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "aeon-intelligence",
        "version": "3.0.0",
        "status": "operational",
        "features": [
            "Event Monitoring",
            "Live News Feed",
            "Portfolio Tracking",
            "Smart Alerts",
            "Pattern Analysis",
            "Sentiment Analysis",
            "AI Chat Assistant"
        ]
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "aeon-intelligence",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
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


@app.get("/api/calendar")
async def get_economic_calendar():
    """Get economic calendar events"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT id, event_name, date, importance, actual, forecast, previous
        FROM economic_calendar
        WHERE date >= ?
        ORDER BY date ASC
        LIMIT 50
    ''', (datetime.now().isoformat(),))

    calendar = []
    for row in c.fetchall():
        calendar.append({
            "id": row[0],
            "event_name": row[1],
            "date": row[2],
            "importance": row[3],
            "actual": row[4],
            "forecast": row[5],
            "previous": row[6]
        })

    conn.close()
    return calendar


# Portfolio endpoints
@app.post("/api/portfolio/positions")
async def add_position(position: PortfolioPosition):
    """Add portfolio position"""
    result = portfolio_tracker.add_position(
        position.ticker,
        position.quantity,
        position.entry_price
    )
    return result


@app.get("/api/portfolio/summary")
async def get_portfolio():
    """Get portfolio summary with event exposure"""
    return portfolio_tracker.get_portfolio_summary()


@app.get("/api/portfolio/alerts")
async def get_portfolio_alerts():
    """Get portfolio risk alerts"""
    return portfolio_tracker.get_risk_alerts()


# Alert endpoints
@app.post("/api/alerts/config")
async def create_alert(config: AlertConfig):
    """Create alert configuration"""
    result = alert_manager.create_alert_config(
        config.alert_type,
        config.ticker,
        config.days_before,
        config.channels
    )
    return result


@app.post("/api/alerts/check")
async def check_alerts():
    """Manually trigger alert check"""
    triggered = alert_manager.check_and_trigger_alerts()
    return {"alerts_triggered": triggered}


@app.get("/api/alerts/history")
async def get_alert_history():
    """Get alert history"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT alert_type, message, channel, triggered_at, acknowledged
        FROM alert_history
        ORDER BY triggered_at DESC
        LIMIT 50
    ''')

    history = []
    for row in c.fetchall():
        history.append({
            "alert_type": row[0],
            "message": row[1],
            "channel": row[2],
            "triggered_at": row[3],
            "acknowledged": bool(row[4])
        })

    conn.close()
    return history


# Pattern analysis endpoints
@app.get("/api/patterns/{ticker}/{event_type}")
async def get_pattern(ticker: str, event_type: str):
    """Get historical pattern analysis"""
    pattern = pattern_analyzer.analyze_historical_pattern(ticker.upper(), event_type)
    return pattern


@app.get("/api/predictions/{event_id}")
async def get_prediction(event_id: int):
    """Get AI prediction for event"""
    prediction = pattern_analyzer.generate_prediction(event_id)
    return prediction


@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """Run strategy backtest"""
    results = pattern_analyzer.backtest_strategy(
        request.ticker.upper(),
        request.event_type,
        request.buy_day,
        request.sell_day
    )
    return results


# Sentiment analysis endpoints
@app.get("/api/sentiment/{ticker}")
async def get_ticker_sentiment(ticker: str, hours: int = 24):
    """Get sentiment analysis for ticker"""
    analyzer = get_sentiment_analyzer()
    if not analyzer:
        raise HTTPException(status_code=503, detail="Sentiment analyzer not available")

    sentiment = analyzer.analyze_ticker_sentiment(ticker.upper(), hours)
    return sentiment


@app.get("/api/sentiment/market")
async def get_market_sentiment():
    """Get overall market sentiment"""
    analyzer = get_sentiment_analyzer()
    if not analyzer:
        raise HTTPException(status_code=503, detail="Sentiment analyzer not available")

    sentiment = analyzer.analyze_market_sentiment()
    return sentiment


# Bot features endpoints
@app.get("/api/analyze/{ticker}")
async def analyze_ticker(ticker: str):
    """Complete ticker analysis"""
    analysis = bot_features.analyze_ticker(ticker.upper())
    return analysis


@app.get("/api/briefing/daily")
async def get_daily_brief():
    """Get daily market briefing"""
    brief = bot_features.generate_daily_brief()
    return brief


@app.get("/api/briefing/weekly")
async def get_weekly_outlook():
    """Get weekly market outlook"""
    outlook = bot_features.generate_weekly_outlook()
    return outlook


# Chat endpoint
@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Natural language chat interface"""
    agent = get_langchain_agent()

    if not agent:
        # Fallback to bot features if LangChain not available
        response = bot_features.process_natural_language_query(message.message)
        return {"response": response}

    try:
        response = agent.chat_sync(message.message)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error processing query: {str(e)}"}


@app.get("/api/system/info")
async def system_info():
    """Get system information and feature availability"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check data availability
    c.execute('SELECT COUNT(*) FROM events')
    events_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM news_feed')
    news_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM portfolio_positions')
    portfolio_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM alert_configurations')
    alerts_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM historical_patterns')
    patterns_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM pattern_predictions')
    predictions_count = c.fetchone()[0]

    conn.close()

    return {
        "version": "3.0.0",
        "features": {
            "events": events_count > 0,
            "news_feed": news_count > 0,
            "portfolio": portfolio_count > 0,
            "alerts": alerts_count > 0,
            "patterns": patterns_count > 0,
            "predictions": predictions_count > 0,
            "sentiment": sentiment_analyzer is not None,
            "ai_chat": langchain_agent is not None
        },
        "data_counts": {
            "events": events_count,
            "news_feed": news_count,
            "portfolio_positions": portfolio_count,
            "alert_configurations": alerts_count,
            "historical_patterns": patterns_count,
            "pattern_predictions": predictions_count
        },
        "database": DB_PATH
    }


# Startup
@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    print(f"✅ Aeon Nimbus Intelligence API v3.0 started")
    print(f"📊 Database: {DB_PATH}")
    print(f"🌐 Docs: http://localhost:8001/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
