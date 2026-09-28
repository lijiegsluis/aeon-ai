"""
Aeon Intelligence - Real Insider-Buy Signal Backtest

Answers a narrower, honest question than "this app has a real track record":
historically, when a company insider (officer/director) filed a real SEC Form 4
buy - or when 2+ distinct insiders bought the same stock within a week ("cluster
buying", the highest-conviction version of the same signal) - how did the stock
actually perform over the following 5/10/20/30 trading days?

This backtests the one signal in the live Insider Trading / AI Predictions logic
that can be tested against real historical data with free sources: SEC Form 4
filing history (data.sec.gov) + real historical daily closes (Yahoo Finance).

It is explicitly NOT a backtest of the free-tier LLM's live grounded predictions -
those are generated fresh against today's data and there is no stored point-in-time
snapshot of "what the news/sentiment looked like" on each past day to replay them
against, and free-tier LLM rate limits couldn't sustain re-running them day-by-day
over 6 months anyway. Every field below says exactly what was and wasn't measured
so this can never be read as "the app has been live and correct for 6 months."

Runs once in a background thread on startup (network-heavy - a few minutes) and
refreshes every 24h. Never computed inline on a request. Caches to disk so a
backend restart doesn't always require a full recompute.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import real_data

_CACHE_PATH = Path(__file__).parent / "backtest_cache.json"
_REFRESH_SECONDS = 24 * 3600
_lock = threading.Lock()

# Large, liquid, frequently-covered names - real stocks, not ETFs/crypto (Form 4s
# don't apply to those). Kept small enough that a full run finishes in a few minutes.
_TICKERS = ["NVDA", "AAPL", "MSFT", "GOOGL", "META", "TSLA", "AMD", "AMZN", "ORCL", "COIN", "SQ", "SHOP"]
_LOOKBACK_DAYS = 180
_CLUSTER_WINDOW_DAYS = 7
_HORIZONS = (5, 10, 20, 30)  # trading days forward
_MAX_FILINGS_PER_TICKER = 30

_status = {
    "state": "not_started",  # not_started | running | done | failed
    "last_run_started": None,
    "last_run_finished": None,
    "last_error": None,
}


def get_status() -> Dict[str, Any]:
    with _lock:
        return dict(_status)


def _load_cache() -> Optional[Dict[str, Any]]:
    try:
        if _CACHE_PATH.exists():
            return json.loads(_CACHE_PATH.read_text())
    except Exception as e:
        print(f"[backtest_engine] cache load failed: {e}")
    return None


def _save_cache(result: Dict[str, Any]) -> None:
    try:
        _CACHE_PATH.write_text(json.dumps({"result": result}, indent=2, default=str))
    except Exception as e:
        print(f"[backtest_engine] cache save failed: {e}")


def get_cached_backtest() -> Dict[str, Any]:
    """Always returns something honest - either a real cached backtest result or an explicit
    'not computed yet' / 'failed' placeholder. Never fabricates a result."""
    cached = _load_cache()
    if cached and cached.get("result"):
        return cached["result"]
    state = get_status()["state"]
    if state in ("not_started", "running"):
        note = ("Historical backtest has not completed yet - it runs once in the background on "
                 "startup (real SEC Form 4 history + real historical prices, takes a few minutes) "
                 "and refreshes daily. Check back shortly.")
    else:
        note = "Historical backtest failed on its last run - see server logs."
    return {"status": state, "note": note}


# ---------------------------------------------------------------------------
# CIK lookup
# ---------------------------------------------------------------------------

_TICKER_TO_CIK: Dict[str, str] = {}


def _build_ticker_to_cik() -> None:
    global _TICKER_TO_CIK
    if _TICKER_TO_CIK:
        return
    mapping = real_data.get_sec_ticker_map()
    for cik, info in mapping.items():
        t = (info.get("ticker") or "").upper()
        if t:
            _TICKER_TO_CIK[t] = cik


# ---------------------------------------------------------------------------
# Historical Form 4 filings via SEC's per-company submissions API
# ---------------------------------------------------------------------------

def _fetch_recent_form4_filings(cik: str, cutoff: datetime) -> List[Dict[str, str]]:
    padded = cik.zfill(10)
    resp = real_data._get(
        f"https://data.sec.gov/submissions/CIK{padded}.json",
        headers={"User-Agent": real_data.SEC_UA},
    )
    if not resp:
        return []
    try:
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        out = []
        for form, date_str, accession in zip(recent.get("form", []), recent.get("filingDate", []),
                                               recent.get("accessionNumber", [])):
            if form != "4":
                continue
            try:
                filed = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                continue
            if filed < cutoff:
                continue
            out.append({"accession": accession, "filed": date_str})
        return out
    except Exception as e:
        print(f"[backtest_engine] submissions parse error for CIK {cik}: {e}")
        return []


def _filing_index_url(cik: str, accession: str) -> str:
    nodash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{nodash}/{accession}-index.htm"


def _fetch_filing_transaction(cik: str, accession: str) -> Optional[Dict[str, Any]]:
    index_url = _filing_index_url(cik, accession)
    xml_url = real_data._find_form4_xml_url(index_url)
    if not xml_url:
        return None
    time.sleep(0.12)
    resp = real_data._get(xml_url, headers={"User-Agent": real_data.SEC_UA})
    if not resp:
        return None
    return real_data._parse_form4_xml(resp.text)


# ---------------------------------------------------------------------------
# Historical prices via Yahoo Finance chart API
# ---------------------------------------------------------------------------

def _get_historical_prices_twelvedata(ticker: str, start: datetime, end: datetime) -> Optional[List[Dict[str, Any]]]:
    """Free-tier fallback (800 req/day, no cost) for when Yahoo rate-limits this network -
    only used if TWELVE_DATA_API_KEY is configured; skipped silently otherwise."""
    api_key = os.environ.get("TWELVE_DATA_API_KEY", "").strip()
    if not api_key:
        return None
    resp = real_data._get(
        "https://api.twelvedata.com/time_series",
        params={
            "symbol": ticker,
            "interval": "1day",
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "apikey": api_key,
        },
    )
    if not resp:
        return None
    try:
        data = resp.json()
        values = data.get("values")
        if not values:
            print(f"[backtest_engine] Twelve Data returned no values for {ticker}: {data.get('message') or data.get('status')}")
            return None
        out = [{"date": v["datetime"][:10], "close": float(v["close"])} for v in values]
        out.sort(key=lambda p: p["date"])
        return out or None
    except Exception as e:
        print(f"[backtest_engine] Twelve Data parse error for {ticker}: {e}")
        return None


def _get_historical_prices(ticker: str, start: datetime, end: datetime) -> Optional[List[Dict[str, Any]]]:
    resp = None
    # Yahoo's chart API rate-limits (429) hard, and this backend already polls it for live VIX -
    # a real backtest run only touches a handful of tickers (one per distinct real buy found), so
    # it's worth spending real time on retries with a long backoff and alternating hosts rather
    # than giving up and reporting an empty result that isn't actually true.
    hosts = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
    for attempt, delay in enumerate((0, 5, 15, 30, 60)):
        if delay:
            time.sleep(delay)
        host = hosts[attempt % len(hosts)]
        resp = real_data._get(
            f"https://{host}/v8/finance/chart/{ticker}",
            headers={"User-Agent": real_data.BROWSER_UA},
            params={"period1": int(start.timestamp()), "period2": int(end.timestamp()), "interval": "1d"},
        )
        if resp:
            break
    if not resp:
        fallback = _get_historical_prices_twelvedata(ticker, start, end)
        if fallback:
            print(f"[backtest_engine] Yahoo exhausted for {ticker} - used Twelve Data fallback instead")
        return fallback
    try:
        result = resp.json()["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        out = []
        for ts, close in zip(timestamps, closes):
            if close is None:
                continue
            out.append({"date": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"), "close": close})
        return out or None
    except Exception as e:
        print(f"[backtest_engine] price history parse error for {ticker}: {e}")
        return None


def _forward_return(prices: List[Dict[str, Any]], event_date: str, horizon_trading_days: int) -> Optional[float]:
    dates = [p["date"] for p in prices]
    start_date = event_date
    if start_date not in dates:
        later = [d for d in dates if d >= event_date]
        if not later:
            return None
        start_date = min(later)
    idx = dates.index(start_date)
    target_idx = idx + horizon_trading_days
    if target_idx >= len(prices):
        return None  # not enough real future data yet - never estimated/fabricated
    start_price = prices[idx]["close"]
    end_price = prices[target_idx]["close"]
    if not start_price:
        return None
    return (end_price - start_price) / start_price


# ---------------------------------------------------------------------------
# Cluster detection
# ---------------------------------------------------------------------------

def _detect_buy_clusters(buys: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """A cluster = 2+ distinct insiders buying the same ticker within _CLUSTER_WINDOW_DAYS -
    the same 'highest conviction' signal the live Insider Trading tab flags."""
    by_ticker: Dict[str, List[Dict[str, Any]]] = {}
    for b in buys:
        by_ticker.setdefault(b["ticker"], []).append(b)

    clusters = []
    for ticker, ticker_buys in by_ticker.items():
        ordered = sorted(ticker_buys, key=lambda b: b["date"])
        used = set()
        for i, b in enumerate(ordered):
            if i in used:
                continue
            window_end = datetime.strptime(b["date"], "%Y-%m-%d") + timedelta(days=_CLUSTER_WINDOW_DAYS)
            group, group_idxs = [b], {i}
            for j in range(i + 1, len(ordered)):
                if j in used:
                    continue
                other = ordered[j]
                if datetime.strptime(other["date"], "%Y-%m-%d") > window_end:
                    break
                if other["insider_name"] != b["insider_name"]:
                    group.append(other)
                    group_idxs.add(j)
            distinct_insiders = {g["insider_name"] for g in group}
            if len(distinct_insiders) >= 2:
                used |= group_idxs
                clusters.append({
                    "ticker": ticker,
                    "date": max(g["date"] for g in group),
                    "insiders": sorted(distinct_insiders),
                    "total_value": sum(g["total_value"] for g in group),
                })
    return clusters


# ---------------------------------------------------------------------------
# Backtest run
# ---------------------------------------------------------------------------

def _score_signal(events: List[Dict[str, Any]], price_cache: Dict[str, Optional[List[Dict[str, Any]]]]) -> Dict[str, Any]:
    horizon_agg = {h: {"n": 0, "positive": 0, "returns": []} for h in _HORIZONS}
    sample_events = []

    for ev in events:
        prices = price_cache.get(ev["ticker"])
        if not prices:
            continue
        per_horizon = {}
        for h in _HORIZONS:
            ret = _forward_return(prices, ev["date"], h)
            if ret is None:
                continue
            per_horizon[h] = ret
            horizon_agg[h]["n"] += 1
            horizon_agg[h]["returns"].append(ret)
            if ret > 0:
                horizon_agg[h]["positive"] += 1
        if per_horizon:
            sample_events.append({
                "ticker": ev["ticker"],
                "date": ev["date"],
                "insider_or_insiders": ev.get("insiders") or ev.get("insider_name"),
                "value": round(ev["total_value"], 2),
                "returns_by_horizon_pct": {f"{h}d": round(r * 100, 2) for h, r in per_horizon.items()},
            })

    by_horizon = {}
    for h, agg in horizon_agg.items():
        n = agg["n"]
        by_horizon[f"{h}d"] = {
            "signals_tested": n,
            "pct_positive": round(100 * agg["positive"] / n, 1) if n else None,
            "avg_return_pct": round(100 * sum(agg["returns"]) / n, 2) if n else None,
        }

    return {
        "events_found": len(events),
        "by_horizon": by_horizon,
        "sample_events": sample_events[:15],
    }


def run_backtest() -> Dict[str, Any]:
    with _lock:
        _status["state"] = "running"
        _status["last_run_started"] = datetime.now().isoformat()
        _status["last_error"] = None

    try:
        _build_ticker_to_cik()
        cutoff = datetime.now() - timedelta(days=_LOOKBACK_DAYS)
        all_buys: List[Dict[str, Any]] = []
        filings_checked = 0

        for ticker in _TICKERS:
            cik = _TICKER_TO_CIK.get(ticker)
            if not cik:
                continue
            filings = _fetch_recent_form4_filings(cik, cutoff)[:_MAX_FILINGS_PER_TICKER]
            time.sleep(0.12)
            for f in filings:
                parsed = _fetch_filing_transaction(cik, f["accession"])
                filings_checked += 1
                if not parsed or not parsed.get("is_buy") or parsed.get("total_value", 0) <= 0:
                    continue
                parsed["ticker"] = ticker
                all_buys.append(parsed)

        clusters = _detect_buy_clusters(all_buys)

        # One real historical price series per ticker, reused for every event on that ticker.
        price_cache: Dict[str, Optional[List[Dict[str, Any]]]] = {}
        for ticker in {b["ticker"] for b in all_buys}:
            price_cache[ticker] = _get_historical_prices(ticker, cutoff - timedelta(days=5), datetime.now())
            time.sleep(0.2)

        result = {
            "methodology": (
                "Tests two real, mechanical signals from the live Insider Trading logic against what the stock "
                "actually did afterward - not a backtest of the free-tier LLM's live grounded predictions (those "
                "are generated fresh each time and there is no stored point-in-time data to replay them against). "
                "signal 'single_buy': every real SEC Form 4 officer/director buy found in the window. signal "
                f"'cluster_buy': 2+ distinct insiders buying the same stock within {_CLUSTER_WINDOW_DAYS} days "
                "(the highest-conviction version of the same signal). For each real historical occurrence, this "
                "measures the stock's actual forward return using real historical closing prices."
            ),
            "universe": _TICKERS,
            "period": {
                "start": cutoff.strftime("%Y-%m-%d"),
                "end": datetime.now().strftime("%Y-%m-%d"),
                "days": _LOOKBACK_DAYS,
            },
            "filings_checked": filings_checked,
            "signals": {
                "single_buy": _score_signal(all_buys, price_cache),
                "cluster_buy": _score_signal(clusters, price_cache),
            },
            "computed_at": datetime.now().isoformat(),
            "data_sources": "Real SEC Form 4 filing history (data.sec.gov) + real historical daily closes (Yahoo Finance)",
            "caveat": ("Small sample size for a handful of large-cap tickers over 6 months - read percentages as "
                       "directional, not a statistically robust edge. This does not measure the accuracy of the "
                       "live LLM-generated predictions themselves."),
        }

        with _lock:
            _status["state"] = "done"
            _status["last_run_finished"] = datetime.now().isoformat()
        _save_cache(result)
        print(f"[backtest_engine] backtest complete: {len(all_buys)} buys, {len(clusters)} clusters, "
              f"{filings_checked} filings checked")
        return result
    except Exception as e:
        with _lock:
            _status["state"] = "failed"
            _status["last_error"] = str(e)
        print(f"[backtest_engine] backtest failed: {e}")
        return {"status": "failed", "error": str(e)}


def start_background() -> None:
    """Fire-and-forget: run once now, then every _REFRESH_SECONDS. Never blocks the API."""

    def _loop():
        while True:
            try:
                run_backtest()
            except Exception as e:
                print(f"[backtest_engine] unexpected error: {e}")
            time.sleep(_REFRESH_SECONDS)

    threading.Thread(target=_loop, daemon=True).start()
