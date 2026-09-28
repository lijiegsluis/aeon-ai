"""
Enhanced Intelligence Service - Complete Integration
All features unified: Portfolio, Alerts, Patterns, News Aggregation
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our modules
import sys
sys.path.append(os.path.dirname(__file__))

DB_PATH = os.path.expanduser("~/.aeon/intelligence.db")

app = FastAPI(title="Aeon Nimbus Intelligence API - Enhanced", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "http://127.0.0.1:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════

class AddPositionRequest(BaseModel):
    ticker: str
    shares: float
    avg_cost: float

class CreateAlertRequest(BaseModel):
    name: str
    alert_type: str
    conditions: dict
    channels: List[str]
    cooldown_minutes: int = 60

class BacktestRequest(BaseModel):
    strategy_name: str
    event_type: str

# ═══════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════
# ORIGINAL ENDPOINTS (from intelligence_service.py)
# ═══════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "healthy", "service": "aeon-intelligence-enhanced", "version": "2.0.0"}

@app.get("/api/events/live")
def get_live_events(timeframe: str = "30days"):
    """Get all events with D-X countdown"""
    if timeframe == "30days":
        end_date = datetime.now() + timedelta(days=30)
    elif timeframe == "7days":
        end_date = datetime.now() + timedelta(days=7)
    elif timeframe == "90days":
        end_date = datetime.now() + timedelta(days=90)
    else:
        end_date = datetime.now() + timedelta(days=30)

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM events
            WHERE date(event_date) BETWEEN date('now') AND date(?)
            ORDER BY event_date ASC
        """, (end_date.date().isoformat(),)).fetchall()

        events = []
        for row in rows:
            event = dict(row)
            event_date = datetime.fromisoformat(event['event_date'])
            days_until = (event_date.date() - datetime.now().date()).days

            # Calculate phase
            if days_until <= 0:
                phase = "live"
                phase_color = "#ef4444"
            elif days_until <= 2:
                phase = "danger"
                phase_color = "#ef4444"
            elif days_until <= 9:
                phase = "euforia"
                phase_color = "#f59e0b"
            elif days_until <= 20:
                phase = "accumulation"
                phase_color = "#10b981"
            else:
                phase = "pre-rumor"
                phase_color = "#3b82f6"

            event['days_until'] = days_until
            event['phase'] = phase
            event['phase_color'] = phase_color

            # Parse affected_assets
            try:
                if event['affected_assets']:
                    # Handle both JSON array and string format
                    assets_str = event['affected_assets']
                    if assets_str.startswith('['):
                        event['affected_assets'] = json.loads(assets_str)
                    else:
                        # String format like "['SPY', 'QQQ']"
                        event['affected_assets'] = eval(assets_str)
                else:
                    event['affected_assets'] = []
            except:
                event['affected_assets'] = []

            events.append(event)

    return {
        "timeframe": timeframe,
        "total_events": len(events),
        "events": events,
        "phases": {
            "danger": len([e for e in events if e['phase'] == 'danger']),
            "euforia": len([e for e in events if e['phase'] == 'euforia']),
            "accumulation": len([e for e in events if e['phase'] == 'accumulation']),
            "pre_rumor": len([e for e in events if e['phase'] == 'pre-rumor'])
        }
    }

@app.get("/api/stats")
def get_stats():
    """Get dashboard statistics"""
    with get_db() as conn:
        total_events = conn.execute("SELECT COUNT(*) as cnt FROM events").fetchone()['cnt']
        upcoming_7d = conn.execute("""
            SELECT COUNT(*) as cnt FROM events
            WHERE date(event_date) BETWEEN date('now') AND date('now', '+7 days')
        """).fetchone()['cnt']

        # News feed stats
        try:
            total_news = conn.execute("SELECT COUNT(*) as cnt FROM news_feed").fetchone()['cnt']
            unprocessed = conn.execute("SELECT COUNT(*) as cnt FROM news_feed WHERE processed = 0").fetchone()['cnt']
        except:
            total_news = 0
            unprocessed = 0

        return {
            "total_events": total_events,
            "upcoming_7days": upcoming_7d,
            "total_news_items": total_news,
            "unprocessed_news": unprocessed
        }

# ═══════════════════════════════════════════════════════════
# PORTFOLIO ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/portfolio/positions")
def add_position(req: AddPositionRequest):
    """Add position to portfolio"""
    try:
        from portfolio_tracker import PortfolioTracker
        tracker = PortfolioTracker()
        position_id = tracker.add_position(req.ticker, req.shares, req.avg_cost)
        return {"id": position_id, "status": "created"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/portfolio/summary")
def get_portfolio():
    """Get portfolio with event exposure"""
    try:
        from portfolio_tracker import PortfolioTracker
        tracker = PortfolioTracker()
        return tracker.get_portfolio_summary()
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/portfolio/alerts")
def get_risk_alerts():
    """Get active risk alerts"""
    try:
        from portfolio_tracker import PortfolioTracker
        tracker = PortfolioTracker()
        return {"alerts": tracker.get_risk_alerts()}
    except Exception as e:
        raise HTTPException(500, str(e))

# ═══════════════════════════════════════════════════════════
# ALERT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/alerts/config")
def create_alert(req: CreateAlertRequest):
    """Create alert configuration"""
    try:
        from alert_manager import AlertManager
        manager = AlertManager()
        config_id = manager.create_alert_config(
            req.name, req.alert_type, req.conditions, req.channels, req.cooldown_minutes
        )
        return {"id": config_id, "status": "created"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/alerts/check")
def check_alerts(background_tasks: BackgroundTasks):
    """Check and trigger alerts"""
    try:
        from alert_manager import AlertManager
        manager = AlertManager()
        sent = manager.check_event_alerts()
        return {"alerts_sent": sent}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/alerts/history")
def get_alert_history(limit: int = 50):
    """Get alert history"""
    try:
        from alert_manager import AlertManager
        manager = AlertManager()
        return {"history": manager.get_alert_history(limit)}
    except Exception as e:
        raise HTTPException(500, str(e))

# ═══════════════════════════════════════════════════════════
# PATTERN ANALYSIS ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/api/patterns/{ticker}/{event_type}")
def get_pattern(ticker: str, event_type: str):
    """Get historical pattern analysis"""
    try:
        from pattern_analyzer import PatternAnalyzer
        analyzer = PatternAnalyzer()
        summary = analyzer.get_pattern_summary(event_type, ticker)
        return {"ticker": ticker, "event_type": event_type, "patterns": summary}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/predictions/{event_id}")
def get_predictions(event_id: int):
    """Get pattern-based predictions for event"""
    try:
        from pattern_analyzer import PatternAnalyzer
        analyzer = PatternAnalyzer()
        predictions = analyzer.predict_event_impact(event_id)
        return {"event_id": event_id, "predictions": predictions}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    """Run strategy backtest"""
    try:
        from pattern_analyzer import PatternAnalyzer
        analyzer = PatternAnalyzer()
        result = analyzer.backtest_strategy(req.strategy_name, req.event_type)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

# ═══════════════════════════════════════════════════════════
# NEWS FEED ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/api/news/live")
def get_live_news(limit: int = 50):
    """Get live news feed"""
    with get_db() as conn:
        try:
            rows = conn.execute("""
                SELECT * FROM news_feed
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
            return {"news": [dict(r) for r in rows], "count": len(rows)}
        except:
            return {"news": [], "count": 0}

@app.get("/api/calendar")
def get_calendar(view: str = "month"):
    """Get calendar view"""
    if view == "week":
        end_date = datetime.now() + timedelta(days=7)
    elif view == "month":
        end_date = datetime.now() + timedelta(days=30)
    else:
        end_date = datetime.now() + timedelta(days=90)

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM events
            WHERE date(event_date) BETWEEN date('now') AND date(?)
            ORDER BY event_date ASC
        """, (end_date.date().isoformat(),)).fetchall()

        calendar = {}
        for row in rows:
            event = dict(row)
            date_key = event['event_date']
            if date_key not in calendar:
                calendar[date_key] = []

            try:
                assets_str = event['affected_assets']
                if assets_str and assets_str.startswith('['):
                    event['affected_assets'] = json.loads(assets_str)
                elif assets_str:
                    event['affected_assets'] = eval(assets_str)
                else:
                    event['affected_assets'] = []
            except:
                event['affected_assets'] = []

            calendar[date_key].append(event)

    return {"view": view, "calendar": calendar}

# ═══════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════

@app.get("/api/system/info")
def system_info():
    """Get complete system information"""
    with get_db() as conn:
        # Count records in each table
        tables = ['events', 'news_feed', 'portfolio_positions', 'alert_configurations',
                  'historical_patterns', 'pattern_predictions']

        counts = {}
        for table in tables:
            try:
                result = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
                counts[table] = result['cnt'] if result else 0
            except:
                counts[table] = 0

        return {
            "version": "2.0.0",
            "features": {
                "events": True,
                "portfolio": counts['portfolio_positions'] > 0,
                "alerts": counts['alert_configurations'] > 0,
                "patterns": counts['historical_patterns'] > 0,
                "news_feed": counts['news_feed'] > 0
            },
            "data_counts": counts,
            "database": DB_PATH
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced Aeon Nimbus Intelligence API")
    print("   Version: 2.0.0")
    print("   Features: Events, Portfolio, Alerts, Patterns, News")
    print("   Port: 8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
