"""
Aeon Intelligence - alpha engine.

Four rule-based strategies, each (1) backtested on real historical events against
the S&P 500 (SPY) over the same holding window, (2) turned into live signals with an
entry, stop, target and exit date, and (3) recorded as paper trades that are closed
at real prices, so the strategy's forward track record builds itself over time.

  insider_cluster  2+ insiders buying their own stock on the open market (OpenInsider,
                   from SEC Form 4). Enter the first close after the filing, hold 20d.
  pead             Post-earnings drift: EPS beat consensus by >=10% and the stock
                   closed up on the reaction day. Enter that close, hold 20d.
  earnings_runup   "Buy the rumor": large caps into their report — enter 10 trading
                   days before, exit at the last close before the numbers.
  fear_rebound     CNN Fear & Greed falls to 25 or lower (extreme fear): buy SPY, hold 20d.

Nothing here is a promise of returns: every strategy shows its sample size, hit rate,
average excess return vs SPY and a t-statistic, and says plainly when the evidence
is too thin to call it an edge.
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import alpha_data
import history_db

STRATEGIES: Dict[str, Dict[str, Any]] = {
    "insider_cluster": {
        "name": "Insider cluster buy",
        "thesis": "When several executives buy their own stock with their own money at once, they are "
                  "usually right more often than the market expects.",
        "rules": "2+ insiders, open-market purchases (Form 4 code P), $100K+ combined, price >= $2. "
                 "Enter the first close after the filing date, exit 20 trading days later.",
        "hold_days": 20,
    },
    "pead": {
        "name": "Post-earnings drift",
        "thesis": "Big earnings beats keep drifting up for weeks because the market under-reacts on day one.",
        "rules": "EPS beat consensus by >= 10% (consensus >= $0.05), market cap >= $2B, and the stock closed "
                 "up at least 3% on the reaction day — the market confirming the beat. Enter that close, exit "
                 "40 trading days later.",
        "hold_days": 40,
        "min_surprise": 10, "min_reaction": 3.0,
    },
    "earnings_runup": {
        "name": "Earnings run-up (buy the rumor)",
        "thesis": "Anticipation builds into a report; the move before the numbers is often better than the "
                  "move after them.",
        "rules": "Market cap >= $10B and the stock above its 50-day average (an existing uptrend). Enter the "
                 "close 10 trading days before the report, exit at the last close before the release (the "
                 "report day itself when it reports after the close) — never hold through the numbers.",
        "hold_days": 9,
        "lead": 10, "trend": True,
    },
    "fear_rebound": {
        "name": "Extreme-fear rebound",
        "thesis": "Buying the S&P 500 when crowd fear peaks has historically beaten buying on an average day.",
        "rules": "CNN Fear & Greed crosses down to <= 25. Buy SPY at that close, exit 20 trading days later. "
                 "Excess is measured against SPY's average 20-day return over the same year.",
        "hold_days": 20,
    },
}

MIN_SAMPLE = 20  # fewer events than this and we don't call anything an edge
# How the PEAD and run-up parameters were chosen: .github/scripts/explore_alpha.py replays a small grid of
# economically motivated variants on real data, and a variant is only adopted if its excess return is
# positive in both halves of the year, not just on average. summarize() applies the same stability test.

_state: Dict[str, Any] = {"signals": [], "backtests": {}, "generated_at": None, "backtested_at": None,
                          "status": "not_started", "errors": {}}
# Called after every refresh (e.g. to rebuild the rule-based brief from the new signals).
on_refresh: List[Callable[[], None]] = []
_lock = threading.Lock()


# ─── price helpers ──────────────────────────────────────────────────

def _index_on_or_after(bars: List[Dict[str, Any]], iso: str) -> Optional[int]:
    for i, b in enumerate(bars):
        if b["date"] >= iso:
            return i
    return None


def _index_on_or_before(bars: List[Dict[str, Any]], iso: str) -> Optional[int]:
    idx = None
    for i, b in enumerate(bars):
        if b["date"] <= iso:
            idx = i
        else:
            break
    return idx


def _close_on(bars: List[Dict[str, Any]], iso: str) -> Optional[float]:
    i = _index_on_or_before(bars, iso)
    return bars[i]["close"] if i is not None else None


def atr(bars: List[Dict[str, Any]], n: int = 14) -> Optional[float]:
    if len(bars) < n + 1:
        return None
    trs = []
    for prev, b in zip(bars[-n - 1:-1], bars[-n:]):
        h, lo, pc = b.get("high") or b["close"], b.get("low") or b["close"], prev["close"]
        trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
    return sum(trs) / len(trs)


def add_trading_days(start: date, n: int) -> date:
    d, left = start, n
    while left > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def _window_return(bars, i0: int, i1: int) -> Optional[float]:
    if i0 is None or i1 is None or i0 < 0 or i1 >= len(bars) or i1 <= i0:
        return None
    a, b = bars[i0]["close"], bars[i1]["close"]
    return (b / a - 1) if a else None


def _event_result(ticker: str, bars, spy, i0: int, i1: int, event_date: str, extra=None) -> Optional[Dict[str, Any]]:
    r = _window_return(bars, i0, i1)
    if r is None:
        return None
    d0, d1 = bars[i0]["date"], bars[i1]["date"]
    s0, s1 = _close_on(spy, d0), _close_on(spy, d1)
    spy_r = (s1 / s0 - 1) if s0 and s1 else None
    if spy_r is None:
        return None
    return {"ticker": ticker, "event_date": event_date, "entry_date": d0, "exit_date": d1,
            "return_pct": round(r * 100, 2), "spy_return_pct": round(spy_r * 100, 2),
            "excess_pct": round((r - spy_r) * 100, 2), **(extra or {})}


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sample size, hit rate, average/median excess vs SPY, t-stat and a plain verdict."""
    n = len(events)
    if not n:
        return {"n": 0, "verdict": "no historical events found yet", "edge": False}
    ex = [e["excess_pct"] for e in events]
    raw = [e["return_pct"] for e in events]
    mean_ex = statistics.fmean(ex)
    sd = statistics.stdev(ex) if n > 1 else 0.0
    t = mean_ex / (sd / math.sqrt(n)) if sd > 0 else 0.0
    ordered = [e["excess_pct"] for e in sorted(events, key=lambda e: e.get("event_date") or "")]
    halves = (ordered[: n // 2], ordered[n // 2:]) if n >= 2 else ([], ordered)
    half_means = [round(statistics.fmean(h), 2) if h else None for h in halves]
    stable = all(m is not None and m > 0 for m in half_means)
    if n < MIN_SAMPLE:
        verdict, edge = f"only {n} events — too few to call an edge", False
    elif t >= 2 and mean_ex > 0 and stable:
        verdict, edge = "positive edge vs the S&P 500 (t ≥ 2, and positive in both halves of the year)", True
    elif t >= 2 and mean_ex > 0:
        verdict, edge = "significant on average but carried by one half of the year — not treated as an edge", False
    elif mean_ex > 0:
        verdict, edge = "beat the S&P 500 on average, but not significantly", False
    else:
        verdict, edge = "no edge in this sample — lagged the S&P 500", False
    return {
        "n": n,
        "win_rate": round(100 * sum(1 for x in ex if x > 0) / n, 1),
        "hit_rate_abs": round(100 * sum(1 for x in raw if x > 0) / n, 1),
        "avg_return_pct": round(statistics.fmean(raw), 2),
        "avg_excess_pct": round(mean_ex, 2),
        "median_excess_pct": round(statistics.median(ex), 2),
        "t_stat": round(t, 2),
        "first_half_excess_pct": half_means[0],
        "second_half_excess_pct": half_means[1],
        "stable": stable,
        "best_pct": round(max(raw), 2),
        "worst_pct": round(min(raw), 2),
        "avg_win_pct": round(statistics.fmean([x for x in raw if x > 0]), 2) if any(x > 0 for x in raw) else None,
        "verdict": verdict,
        "edge": edge,
    }


# ─── backtests ──────────────────────────────────────────────────────

PriceFn = Callable[[str], List[Dict[str, Any]]]


def backtest_insider(clusters, prices: PriceFn, spy, hold: int = 20, min_value: float = 100_000,
                     min_insiders: int = 2, min_price: float = 2) -> List[Dict[str, Any]]:
    out = []
    for c in clusters:
        if (c.get("value") or 0) < min_value or (c.get("price") or 0) < min_price or c.get("insiders", 0) < min_insiders:
            continue
        if "P" not in (c.get("trade_type") or "P"):
            continue
        bars = prices(c["ticker"])
        if not bars:
            continue
        i0 = _index_on_or_after(bars, (date.fromisoformat(c["filing_date"]) + timedelta(days=1)).isoformat())
        if i0 is None:
            continue
        res = _event_result(c["ticker"], bars, spy, i0, i0 + hold, c["filing_date"],
                            {"insiders": c["insiders"], "value": c.get("value"), "company": c.get("company")})
        if res:
            out.append(res)
    return out


def _reaction_index(bars, row) -> Optional[int]:
    """First close that reflects the report: the report day for pre-market releases,
    otherwise the next session."""
    i = _index_on_or_after(bars, row["date"])
    if i is None:
        return None
    if bars[i]["date"] == row["date"] and row.get("time") != "pre":
        i += 1
    return i if i < len(bars) else None


def pead_candidate(row, min_surprise: float = 10, min_mcap: float = 2e9) -> bool:
    return ((row.get("surprise_pct") or 0) >= min_surprise and abs(row.get("eps_forecast") or 0) >= 0.05
            and (row.get("market_cap") or 0) >= min_mcap)


def backtest_pead(rows, prices: PriceFn, spy, hold: int = 40, limit: int = 250, min_surprise: float = 10,
                  min_reaction: float = 3.0, min_mcap: float = 2e9) -> List[Dict[str, Any]]:
    cands = sorted([r for r in rows if pead_candidate(r, min_surprise, min_mcap)],
                   key=lambda r: -(r.get("market_cap") or 0))[:limit]
    out = []
    for r in cands:
        bars = prices(r["symbol"])
        if not bars:
            continue
        i = _reaction_index(bars, r)
        if i is None or i < 1 or bars[i]["close"] <= bars[i - 1]["close"] * (1 + min_reaction / 100):
            continue  # the rule needs a positive first reaction
        res = _event_result(r["symbol"], bars, spy, i, i + hold, r["date"],
                            {"surprise_pct": r["surprise_pct"], "company": r.get("name")})
        if res:
            out.append(res)
    return out


def runup_window(bars, row, lead: int = 10) -> Optional[tuple]:
    """(entry_idx, exit_idx): exit at the last close before the release."""
    i = _index_on_or_after(bars, row["date"])
    if i is None or bars[i]["date"] != row["date"]:
        return None
    exit_i = i if row.get("time") == "after" else i - 1
    entry_i = exit_i - (lead - 1)
    return (entry_i, exit_i) if entry_i >= 0 else None


def _above_ma(bars, i: int, n: int = 50) -> bool:
    if i < n:
        return False
    return bars[i]["close"] > sum(b["close"] for b in bars[i - n:i]) / n


def backtest_runup(rows, prices: PriceFn, spy, limit: int = 250, lead: int = 10, min_mcap: float = 10e9,
                   trend: bool = True) -> List[Dict[str, Any]]:
    cands = sorted([r for r in rows if (r.get("market_cap") or 0) >= min_mcap and r.get("eps_actual") is not None],
                   key=lambda r: -(r.get("market_cap") or 0))[:limit]
    out = []
    for r in cands:
        bars = prices(r["symbol"])
        if not bars:
            continue
        w = runup_window(bars, r, lead)
        if not w or (trend and not _above_ma(bars, w[0])):
            continue
        res = _event_result(r["symbol"], bars, spy, w[0], w[1], r["date"], {"company": r.get("name")})
        if res:
            out.append(res)
    return out


def backtest_fear(history, spy, hold: int = 20, threshold: float = 25) -> List[Dict[str, Any]]:
    if not history or len(spy) < hold + 2:
        return []
    # baseline: SPY's average `hold`-day return over the same stretch
    base = [spy[i + hold]["close"] / spy[i]["close"] - 1 for i in range(len(spy) - hold)
            if spy[i]["date"] >= history[0]["date"]]
    baseline = statistics.fmean(base) if base else 0.0
    out, prev = [], None
    for pt in history:
        v = pt["value"]
        if v <= threshold and (prev is None or prev > threshold):
            i0 = _index_on_or_after(spy, pt["date"])
            r = _window_return(spy, i0, (i0 or 0) + hold) if i0 is not None else None
            if r is not None:
                out.append({"ticker": "SPY", "event_date": pt["date"], "entry_date": spy[i0]["date"],
                            "exit_date": spy[i0 + hold]["date"], "return_pct": round(r * 100, 2),
                            "spy_return_pct": round(baseline * 100, 2), "excess_pct": round((r - baseline) * 100, 2),
                            "fear_greed": v})
        prev = v
    return out


# ─── live signals ───────────────────────────────────────────────────

def _signal(strategy: str, ticker: str, bars, event_date: str, exit_date: str, reason: str,
            backtest: Optional[Dict[str, Any]], extra=None) -> Optional[Dict[str, Any]]:
    if not bars:
        return None
    entry = bars[-1]["close"]
    a = atr(bars) or entry * 0.03
    stop = round(entry - 2 * a, 2)
    exp_move = (backtest or {}).get("avg_win_pct") or 8.0
    target = round(entry * (1 + exp_move / 100), 2)
    # a win rate is only quoted as confidence when the backtest shows a significant edge
    proven = bool(backtest and backtest.get("edge"))
    return {
        "key": f"{strategy}:{ticker}:{event_date}",
        "strategy": strategy,
        "strategy_name": STRATEGIES[strategy]["name"],
        "ticker": ticker,
        "direction": "LONG",
        "event_date": event_date,
        "entry_price": round(entry, 2),
        "entry_date": bars[-1]["date"],
        "stop": stop,
        "target": target,
        "exit_date": exit_date,
        "risk_reward": round((target - entry) / (entry - stop), 2) if entry > stop else None,
        "confidence": backtest.get("win_rate") if proven else None,
        "backtest_edge": proven,
        "tier": "trade" if proven else "watch",
        "reason": reason,
        **(extra or {}),
    }


RUNUP_SCAN = 25   # largest reporters checked for a beat record
WATCH_CAP = 6     # max signals per strategy that has no proven edge


def _money(v) -> str:
    return "n/a" if v is None else f"{'-' if v < 0 else ''}${abs(v):,.2f}"


def live_signals(prices: PriceFn, backtests: Dict[str, Dict[str, Any]], today: Optional[date] = None,
                 clusters=None, recent_rows=None, upcoming_rows=None, fear=None,
                 surprises: Callable[[str], List[Dict[str, Any]]] = alpha_data.earnings_surprises) -> List[Dict[str, Any]]:
    today = today or date.today()
    sigs: List[Dict[str, Any]] = []

    # insider clusters filed in the last 7 calendar days
    for c in clusters or []:
        if (c.get("value") or 0) < 100_000 or (c.get("price") or 0) < 2 or c.get("insiders", 0) < 2:
            continue
        if (today - date.fromisoformat(c["filing_date"])).days > 7:
            continue
        bars = prices(c["ticker"])
        s = _signal("insider_cluster", c["ticker"], bars, c["filing_date"],
                    add_trading_days(today, STRATEGIES["insider_cluster"]["hold_days"]).isoformat(),
                    f"{c['insiders']} insiders bought ${(c.get('value') or 0) / 1e6:,.2f}M of {c.get('company') or c['ticker']} "
                    f"(filed {c['filing_date']}, avg ${c.get('price')})",
                    backtests.get("insider_cluster"), {"company": c.get("company")})
        if s:
            sigs.append(s)

    # post-earnings drift: reports in the last 4 calendar days
    for r in recent_rows or []:
        if not pead_candidate(r) or (today - date.fromisoformat(r["date"])).days > 4:
            continue
        bars = prices(r["symbol"])
        if not bars:
            continue
        i = _reaction_index(bars, r)
        min_react = STRATEGIES["pead"]["min_reaction"]
        if i is None or i < 1 or bars[i]["close"] <= bars[i - 1]["close"] * (1 + min_react / 100):
            continue
        s = _signal("pead", r["symbol"], bars, r["date"],
                    add_trading_days(date.fromisoformat(bars[i]["date"]), STRATEGIES["pead"]["hold_days"]).isoformat(),
                    f"EPS {_money(r.get('eps_actual'))} vs {_money(r.get('eps_forecast'))} expected (+{r['surprise_pct']:.0f}% surprise) "
                    f"and the stock closed up {100 * (bars[i]['close'] / bars[i - 1]['close'] - 1):.1f}% on the reaction day",
                    backtests.get("pead"), {"company": r.get("name")})
        if s:
            sigs.append(s)

    # earnings run-up: large caps in an uptrend, reporting 8-12 trading days out (the backtested rule);
    # the recent beat record is shown for context but is not part of the rule
    window = [r for r in upcoming_rows or [] if (r.get("market_cap") or 0) >= 10e9]
    window = [r for r in window if 8 <= _trading_days_between(today, date.fromisoformat(r["date"])) <= 12]
    for r in sorted(window, key=lambda r: -(r.get("market_cap") or 0))[:RUNUP_SCAN]:
        bars = prices(r["symbol"])
        if not bars or (STRATEGIES["earnings_runup"]["trend"] and not _above_ma(bars, len(bars) - 1)):
            continue
        hist = surprises(r["symbol"])
        beats = sum(1 for h in hist if (h.get("surprise_pct") or 0) > 0)
        record = f" Beat consensus in {beats} of the last {len(hist)} quarters." if hist else ""
        report = date.fromisoformat(r["date"])
        exit_day = report if r.get("time") == "after" else _prev_weekday(report)
        when = "after close" if r.get("time") == "after" else "pre-market" if r.get("time") == "pre" else "time TBA"
        s = _signal("earnings_runup", r["symbol"], bars, r["date"], exit_day.isoformat(),
                    f"Reports {r['date']} ({when}); trading above its 50-day average.{record} Exit before the release.",
                    backtests.get("earnings_runup"), {"company": r.get("name")})
        if s:
            sigs.append(s)

    # extreme fear
    if fear and fear[-1]["value"] <= 25:
        spy = prices("SPY")
        s = _signal("fear_rebound", "SPY", spy, fear[-1]["date"],
                    add_trading_days(today, STRATEGIES["fear_rebound"]["hold_days"]).isoformat(),
                    f"CNN Fear & Greed at {fear[-1]['value']:.0f} (extreme fear)", backtests.get("fear_rebound"))
        if s:
            sigs.append(s)

    # proven edges first, then by confidence; unproven strategies are capped so they don't flood the list
    sigs = sorted(sigs, key=lambda s: (not s["backtest_edge"], -(s["confidence"] or 0)))
    kept, per = [], {}
    for s in sigs:
        per[s["strategy"]] = per.get(s["strategy"], 0) + 1
        if s["backtest_edge"] or per[s["strategy"]] <= WATCH_CAP:
            kept.append(s)
    return kept


def _trading_days_between(a: date, b: date) -> int:
    n, d = 0, a
    while d < b:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def _prev_weekday(d: date) -> date:
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


# ─── paper portfolio (forward track record) ─────────────────────────

@contextmanager
def _db():
    conn = sqlite3.connect(str(history_db.DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_portfolio():
    history_db.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS alpha_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, signal_key TEXT UNIQUE, strategy TEXT, ticker TEXT,
            opened_at TEXT, entry_date TEXT, entry_price REAL, spy_entry REAL, planned_exit TEXT,
            stop REAL, target REAL, reason TEXT, status TEXT DEFAULT 'open', exit_date TEXT,
            exit_price REAL, spy_exit REAL, return_pct REAL, spy_return_pct REAL, excess_pct REAL,
            exit_reason TEXT)""")


def open_positions_from(signals: List[Dict[str, Any]], spy_close: Optional[float]) -> int:
    added = 0
    with _db() as c:
        for s in signals:
            cur = c.execute(
                """INSERT OR IGNORE INTO alpha_positions (signal_key, strategy, ticker, opened_at, entry_date,
                   entry_price, spy_entry, planned_exit, stop, target, reason) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (s["key"], s["strategy"], s["ticker"], datetime.now().isoformat(timespec="seconds"), s["entry_date"],
                 s["entry_price"], spy_close, s["exit_date"], s["stop"], s["target"], s["reason"]))
            added += cur.rowcount
    return added


def resolve_positions(prices: PriceFn, today: Optional[date] = None) -> int:
    """Close positions that hit their stop (intraday low) or reached their exit date, at real prices."""
    today = today or date.today()
    spy = prices("SPY")
    closed = 0
    with _db() as c:
        rows = c.execute("SELECT * FROM alpha_positions WHERE status = 'open'").fetchall()
    for p in rows:
        bars = prices(p["ticker"])
        if not bars:
            continue
        after = [b for b in bars if p["entry_date"] < b["date"] <= min(p["planned_exit"], today.isoformat())]
        exit_bar, reason, px = None, None, None
        for b in after:
            if b.get("low") is not None and b["low"] <= p["stop"]:
                exit_bar, reason, px = b, "stop", min(p["stop"], b["open"] or p["stop"])
                break
        if exit_bar is None and today.isoformat() >= p["planned_exit"] and after:
            exit_bar, reason, px = after[-1], "time", after[-1]["close"]
        if exit_bar is None:
            continue
        spy_exit = _close_on(spy, exit_bar["date"])
        ret = px / p["entry_price"] - 1
        spy_ret = (spy_exit / p["spy_entry"] - 1) if spy_exit and p["spy_entry"] else 0.0
        with _db() as c:
            c.execute("""UPDATE alpha_positions SET status='closed', exit_date=?, exit_price=?, spy_exit=?,
                         return_pct=?, spy_return_pct=?, excess_pct=?, exit_reason=? WHERE id=?""",
                      (exit_bar["date"], round(px, 4), spy_exit, round(ret * 100, 2), round(spy_ret * 100, 2),
                       round((ret - spy_ret) * 100, 2), reason, p["id"]))
        closed += 1
    return closed


def portfolio(prices: Optional[PriceFn] = None) -> Dict[str, Any]:
    with _db() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM alpha_positions ORDER BY id DESC")]
    open_ = [r for r in rows if r["status"] == "open"]
    closed = [r for r in rows if r["status"] == "closed"]
    if prices:
        spy = prices("SPY")
        spy_now = spy[-1]["close"] if spy else None
        for r in open_:
            bars = prices(r["ticker"])
            if bars:
                r["last_price"] = bars[-1]["close"]
                r["unrealized_pct"] = round((bars[-1]["close"] / r["entry_price"] - 1) * 100, 2)
                if spy_now and r["spy_entry"]:
                    r["unrealized_excess_pct"] = round(r["unrealized_pct"] - (spy_now / r["spy_entry"] - 1) * 100, 2)
    stats: Dict[str, Any] = {"open": len(open_), "closed": len(closed)}
    if closed:
        ex = [r["excess_pct"] for r in closed]
        stats.update(win_rate=round(100 * sum(1 for x in ex if x > 0) / len(ex), 1),
                     avg_return_pct=round(statistics.fmean(r["return_pct"] for r in closed), 2),
                     avg_excess_pct=round(statistics.fmean(ex), 2),
                     by_strategy={k: summarize([{"excess_pct": r["excess_pct"], "return_pct": r["return_pct"]}
                                                for r in closed if r["strategy"] == k])
                                  for k in {r["strategy"] for r in closed}})
    equity, cum = [], 0.0
    for r in sorted(closed, key=lambda r: r["exit_date"]):
        cum += r["excess_pct"]
        equity.append({"date": r["exit_date"], "cumulative_excess_pct": round(cum, 2), "ticker": r["ticker"]})
    return {"open": open_, "closed": closed[:100], "stats": stats, "equity": equity,
            "started": min((r["opened_at"] for r in rows), default=None)}


# ─── orchestration ──────────────────────────────────────────────────

_BACKTEST_SECONDS = 24 * 3600
_LIVE_SECONDS = 30 * 60


def run_backtests() -> Dict[str, Any]:
    spy = alpha_data.price_history("SPY")
    if not spy:
        raise RuntimeError("no SPY history — price source unreachable")
    today = date.today()
    past = alpha_data.earnings_between(today - timedelta(days=330), today - timedelta(days=32))
    events = {
        "insider_cluster": backtest_insider(alpha_data.insider_cluster_buys(), alpha_data.price_history, spy),
        "pead": backtest_pead(past, alpha_data.price_history, spy),
        "earnings_runup": backtest_runup(past, alpha_data.price_history, spy),
        "fear_rebound": backtest_fear(alpha_data.fear_greed_history(), spy),
    }
    period = {"start": (today - timedelta(days=330)).isoformat(), "end": today.isoformat()}
    return {k: {**STRATEGIES[k], **summarize(v), "period": period,
                "events": sorted(v, key=lambda e: e["event_date"], reverse=True)[:60]} for k, v in events.items()}


def refresh(full: bool = False) -> None:
    errors: Dict[str, str] = {}
    backtests = _state.get("backtests") or {}
    if full or not backtests:
        try:
            backtests = run_backtests()
            with _lock:
                _state.update(backtests=backtests, backtested_at=datetime.now().isoformat(timespec="seconds"))
        except Exception as e:
            errors["backtest"] = str(e)[:300]
    today = date.today()
    try:
        sigs = live_signals(
            alpha_data.price_history, backtests, today,
            clusters=alpha_data.insider_cluster_buys(),
            recent_rows=alpha_data.earnings_between(today - timedelta(days=5), today),
            upcoming_rows=alpha_data.earnings_between(today + timedelta(days=7), today + timedelta(days=20)),
            fear=alpha_data.fear_greed_history())
    except Exception as e:
        sigs = _state.get("signals") or []
        errors["signals"] = str(e)[:300]
    try:
        spy = alpha_data.price_history("SPY")
        open_positions_from(sigs, spy[-1]["close"] if spy else None)
        resolve_positions(alpha_data.price_history)
    except Exception as e:
        errors["portfolio"] = str(e)[:300]
    with _lock:
        _state.update(signals=sigs, generated_at=datetime.now().isoformat(timespec="seconds"),
                      status="ready" if not errors.get("signals") else "degraded", errors=errors)
    for cb in list(on_refresh):
        try:
            cb()
        except Exception as e:
            print(f"[alpha_engine] on_refresh callback failed: {e}")


def get_state() -> Dict[str, Any]:
    with _lock:
        return dict(_state)


def start_background() -> None:
    init_portfolio()

    def loop():
        last_full = 0.0
        while True:
            full = time.time() - last_full >= _BACKTEST_SECONDS
            try:
                with _lock:
                    _state["status"] = "running"
                refresh(full=full)
                if full:
                    last_full = time.time()
            except Exception as e:
                print(f"[alpha_engine] refresh failed: {e}")
            time.sleep(_LIVE_SECONDS)

    threading.Thread(target=loop, daemon=True).start()
