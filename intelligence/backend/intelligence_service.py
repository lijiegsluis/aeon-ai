"""
Aeon Nimbus Intelligence - Dedicated Market Event Monitoring Service
Port: 8003 (8001 is TradingAgents in the Analysis terminal stack)
Purpose: Real-time event aggregation, countdown tracking, sentiment analysis
"""
import json
import os
import re
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import real_data
import history_db
import telegram_feed
import backtest_engine
import calendar_sync
import alpha_engine
import ai_engine
import alpha_data
from prediction_engine import generate_ai_predictions, generate_daily_brief

app = FastAPI(title="Aeon Nimbus Intelligence API", version="1.0.0")

_DEFAULT_ORIGINS = [
    "http://localhost:5175", "http://127.0.0.1:5175",
    # Aeon Analysis links into Intelligence (?ticker=) and reads its ticker lens
    "http://localhost:5173", "http://127.0.0.1:5173",
    "https://aeon-ai-1.onrender.com", "https://aeon-ai-2.onrender.com", "https://aeon-ai-3.onrender.com",
    "https://aeon-platform.onrender.com", "https://aeon-nimbus.onrender.com",
]
_EXTRA_ORIGINS = [o.strip() for o in os.environ.get("AEON_INTEL_ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEFAULT_ORIGINS + _EXTRA_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("AEON_INTEL_DB_PATH", os.path.expanduser("~/.aeon/intelligence.db"))

# ─── Database Setup ──────────────────────────────────────────
# NOTE: the `events` and `news_feed` schemas below match what's actually on
# disk (created long ago by calendar_sync.py's INSERT shape / an older
# service variant) — not the richer schema this file used to declare
# (event_date/category/affected_assets/source/...), which never matched the
# real table and made every query here raise "no such column" at request
# time. `economic_calendar` and `alert_rules` were already consistent.

@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.executescript("""
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
            );

            CREATE TABLE IF NOT EXISTS news_feed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                source TEXT,
                url TEXT,
                timestamp TEXT NOT NULL,
                affected_tickers TEXT,
                sentiment TEXT
            );

            CREATE TABLE IF NOT EXISTS economic_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country TEXT,
                event_date TEXT NOT NULL,
                event_time TEXT,
                previous_value TEXT,
                forecast_value TEXT,
                actual_value TEXT,
                importance INTEGER,
                affected_currencies TEXT,
                synced_at TEXT
            );

            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                event_category TEXT,
                min_days_before INTEGER,
                max_days_before INTEGER,
                assets_filter TEXT,
                notification_channels TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_feed(timestamp);
        """)
        # `source` separates hand-added events (kept forever) from calendar_sync's
        # seeded rows (rebuilt every sync). Older databases predate the column.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(events)")}
        if "source" not in cols:
            conn.execute("ALTER TABLE events ADD COLUMN source TEXT DEFAULT 'calendar'")
        # Earlier versions filled news_feed with invented headlines (credited to
        # Reuters/Bloomberg/CNBC, linked to example.com) whenever every RSS feed
        # failed. Remove any that were persisted.
        conn.execute("DELETE FROM news_feed WHERE url LIKE 'https://example.com/%'")
        conn.commit()

init_db()

# ─── Real data sync ──────────────────────────────────────────
# Pulls real_data.py's fetchers (RSS news, CNN Fear & Greed, VIX, SEC Form 4
# insider filings) into news_feed as regular rows, tagged with their real
# source — never 'demo'. Runs once at startup in a background thread so slow
# or timed-out network calls never delay the API from serving requests.
# Every fetch fails soft (returns None/[]) per real_data.py's own contract.

def sync_real_data():
    rows_to_add = []

    for item in real_data.get_real_news(limit=30):
        rows_to_add.append((
            item["title"], item["summary"], item["source"], item["url"],
            item["published_at"], item["tickers"], item["sentiment"],
        ))

    fear_greed = real_data.get_fear_greed()
    if fear_greed:
        rating_word = ("bullish" if fear_greed["value"] > 55
                        else "bearish" if fear_greed["value"] < 45 else "neutral")
        rows_to_add.append((
            f"Fear & Greed Index: {fear_greed['value']} ({fear_greed['rating']})",
            "CNN Fear & Greed Index reading", "Fear & Greed Index", "",
            datetime.now().isoformat(), "", rating_word,
        ))

    vix = real_data.get_vix()
    if vix is not None:
        rows_to_add.append((
            f"VIX: {vix}", "CBOE Volatility Index (VIX) latest close", "VIX Index", "",
            datetime.now().isoformat(), "", "bearish" if vix > 20 else "neutral",
        ))

    for t in real_data.get_recent_form4_trades(max_filings=8):
        if not t.get("issuer_ticker") or not t.get("total_value"):
            continue
        action = "buys" if t["is_buy"] else "sells"
        rows_to_add.append((
            f"{t['insider_name']} ({t['role']}) {action} {t['issuer_ticker']}",
            f"SEC Form 4: {t['insider_name']} {action} {t['shares']:,} shares of "
            f"{t['issuer_ticker']} (~${t['total_value']:,.0f}) at {t['issuer_name']}",
            "SEC Form 4", "", t.get("filed_at") or t["date"], t["issuer_ticker"],
            "bullish" if t["is_buy"] else "bearish",
        ))

    if not rows_to_add:
        print("[sync_real_data] no real data available this run (all sources failed soft)")
        return

    with get_db() as conn:
        existing_titles = {r[0] for r in conn.execute("SELECT title FROM news_feed").fetchall()}
        added = 0
        for title, content, source, url, timestamp, tickers, sentiment in rows_to_add:
            if title in existing_titles:
                continue
            conn.execute("""
                INSERT INTO news_feed (title, content, source, url, timestamp, affected_tickers, sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, content, source, url, timestamp, tickers, sentiment))
            existing_titles.add(title)
            added += 1
        conn.commit()

    print(f"[sync_real_data] added {added} real news_feed rows ({len(rows_to_add)} fetched)")

@app.on_event("startup")
def _start_real_data_sync():
    threading.Thread(target=sync_real_data, daemon=True).start()

_CALENDAR_RESEED_SECONDS = 6 * 60 * 60  # re-pull real per-ticker earnings dates every 6h so future D-X dates stay current

def _calendar_seed_loop():
    while True:
        try:
            calendar_sync.seed_calendar()
        except Exception as e:
            print(f"[calendar_sync] seed failed: {e}")
        time.sleep(_CALENDAR_RESEED_SECONDS)

@app.on_event("startup")
def _start_calendar_seed():
    threading.Thread(target=_calendar_seed_loop, daemon=True).start()

def _tickers(raw: Optional[str]) -> List[str]:
    """affected_tickers is stored as a plain comma-joined string, not JSON."""
    return [t.strip() for t in raw.split(",") if t.strip()] if raw else []

def _phase_for(days_until: int):
    if days_until <= 0:
        return "live", "#ef4444"
    if days_until <= 2:
        return "danger", "#ef4444"
    if days_until <= 9:
        return "euforia", "#f59e0b"
    if days_until <= 20:
        return "accumulation", "#10b981"
    return "pre-rumor", "#3b82f6"

def _entry_exit_note(phase: str, days_until: int) -> str:
    """Deterministic, rule-based entry/exit guidance from the real D-day + phase -
    never LLM-generated, so it's exactly as trustworthy as the underlying date."""
    label = phase.capitalize()
    if phase == "pre-rumor":
        return f"Watch (D-{days_until}, {label}). Accumulation window opens ~D-20."
    if phase == "accumulation":
        return f"Enter now (D-{days_until}, {label}). Exit D-1."
    if phase == "euforia":
        return f"Late entry only (D-{days_until}, {label}). Tight stops."
    if phase == "danger":
        return f"Danger zone (D-{days_until}). Avoid new entries; consider closing before the event."
    return f"Event live (D-{days_until})."

# ─── Real-data intelligence layer (ported from archive/populated_api.py) ────
# Powers /api/dashboard, /api/smart-money/notifications, /api/ai-predictions,
# and /api/telegram/breaking-news for the Intelligence.tsx frontend. One
# fully-fabricated feature from populated_api.py - the simulated
# /api/sources/status ("Simulate source status" per its own comment) - was
# initially dropped rather than relabeled or backfilled, then later rebuilt
# for real: /api/sources/status below is computed live from real_data's and
# telegram_feed's actual per-call success/failure counters, not randomized.
# The economic/earnings calendar (generate_market_events/generate_predicted_events
# in the old file) was also fabricated and dropped; it's since been rebuilt for
# real via calendar_sync.py, which seeds `events` from each source's actually
# published schedule (FOMC/NFP/CPI/PPI/ECB/BOJ) plus a real per-ticker earnings
# fetch, honestly falling back to a labeled "(estimated date)" placeholder only
# where no real schedule exists. Everything else below is either real (SEC
# Form 4, RSS news, CoinGecko, CNN Fear&Greed/VIX/Reddit, Telegram) or an
# empty when a real fetch fails - the previous real batch is kept, and nothing is
# ever invented to fill the gap.
#
# Unlike populated_api.py, these caches are populated in a background thread
# at startup rather than synchronously at import time, so slow SEC/RSS/LLM
# calls never block FastAPI from serving requests.

NEWS: List[Dict[str, Any]] = []
CRYPTO: List[Dict[str, Any]] = []
SENTIMENT: List[Dict[str, Any]] = []
INSIDER_TRADES: List[Dict[str, Any]] = []
SIGNALS: List[Dict[str, Any]] = []
SMART_MONEY_NOTIFICATIONS: Dict[str, Any] = {
    "past_filings": [], "future_expected": [], "total_past": 0, "total_future": 0,
}
AI_PREDICTIONS: Dict[str, Any] = {}
DAILY_BRIEF: Dict[str, Any] = {}


def generate_insider_trades():
    """Real SEC Form 4 open-market trades, plus whether this call fetched fresh data.
    When SEC is unreachable the previous real batch is returned unchanged (flag False,
    so it isn't re-persisted); nothing is ever invented."""
    real_trades = real_data.get_recent_form4_trades(max_filings=30)
    if not real_trades:
        # Keep whatever real trades we already have rather than inventing any.
        return INSIDER_TRADES, False

    ticker_map = real_data.get_sec_ticker_map()
    now = datetime.now()
    out = []

    for t in real_trades:
        ticker = t.get("issuer_ticker") or ticker_map.get(t["issuer_cik"], {}).get("ticker") or "N/A"
        total_value = t["total_value"]

        if total_value > 20_000_000:
            significance = "EXTREME"
        elif total_value > 10_000_000:
            significance = "HIGH"
        elif total_value > 3_000_000:
            significance = "MEDIUM"
        else:
            significance = "LOW"

        if t["is_buy"]:
            signal = (f"VERY BULLISH - {t['role']} accumulating large position" if significance == "EXTREME"
                       else f"BULLISH - {t['role']} insider buy" if significance == "HIGH"
                       else "Positive - insider accumulation")
        else:
            signal = "Large sale - monitor for reasons" if total_value > 15_000_000 else \
                     "Routine sale - may be diversification"

        try:
            trade_date = datetime.strptime(t["date"], "%Y-%m-%d")
            days_ago = max((now - trade_date).days, 0)
        except Exception:
            days_ago = 0

        out.append({
            "ticker": ticker,
            "insider_name": t.get("insider_name") or "Unknown",
            "role": t.get("role") or "Insider",
            "transaction_type": "BUY" if t["is_buy"] else "SELL",
            "shares": t["shares"],
            "price": round(t["price"], 2),
            "total_value": int(total_value),
            "date": t["date"],
            "filing_date": t.get("filed_at", t["date"]),
            "ownership_change": "N/A",
            "significance": significance,
            "smart_money_signal": signal,
            "days_ago": days_ago,
        })

    return sorted(out, key=lambda x: x["days_ago"]), True


def generate_smart_money_notifications():
    """Derive notification-shaped events from the real SEC Form 4 insider trade data,
    plus a small set of genuinely real recurring regulatory calendar facts."""
    now = datetime.now()
    top_trades = sorted(INSIDER_TRADES, key=lambda x: x.get("total_value", 0), reverse=True)[:9]

    past_filings = []
    for idx, t in enumerate(top_trades, start=1):
        try:
            trade_date = datetime.strptime(t["date"], "%Y-%m-%d")
        except Exception:
            trade_date = now
        days_ago = max((now - trade_date).days, 0)
        action = t["transaction_type"]
        verb = "BOUGHT" if action == "BUY" else "SOLD"
        past_filings.append({
            "id": idx,
            "type": "SEC Form 4 Filed",
            "ticker": t["ticker"],
            "title": f"{t['ticker']} {t['role']} {t['insider_name']} - {'Buy' if action == 'BUY' else 'Sale'} Filing",
            "message": (f"{t['insider_name']} filed Form 4: {verb} ${t['total_value']:,} "
                        f"({t['shares']:,} shares @ ${t['price']:.2f})."),
            "significance": t["significance"],
            "timestamp": trade_date.isoformat(),
            "days_ago": days_ago,
            "action": action,
            "value": t["total_value"],
        })

    # 13F-HR is due 45 days after each calendar quarter ends (SEC Rule 13f-1).
    quarter_ends = [datetime(y, m, d) for y in (now.year - 1, now.year, now.year + 1)
                    for m, d in ((3, 31), (6, 30), (9, 30), (12, 31))]
    deadline = min(q + timedelta(days=45) for q in quarter_ends if q + timedelta(days=45) >= now.replace(hour=0, minute=0))
    days_ahead = (deadline.date() - now.date()).days
    future_filings = [
        {
            "id": 100,
            "type": "13F Filing Deadline",
            "ticker": "ALL",
            "title": f"Quarterly 13F Filing Deadline - {deadline.strftime('%b %d, %Y')}",
            "message": ("Institutional managers with $100M+ must file 13F-HR within 45 days of quarter end - "
                        "hedge fund and fund-manager position disclosures cluster in the days before."),
            "significance": "MEDIUM",
            "timestamp": deadline.isoformat(),
            "days_ahead": days_ahead,
            "action": "WATCH",
            "expected": True,
        },
    ]

    return {
        "past_filings": past_filings,
        "future_expected": future_filings,
        "total_past": len(past_filings),
        "total_future": len(future_filings),
    }


def generate_news():
    """Real RSS-aggregated market news. If every feed fails, keep the last real batch -
    an empty feed is honest, invented headlines are not."""
    real_items = real_data.get_real_news(limit=30)
    if real_items:
        return [dict(item, id=idx + 1) for idx, item in enumerate(real_items)]
    return NEWS


def _all_news() -> List[Dict[str, Any]]:
    """NEWS (RSS) plus real live Telegram breaking-news messages, newest first."""
    # telegram_feed items carry no id of their own, so re-number the combined list -
    # otherwise every telegram-sourced row shares key=undefined in the frontend.
    combined = telegram_feed.get_recent(15) + NEWS
    return [dict(item, id=idx + 1) for idx, item in enumerate(combined)]


def generate_signals():
    """Real market-context opportunity detection. Each signal cites the specific real fact it's
    derived from (an insider cluster buy, a real tagged news item, a real sentiment/VIX extreme,
    or real crypto momentum) - no random tickers, phases, or prices. target_price/stop_loss are
    left null rather than fabricated, since there's no real price series fetched here to derive
    them honestly."""
    out: List[Dict[str, Any]] = []
    sid = 0
    now_iso = datetime.now().isoformat()

    # Alpha-engine trades first: each has an entry, stop, target and a backtested track record.
    seen_tickers = set()
    for a in alpha_engine.get_state().get("signals") or []:
        sid += 1
        out.append({
            "id": sid, "ticker": a["ticker"], "signal_type": a["strategy"], "phase": "ACCUMULATION",
            "entry_price": a["entry_price"], "target_price": a["target"], "stop_loss": a["stop"],
            "confidence": a["confidence"] if a["confidence"] is not None else 50.0,
            "reasoning": f"{a['strategy_name']}: {a['reason']}. Exit by {a['exit_date']}.",
            "trigger": a["strategy"], "generated_at": now_iso, "exit_date": a["exit_date"],
            "backtest_edge": a["backtest_edge"], "alpha": True,
        })
        seen_tickers.add(a["ticker"])

    buys = [t for t in INSIDER_TRADES if t["transaction_type"] == "BUY"]
    by_ticker: Dict[str, List[Dict[str, Any]]] = {}
    for t in buys:
        by_ticker.setdefault(t["ticker"], []).append(t)

    for ticker, trades in by_ticker.items():
        distinct_insiders = sorted({t["insider_name"] for t in trades})
        if len(distinct_insiders) >= 2:
            sid += 1
            total_value = sum(t["total_value"] for t in trades)
            out.append({
                "id": sid, "ticker": ticker, "signal_type": "insider_cluster_buy", "phase": "ACCUMULATION",
                "entry_price": trades[0]["price"], "target_price": None, "stop_loss": None,
                "confidence": round(min(60 + len(distinct_insiders) * 8, 90), 1),
                "reasoning": (f"{len(distinct_insiders)} distinct insiders ({', '.join(distinct_insiders)}) bought "
                              f"{ticker} for a combined ${total_value:,.0f} within days of each other - real SEC "
                              "Form 4 filings"),
                "trigger": "insider_cluster_buy", "generated_at": now_iso,
            })
            seen_tickers.add(ticker)

    for t in buys:
        if t["ticker"] in seen_tickers or t["significance"] not in ("HIGH", "EXTREME"):
            continue
        sid += 1
        out.append({
            "id": sid, "ticker": t["ticker"], "signal_type": "insider_buy", "phase": "ACCUMULATION",
            "entry_price": t["price"], "target_price": None, "stop_loss": None,
            "confidence": 75.0 if t["significance"] == "EXTREME" else 65.0,
            "reasoning": f"{t['role']} {t['insider_name']} bought ${t['total_value']:,.0f} of {t['ticker']} - real SEC Form 4 filing",
            "trigger": "insider_buy", "generated_at": now_iso,
        })
        seen_tickers.add(t["ticker"])

    for item in _all_news()[:30]:
        raw_tickers = item.get("tickers")
        if not raw_tickers or raw_tickers == "N/A" or item.get("sentiment") not in ("bullish", "bearish"):
            continue
        for ticker in [t.strip() for t in str(raw_tickers).split(",") if t.strip()][:2]:
            sid += 1
            out.append({
                "id": sid, "ticker": ticker, "signal_type": "news_catalyst",
                "phase": "EUFORIA" if item["sentiment"] == "bullish" else "DANGER",
                "entry_price": None, "target_price": None, "stop_loss": None,
                "confidence": 70.0 if item.get("urgency") == "breaking" else 55.0,
                "reasoning": f"{item['sentiment'].upper()} news: \"{item['title']}\" ({item['source']})",
                "trigger": "news_catalyst", "generated_at": now_iso,
            })

    for ind in SENTIMENT:
        if ind["indicator_name"] == "Fear & Greed" and (ind["value"] <= 20 or ind["value"] >= 80):
            sid += 1
            out.append({
                "id": sid, "ticker": "SPY", "signal_type": "sentiment_extreme",
                "phase": "ACCUMULATION" if ind["value"] <= 20 else "DANGER",
                "entry_price": None, "target_price": None, "stop_loss": None, "confidence": 60.0,
                "reasoning": f"CNN Fear & Greed at {ind['value']} ({ind['interpretation']}) - contrarian extreme reading",
                "trigger": "sentiment_extreme", "generated_at": now_iso,
            })
        if ind["indicator_name"] == "VIX" and ind["value"] >= 25:
            sid += 1
            out.append({
                "id": sid, "ticker": "VIX", "signal_type": "sentiment_extreme", "phase": "DANGER",
                "entry_price": ind["value"], "target_price": None, "stop_loss": None, "confidence": 55.0,
                "reasoning": f"VIX at {ind['value']} - elevated real volatility reading",
                "trigger": "sentiment_extreme", "generated_at": now_iso,
            })

    for c in CRYPTO:
        change = c.get("change_24h", 0) or 0
        if abs(change) >= 8:
            sid += 1
            out.append({
                "id": sid, "ticker": c["symbol"], "signal_type": "crypto_momentum",
                "phase": "EUFORIA" if change > 0 else "DANGER",
                "entry_price": round(c["price"], 2), "target_price": None, "stop_loss": None,
                "confidence": round(min(50 + abs(change), 85), 1),
                "reasoning": f"{c['name']} {'up' if change > 0 else 'down'} {abs(change)}% in 24h - real CoinGecko price",
                "trigger": "crypto_momentum", "generated_at": now_iso,
            })

    return sorted(out, key=lambda s: (not s.get("alpha"), -(s["confidence"] or 0)))[:30]


def generate_crypto():
    """Real CoinGecko prices; keeps the last real snapshot if CoinGecko is unreachable."""
    real_prices = real_data.get_crypto_prices()
    if real_prices:
        return real_prices
    return CRYPTO


def _fear_greed_label(value: int) -> str:
    if value >= 75:
        return "Extreme Greed"
    if value >= 55:
        return "Greed"
    if value >= 45:
        return "Neutral"
    if value >= 25:
        return "Fear"
    return "Extreme Fear"


def generate_sentiment():
    """Real Fear & Greed / Reddit / VIX readings. A source that can't be reached is
    simply left out (the Data Sources tab shows why) - never replaced by a random number."""
    indicators = []
    now_iso = datetime.now().isoformat()

    fg = real_data.get_fear_greed()
    if fg:
        value = fg["value"]
        indicators.append({
            "id": 1, "source": "CNN Fear & Greed Index", "timestamp": now_iso,
            "indicator_name": "Fear & Greed", "value": value,
            "interpretation": fg["rating"].title() if fg.get("rating") else _fear_greed_label(value),
            "affected_markets": "SPY,QQQ,DIA",
        })

    reddit = real_data.get_reddit_sentiment()
    if reddit:
        value = reddit["value"]
        indicators.append({
            "id": 2, "source": "Reddit Sentiment", "timestamp": now_iso,
            "indicator_name": "Social Sentiment", "value": value,
            "interpretation": "Very Bullish" if value >= 70 else "Bullish" if value >= 55 else
                              "Neutral" if value >= 40 else "Bearish",
            "affected_markets": "Meme stocks",
        })

    vix = real_data.get_vix()
    if vix is not None:
        indicators.append({
            "id": 3, "source": "CBOE", "timestamp": now_iso,
            "indicator_name": "VIX", "value": vix,
            "interpretation": "High volatility" if vix >= 25 else "Moderate volatility" if vix >= 18 else "Low volatility",
            "affected_markets": "SPY,QQQ,VIX",
        })

    return indicators or SENTIMENT


_SCREENER_UNIVERSE = sorted(set(real_data.WATCHLIST) | set(backtest_engine._TICKERS))


def _upcoming_events_for_context(days: int = 21, limit: int = 15) -> List[Dict[str, Any]]:
    """Real, dated catalysts from the same events table that powers /api/events/live -
    gives the LLM actual upcoming events instead of inferring 'key events today' from news."""
    end_date = datetime.now() + timedelta(days=days)
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM events
            WHERE date(date) BETWEEN date('now') AND date(?)
            ORDER BY date ASC
            LIMIT ?
        """, (end_date.date().isoformat(), limit)).fetchall()
    out = []
    for row in rows:
        event = dict(row)
        event_date = datetime.fromisoformat(event['date'])
        days_until = (event_date.date() - datetime.now().date()).days
        phase, _ = _phase_for(days_until)
        out.append({
            "title": event["title"],
            "date": event["date"],
            "days_until": days_until,
            "phase": phase,
            "affected_tickers": _tickers(event["affected_tickers"]),
        })
    return out


def _macro_context() -> Optional[Dict[str, Any]]:
    """Real Fed Funds context - CME futures-implied rate (always attempted, keyless) and/or
    the actual FRED target range/effective rate (only if FRED_API_KEY is set) - plus a best-effort
    real economic calendar from FRED releases/dates (key-gated) and investing.com (keyless,
    expected to legitimately come back down given its bot protection). Each sub-source is
    attempted independently so it registers in /api/sources/status even when it fails; omits
    the whole key if everything fails, never fabricates a placeholder."""
    macro: Dict[str, Any] = {}
    futures = real_data.get_fed_funds_futures()
    if futures:
        macro["fed_funds_futures_implied"] = futures
    fred_rate = real_data.get_fed_funds_rate()
    if fred_rate:
        macro["fed_funds_rate_fred"] = fred_rate
    fred_releases = real_data.get_economic_releases()
    if fred_releases:
        macro["economic_releases_fred"] = fred_releases
    investing_calendar = real_data.get_investing_economic_calendar()
    if investing_calendar:
        macro["economic_calendar_investing"] = investing_calendar
    return macro or None


def _screener_context(limit_tickers: int = 25) -> List[Dict[str, Any]]:
    """Real per-ticker scan over a fixed universe (real_data.WATCHLIST merged with
    backtest_engine's real backtest universe) - real price/move data cross-referenced against
    the real events table and the real in-memory news/insider trades, not more LLM prose."""
    universe = _SCREENER_UNIVERSE[:limit_tickers]
    snapshot = real_data.get_screener_snapshot(universe)
    if not snapshot:
        return []

    with get_db() as conn:
        event_rows = conn.execute("""
            SELECT affected_tickers, date FROM events
            WHERE date(date) >= date('now')
            ORDER BY date ASC
        """).fetchall()
    next_event_by_ticker: Dict[str, int] = {}
    for row in event_rows:
        event_date = datetime.fromisoformat(row["date"]).date()
        for t in _tickers(row["affected_tickers"]):
            if t not in next_event_by_ticker:
                next_event_by_ticker[t] = (event_date - datetime.now().date()).days

    news_tickers = set()
    for n in _all_news()[:50]:
        news_tickers.update(_tickers(n.get("tickers", "")))
    insider_tickers = {t.get("ticker") for t in INSIDER_TRADES if t.get("ticker")}

    return [
        {
            **row,
            "days_to_next_event": next_event_by_ticker.get(row["ticker"]),
            "recent_news_activity": row["ticker"] in news_tickers,
            "recent_insider_activity": row["ticker"] in insider_tickers,
        }
        for row in snapshot
    ]


def _build_ai_context() -> Dict[str, Any]:
    """Compact real-data context passed to the LLM for grounded predictions/daily brief."""
    top_news = sorted(_all_news(), key=lambda x: x["published_at"], reverse=True)[:12]
    top_insider_trades = sorted(INSIDER_TRADES, key=lambda x: x.get("total_value", 0), reverse=True)[:10]
    context: Dict[str, Any] = {
        "news": [{"title": n["title"], "sentiment": n["sentiment"], "tickers": n["tickers"],
                  "summary": n["summary"]} for n in top_news],
        "telegram_breaking_news": [{"title": m["title"], "summary": m["summary"]}
                                     for m in telegram_feed.get_recent(8)],
        "insider_trades": [{"ticker": t["ticker"], "insider_name": t["insider_name"], "role": t["role"],
                             "transaction_type": t["transaction_type"], "total_value": t["total_value"],
                             "shares": t["shares"], "date": t["date"]} for t in top_insider_trades],
        "sentiment": SENTIMENT,
        "crypto": CRYPTO,
    }
    try:
        st = alpha_engine.get_state()
        context["alpha"] = {
            "signals": st.get("signals") or [],
            "strategies": {k: {kk: vv for kk, vv in v.items() if kk != "events"}
                           for k, v in (st.get("backtests") or {}).items()},
        }
    except Exception as e:
        print(f"[ai_context] alpha failed, omitting: {e}")
    try:
        context["upcoming_events"] = _upcoming_events_for_context()
    except Exception as e:
        print(f"[ai_context] upcoming_events failed, omitting: {e}")
    try:
        macro = _macro_context()
        if macro:
            context["macro"] = macro
    except Exception as e:
        print(f"[ai_context] macro failed, omitting: {e}")
    try:
        screener = _screener_context()
        if screener:
            context["screener"] = screener
    except Exception as e:
        print(f"[ai_context] screener failed, omitting: {e}")
    return context


_DIRECTIONAL_CATEGORIES = ["high_confidence_predictions", "pattern_based_predictions",
                           "causal_predictions", "contrarian_predictions"]
# black_swan_monitors are risk monitors (probability of a scenario), not directional
# bullish/bearish calls, so they're excluded from resolution scoring.


def _parse_resolve_at(timeframe: Optional[str], generated_at: datetime) -> str:
    """Best-effort parse of a free-text timeframe like '2 weeks' or '30 days' into a real
    resolve-by date. Defaults to the engine's own 30-day prediction horizon when unparseable."""
    if timeframe:
        m = re.search(r"(\d+)\s*(day|week|month)", timeframe.lower())
        if m:
            n, unit = int(m.group(1)), m.group(2)
            days = n if unit == "day" else n * 7 if unit == "week" else n * 30
            return (generated_at + timedelta(days=days)).isoformat()
    return (generated_at + timedelta(days=30)).isoformat()


def _build_pending_resolutions(predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Turns each scoreable live prediction into a pending resolution row - skips anything
    without a ticker, a clear bullish/bearish direction (via real_data's own keyword
    classifier), or a real fetchable current price. Never scores demo/illustrative
    predictions as if they were real calls."""
    if (predictions.get("meta") or {}).get("mode") not in ("live", "rules"):
        return []

    now = datetime.now()
    rows = []
    for category in _DIRECTIONAL_CATEGORIES:
        for item in predictions.get(category) or []:
            ticker = item.get("ticker")
            if not ticker:
                continue
            text = " ".join(str(item.get(k, "")) for k in ("action", "prediction", "reasoning"))
            direction = item.get("direction") or real_data._classify_sentiment(text)
            if direction == "neutral":
                continue
            entry_price = real_data.get_current_price(ticker)
            if entry_price is None:
                continue
            rows.append({
                "prediction_id": item.get("prediction_id"),
                "ticker": ticker,
                "category": category,
                "predicted_direction": direction,
                "confidence": item.get("confidence"),
                "generated_at": now.isoformat(),
                "timeframe_raw": item.get("timeframe"),
                "resolve_at": _parse_resolve_at(item.get("timeframe"), now),
                "entry_price": entry_price,
            })
    return rows


def _persist_and_annotate_predictions(predictions: Dict[str, Any]) -> Dict[str, Any]:
    """Save a snapshot to the real persistent history, then reflect the real
    accumulated count back into the response instead of a permanent 0."""
    history_db.save_prediction_snapshot(predictions)
    real_count = history_db.get_predictions_made_count(days=30)
    predictions["prediction_accuracy_stats"]["last_30_days"]["predictions_made"] = real_count

    pending = _build_pending_resolutions(predictions)
    if pending:
        history_db.save_pending_resolutions(pending)

    return predictions


def _backtest_by_category(backtest: dict) -> dict:
    """Flattens the real backtest's per-signal/per-horizon results into the {accuracy, n} shape
    prediction_accuracy_stats.by_category renders - the real evidence behind the accuracy claim."""
    out = {}
    for sig_name, sig in (backtest.get("signals") or {}).items():
        for horizon, stats in (sig.get("by_horizon") or {}).items():
            if stats.get("signals_tested"):
                out[f"{sig_name}_{horizon}"] = {
                    "accuracy": round((stats["pct_positive"] or 0) / 100, 3),
                    "n": stats["signals_tested"],
                }
    return out


def _populate_intel_data():
    """Runs once in a background thread at startup: populates all module-level
    caches above from real sources (empty where a source is unreachable), in dependency order."""
    global NEWS, CRYPTO, SENTIMENT, INSIDER_TRADES, SIGNALS, SMART_MONEY_NOTIFICATIONS
    global AI_PREDICTIONS, DAILY_BRIEF

    try:
        history_db.init()
        NEWS = generate_news()
        CRYPTO = generate_crypto()
        SENTIMENT = generate_sentiment()
        INSIDER_TRADES, insider_trades_are_real = generate_insider_trades()
        SIGNALS = generate_signals()
        SMART_MONEY_NOTIFICATIONS = generate_smart_money_notifications()

        context = _build_ai_context()
        AI_PREDICTIONS = _persist_and_annotate_predictions(generate_ai_predictions(context))
        DAILY_BRIEF = generate_daily_brief(context)

        history_db.save_daily_brief(DAILY_BRIEF)
        history_db.save_sentiment_snapshot(SENTIMENT)
        history_db.save_news_items(NEWS)
        if insider_trades_are_real:
            history_db.save_insider_trades(INSIDER_TRADES)
        print("[intel_data] initial population complete")
    except Exception as e:
        print(f"[intel_data] initial population failed, keeping honest empty defaults: {e}")


_FAST_REFRESH_SECONDS = 600   # ~10 min: news / sentiment / crypto / signals
_SLOW_REFRESH_TICKS = 3       # every 3rd fast tick (~30 min): insider trades + AI predictions/brief


def _refresh_intel_fast():
    global NEWS, SENTIMENT, CRYPTO, SIGNALS
    try:
        NEWS = generate_news()
        history_db.save_news_items(NEWS)
    except Exception as e:
        print(f"[intel_refresh] news refresh failed, keeping last-known-good: {e}")
    try:
        SENTIMENT = generate_sentiment()
        history_db.save_sentiment_snapshot(SENTIMENT)
    except Exception as e:
        print(f"[intel_refresh] sentiment refresh failed, keeping last-known-good: {e}")
    try:
        CRYPTO = generate_crypto()
    except Exception as e:
        print(f"[intel_refresh] crypto refresh failed, keeping last-known-good: {e}")
    try:
        SIGNALS = generate_signals()
    except Exception as e:
        print(f"[intel_refresh] signals refresh failed, keeping last-known-good: {e}")


def _refresh_intel_slow():
    global INSIDER_TRADES, SMART_MONEY_NOTIFICATIONS, AI_PREDICTIONS, DAILY_BRIEF, SIGNALS
    try:
        INSIDER_TRADES, insider_trades_are_real = generate_insider_trades()
        SMART_MONEY_NOTIFICATIONS = generate_smart_money_notifications()
        if insider_trades_are_real:
            history_db.save_insider_trades(INSIDER_TRADES)
        SIGNALS = generate_signals()
    except Exception as e:
        print(f"[intel_refresh] insider trades refresh failed, keeping last-known-good: {e}")
    try:
        context = _build_ai_context()
        AI_PREDICTIONS = _persist_and_annotate_predictions(generate_ai_predictions(context))
        DAILY_BRIEF = generate_daily_brief(context)
        history_db.save_daily_brief(DAILY_BRIEF)
    except Exception as e:
        print(f"[intel_refresh] AI predictions/brief refresh failed, keeping last-known-good: {e}")
    try:
        resolved = history_db.resolve_due_predictions()
        if resolved:
            print(f"[intel_refresh] resolved {resolved} due prediction(s) against real prices")
    except Exception as e:
        print(f"[intel_refresh] prediction resolution pass failed: {e}")


def _intel_refresh_loop():
    tick = 0
    while True:
        time.sleep(_FAST_REFRESH_SECONDS)
        tick += 1
        _refresh_intel_fast()
        if tick % _SLOW_REFRESH_TICKS == 0:
            _refresh_intel_slow()


@app.on_event("startup")
def _start_intel_data():
    def _init_then_loop():
        _populate_intel_data()
        _intel_refresh_loop()
    threading.Thread(target=_init_then_loop, daemon=True).start()
    try:
        telegram_feed.start_background(
            on_new_message=lambda item: history_db.save_news_items([item])
        )
    except Exception as e:
        print(f"[telegram_feed] failed to start: {e}")
    try:
        backtest_engine.start_background()
    except Exception as e:
        print(f"[backtest_engine] failed to start: {e}")
    def _rebuild_rules_outputs():
        # LLM runs stay on their own (rate-limited) schedule; rule-based outputs are cheap,
        # so rebuild them as soon as the alpha engine has new signals.
        global AI_PREDICTIONS, DAILY_BRIEF
        if ai_engine.available():
            return
        context = _build_ai_context()
        AI_PREDICTIONS = _persist_and_annotate_predictions(generate_ai_predictions(context))
        DAILY_BRIEF = generate_daily_brief(context)
        history_db.save_daily_brief(DAILY_BRIEF)

    alpha_engine.on_refresh.append(_rebuild_rules_outputs)
    try:
        alpha_engine.start_background()
    except Exception as e:
        print(f"[alpha_engine] failed to start: {e}")

# ─── Request/Response Models ─────────────────────────────────

class CreateEventRequest(BaseModel):
    title: str
    event_type: str
    date: str
    description: Optional[str] = None
    affected_tickers: Optional[List[str]] = None
    impact_score: Optional[float] = None

class AlertRuleRequest(BaseModel):
    event_category: Optional[str] = None
    min_days_before: int
    max_days_before: int
    assets_filter: Optional[List[str]] = None
    notification_channels: List[str] = ["push"]

# ─── Core API Endpoints ──────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "service": "aeon-intelligence", "version": "1.0.0"}

@app.get("/api/events/live")
def get_live_events(timeframe: str = "30days"):
    """Get all events within timeframe with D-X countdown"""

    days = {"7days": 7, "30days": 30, "90days": 90}.get(timeframe, 30)
    end_date = datetime.now() + timedelta(days=days)

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM events
            WHERE date(date) BETWEEN date('now') AND date(?)
            ORDER BY date ASC
        """, (end_date.date().isoformat(),)).fetchall()

        events = []
        for row in rows:
            event = dict(row)
            event_date = datetime.fromisoformat(event['date'])
            days_until = (event_date.date() - datetime.now().date()).days
            phase, phase_color = _phase_for(days_until)

            event['days_until'] = days_until
            event['phase'] = phase
            event['phase_color'] = phase_color
            event['recommendation'] = _entry_exit_note(phase, days_until)
            event['affected_tickers'] = _tickers(event['affected_tickers'])

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

@app.get("/api/events/{event_id}")
def get_event_detail(event_id: int):
    """Get detailed analysis of single event"""

    with get_db() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")

        event = dict(row)
        event_date = datetime.fromisoformat(event['date'])
        days_until = (event_date.date() - datetime.now().date()).days

        event['days_until'] = days_until
        tickers = _tickers(event['affected_tickers'])
        event['affected_tickers'] = tickers

        # Related news: no FK between events and news_feed in the real schema,
        # so match on ticker overlap instead.
        related_news = []
        if tickers:
            like_clauses = " OR ".join(["affected_tickers LIKE ?"] * len(tickers))
            news_rows = conn.execute(f"""
                SELECT * FROM news_feed
                WHERE {like_clauses}
                ORDER BY timestamp DESC
                LIMIT 10
            """, tuple(f"%{t}%" for t in tickers)).fetchall()
            related_news = [dict(n) for n in news_rows]

        event['related_news'] = related_news

        # Calculate phase progress
        if days_until <= 0:
            phase_progress = 100
        elif days_until <= 2:
            phase_progress = 90 + (days_until * 5)
        elif days_until <= 9:
            phase_progress = 50 + ((9 - days_until) * 5)
        elif days_until <= 20:
            phase_progress = 20 + ((20 - days_until) * 3)
        else:
            phase_progress = max(0, 20 - (days_until - 20))

        event['phase_progress'] = phase_progress

        return event

@app.post("/api/events")
def create_event(req: CreateEventRequest):
    """Create new event (manual or from data source)"""

    with get_db() as conn:
        try:
            datetime.fromisoformat(req.date)
        except ValueError:
            raise HTTPException(422, "date must be ISO format, e.g. 2026-10-28 or 2026-10-28T14:00")
        cursor = conn.execute("""
            INSERT INTO events
            (title, description, date, event_type, affected_tickers, impact_score, source)
            VALUES (?, ?, ?, ?, ?, ?, 'manual')
        """, (
            req.title,
            req.description,
            req.date,
            req.event_type,
            ",".join(t.strip().upper() for t in req.affected_tickers if t.strip()) if req.affected_tickers else None,
            req.impact_score,
        ))
        conn.commit()
        event_id = cursor.lastrowid

    return {"id": event_id, "status": "created"}

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int):
    """Delete a hand-added event. Calendar-seeded events are rebuilt on every sync,
    so they can't be deleted here."""
    with get_db() as conn:
        row = conn.execute("SELECT source FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")
        if (row["source"] or "calendar") != "manual":
            raise HTTPException(409, "Only manually added events can be deleted")
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
    return {"status": "deleted"}

@app.get("/api/news/feed")
def get_news_feed(limit: int = 50):
    """Get raw news feed from all sources"""

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM news_feed
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return {"feed": [dict(r) for r in rows], "count": len(rows)}

@app.post("/api/news/feed")
def add_news_item(source: str, message: str, title: Optional[str] = None, url: Optional[str] = None):
    """Add news item to feed (called by Telegram monitor or a fetcher)"""

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO news_feed (title, content, source, url, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (title or message[:80], message, source, url, datetime.now().isoformat()))
        conn.commit()
        news_id = cursor.lastrowid

    return {"id": news_id, "status": "added"}

@app.get("/api/calendar")
def get_calendar(view: str = "month"):
    """Get calendar view of events"""

    days = {"week": 7, "month": 30}.get(view, 90)
    end_date = datetime.now() + timedelta(days=days)

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM events
            WHERE date(date) BETWEEN date('now') AND date(?)
            ORDER BY date ASC
        """, (end_date.date().isoformat(),)).fetchall()

        # Group by date
        calendar = {}
        for row in rows:
            event = dict(row)
            date_key = event['date']
            if date_key not in calendar:
                calendar[date_key] = []

            event_date = datetime.fromisoformat(event['date'])
            days_until = (event_date.date() - datetime.now().date()).days
            phase, phase_color = _phase_for(days_until)
            event['days_until'] = days_until
            event['phase'] = phase
            event['phase_color'] = phase_color
            event['recommendation'] = _entry_exit_note(phase, days_until)
            event['affected_tickers'] = _tickers(event['affected_tickers'])
            calendar[date_key].append(event)

    return {"view": view, "calendar": calendar}

@app.post("/api/alerts")
def create_alert_rule(req: AlertRuleRequest):
    """Create alert rule for event notifications"""

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO alert_rules
            (event_category, min_days_before, max_days_before, assets_filter, notification_channels, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            req.event_category,
            req.min_days_before,
            req.max_days_before,
            json.dumps(req.assets_filter) if req.assets_filter else None,
            json.dumps(req.notification_channels),
            datetime.now().isoformat()
        ))
        conn.commit()
        alert_id = cursor.lastrowid

    return {"id": alert_id, "status": "created"}

@app.get("/api/alerts")
def list_alert_rules():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM alert_rules WHERE is_active = 1 ORDER BY id DESC").fetchall()
    rules = []
    for r in rows:
        rule = dict(r)
        rule["assets_filter"] = json.loads(rule["assets_filter"]) if rule.get("assets_filter") else None
        rule["notification_channels"] = json.loads(rule["notification_channels"]) if rule.get("notification_channels") else []
        rules.append(rule)
    return {"rules": rules}

@app.delete("/api/alerts/{rule_id}")
def delete_alert_rule(rule_id: int):
    with get_db() as conn:
        cur = conn.execute("UPDATE alert_rules SET is_active = 0 WHERE id = ?", (rule_id,))
        conn.commit()
    if not cur.rowcount:
        raise HTTPException(404, "Alert rule not found")
    return {"status": "deleted"}

@app.get("/api/alerts/triggered")
def get_triggered_alerts():
    """Events matching each active rule's day window, category and ticker filter."""

    with get_db() as conn:
        rules = conn.execute("SELECT * FROM alert_rules WHERE is_active = 1").fetchall()

        triggered = []
        for rule in rules:
            rule_dict = dict(rule)
            category = rule_dict.get("event_category")
            assets = {a.upper() for a in json.loads(rule_dict["assets_filter"])} if rule_dict.get("assets_filter") else None

            events = conn.execute("""
                SELECT * FROM events
                WHERE date(date) BETWEEN date('now', ? || ' days') AND date('now', ? || ' days')
                ORDER BY date ASC
            """, (f"+{rule_dict['min_days_before']}", f"+{rule_dict['max_days_before']}")).fetchall()

            for event in events:
                event_dict = dict(event)
                if category and category != "all" and event_dict.get("event_type") != category:
                    continue
                tickers = set(_tickers(event_dict.get("affected_tickers")))
                if assets and not (assets & tickers):
                    continue
                days_until = (datetime.fromisoformat(event_dict['date']).date() - datetime.now().date()).days
                event_dict["affected_tickers"] = sorted(tickers)
                triggered.append({
                    "rule_id": rule_dict['id'],
                    "event": event_dict,
                    "days_until": days_until,
                    "message": f"{event_dict['title']} in {days_until} day{'s' if days_until != 1 else ''}"
                })

    return {"triggered": triggered, "count": len(triggered)}

@app.get("/api/stats")
def get_stats():
    """Get dashboard statistics"""

    with get_db() as conn:
        total_events = conn.execute("SELECT COUNT(*) as cnt FROM events").fetchone()['cnt']
        upcoming_7d = conn.execute("""
            SELECT COUNT(*) as cnt FROM events
            WHERE date(date) BETWEEN date('now') AND date('now', '+7 days')
        """).fetchone()['cnt']
        total_news = conn.execute("SELECT COUNT(*) as cnt FROM news_feed").fetchone()['cnt']

        return {
            "total_events": total_events,
            "upcoming_7days": upcoming_7d,
            "total_news_items": total_news,
        }

@app.get("/api/dashboard")
def get_intel_dashboard():
    """Real-data intelligence dashboard for Intelligence.tsx. Calendar/events live under
    /api/events/live and /api/calendar; source status under /api/sources/status; the
    90-day insider tracker under /api/insider-trades; VIX/sentiment aggregate under
    /api/volatility - all real, none of them the old fabricated populated_api.py generators."""
    return {
        "news": _all_news()[:20],
        "signals": generate_signals(),  # cheap and in-memory; always reflects the latest alpha run
        "crypto": CRYPTO,
        "sentiment": SENTIMENT,
        "insider_trades": INSIDER_TRADES,
        "daily_brief": DAILY_BRIEF,
        "last_update": datetime.now().isoformat(),
    }

@app.get("/api/smart-money/notifications")
def get_smart_money_notifications_endpoint():
    """Past 7 days of Smart Money Flow notifications + future expected filings."""
    return {
        "notifications": SMART_MONEY_NOTIFICATIONS,
        "source": "Smart Money Flow",
        "description": "Upcoming public regulatory disclosure deadlines (e.g. 13F). Past filings are the same real SEC Form 4 data shown on the Insider Trading tab.",
        "last_update": datetime.now().isoformat(),
    }

@app.get("/api/ai-predictions")
def get_ai_predictions_endpoint():
    """AI-powered market predictions (cached; refreshed on the slow background cycle).
    prediction_accuracy_stats.last_30_days is overwritten with real resolved-prediction
    numbers once at least one live prediction has been graded against a real fetched price
    (history_db.get_calibration_stats) - before that it keeps the honest hardcoded 0s from
    prediction_engine.py. by_category is populated from the real historical backtest of the
    underlying insider-buy signal - a different, real thing from the live-prediction
    calibration above, so it's kept under its own live_prediction_by_category key instead
    of overwriting by_category's backtest-signal semantics."""
    backtest = backtest_engine.get_cached_backtest()
    result = dict(AI_PREDICTIONS)
    stats = dict(result.get("prediction_accuracy_stats") or {})
    last_30 = dict(stats.get("last_30_days") or {})

    calibration = history_db.get_calibration_stats(days=30)
    if calibration["predictions_resolved"]:
        last_30["predictions_resolved"] = calibration["predictions_resolved"]
        last_30["correct"] = calibration["correct"]
        last_30["accuracy"] = calibration["accuracy"]
        last_30["avg_confidence"] = calibration["avg_confidence"]
        last_30["calibration_score"] = calibration["calibration_score"]
        stats["live_prediction_by_category"] = calibration["by_category"]
    stats["last_30_days"] = last_30

    by_cat: Dict[str, Any] = {}
    # alpha-engine strategies: every rule-based prediction is one of these signals, so their
    # one-year backtests (excess return vs the S&P 500) are the direct evidence behind them
    for key, bt in (alpha_engine.get_state().get("backtests") or {}).items():
        if bt.get("n"):
            by_cat[bt.get("name", key)] = {"accuracy": (bt.get("win_rate") or 0) / 100, "n": bt["n"],
                                          "avg_excess_pct": bt.get("avg_excess_pct"), "t_stat": bt.get("t_stat"),
                                          "edge": bool(bt.get("edge")), "basis": "beat_spy"}
    if backtest.get("signals"):
        by_cat.update(_backtest_by_category(backtest))
    if by_cat:
        stats["by_category"] = by_cat
        stats["model_improvements"] = ([
            f"{calibration['predictions_resolved']} live prediction(s) resolved against real prices in the last "
            "30 days - see the live column for real accuracy and calibration."
        ] if calibration["predictions_resolved"] else [
            "No live prediction has reached its horizon yet, so there is no graded live record. Every open "
            "prediction is graded automatically against the real price on its target date."
        ]) + [
            "By-category figures are real historical backtests of the signals behind the predictions: alpha "
            "strategies are scored as % of events that beat the S&P 500 over the same window; the Form 4 "
            "insider-buy study below is scored as % of events with a positive return.",
            "The Alpha tab carries each strategy's full evidence and a forward paper-trading record.",
        ]
    result["prediction_accuracy_stats"] = stats
    result["historical_backtest"] = backtest
    return result

@app.get("/api/sources/status")
def get_sources_status():
    """Real per-source status, computed live from actual call outcomes this process has
    made this run - never randomized or backfilled (unlike populated_api.py's old simulated
    'Simulate source status' version, which this replaces for real)."""
    sources = []
    for name, entry in real_data.get_source_status().items():
        sources.append({"name": name, "category": "market_data", **entry})

    telegram_status = telegram_feed.get_status()
    sources.append({
        "name": "Telegram: Breaking News",
        "category": "news",
        "status": "active" if telegram_status.get("connected") else (
            "degraded" if telegram_status.get("message_count") else "down"),
        "success_rate": None,
        **telegram_status,
    })

    active_now = sum(1 for s in sources if s.get("status") == "active")
    rates = [s["success_rate"] for s in sources if s.get("success_rate") is not None]
    avg_success_rate = round(sum(rates) / len(rates), 3) if rates else None

    return {
        "sources": sources,
        "summary": {
            "total_sources": len(sources),
            "active_now": active_now,
            "avg_success_rate": avg_success_rate,
        },
        "last_update": datetime.now().isoformat(),
    }

@app.get("/api/insider-trades")
def get_insider_trades_endpoint(days: int = 90):
    """Real, persisted rolling window of SEC Form 4 trades - not just whatever's in the
    current live batch. Backed by insider_trade_snapshots, which only ever receives
    genuinely real trades (see generate_insider_trades()'s is_real flag)."""
    data = history_db.get_insider_trades_since(days=days)
    return {**data, "last_update": datetime.now().isoformat()}

@app.get("/api/volatility")
def get_volatility_endpoint():
    """Real VIX + Fear & Greed + Reddit sentiment together, plus real upcoming
    high-phase (danger/euforia) calendar events as volatility catalysts - replaces the old
    fabricated impact_score-threshold event filter with the real D-X/phase system."""
    vix = real_data.get_vix()
    vix_bucket = ("Extreme" if vix is not None and vix >= 30 else
                  "High" if vix is not None and vix >= 25 else
                  "Moderate" if vix is not None and vix >= 18 else
                  "Low" if vix is not None else "Unknown")
    fear_greed = real_data.get_fear_greed()
    reddit = real_data.get_reddit_sentiment()

    end_date = datetime.now() + timedelta(days=30)
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM events
            WHERE date(date) BETWEEN date('now') AND date(?)
            ORDER BY date ASC
        """, (end_date.date().isoformat(),)).fetchall()

    catalysts = []
    for row in rows:
        event = dict(row)
        event_date = datetime.fromisoformat(event['date'])
        days_until = (event_date.date() - datetime.now().date()).days
        phase, phase_color = _phase_for(days_until)
        if phase not in ("danger", "euforia"):
            continue
        event['days_until'] = days_until
        event['phase'] = phase
        event['phase_color'] = phase_color
        event['recommendation'] = _entry_exit_note(phase, days_until)
        event['affected_tickers'] = _tickers(event['affected_tickers'])
        catalysts.append(event)

    return {
        "vix": {"value": vix, "bucket": vix_bucket},
        "fear_greed": fear_greed,
        "reddit_sentiment": reddit,
        "volatility_catalysts": catalysts,
        "last_update": datetime.now().isoformat(),
    }

@app.get("/api/alpha")
def get_alpha():
    """Live alpha signals, each strategy's backtest vs the S&P 500, and the forward
    paper-trading record built from every signal the engine has issued."""
    state = alpha_engine.get_state()
    try:
        book = alpha_engine.portfolio(alpha_data.price_history)
    except Exception as e:
        book = {"open": [], "closed": [], "stats": {}, "equity": [], "error": str(e)[:200]}
    strategies = {}
    for key, meta in alpha_engine.STRATEGIES.items():
        bt = (state.get("backtests") or {}).get(key) or {}
        strategies[key] = {**meta, **{k: v for k, v in bt.items() if k != "events"}, "sample_events": (bt.get("events") or [])[:12]}
    return {
        "status": state.get("status"),
        "generated_at": state.get("generated_at"),
        "backtested_at": state.get("backtested_at"),
        "errors": state.get("errors"),
        "signals": state.get("signals") or [],
        "strategies": strategies,
        "portfolio": book,
        "disclaimer": ("Rule-based research signals with their historical evidence, not investment advice. "
                       "Backtests use one year of events with overlapping windows and no trading costs."),
    }


@app.get("/api/alpha/strategy/{key}")
def get_alpha_strategy(key: str):
    state = alpha_engine.get_state()
    bt = (state.get("backtests") or {}).get(key)
    if key not in alpha_engine.STRATEGIES:
        raise HTTPException(404, "unknown strategy")
    return {"key": key, **alpha_engine.STRATEGIES[key], **(bt or {"events": []})}


_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-^=]{1,12}$")


def _timing_verdict(next_event: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """One-line timing read for a ticker from its nearest dated catalyst - the same
    rule-based phase system as the calendar, so it's exactly as reliable as the date."""
    if not next_event:
        return {"phase": None, "headline": "No dated catalyst in the next 90 days",
                "detail": "Nothing on the calendar is tagged with this ticker, so there is no event to time around.",
                "estimated_date": False}
    phase, days = next_event["phase"], next_event["days_until"]
    title = next_event["title"]
    headline = {
        "pre-rumor": f"Too early - {title} is D-{days}",
        "accumulation": f"Accumulation window - {title} is D-{days}",
        "euforia": f"Late - {title} is D-{days}",
        "danger": f"Danger zone - {title} is D-{days}",
        "live": f"{title} is today",
    }.get(phase, f"{title} is D-{days}")
    return {"phase": phase, "headline": headline, "detail": next_event["recommendation"],
            "estimated_date": "estimated date" in title.lower()}


@app.get("/api/ticker/{symbol}")
def get_ticker_lens(symbol: str):
    """Everything Intelligence knows about one ticker: dated catalysts with D-X phase,
    news and Telegram mentions, 90-day insider trades, live signals, AI calls, and the
    latest price. Built entirely from data the other endpoints already serve."""
    tk = symbol.strip().upper()
    if not _SYMBOL_RE.match(tk):
        raise HTTPException(400, "invalid ticker")

    end_date = datetime.now() + timedelta(days=90)
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM events
            WHERE date(date) BETWEEN date('now') AND date(?)
            ORDER BY date ASC
        """, (end_date.date().isoformat(),)).fetchall()
        stored_news = conn.execute("""
            SELECT title, content, source, url, timestamp, affected_tickers, sentiment FROM news_feed
            WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT 500
        """, ((datetime.now() - timedelta(days=30)).isoformat(),)).fetchall()

    events = []
    for row in rows:
        event = dict(row)
        tickers = _tickers(event["affected_tickers"])
        if tk not in tickers:
            continue
        days_until = (datetime.fromisoformat(event["date"]).date() - datetime.now().date()).days
        phase, color = _phase_for(days_until)
        event.update(affected_tickers=tickers, days_until=days_until, phase=phase, phase_color=color,
                     recommendation=_entry_exit_note(phase, days_until))
        events.append(event)

    word = re.compile(rf"(?<![A-Z0-9]){re.escape(tk)}(?![A-Z0-9])")
    news, seen = [], set()
    for n in _all_news():
        if tk in _tickers(n.get("tickers")) or word.search(n.get("title", "")):
            if n["title"] not in seen:
                seen.add(n["title"])
                news.append(n)
    for r in stored_news:
        n = dict(r)
        if n["title"] in seen:
            continue
        if tk in _tickers(n.get("affected_tickers")) or word.search(n.get("title") or ""):
            seen.add(n["title"])
            news.append({"title": n["title"], "summary": n["content"], "source": n["source"], "url": n["url"],
                         "published_at": n["timestamp"], "tickers": n["affected_tickers"], "sentiment": n["sentiment"]})
    news.sort(key=lambda x: x.get("published_at") or "", reverse=True)

    insider = history_db.get_insider_trades_since(days=90)
    trades = [t for t in insider["trades"] if (t.get("ticker") or "").upper() == tk]
    buys = [t for t in trades if t["transaction_type"] == "BUY"]
    sells = [t for t in trades if t["transaction_type"] == "SELL"]

    predictions = []
    for category in _DIRECTIONAL_CATEGORIES + ["black_swan_monitors"]:
        for item in AI_PREDICTIONS.get(category) or []:
            if (item.get("ticker") or "").upper() == tk:
                predictions.append({**item, "category": category})

    sentiments = [n.get("sentiment") for n in news[:20]]
    return {
        "ticker": tk,
        "price": real_data.get_current_price(tk),
        "timing": _timing_verdict(events[0] if events else None),
        "events": events,
        "news": news[:40],
        "news_tone": {s: sentiments.count(s) for s in ("bullish", "neutral", "bearish")},
        "insider": {
            "trades": trades,
            "buys": len(buys), "sells": len(sells),
            "buy_value": sum(t["total_value"] or 0 for t in buys),
            "sell_value": sum(t["total_value"] or 0 for t in sells),
        },
        "signals": [s for s in generate_signals() if (s.get("ticker") or "").upper() == tk],
        "predictions": predictions,
        "ai_mode": (AI_PREDICTIONS.get("meta") or {}).get("mode"),
        "last_update": datetime.now().isoformat(),
    }


@app.get("/api/telegram/breaking-news")
def get_telegram_breaking_news_endpoint(limit: int = 300):
    """Real messages from the Tradeul_Breaking_News Telegram channel: a real backfilled
    history window (see status.history_window_days) plus anything arriving live."""
    return {"messages": telegram_feed.get_recent(max(1, min(limit, 5000))), "status": telegram_feed.get_status()}

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("AEON_INTEL_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("AEON_INTEL_PORT", "8003")))
    print(f"🚀 Starting Aeon Nimbus Intelligence API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
