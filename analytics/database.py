"""
Database layer for Aeon Nimbus Terminal persistence
SQLite for simplicity, easy to upgrade to Postgres later
"""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DB_PATH = Path(os.environ.get("AEON_ANALYTICS_DB_PATH", str(Path.home() / ".aeon" / "terminal.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Single-user app for now: the frontend hardcodes user_id=1 everywhere
# (AlertsManager, WatchlistManager, AnalysisHistory) rather than pretending
# to support multiple accounts it has no auth for. This is the same default
# those callers already assume.
DEFAULT_USER_ID = 1


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticker TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_analyses_ticker ON analyses(ticker);
            CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analyses(user_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS watchlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                tickers_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_watchlists_user ON watchlists(user_id);

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                threshold REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active, ticker);

            CREATE TABLE IF NOT EXISTS shared_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                share_token TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT,
                FOREIGN KEY (analysis_id) REFERENCES analyses(id)
            );
            CREATE INDEX IF NOT EXISTS idx_shared_token ON shared_analyses(share_token);

            CREATE TABLE IF NOT EXISTS market_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                event_date TEXT,
                source TEXT DEFAULT 'manual',
                raw_text TEXT,
                affected_assets TEXT,
                analysis_json TEXT,
                sentiment_score INTEGER,
                analyzed_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_events_date ON market_events(event_date);
            CREATE INDEX IF NOT EXISTS idx_events_category ON market_events(category);
            CREATE INDEX IF NOT EXISTS idx_events_sentiment ON market_events(sentiment_score);

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL,
                data TEXT NOT NULL,
                read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, read);
        """)


def save_analysis(user_id: Optional[int], ticker: str, result: Dict[str, Any]) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO analyses (user_id, ticker, result_json) VALUES (?, ?, ?)",
            (user_id if user_id is not None else DEFAULT_USER_ID, ticker, json.dumps(result))
        )
        return cursor.lastrowid


def get_analysis_history(user_id: Optional[int], ticker: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    # `user_id = ?` with a bound NULL never matches in SQLite (three-valued
    # logic), so an omitted user_id used to come back empty rather than
    # falling back to the one user this single-user app actually has.
    uid = user_id if user_id is not None else DEFAULT_USER_ID
    with get_db() as conn:
        if ticker:
            rows = conn.execute(
                "SELECT * FROM analyses WHERE user_id = ? AND ticker = ? ORDER BY created_at DESC LIMIT ?",
                (uid, ticker, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (uid, limit)
            ).fetchall()
        return [dict(row) for row in rows]


def save_watchlist(user_id: int, name: str, tickers: List[str]) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO watchlists (user_id, name, tickers_json) VALUES (?, ?, ?)",
            (user_id, name, json.dumps(tickers))
        )
        return cursor.lastrowid


def get_watchlists(user_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM watchlists WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
        return [{**dict(row), 'tickers': json.loads(row['tickers_json'])} for row in rows]


def create_alert(user_id: int, ticker: str, condition_type: str, threshold: float) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO alerts (user_id, ticker, condition_type, threshold) VALUES (?, ?, ?, ?)",
            (user_id, ticker, condition_type, threshold)
        )
        return cursor.lastrowid


def get_active_alerts(ticker: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        if ticker:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE is_active = 1 AND ticker = ?",
                (ticker,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM alerts WHERE is_active = 1").fetchall()
        return [dict(row) for row in rows]


init_db()
