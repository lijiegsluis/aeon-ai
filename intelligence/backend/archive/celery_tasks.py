"""
Celery Background Tasks for Aeon Nimbus Intelligence
Handles scheduled data syncing, analysis, and notifications
"""

from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import sqlite3
import os

# Initialize Celery
app = Celery(
    'aeon_intelligence',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        # Sync news every 5 minutes
        'sync-news-feeds': {
            'task': 'celery_tasks.sync_news_feeds',
            'schedule': 300.0,  # 5 minutes
        },
        # Update patterns daily at 2 AM
        'update-patterns': {
            'task': 'celery_tasks.update_patterns',
            'schedule': crontab(hour=2, minute=0),
        },
        # Send daily brief at 8 AM
        'send-daily-brief': {
            'task': 'celery_tasks.send_daily_brief',
            'schedule': crontab(hour=8, minute=0),
        },
        # Check alerts every minute
        'check-alerts': {
            'task': 'celery_tasks.check_alerts',
            'schedule': 60.0,  # 1 minute
        },
        # Update sentiment hourly
        'update-sentiment': {
            'task': 'celery_tasks.update_sentiment',
            'schedule': 3600.0,  # 1 hour
        },
        # Sync economic calendar weekly
        'sync-economic-calendar': {
            'task': 'celery_tasks.sync_economic_calendar',
            'schedule': crontab(day_of_week=1, hour=0, minute=0),
        },
    }
)


@app.task(name='celery_tasks.sync_news_feeds')
def sync_news_feeds():
    """Sync news from all sources"""
    try:
        from news_aggregator import NewsAggregator

        aggregator = NewsAggregator()

        # Fetch from RSS feeds (Telegram requires user auth)
        aggregator.fetch_rss_feeds()

        # Fetch from Twitter via Nitter
        aggregator.fetch_twitter_feeds()

        print(f"[{datetime.now()}] News feeds synced successfully")
        return {"status": "success", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        print(f"Error syncing news feeds: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.update_patterns')
def update_patterns():
    """Update historical patterns for all tickers"""
    try:
        from pattern_analyzer import PatternAnalyzer

        analyzer = PatternAnalyzer()

        # Major tickers to analyze
        tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
            "SPY", "QQQ", "IWM", "DIA",
            "GLD", "SLV", "USO",
            "EURUSD", "GBPUSD", "USDJPY"
        ]

        event_types = ["earnings", "FOMC", "CPI", "NFP"]

        patterns_updated = 0
        for ticker in tickers:
            for event_type in event_types:
                try:
                    analyzer.analyze_historical_pattern(ticker, event_type)
                    patterns_updated += 1
                except:
                    pass

        print(f"[{datetime.now()}] Updated {patterns_updated} patterns")
        return {"status": "success", "patterns_updated": patterns_updated}

    except Exception as e:
        print(f"Error updating patterns: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.send_daily_brief')
def send_daily_brief():
    """Generate and send daily briefing"""
    try:
        from bot_features import BotFeatures

        bot = BotFeatures()
        brief = bot.generate_daily_brief()

        # Store brief
        db_path = os.path.expanduser("~/.aeon/intelligence.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO daily_briefs (date, content, major_events, market_sentiment)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().date().isoformat(),
            str(brief),
            str(brief.get("major_events", [])),
            brief.get("market_sentiment", "neutral")
        ))

        conn.commit()
        conn.close()

        print(f"[{datetime.now()}] Daily brief generated")
        return {"status": "success", "brief": brief}

    except Exception as e:
        print(f"Error generating daily brief: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.check_alerts')
def check_alerts():
    """Check and trigger alerts"""
    try:
        from alert_manager import AlertManager

        manager = AlertManager()
        triggered = manager.check_and_trigger_alerts()

        if triggered > 0:
            print(f"[{datetime.now()}] Triggered {triggered} alerts")

        return {"status": "success", "alerts_triggered": triggered}

    except Exception as e:
        print(f"Error checking alerts: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.update_sentiment')
def update_sentiment():
    """Update sentiment analysis for major tickers"""
    try:
        from sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        # Major tickers
        tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "META", "AMZN"]

        results = {}
        for ticker in tickers:
            try:
                sentiment = analyzer.analyze_ticker_sentiment(ticker, hours=24)
                results[ticker] = sentiment
            except:
                pass

        print(f"[{datetime.now()}] Updated sentiment for {len(results)} tickers")
        return {"status": "success", "tickers_analyzed": len(results)}

    except Exception as e:
        print(f"Error updating sentiment: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.sync_economic_calendar')
def sync_economic_calendar():
    """Sync economic calendar events"""
    try:
        from calendar_sync import seed_calendar

        seed_calendar()

        print(f"[{datetime.now()}] Economic calendar synced")
        return {"status": "success", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        print(f"Error syncing calendar: {e}")
        return {"status": "error", "error": str(e)}


@app.task(name='celery_tasks.analyze_ticker_on_demand')
def analyze_ticker_on_demand(ticker: str):
    """On-demand ticker analysis (called from API)"""
    try:
        from bot_features import BotFeatures

        bot = BotFeatures()
        analysis = bot.analyze_ticker(ticker)

        return {"status": "success", "analysis": analysis}

    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    print("Celery tasks defined:")
    print("- sync_news_feeds (every 5 minutes)")
    print("- update_patterns (daily at 2 AM)")
    print("- send_daily_brief (daily at 8 AM)")
    print("- check_alerts (every minute)")
    print("- update_sentiment (hourly)")
    print("- sync_economic_calendar (weekly)")
    print("\nTo start worker: celery -A celery_tasks worker --loglevel=info")
    print("To start beat scheduler: celery -A celery_tasks beat --loglevel=info")
