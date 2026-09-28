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
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(os.environ.get("AEON_INTEL_DB_PATH", str(Path.home() / ".aeon" / "intelligence.db")))

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
CREATE TABLE IF NOT EXISTS prediction_resolutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id TEXT,
    ticker TEXT NOT NULL,
    category TEXT,
    predicted_direction TEXT NOT NULL,
    confidence REAL,
    generated_at TEXT NOT NULL,
    timeframe_raw TEXT,
    resolve_at TEXT NOT NULL,
    resolved_at TEXT,
    entry_price REAL,
    exit_price REAL,
    actual_return_pct REAL,
    correct INTEGER
);
CREATE INDEX IF NOT EXISTS idx_pred_res_resolve ON prediction_resolutions(resolve_at, resolved_at);
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


def get_insider_trades_since(days: int = 90) -> Dict[str, Any]:
    """Real, persisted insider trades over a rolling window - not just whatever's in the
    current live batch. DISTINCT on content (not id/captured_at) dedups trades re-seen
    across refresh cycles, the same way real_data.py dedups within a single fetch."""
    empty_summary = {"window_days": days, "total_trades": 0, "buys": 0, "sells": 0,
                      "total_buy_value": 0.0, "total_sell_value": 0.0}
    try:
        cutoff = (datetime.now() - timedelta(days=days)).date().isoformat()
        with _conn() as conn:
            rows = conn.execute(
                """SELECT DISTINCT ticker, insider_name, role, transaction_type, total_value, shares, trade_date
                   FROM insider_trade_snapshots
                   WHERE trade_date >= ?
                   ORDER BY trade_date DESC""",
                (cutoff,),
            ).fetchall()
    except Exception as e:
        print(f"[history_db] get_insider_trades_since failed: {e}")
        return {"trades": [], "summary": empty_summary}

    trades = [
        {"ticker": r[0], "insider_name": r[1], "role": r[2], "transaction_type": r[3],
         "total_value": r[4], "shares": r[5], "date": r[6]}
        for r in rows
    ]
    buys = [t for t in trades if t["transaction_type"] == "BUY"]
    sells = [t for t in trades if t["transaction_type"] == "SELL"]
    return {
        "trades": trades,
        "summary": {
            "window_days": days,
            "total_trades": len(trades),
            "buys": len(buys),
            "sells": len(sells),
            "total_buy_value": sum(t["total_value"] or 0 for t in buys),
            "total_sell_value": sum(t["total_value"] or 0 for t in sells),
        },
    }


def save_pending_resolutions(rows: List[Dict[str, Any]]):
    """Insert one pending (unresolved) row per scoreable prediction - skips anything without
    a real entry_price, never guesses a starting price for the ones it can't fetch."""
    try:
        with _conn() as conn:
            for r in rows or []:
                if not r.get("ticker") or not r.get("entry_price") or not r.get("resolve_at"):
                    continue
                conn.execute(
                    """INSERT INTO prediction_resolutions
                       (prediction_id, ticker, category, predicted_direction, confidence,
                        generated_at, timeframe_raw, resolve_at, entry_price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (r.get("prediction_id"), r["ticker"], r.get("category"), r.get("predicted_direction"),
                     r.get("confidence"), r.get("generated_at", datetime.now().isoformat()),
                     r.get("timeframe_raw"), r["resolve_at"], r["entry_price"]),
                )
    except Exception as e:
        print(f"[history_db] save_pending_resolutions failed: {e}")


def resolve_due_predictions() -> int:
    """Grades every prediction whose resolve_at has passed against a real fetched price.
    Fails soft per-row: a pricing hiccup just leaves that row pending for the next cycle,
    never guesses a price to force a resolution."""
    import real_data

    now = datetime.now().isoformat()
    try:
        with _conn() as conn:
            due = conn.execute(
                """SELECT id, ticker, predicted_direction, entry_price FROM prediction_resolutions
                   WHERE resolve_at <= ? AND resolved_at IS NULL""",
                (now,),
            ).fetchall()
    except Exception as e:
        print(f"[history_db] resolve_due_predictions failed to read due rows: {e}")
        return 0

    resolved = 0
    for row_id, ticker, predicted_direction, entry_price in due:
        price = real_data.get_current_price(ticker)
        if price is None:
            continue
        actual_return_pct = round((price - entry_price) / entry_price * 100, 3) if entry_price else None
        if actual_return_pct is None:
            continue
        correct = 1 if (actual_return_pct > 0) == (predicted_direction == "bullish") else 0
        try:
            with _conn() as conn:
                conn.execute(
                    """UPDATE prediction_resolutions
                       SET resolved_at = ?, exit_price = ?, actual_return_pct = ?, correct = ?
                       WHERE id = ?""",
                    (now, price, actual_return_pct, correct, row_id),
                )
            resolved += 1
        except Exception as e:
            print(f"[history_db] resolve_due_predictions failed to write row {row_id}: {e}")
    return resolved


def get_calibration_stats(days: int = 30) -> Dict[str, Any]:
    """Real resolved-prediction accuracy/calibration - replaces prediction_engine.py's
    hardcoded zeros once at least one prediction has been graded against a real outcome."""
    empty = {"predictions_resolved": 0, "correct": 0, "accuracy": 0.0, "avg_confidence": 0.0,
             "calibration_score": 0.0, "by_category": {}}
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with _conn() as conn:
            rows = conn.execute(
                """SELECT category, confidence, correct FROM prediction_resolutions
                   WHERE generated_at >= ? AND resolved_at IS NOT NULL AND correct IS NOT NULL""",
                (cutoff,),
            ).fetchall()
    except Exception as e:
        print(f"[history_db] get_calibration_stats failed: {e}")
        return empty

    resolved = len(rows)
    if not resolved:
        return empty
    correct = sum(1 for _, _, c in rows if c)
    accuracy = round(correct / resolved, 3)
    avg_confidence = round(sum((conf or 0) for _, conf, _ in rows) / resolved, 3)
    calibration_score = round(1 - abs(avg_confidence - accuracy), 3)

    by_category: Dict[str, Dict[str, Any]] = {}
    for cat, _, c in rows:
        cat = cat or "uncategorized"
        entry = by_category.setdefault(cat, {"n": 0, "correct": 0})
        entry["n"] += 1
        entry["correct"] += 1 if c else 0
    for entry in by_category.values():
        entry["accuracy"] = round(entry["correct"] / entry["n"], 3) if entry["n"] else 0.0

    return {
        "predictions_resolved": resolved,
        "correct": correct,
        "accuracy": accuracy,
        "avg_confidence": avg_confidence,
        "calibration_score": calibration_score,
        "by_category": by_category,
    }


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
