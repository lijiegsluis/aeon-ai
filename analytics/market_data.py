"""
Market data with fallbacks.

yfinance is the primary source, but its cookie/crumb handshake is the first thing
Yahoo breaks for cloud IPs (Render, Fly, GitHub runners). Each accessor below
falls back to sources that don't need the handshake:

  prices   yfinance -> Yahoo chart API (plain JSON, no crumb) -> Stooq daily CSV
  quote    yfinance .info -> quote fields rebuilt from the chart API

Fundamentals (cash flow, EPS, book value, analyst targets) only exist in
yfinance, so those callers still need it; everything price-based keeps working
when it's down. Results are cached briefly so the Overview, Markets and Fusion
tabs hitting the same ticker within seconds share one upstream call.
"""
from __future__ import annotations

import io
import threading
import time
from typing import Callable

import pandas as pd
import requests
import yfinance as yf

try:  # browser TLS fingerprint — the same thing that gets yfinance past Yahoo's bot checks
    from curl_cffi import requests as browser_requests
except ImportError:  # pragma: no cover
    browser_requests = None

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
PERIOD_DAYS = {"5d": 5, "1mo": 31, "3mo": 92, "6mo": 183, "1y": 366, "2y": 731, "5y": 1827, "max": 36500}

_CACHE: dict[str, tuple[float, object]] = {}
_LOCK = threading.Lock()
# Which upstream actually answered most recently, per kind — surfaced by /health.
LAST_SOURCE: dict[str, str] = {}
# Why the most recent attempt at each fallback came back empty (diagnostics).
LAST_ERROR: dict[str, str] = {}


def _get(url: str, **kw):
    if browser_requests is not None:
        return browser_requests.get(url, impersonate="chrome", **kw)
    return requests.get(url, headers=UA, **kw)


def cached(key: str, ttl: float, fn: Callable[[], object]):
    now = time.time()
    with _LOCK:
        hit = _CACHE.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    val = fn()
    with _LOCK:
        _CACHE[key] = (now, val)
    return val


def clear_cache():
    with _LOCK:
        _CACHE.clear()


# ─── Individual upstreams ────────────────────────────────────────────

def _yf_history(tk: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.Ticker(tk).history(period=period, interval=interval)
    return df[["Open", "High", "Low", "Close", "Volume"]] if not df.empty else df


def _chart(tk: str, period: str, interval: str) -> dict | None:
    for host in ("query2", "query1"):
        try:
            r = _get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{tk}",
                     params={"range": period, "interval": interval, "includePrePost": "false"}, timeout=12)
            if r.status_code != 200:
                LAST_ERROR["yahoo-chart"] = f"{host}: HTTP {r.status_code}"
                continue
            res = (r.json().get("chart") or {}).get("result") or []
            if res:
                return res[0]
            LAST_ERROR["yahoo-chart"] = f"{host}: empty result"
        except Exception as e:  # noqa: BLE001 — requests and curl_cffi raise different types
            LAST_ERROR["yahoo-chart"] = f"{host}: {type(e).__name__}"
    return None


def _chart_history(tk: str, period: str, interval: str) -> pd.DataFrame:
    res = _chart(tk, period, interval)
    if not res or not res.get("timestamp"):
        return pd.DataFrame()
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True)
    df = pd.DataFrame({"Open": q.get("open"), "High": q.get("high"), "Low": q.get("low"),
                       "Close": q.get("close"), "Volume": q.get("volume")}, index=idx)
    return df.dropna(subset=["Close"])


def _stooq_history(tk: str, period: str, interval: str) -> pd.DataFrame:
    if interval != "1d" or "^" in tk or "=" in tk:
        return pd.DataFrame()
    sym = tk.lower().replace(".", "-")
    try:
        r = _get("https://stooq.com/q/d/l/", params={"s": f"{sym}.us", "i": "d"}, timeout=12)
        if r.status_code != 200 or not r.text.startswith("Date"):
            LAST_ERROR["stooq"] = f"HTTP {r.status_code}: {r.text[:60]!r}"
            return pd.DataFrame()
        df = pd.read_csv(io.StringIO(r.text), parse_dates=["Date"]).set_index("Date")
    except Exception as e:  # noqa: BLE001
        LAST_ERROR["stooq"] = type(e).__name__
        return pd.DataFrame()
    df.index = df.index.tz_localize("UTC")
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=PERIOD_DAYS.get(period, 366))
    return df[df.index >= cutoff][["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])


# ─── Public accessors ────────────────────────────────────────────────

def history(tk: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """OHLCV DataFrame (possibly empty), newest last."""
    def fetch():
        for name, fn in (("yfinance", _yf_history), ("yahoo-chart", _chart_history), ("stooq", _stooq_history)):
            try:
                df = fn(tk, period, interval)
            except Exception:  # noqa: BLE001 — any upstream failure means "try the next one"
                continue
            if df is not None and not df.empty:
                LAST_SOURCE["history"] = name
                return df
        return pd.DataFrame()
    return cached(f"hist:{tk}:{period}:{interval}", 300, fetch)


def _info_from_chart(tk: str) -> dict:
    res = _chart(tk, "1y", "1d")
    if not res:
        return {}
    meta = res.get("meta") or {}
    closes = [c for c in (res.get("indicators", {}).get("quote", [{}])[0].get("close") or []) if c is not None]
    price = meta.get("regularMarketPrice") or (closes[-1] if closes else None)
    if price is None:
        return {}
    # On a 1y chart, chartPreviousClose is the close before the range starts — the
    # prior session's close is the second-to-last bar.
    prev = closes[-2] if len(closes) >= 2 else meta.get("previousClose")
    out = {
        "regularMarketPrice": price,
        "shortName": meta.get("shortName") or meta.get("longName"),
        "currency": meta.get("currency"),
        "fiftyTwoWeekHigh": meta.get("fiftyTwoWeekHigh") or (max(closes) if closes else None),
        "fiftyTwoWeekLow": meta.get("fiftyTwoWeekLow") or (min(closes) if closes else None),
        "regularMarketVolume": meta.get("regularMarketVolume"),
        "_source": "yahoo-chart",
    }
    if prev:
        out["regularMarketChange"] = price - prev
        out["regularMarketChangePercent"] = (price / prev - 1) * 100
    return out


def info(tk: str) -> dict:
    """yfinance's .info dict, or the price-only subset rebuilt from the chart API."""
    def fetch():
        try:
            i = yf.Ticker(tk).info or {}
        except Exception:  # noqa: BLE001
            i = {}
        if i.get("currentPrice") is not None or i.get("regularMarketPrice") is not None:
            LAST_SOURCE["quote"] = "yfinance"
            return i
        fallback = _info_from_chart(tk)
        if fallback:
            LAST_SOURCE["quote"] = "yahoo-chart"
        return fallback
    return cached(f"info:{tk}", 120, fetch)


def has_fundamentals(i: dict) -> bool:
    return i.get("_source") != "yahoo-chart"


def joint_closes(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    """Aligned daily closes for several tickers (dates where all traded)."""
    frames = {}
    for tk in tickers:
        df = history(tk, period)
        if not df.empty:
            s = df["Close"].copy()
            s.index = s.index.tz_convert("UTC").normalize() if s.index.tz is not None else s.index.normalize()
            frames[tk] = s[~s.index.duplicated(keep="last")]
    if len(frames) < len(tickers):
        return pd.DataFrame()
    return pd.DataFrame(frames).dropna()
