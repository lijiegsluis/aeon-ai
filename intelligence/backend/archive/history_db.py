"""
Aeon Intelligence - Persistent History

populated_api.py otherwise keeps everything in module-level globals: a
restart wipes all history, so prediction accuracy can never become a real,
growing number. This module persists snapshots into the shared local
~/.aeon/intelligence.db (the same SQLite file other Aeon backend modules
already use), so predictions/briefs/sentiment/news survive restarts and can
eventually be measured against real outcomes.

Every write fails soft (logs and returns) - a DB hiccup should never take
down a live API response.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path.home() / ".aeon" / "intelligence.db"

_NEW_TABLES = """
CREATE TABLE IF NOT EXISTS prediction_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at TEXT NOT NULL,
    mode TEXT,
    high_confidence_count INTEGER,
    pattern_based_count INTEGER,
    causal_count INTEGER,
    contrarian_count INTEGER,
    black_swan_count INTEGER,
    content_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS insider_trade_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    ticker TEXT,
    insider_name TEXT,
    role TEXT,
    transaction_type TEXT,
    total_value REAL,
    shares INTEGER,
    trade_date TEXT
);
"""


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init():
    try:
        with _conn() as conn:
            conn.executescript(_NEW_TABLES)
    except Exception as e:
        print(f"[history_db] init failed: {e}")


def save_daily_brief(brief: Dict[str, Any]):
    try:
        now = datetime.now()
        with _conn() as conn:
            conn.execute(
                "INSERT INTO daily_briefs (user_id, brief_date, content_json, generated_at) VALUES (1, ?, ?, ?)",
                (now.strftime("%Y-%m-%d"), json.dumps(brief, default=str), now.isoformat()),
            )
    except Exception as e:
        print(f"[history_db] save_daily_brief failed: {e}")


def save_prediction_snapshot(predictions: Dict[str, Any]):
    try:
        now = datetime.now().isoformat()
        mode = (predictions.get("meta") or {}).get("mode", "unknown")
        with _conn() as conn:
            conn.execute(
                """INSERT INTO prediction_snapshots
                   (generated_at, mode, high_confidence_count, pattern_based_count,
                    causal_count, contrarian_count, black_swan_count, content_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    now, mode,
                    len(predictions.get("high_confidence_predictions") or []),
                    len(predictions.get("pattern_based_predictions") or []),
                    len(predictions.get("causal_predictions") or []),
                    len(predictions.get("contrarian_predictions") or []),
                    len(predictions.get("black_swan_monitors") or []),
                    json.dumps(predictions, default=str),
                ),
            )
    except Exception as e:
        print(f"[history_db] save_prediction_snapshot failed: {e}")


def save_sentiment_snapshot(sentiment: Any):
    try:
        now = datetime.now().isoformat()
        value = None
        if isinstance(sentiment, dict):
            value = sentiment.get("fear_greed_value") or sentiment.get("value")
        with _conn() as conn:
            conn.execute(
                """INSERT INTO sentiment_snapshots
                   (ticker, sector, sentiment_score, confidence, sources_json, snapshot_at)
                   VALUES ('MARKET', NULL, ?, 1.0, ?, ?)""",
                (int(value) if value is not None else 50, json.dumps(sentiment, default=str), now),
            )
    except Exception as e:
        print(f"[history_db] save_sentiment_snapshot failed: {e}")


def save_news_items(items: List[Dict[str, Any]]):
    try:
        with _conn() as conn:
            existing = {row[0] for row in conn.execute(
                "SELECT title FROM news_feed WHERE timestamp >= ?",
                ((datetime.now() - timedelta(days=2)).isoformat(),),
            )}
            for item in items or []:
                title = item.get("title", "")
                if not title or title in existing:
                    continue
                conn.execute(
                    """INSERT INTO news_feed (title, content, source, url, timestamp, affected_tickers, sentiment)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (title, item.get("summary", ""), item.get("source", ""), item.get("url", ""),
                     item.get("published_at", datetime.now().isoformat()), item.get("tickers", ""),
                     item.get("sentiment", "neutral")),
                )
                existing.add(title)
    except Exception as e:
        print(f"[history_db] save_news_items failed: {e}")


def save_insider_trades(trades: List[Dict[str, Any]]):
    try:
        now = datetime.now().isoformat()
        with _conn() as conn:
            for t in trades or []:
                conn.execute(
                    """INSERT INTO insider_trade_snapshots
                       (captured_at, ticker, insider_name, role, transaction_type, total_value, shares, trade_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (now, t.get("ticker"), t.get("insider_name"), t.get("role"),
                     t.get("transaction_type"), t.get("total_value"), t.get("shares"), t.get("date")),
                )
    except Exception as e:
        print(f"[history_db] save_insider_trades failed: {e}")


def get_predictions_made_count(days: int = 30) -> int:
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with _conn() as conn:
            row = conn.execute(
                """SELECT COALESCE(SUM(high_confidence_count + pattern_based_count + causal_count +
                          contrarian_count), 0)
                   FROM prediction_snapshots WHERE generated_at >= ? AND mode = 'live'""",
                (cutoff,),
            ).fetchone()
            return int(row[0]) if row else 0
    except Exception as e:
        print(f"[history_db] get_predictions_made_count failed: {e}")
        return 0


def get_daily_brief_history(limit: int = 30) -> List[Dict[str, Any]]:
    try:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT brief_date, generated_at, content_json FROM daily_briefs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [{"brief_date": r[0], "generated_at": r[1], "content": json.loads(r[2])} for r in rows]
    except Exception as e:
        print(f"[history_db] get_daily_brief_history failed: {e}")
        return []
