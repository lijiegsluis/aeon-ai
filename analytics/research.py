"""
Native research endpoints — price-based analytics that work from market_data
alone, so the Compare and Deep Research tabs stay useful without the optional
vendor engines. Every section is computed independently and fails soft.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException

import market_data as md

router = APIRouter()

WINDOWS = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252}


def _f(x, nd=2):
    try:
        v = float(x)
        return None if math.isnan(v) or math.isinf(v) else round(v, nd)
    except (TypeError, ValueError):
        return None


def _closes(tk: str, period: str = "1y") -> pd.Series:
    df = md.history(tk, period)
    if df.empty:
        return pd.Series(dtype=float)
    s = df["Close"].astype(float)
    s.index = s.index.tz_convert("UTC").normalize() if s.index.tz is not None else s.index.normalize()
    return s[~s.index.duplicated(keep="last")]


def _stats(s: pd.Series) -> dict:
    out: dict = {}
    for label, n in WINDOWS.items():
        if len(s) > n:
            out[f"ret{label}"] = _f(100 * (s.iloc[-1] / s.iloc[-n - 1] - 1))
        elif len(s) >= n * 0.95:  # a "1y" download is ~250 sessions, a few short of 252
            out[f"ret{label}"] = _f(100 * (s.iloc[-1] / s.iloc[0] - 1))
        else:
            out[f"ret{label}"] = None
    ytd = s[s.index.year == s.index[-1].year]
    out["retYTD"] = _f(100 * (s.iloc[-1] / ytd.iloc[0] - 1)) if len(ytd) > 1 else None
    rets = np.log(s / s.shift(1)).dropna()
    out["vol"] = _f(rets.std() * math.sqrt(252) * 100) if len(rets) > 20 else None
    peak = s.cummax()
    out["maxDrawdown"] = _f(100 * (s / peak - 1).min())
    return out


def _check(tk: str) -> str:
    t = tk.strip().upper()
    if not t or len(t) > 10 or not all(c.isalnum() or c in ".-^" for c in t):
        raise HTTPException(400, f"invalid ticker: {tk}")
    return t


@router.get("/market/compare")
def compare(tickers: str, period: str = "1y"):
    """Growth of $100 for up to 6 tickers on their common trading days, plus
    return/volatility/drawdown stats for each."""
    if period not in {"3mo", "6mo", "1y", "2y", "5y"}:
        raise HTTPException(400, "invalid period")
    syms = list(dict.fromkeys(_check(t) for t in tickers.split(",") if t.strip()))[:6]
    if not syms:
        raise HTTPException(400, "no tickers")
    series, stats, missing = {}, {}, []
    for tk in syms:
        s = _closes(tk, period)
        if len(s) < 10:
            missing.append(tk)
            continue
        series[tk] = s
        stats[tk] = _stats(s)
    if not series:
        raise HTTPException(503, "Market data provider unavailable, please retry shortly")
    joined = pd.DataFrame(series).dropna()
    if joined.empty:
        raise HTTPException(404, "no overlapping trading days")
    norm = 100 * joined / joined.iloc[0]
    step = max(1, len(norm) // 260)  # ~260 points is plenty for a chart
    sampled = norm.iloc[::step]
    if sampled.index[-1] != norm.index[-1]:
        sampled = pd.concat([sampled, norm.iloc[[-1]]])
    return {
        "tickers": list(series),
        "missing": missing,
        "series": [{"date": d.strftime("%Y-%m-%d"), **{k: _f(v) for k, v in row.items()}} for d, row in sampled.iterrows()],
        "stats": stats,
    }


def _rsi(s: pd.Series, n: int = 14):
    d = s.diff().dropna()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    down = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up.iloc[-1] / down.iloc[-1] if down.iloc[-1] else float("inf")
    return _f(100 - 100 / (1 + rs), 1)


@router.get("/research/snapshot/{ticker}")
def snapshot(ticker: str):
    """One-call deep dive: performance vs SPY, risk, technicals, analyst view,
    earnings history and insider activity. Sections that can't be computed are
    null, with the reason in `unavailable`."""
    tk = _check(ticker)
    out: dict = {"ticker": tk, "asOf": datetime.now(timezone.utc).isoformat(timespec="seconds"), "unavailable": {}}

    s, spy = _closes(tk, "2y"), _closes("SPY", "2y")
    if len(s) < 30:
        raise HTTPException(503 if s.empty else 404, "no price history for ticker")
    out["price"] = _f(s.iloc[-1])

    perf = _stats(s)
    if len(spy) > 30:
        bench = _stats(spy)
        perf["relative"] = {k: _f(perf[k] - bench[k]) if perf.get(k) is not None and bench.get(k) is not None else None
                            for k in ("ret1M", "ret3M", "ret6M", "ret1Y", "retYTD")}
        perf["benchmark"] = {k: bench[k] for k in ("ret1M", "ret3M", "ret6M", "ret1Y", "retYTD")}
        both = pd.DataFrame({"a": np.log(s / s.shift(1)), "m": np.log(spy / spy.shift(1))}).dropna().iloc[-252:]
        if len(both) > 60:
            perf["beta"] = _f(both.a.cov(both.m) / both.m.var())
            perf["correlation"] = _f(both.a.corr(both.m))
    out["performance"] = perf

    last = s.iloc[-1]
    y1 = s.iloc[-252:]
    out["technicals"] = {
        "ma50": _f(s.iloc[-50:].mean()) if len(s) >= 50 else None,
        "ma200": _f(s.iloc[-200:].mean()) if len(s) >= 200 else None,
        "aboveMa200": bool(last > s.iloc[-200:].mean()) if len(s) >= 200 else None,
        "rsi14": _rsi(s),
        "high52": _f(y1.max()), "low52": _f(y1.min()),
        "fromHigh52": _f(100 * (last / y1.max() - 1)),
    }

    i = md.info(tk)
    if md.has_fundamentals(i):
        out["profile"] = {k: i.get(k) for k in ("shortName", "sector", "industry", "marketCap", "country")}
        out["valuation"] = {"pe": _f(i.get("trailingPE")), "forwardPe": _f(i.get("forwardPE")),
                            "peg": _f(i.get("pegRatio") or i.get("trailingPegRatio")),
                            "priceToBook": _f(i.get("priceToBook")), "evToEbitda": _f(i.get("enterpriseToEbitda"))}
        out["analysts"] = {"recommendation": i.get("recommendationKey"), "mean": _f(i.get("recommendationMean")),
                           "count": i.get("numberOfAnalystOpinions"),
                           "targetMean": _f(i.get("targetMeanPrice")), "targetHigh": _f(i.get("targetHighPrice")),
                           "targetLow": _f(i.get("targetLowPrice")),
                           "targetUpside": _f(100 * (i["targetMeanPrice"] / last - 1)) if i.get("targetMeanPrice") else None}
    else:
        out["unavailable"]["fundamentals"] = "fundamentals provider unreachable — price-based sections only"

    try:
        ed = md.cached(f"earnings:{tk}", 3600, lambda: yf.Ticker(tk).get_earnings_dates(limit=12))
        rows = []
        if ed is not None and not ed.empty:
            for d, r in ed.iterrows():
                rows.append({"date": d.strftime("%Y-%m-%d"), "epsEstimate": _f(r.get("EPS Estimate")),
                             "epsActual": _f(r.get("Reported EPS")), "surprisePct": _f(r.get("Surprise(%)"))})
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        upcoming = sorted([r for r in rows if r["date"] >= today and r["epsActual"] is None], key=lambda r: r["date"])
        past = [r for r in rows if r["epsActual"] is not None][:8]
        beats = [r for r in past if r["surprisePct"] is not None and r["surprisePct"] > 0]
        out["earnings"] = {"next": upcoming[0] if upcoming else None, "history": past,
                           "beatRate": _f(100 * len(beats) / len(past), 0) if past else None}
    except Exception as e:  # noqa: BLE001
        out["earnings"] = None
        out["unavailable"]["earnings"] = f"earnings calendar unavailable ({type(e).__name__})"

    try:
        it = md.cached(f"insiders:{tk}", 3600, lambda: yf.Ticker(tk).insider_transactions)
        trades = []
        if it is not None and not it.empty:
            for _, r in it.head(15).iterrows():
                text = str(r.get("Text") or r.get("Transaction") or "")
                kind = "BUY" if "Purchase" in text else "SELL" if "Sale" in text else "OTHER"
                date = r.get("Start Date")
                trades.append({"insider": r.get("Insider"), "position": r.get("Position"), "type": kind,
                               "shares": int(r["Shares"]) if r.get("Shares") == r.get("Shares") and r.get("Shares") is not None else None,
                               "value": _f(r.get("Value"), 0),
                               "date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date or ""),
                               "text": text})
        out["insiders"] = {"trades": trades,
                           "buys": sum(t["type"] == "BUY" for t in trades), "sells": sum(t["type"] == "SELL" for t in trades)}
    except Exception as e:  # noqa: BLE001
        out["insiders"] = None
        out["unavailable"]["insiders"] = f"insider transactions unavailable ({type(e).__name__})"

    return out
