"""
Aeon Nimbus Terminal — Analytics Service
Feature packs inspired by OpenBB (market data), financial-research-analyst-agent
(quant methods), TradingAgents (agent debate), Fincept/FinRobot (investor personas).
Runs locally on :8000. No data leaves the machine except provider API calls.
"""
import configparser
import json
import math
import os
import threading
import time
import re
from typing import List, Optional
from datetime import datetime

import numpy as np
import pandas as pd
import requests as http
import yfinance as yf
from curl_cffi.curl import CurlError
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from yfinance.exceptions import YFException, YFPricesMissingError, YFTickerMissingError

from database import (
    save_analysis, get_analysis_history, save_watchlist, get_watchlists,
    create_alert, get_active_alerts, get_db
)

from sentiment_analyzer import analyze_market_event, SentimentAnalyzer
from api_extensions import register_api_extensions
import market_data as md

app = FastAPI(title="Aeon Nimbus Analytics")
_DEFAULT_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5174", "http://127.0.0.1:5174",
    "http://localhost:5176", "http://127.0.0.1:5176",
    "http://localhost:5177", "http://127.0.0.1:5177",
    "http://localhost:5180", "http://127.0.0.1:5180",
    "http://localhost:5178", "http://127.0.0.1:5178",
    "https://aeon-ai-1.onrender.com", "https://aeon-ai-2.onrender.com", "https://aeon-ai-3.onrender.com",
    "https://aeon-platform.onrender.com", "https://aeon-nimbus.onrender.com",
]
_EXTRA_ORIGINS = [o.strip() for o in os.environ.get("AEON_ANALYTICS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEFAULT_ORIGINS + _EXTRA_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Yahoo throttles/blocks cloud IPs often. Handling these here (inside the CORS
# middleware) turns a bare 500 with no CORS headers into a readable 503/404.
async def _upstream_unavailable(request: Request, exc: Exception):
    return JSONResponse(status_code=503, content={"detail": "Market data provider unavailable, please retry shortly"})


async def _ticker_not_found(request: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": "no data for ticker"})


for _exc in (CurlError, http.RequestException, YFException):
    app.add_exception_handler(_exc, _upstream_unavailable)
for _exc in (YFTickerMissingError, YFPricesMissingError):
    app.add_exception_handler(_exc, _ticker_not_found)


@app.on_event("startup")
def _seed_market_events():
    """Populate market_events (backs RumorNewsTiming.tsx) so it's never
    unconditionally empty on a fresh run. Runs in a background thread since
    each seeded event's auto-analysis hits yfinance over the network."""
    from seed_data import seed_database
    threading.Thread(target=seed_database, daemon=True).start()

# Register API extensions
register_api_extensions(app, lambda ticker: quote(ticker))

from research import router as research_router  # noqa: E402
app.include_router(research_router)

TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,10}$")


def check(ticker: str) -> str:
    t = ticker.upper()
    if not TICKER_RE.match(t):
        raise HTTPException(400, "invalid ticker")
    return t


def f(x, nd=2):
    """Round to float or None — keeps JSON clean of NaN."""
    try:
        v = float(x)
        return None if math.isnan(v) or math.isinf(v) else round(v, nd)
    except (TypeError, ValueError):
        return None


@app.get("/health")
def health():
    # last_source shows which upstream answered most recently (yfinance, or a
    # fallback when Yahoo blocks the host) — handy when a deploy looks "stale".
    return {"status": "ok", "service": "aeonnimbus-analytics", "last_source": md.LAST_SOURCE}


# ─── Lightweight cache for upstream (yfinance) calls ────────────────
# yfinance has no built-in caching, so identical requests within the TTL
# (e.g. Markowitz's joint download, or repeated quote hits from Overview +
# Markets + Fusion in the same few seconds) were each hitting Yahoo fresh.
cached = md.cached


_RF_CACHE_KEY = "risk_free_rate"


def risk_free_rate() -> float:
    """Live 10Y Treasury yield (^TNX) as a decimal, cached 15 min. Falls
    back to a fixed 4% if the quote is unavailable."""
    def fetch():
        try:
            hist = md.history("^TNX", "5d")
            if len(hist):
                v = float(hist.Close.iloc[-1])
                # ^TNX has been quoted both as the yield (4.2) and as 10x it (42).
                return (v / 10 if v > 20 else v) / 100
        except Exception:
            pass
        return 0.04
    return cached(_RF_CACHE_KEY, 900, fetch)


EQUITY_RISK_PREMIUM = 0.045  # constant long-run US equity risk premium


def capm_wacc(t, i: dict) -> tuple[float, str]:
    """Per-company discount rate via CAPM cost of equity, blended with a
    rough after-tax cost of debt when balance-sheet data allows it —
    replaces a single hardcoded 9% applied to every ticker."""
    beta = i.get("beta") or 1.0
    rf = risk_free_rate()
    cost_equity = rf + beta * EQUITY_RISK_PREMIUM
    market_cap = i.get("marketCap")
    total_debt = i.get("totalDebt")
    if market_cap and total_debt is not None and (market_cap + total_debt) > 0:
        e_w = market_cap / (market_cap + total_debt)
        d_w = 1 - e_w
        cost_debt_after_tax = (rf + 0.015) * (1 - 0.21)  # rf + rough credit spread, 21% tax shield
        wacc = e_w * cost_equity + d_w * cost_debt_after_tax
        method = (f"CAPM WACC: {e_w:.0%} equity @ {cost_equity*100:.1f}% "
                  f"(β={beta:.2f}, rf={rf*100:.1f}%, ERP={EQUITY_RISK_PREMIUM*100:.1f}%) + "
                  f"{d_w:.0%} debt @ after-tax {cost_debt_after_tax*100:.1f}%")
    else:
        wacc = cost_equity
        method = (f"Cost of equity only (no balance-sheet debt data): "
                  f"rf {rf*100:.1f}% + β {beta:.2f} × ERP {EQUITY_RISK_PREMIUM*100:.1f}% = {wacc*100:.1f}%")
    return wacc, method


# ─── Markets (OpenBB-style data access) ─────────────────────────────

@app.get("/market/quote/{ticker}")
def quote(ticker: str):
    tk = check(ticker)
    i = md.info(tk)
    if not i or i.get("regularMarketPrice") is None and i.get("currentPrice") is None:
        raise HTTPException(404, "no data for ticker")
    # yfinance's dividendYield switched from a fraction to a percent in 2025;
    # trailingAnnualDividendYield is still a fraction, which is what callers expect.
    div_yield = i.get("trailingAnnualDividendYield")
    if div_yield is None and i.get("dividendYield") is not None:
        dy = i["dividendYield"]
        div_yield = dy / 100 if dy > 0.3 else dy
    # Moving averages (and a 52-week range when .info lacks one) from price history,
    # so the Overview and Markets tabs don't depend on OpenBB for them.
    ma50 = ma200 = None
    high52, low52 = i.get("fiftyTwoWeekHigh"), i.get("fiftyTwoWeekLow")
    try:
        closes = md.history(tk, "1y")["Close"]
        if len(closes) >= 50:
            ma50 = closes.iloc[-50:].mean()
        if len(closes) >= 200:
            ma200 = closes.iloc[-200:].mean()
        if len(closes) >= 20 and (high52 is None or low52 is None):
            high52, low52 = closes.max(), closes.min()
    except Exception:
        pass
    return {
        "ticker": tk,
        "name": i.get("shortName") or i.get("longName"),
        "price": f(i.get("currentPrice") or i.get("regularMarketPrice")),
        "change": f(i.get("regularMarketChange")),
        "changePercent": f(i.get("regularMarketChangePercent")),
        "marketCap": i.get("marketCap"),
        "pe": f(i.get("trailingPE")),
        "forwardPe": f(i.get("forwardPE")),
        "eps": f(i.get("trailingEps")),
        "beta": f(i.get("beta")),
        "dividendYield": f(div_yield, 4),
        "high52": f(high52),
        "low52": f(low52),
        "ma50": f(ma50),
        "ma200": f(ma200),
        "volume": i.get("volume") or i.get("regularMarketVolume"),
        "sector": i.get("sector"),
        "industry": i.get("industry"),
        "source": i.get("_source", "yfinance"),
    }


@app.get("/market/history/{ticker}")
def history(ticker: str, period: str = "1y", interval: str = "1d"):
    if period not in {"1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}:
        raise HTTPException(400, "invalid period")
    if interval not in {"1d", "1wk", "1mo"}:
        raise HTTPException(400, "invalid interval")
    tk = check(ticker)
    df = md.history(tk, period, interval)
    if df.empty:
        raise HTTPException(404, "no history")
    return {
        "ticker": tk,
        "candles": [
            {
                "date": d.strftime("%Y-%m-%d"),
                "open": f(r.Open), "high": f(r.High),
                "low": f(r.Low), "close": f(r.Close),
                "volume": int(r.Volume) if r.Volume == r.Volume else None,
            }
            for d, r in df.iterrows()
        ],
    }


@app.get("/market/screener")
def screener(tickers: str = "AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,JPM,V,JNJ"):
    out = []
    for raw in tickers.split(",")[:25]:
        try:
            out.append(quote(raw.strip()))
        except HTTPException:
            continue
    return {"results": out}


# ─── Quant Lab (financial-research-analyst-agent-style methods) ─────

@app.get("/quant/montecarlo/{ticker}")
def montecarlo(ticker: str, days: int = 252, sims: int = 10000):
    days, sims = min(days, 504), min(sims, 20000)
    tk = check(ticker)
    df = md.history(tk, "2y")
    if len(df) < 60:
        raise HTTPException(404, "not enough history")
    rets = np.log(df.Close / df.Close.shift(1)).dropna()
    mu, sigma, s0 = rets.mean(), rets.std(), float(df.Close.iloc[-1])
    rng = np.random.default_rng(42)
    # GBM: S_T = S_0 * exp(cumsum(drift + sigma*Z))
    z = rng.standard_normal((sims, days))
    paths = s0 * np.exp(np.cumsum((mu - 0.5 * sigma**2) + sigma * z, axis=1))
    finals = paths[:, -1]
    pct = lambda q: f(np.percentile(finals, q))
    step = max(1, days // 60)
    sample_paths = paths[:: sims // 20, ::step].round(2).tolist()
    return {
        "ticker": tk, "spot": f(s0), "days": days, "sims": sims,
        "annualVol": f(sigma * math.sqrt(252) * 100),
        "expected": f(finals.mean()),
        "percentiles": {"p5": pct(5), "p25": pct(25), "p50": pct(50), "p75": pct(75), "p95": pct(95)},
        "probUp": f(100 * (finals > s0).mean()),
        "samplePaths": sample_paths,
    }


@app.get("/quant/dcf/{ticker}")
def dcf(ticker: str):
    tk = check(ticker)
    i = md.info(tk)
    if not md.has_fundamentals(i):
        raise HTTPException(503, "Fundamentals provider unavailable — DCF needs cash-flow data; retry shortly")
    def last_fcf():
        try:
            return float(yf.Ticker(tk).cashflow.loc["Free Cash Flow"].iloc[0])
        except Exception:
            return float(i.get("freeCashflow") or 0)
    fcf = cached(f"fcf:{tk}", 3600, last_fcf)
    shares = i.get("sharesOutstanding")
    price = i.get("currentPrice") or i.get("regularMarketPrice")
    if not fcf or not shares or not price:
        raise HTTPException(404, "missing fundamentals for DCF")
    if fcf < 0:
        # Discounting negative cash flows gives a negative "fair value" — not a
        # valuation, just noise that would drag the Fusion ensemble median.
        raise HTTPException(422, f"Free cash flow is negative (${fcf/1e6:,.0f}M) — a cash-flow DCF isn't meaningful for {tk}")

    wacc, methodology = capm_wacc(tk, i)
    tg = min(0.025, wacc - 0.01)  # terminal growth must stay below the discount rate

    g_base = i.get("earningsGrowth")
    if g_base is None:
        g_base = i.get("revenueGrowth")
    if g_base is None:
        g_base = 0.07
    g_base = max(min(g_base, 0.35), -0.15)
    spread = max(abs(g_base) * 0.5, 0.02)
    growth_map = {"bear": g_base - spread, "base": g_base, "bull": g_base + spread}

    scenarios = {}
    for name, g in growth_map.items():
        # Two-stage: the scenario growth rate for years 1-5, then a straight-line
        # fade to terminal growth by year 10 — compounding even 25% for a full
        # decade produced fair values several times the price for mega-caps.
        flows, cf = [], fcf
        for yr in range(1, 11):
            rate = g if yr <= 5 else g + (tg - g) * (yr - 5) / 5
            cf *= 1 + rate
            flows.append(cf)
        pv = sum(c / (1 + wacc) ** yr for yr, c in enumerate(flows, 1))
        terminal = flows[-1] * (1 + tg) / (wacc - tg) / (1 + wacc) ** 10
        fair = (pv + terminal) / shares
        scenarios[name] = {
            "growth": f(g, 4), "fairValue": f(fair),
            "upside": f(100 * (fair / price - 1)),
        }
    return {
        "ticker": tk, "price": f(price), "fcf": fcf,
        "wacc": f(wacc, 4), "terminalGrowth": f(tg, 4), "scenarios": scenarios,
        "methodology": methodology,
    }


@app.get("/quant/markowitz")
def markowitz(tickers: str = "AAPL,MSFT,GOOGL,AMZN"):
    syms = [check(s.strip()) for s in tickers.split(",")[:10]]
    if len(syms) < 2:
        raise HTTPException(400, "need at least 2 tickers")
    px = md.joint_closes(syms, "2y")
    if len(px) < 60:
        raise HTTPException(404, "not enough joint history")
    rets = np.log(px / px.shift(1)).dropna()
    mu, cov = rets.mean() * 252, rets.cov() * 252
    rng = np.random.default_rng(7)
    rf = risk_free_rate()
    n = len(syms)
    best = {"sharpe": -9e9}
    frontier = []
    for _ in range(8000):
        w = rng.random(n)
        w /= w.sum()
        r = float(w @ mu)
        v = float(np.sqrt(w @ cov @ w))
        sh = (r - rf) / v if v > 0 else 0
        frontier.append({"ret": f(r * 100), "vol": f(v * 100)})
        if sh > best["sharpe"]:
            best = {"sharpe": sh, "weights": w, "ret": r, "vol": v}
    return {
        "tickers": syms,
        "optimal": {
            "weights": {s: f(w * 100, 1) for s, w in zip(syms, best["weights"])},
            "expectedReturn": f(best["ret"] * 100),
            "volatility": f(best["vol"] * 100),
            "sharpe": f(best["sharpe"]),
            "riskFree": f(rf * 100),
        },
        "frontier": frontier[::40],
    }


# ─── AI helpers (Gemini via user key, mock fallback) ────────────────

# Free-tier quota lives on the 2.5 models now; cascade + retry on 429.
GEMINI_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]


def gemini(key: str, prompt: str) -> str:
    import time
    last = None
    for model in GEMINI_MODELS:
        for _ in range(2):
            r = http.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                headers={"User-Agent": "AeonNimbusAI/1.0"},
                timeout=60,
            )
            if r.status_code == 429:
                body = r.text
                if "PerDay" in body:
                    # Daily quota exhausted — waiting won't help, try next model
                    last = f"DAILY quota exhausted on {model}"
                    break
                # Per-minute limit — honor the server's suggested retry delay
                last = f"per-minute rate limit on {model}"
                m = re.search(r'retryDelay[^0-9]*(\d+)', body)
                time.sleep(min(int(m.group(1)) if m else 15, 35) + 2)
                continue
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError(
        f"LLM_QUOTA: all Gemini models unavailable (last: {last}). Daily free-tier "
        "quotas (~20 req/day/model) reset at midnight Pacific. Use a paid key or retry tomorrow.")


def snapshot(ticker: str) -> dict:
    q = quote(ticker)
    df = md.history(check(ticker), "6mo")
    q["return6mo"] = f(100 * (df.Close.iloc[-1] / df.Close.iloc[0] - 1)) if len(df) > 10 else None
    return q


class AgentReq(BaseModel):
    ticker: str
    geminiKey: str | None = None


AGENTS = [
    ("bull", "You are the BULL analyst. Argue the strongest data-grounded case FOR buying."),
    ("bear", "You are the BEAR analyst. Argue the strongest data-grounded case AGAINST buying."),
    ("risk", "You are the RISK manager. Assess downside scenarios, volatility and position-sizing limits."),
    ("trader", "You are the head TRADER. Weigh the bull, bear and risk views and give a final BUY/HOLD/SELL call with conviction 1-10."),
]


@app.post("/agents/debate")
def debate(req: AgentReq):
    t = check(req.ticker)
    snap = snapshot(t)
    if not req.geminiKey:
        return _mock_debate(t, snap)
    transcript = []
    context = f"Company data: {json.dumps(snap)}"
    try:
        for role, system in AGENTS:
            prior = "\n\n".join(f"[{r['role'].upper()}]: {r['text']}" for r in transcript)
            out = gemini(req.geminiKey,
                         f"{system}\nBe concise: max 120 words.\n{context}\n\nDebate so far:\n{prior or '(none)'}")
            transcript.append({"role": role, "text": out.strip()})
    except Exception as e:
        raise HTTPException(502, f"Gemini error: {e}")
    return {"ticker": t, "snapshot": snap, "transcript": transcript, "mode": "live"}


def _mock_debate(t, snap):
    up = (snap.get("changePercent") or 0) >= 0
    pe = snap.get("pe")
    return {"ticker": t, "snapshot": snap, "mode": "demo", "transcript": [
        {"role": "bull", "text": f"{t} shows {'positive momentum' if up else 'a buy-the-dip setup'}; "
         f"6-month return {snap.get('return6mo')}% with a durable franchise in {snap.get('sector')}."},
        {"role": "bear", "text": f"At a P/E of {pe}, expectations are demanding; any growth miss "
         f"re-rates the stock toward its 52-week low of ${snap.get('low52')}."},
        {"role": "risk", "text": f"Beta {snap.get('beta')} implies market-plus volatility. Cap position at 5% "
         f"of book; invalidation below ${snap.get('low52')}."},
        {"role": "trader", "text": f"Netting the views: {'BUY, conviction 6/10' if up else 'HOLD, conviction 5/10'}. "
         "Demo mode — add a Gemini key for a live multi-agent debate."},
    ]}


def persona_metrics(tk: str, i: dict) -> dict:
    """One computed, philosophy-specific number per persona, reusing the same
    math as /fusion/valuation and /quant/montecarlo — so both the live-LLM
    prompt and the offline mock fallback ground their commentary in real
    per-persona metrics instead of only shared price/PE/dividend fields."""
    price = i.get("currentPrice") or i.get("regularMarketPrice")
    eps, bvps = i.get("trailingEps"), i.get("bookValue")
    growth = i.get("earningsGrowth") or i.get("revenueGrowth")
    pe = i.get("trailingPE")
    roe = i.get("returnOnEquity")
    op_margin, gross_margin = i.get("operatingMargins"), i.get("grossMargins")
    out: dict = {}

    if eps and bvps and eps > 0 and bvps > 0:
        graham_value = math.sqrt(22.5 * eps * bvps)
        out["graham"] = {
            "grahamNumber": f(graham_value),
            "marginOfSafety": f(100 * (graham_value / price - 1)) if price else None,
        }

    if pe and growth and pe > 0 and growth > 0:
        out["lynch"] = {"peg": f(pe / (growth * 100), 2), "fairPE": f(growth * 100)}

    if roe is not None:
        out["buffett"] = {
            "roe": f(roe * 100),
            "quality": ("a high-ROE compounder" if roe > 0.20 else
                        "an adequate-return business" if roe > 0.10 else
                        "a subpar-return business"),
        }

    if op_margin and gross_margin and gross_margin > 0:
        out["munger"] = {"marginRetention": f(100 * op_margin / gross_margin)}

    try:
        df = md.history(tk, "2y")
        if len(df) > 20 and price:
            out["marks"] = {"cyclePercentile": f(100 * float((df.Close < price).mean()))}
    except Exception:
        pass

    return out


PERSONAS = {
    "buffett": "Warren Buffett: durable moats, owner earnings, margin of safety, decades-long holding period.",
    "graham": "Benjamin Graham: net-nets, asset backing, strict quantitative margin of safety, Mr. Market discipline.",
    "lynch": "Peter Lynch: PEG ratio, invest in what you know, category (stalwart/fast grower/cyclical).",
    "munger": "Charlie Munger: mental models, inversion, quality at a fair price, avoiding stupidity.",
    "marks": "Howard Marks: market cycles, second-level thinking, risk as permanent capital loss.",
}


class PersonaReq(BaseModel):
    ticker: str
    personas: list[str] = ["buffett", "graham", "lynch"]
    geminiKey: str | None = None


@app.post("/agents/personas")
def personas(req: PersonaReq):
    t = check(req.ticker)
    snap = snapshot(t)
    chosen = [p for p in req.personas if p in PERSONAS][:5] or ["buffett"]
    i = md.info(t)
    metrics = persona_metrics(t, i)
    if not req.geminiKey:
        return _mock_personas(t, snap, chosen, metrics)
    out = []
    try:
        for p in chosen:
            m = metrics.get(p)
            metric_line = (f"Your philosophy-specific computed metric for {t}: {json.dumps(m)}" if m else
                           f"No {p}-specific metric could be computed for {t} (missing fundamentals) — rely on the snapshot only.")
            text = gemini(req.geminiKey,
                          f"Channel this investment philosophy: {PERSONAS[p]}\n"
                          f"Analyze {t} using: {json.dumps(snap)}\n"
                          f"{metric_line}\n"
                          "Ground your verdict specifically in that metric, not just price/PE/dividend. "
                          "Give verdict (BUY/HOLD/AVOID), 3 key points, one memorable one-liner. Max 130 words.")
            out.append({"persona": p, "text": text.strip(), "metric": m})
    except Exception as e:
        raise HTTPException(502, f"Gemini error: {e}")
    return {"ticker": t, "snapshot": snap, "analyses": out, "mode": "live"}


def _mock_personas(t, snap, chosen, metrics):
    pe = snap.get("pe")
    canned = {}

    b = metrics.get("buffett")
    if b:
        canned["buffett"] = (
            f"Verdict: {'BUY' if b['roe'] and b['roe'] > 20 else 'HOLD'}. ROE of {b['roe']}% makes this "
            f"{b['quality']} — a {snap.get('sector')} franchise is only wonderful at a fair price. "
            "'Price is what you pay, value is what you get.'")
    else:
        canned["buffett"] = (f"Verdict: HOLD. A {snap.get('sector')} franchise is only wonderful at a fair price — "
                             f"P/E {pe} demands certainty about the moat. 'Price is what you pay, value is what you get.'")

    g = metrics.get("graham")
    if g:
        mos = g["marginOfSafety"]
        canned["graham"] = (
            f"Verdict: {'AVOID' if mos is not None and mos < 0 else 'HOLD'}. Graham number ${g['grahamNumber']} vs. the "
            f"current price implies a {'negative' if mos is not None and mos < 0 else 'positive'} margin of safety of {mos}%. "
            "Mr. Market is optimistic today — demand asset backing before enthusiasm.")
    else:
        canned["graham"] = (f"Verdict: {'AVOID' if (pe or 99) > 20 else 'HOLD'}. The margin of safety at P/E {pe} is thin; "
                            "Mr. Market is optimistic today. Demand asset backing before enthusiasm.")

    l = metrics.get("lynch")
    if l:
        peg = l["peg"]
        verdict = "BUY" if peg < 1 else "HOLD" if peg < 1.5 else "AVOID"
        canned["lynch"] = (f"Verdict: {verdict}. PEG of {peg} "
                           f"({'cheap' if peg < 1 else 'fair' if peg < 1.5 else 'pricey'} relative to growth); "
                           f"fair P/E near {l['fairPE']}. Know the story in two minutes or don't own it.")
    else:
        canned["lynch"] = (f"Verdict: HOLD. Check the PEG: P/E {pe} needs matching earnings growth. "
                           "Know the story in two minutes or don't own it.")

    m = metrics.get("munger")
    if m:
        mr = m["marginRetention"]
        canned["munger"] = (f"Verdict: HOLD. Margin retention of {mr}% (operating ÷ gross margin) shows "
                            f"{'a disciplined' if mr > 50 else 'a leaky'} cost structure. "
                            "Invert: what kills this business? If you can't answer, you don't understand it yet.")
    else:
        canned["munger"] = "Verdict: HOLD. Invert: what kills this business? If you can't answer, you don't understand it yet."

    mk = metrics.get("marks")
    if mk:
        cp = mk["cyclePercentile"]
        pos = "near cycle highs" if cp > 70 else "near cycle lows" if cp < 30 else "mid-cycle"
        canned["marks"] = (f"Verdict: HOLD. At the {cp:.0f}th percentile of its own 2-year price range, the stock is "
                           f"trading {pos}. Second-level thinking beats first-level enthusiasm.")
    else:
        canned["marks"] = (f"Verdict: HOLD. With the stock {snap.get('return6mo')}% over six months, ask where we are "
                           "in the cycle — second-level thinking beats first-level enthusiasm.")

    return {"ticker": t, "snapshot": snap, "mode": "demo",
            "analyses": [{"persona": p, "text": canned[p], "metric": metrics.get(p)} for p in chosen]}


# ─── System helpers ─────────────────────────────────────────────────

class SyncKeysReq(BaseModel):
    groq: str | None = None
    openai: str | None = None
    fmp: str | None = None


VENDOR_DIR = os.path.expanduser("~/aeon-ai/vendor")
FRA_DIR = f"{VENDOR_DIR}/financial-research-analyst-agent"
FINROBOT_CONFIG_DIR = f"{VENDOR_DIR}/FinRobot/finrobot_equity/core/config"


@app.post("/system/sync-keys")
def sync_keys(req: SyncKeysReq):
    """One vault, every engine. Each engine's sync is independent — a
    missing Groq key must not block the OpenAI/FMP sync to Deep Reports,
    and vice versa."""
    result: dict = {}

    if req.groq and os.path.isdir(FRA_DIR):
        env_path = f"{FRA_DIR}/.env"
        lines = []
        found = False
        if os.path.exists(env_path):
            with open(env_path) as fh:
                for line in fh:
                    if line.startswith("GROQ_API_KEY="):
                        lines.append(f"GROQ_API_KEY={req.groq}\n")
                        found = True
                    else:
                        lines.append(line)
        if not found:
            lines.append(f"GROQ_API_KEY={req.groq}\n")
        if not any(l.startswith("LLM_PROVIDER=") for l in lines):
            lines.insert(0, "LLM_PROVIDER=groq\n")
        with open(env_path, "w") as fh:
            fh.writelines(lines)

        # Restart the Deep Research REST API so the new key takes effect.
        import subprocess
        subprocess.run(["bash", "-c", "lsof -ti tcp:8600 | xargs kill -9"],
                        capture_output=True)
        subprocess.Popen(
            ["bash", "-c",
             f'cd "{FRA_DIR}" && "{VENDOR_DIR}/venv-fra/bin/python" -m uvicorn '
             f'src.api.routes:app --host 127.0.0.1 --port 8600 '
             f'> /tmp/fra-api.log 2>&1'],
        )
        result["fra_synced"] = True

    # Deep Reports needs a real config.ini (only a .example template ships in
    # the repo) — write OpenAI in from the vault. FMP has no free-tier
    # equivalent in the vault, so it's synced only once the user supplies one.
    if req.openai or req.fmp:
        os.makedirs(FINROBOT_CONFIG_DIR, exist_ok=True)
        cfg_path = f"{FINROBOT_CONFIG_DIR}/config.ini"
        cfg = configparser.ConfigParser()
        if os.path.exists(cfg_path):
            cfg.read(cfg_path)
        if not cfg.has_section("API_KEYS"):
            cfg.add_section("API_KEYS")
        if req.openai:
            cfg.set("API_KEYS", "openai_api_key", req.openai)
            cfg.set("API_KEYS", "openai_model", "gpt-4.1-mini")
        if req.fmp:
            cfg.set("API_KEYS", "fmp_api_key", req.fmp)
        with open(cfg_path, "w") as fh:
            cfg.write(fh)
        result["finrobot_config_synced"] = True
        result["finrobot_has_fmp"] = cfg.has_option("API_KEYS", "fmp_api_key")

    return result


# ═══ FUSION LAYER ════════════════════════════════════════════════════
# Original composites that use ALL vendored projects' overlapping
# capabilities as an ensemble instead of picking one winner.

TA_SERVICE = os.environ.get("AEON_TA_SERVICE_URL", "http://127.0.0.1:8001")

# FinRobot's real agent profile, quoted from
# vendor/FinRobot/finrobot/agents/agent_library.py (Market_Analyst)
FINROBOT_MARKET_ANALYST = (
    "As a Market Analyst, one must possess strong analytical and "
    "problem-solving abilities, collect necessary financial information "
    "and aggregate them based on client's requirement."
)


@app.get("/fusion/valuation/{ticker}")
def fusion_valuation(ticker: str):
    """Valuation ensemble: five independent philosophies vote on fair value.
    Consensus = median; disagreement index = spread / consensus."""
    t = check(ticker)
    i = md.info(t)
    price = i.get("currentPrice") or i.get("regularMarketPrice")
    if not price:
        raise HTTPException(404, "no price")
    eps = i.get("trailingEps")
    bvps = i.get("bookValue")
    growth = i.get("earningsGrowth") or i.get("revenueGrowth")

    models = {}
    # 1. FCF DCF (Aeon base scenario) — FinRobot/FRA/Fincept all ship one
    try:
        d = dcf(t)
        models["dcf"] = {"value": d["scenarios"]["base"]["fairValue"],
                         "philosophy": f"10Y discounted free cash flow, {d['scenarios']['base']['growth']*100:.1f}% growth "
                                       f"fading to terminal after year 5, WACC {d['wacc']*100:.1f}%"}
    except HTTPException:
        pass
    # 2. Graham number — Research worker's philosophy
    if eps and bvps and eps > 0 and bvps > 0:
        models["graham"] = {"value": f(math.sqrt(22.5 * eps * bvps)),
                            "philosophy": "Graham: sqrt(22.5 × EPS × BVPS)"}
    # 3. Lynch PEG fair value
    if eps and growth and eps > 0 and growth > 0:
        models["lynch"] = {"value": f(eps * min(growth * 100, 40)),
                           "philosophy": "Lynch: fair P/E equals growth rate (PEG = 1)"}
    # 4. Wall Street analyst mean target — what OpenBB/Fincept surface
    if i.get("targetMeanPrice"):
        models["analysts"] = {"value": f(i["targetMeanPrice"]),
                              "philosophy": "Wall Street mean 12M price target"}
    # 5. Monte Carlo median — FRA's stochastic approach
    try:
        models["montecarlo"] = {"value": montecarlo(t, sims=5000)["percentiles"]["p50"],
                                "philosophy": "GBM simulation, median 1Y outcome"}
    except HTTPException:
        pass

    if len(models) < 2:
        raise HTTPException(404, "not enough data for an ensemble")
    vals = sorted(m["value"] for m in models.values())
    n = len(vals)
    consensus = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
    for m in models.values():
        m["upside"] = f(100 * (m["value"] / price - 1))
    disagreement = f(100 * (vals[-1] - vals[0]) / consensus)
    return {
        "ticker": t, "price": f(price), "models": models,
        "consensus": f(consensus),
        "consensusUpside": f(100 * (consensus / price - 1)),
        "disagreementIndex": disagreement,
        "readout": ("models largely agree — higher conviction" if disagreement < 35
                    else "models diverge widely — the value depends on which lens you trust"),
    }


def stooq_quote(ticker: str) -> float | None:
    """Free, unauthenticated last-close quote from Stooq — a genuinely
    independent upstream from Yahoo Finance (different company, different
    data pipeline), used only as a cross-check for /fusion/quote."""
    try:
        r = http.get("https://stooq.com/q/l/",
                     params={"s": f"{ticker.lower()}.us", "f": "sd2t2ohlcv", "e": "csv"},
                     timeout=10)
        lines = r.text.strip().splitlines()
        if len(lines) < 2:
            return None
        row = lines[1].split(",")
        close = float(row[6])  # Symbol,Date,Time,Open,High,Low,Close,Volume
        return close if close > 0 else None
    except Exception:
        return None


def nasdaq_quote(ticker: str) -> float | None:
    """Last sale from Nasdaq's public quote API — an upstream independent of Yahoo
    (Stooq, the original cross-check, now serves a CAPTCHA to most clients)."""
    try:
        r = md._get(f"https://api.nasdaq.com/api/quote/{ticker.upper()}/info",
                    params={"assetclass": "stocks"}, timeout=10)
        data = (r.json() or {}).get("data") or {}
        raw = ((data.get("primaryData") or {}).get("lastSalePrice") or "").replace("$", "").replace(",", "")
        price = float(raw) if raw else None
        return price if price and price > 0 else None
    except Exception:
        return None


@app.get("/fusion/quote/{ticker}")
def fusion_quote(ticker: str):
    """Cross-source integrity check. Yahoo and Nasdaq (Stooq as a backup) are
    genuinely independent upstreams (separate companies, separate data
    pipelines) — that's the actual verification. OpenBB is surfaced as a
    third opinion when reachable, but excluded from the independence check
    when it's itself configured with the yfinance provider, since that just
    re-fetches the same Yahoo data through a second client and would agree
    with yfinance-direct even if Yahoo's own figure were wrong."""
    t = check(ticker)
    sources = {}
    independent = []
    i = md.info(t)
    p1 = i.get("currentPrice") or i.get("regularMarketPrice")
    if p1:
        yahoo = "yahoo-chart" if i.get("_source") == "yahoo-chart" else "yfinance-direct"
        sources[yahoo] = f(p1)
        independent.append(yahoo)
    p2 = nasdaq_quote(t)
    if p2:
        sources["nasdaq"] = f(p2)
        independent.append("nasdaq")
    else:
        p2 = stooq_quote(t)
        if p2:
            sources["stooq"] = f(p2)
            independent.append("stooq")
    try:
        r = http.get("http://127.0.0.1:6900/api/v1/equity/price/quote",
                     params={"provider": "yfinance", "symbol": t}, timeout=10)
        p3 = r.json()["results"][0].get("last_price")
        if p3:
            sources["openbb-platform (yfinance-backed, not independent)"] = f(p3)
    except Exception:
        pass

    indep_vals = [sources[k] for k in independent]
    if len(indep_vals) < 2:
        return {"ticker": t, "sources": sources, "verified": None,
                "note": "fewer than two independent sources reachable — cannot cross-check",
                "methodology": "Yahoo (yfinance or its chart API) and Nasdaq (Stooq as a backup) are the independent upstreams checked; "
                                "OpenBB is informational only when it's backed by the yfinance provider."}
    spread_bps = f(10000 * abs(indep_vals[0] - indep_vals[1]) / indep_vals[0], 1)
    return {"ticker": t, "sources": sources, "spreadBps": spread_bps,
            "verified": spread_bps < 50,
            "note": (f"independent sources ({' vs '.join(independent)}) agree" if spread_bps < 50
                     else "independent sources disagree — data may be stale on one side"),
            "methodology": "Yahoo (yfinance or its chart API) and Nasdaq (Stooq as a backup) are the independent upstreams checked; "
                            "OpenBB is informational only when it's backed by the yfinance provider."}


class CouncilReq(BaseModel):
    ticker: str
    geminiKey: str
    includeDebate: bool = False   # full TradingAgents run adds 3-10 min


COUNCIL_JOBS: dict[str, dict] = {}
VOTE_RE = re.compile(r"\b(STRONG BUY|BUY|SELL|HOLD|AVOID)\b", re.I)


def _vote(text: str) -> str:
    m = VOTE_RE.search(text or "")
    v = (m.group(1).upper() if m else "HOLD")
    return {"STRONG BUY": "BUY", "AVOID": "SELL"}.get(v, v)


def _council(job_id: str, req: CouncilReq):
    import time
    t = check(req.ticker)
    try:
        snap = snapshot(t)
        ctx = json.dumps(snap)
        seats = []
        pace = lambda: time.sleep(7)   # stay under free-tier ~10 req/min
        total = 5 if req.includeDebate else 4

        def phase(i, label):
            COUNCIL_JOBS[job_id].update(phase=label, progress=round(i / total, 2))

        # Seat 1 — FinRobot paradigm: their real Market_Analyst profile
        phase(0, "Seat 1/%d — FinRobot market analyst" % total)
        fr = gemini(req.geminiKey,
                    f"{FINROBOT_MARKET_ANALYST}\nAnalyze {t}: {ctx}\n"
                    "Produce a professional markets brief ending with one word verdict: BUY, HOLD or SELL. Max 130 words.")
        seats.append({"seat": "finrobot", "label": "Market Analyst",
                      "text": fr.strip(), "vote": _vote(fr), "independent": False})
        pace()

        # Seat 2 — FRA paradigm: hierarchical sub-analysts → chief synthesis
        phase(1, "Seat 2/%d — hierarchical research team (3 specialists + chief)" % total)
        subs = {}
        for dim in ("fundamental valuation", "technical momentum", "downside risk"):
            subs[dim] = gemini(req.geminiKey,
                               f"You are the {dim} specialist in a hierarchical research team. "
                               f"Assess {t} strictly on {dim}: {ctx}. Max 60 words.")
            pace()
        chief = gemini(req.geminiKey,
                       "You are the Chief Research Officer synthesizing your specialist team:\n"
                       + "\n".join(f"[{k}]: {v}" for k, v in subs.items())
                       + "\nIssue the house view ending with one word verdict: BUY, HOLD or SELL. Max 100 words.")
        seats.append({"seat": "hierarchy", "label": "Hierarchical Research Team",
                      "text": chief.strip(), "vote": _vote(chief),
                      "specialists": subs, "independent": False})
        pace()

        # Seat 3 — Personas paradigm (Fincept-style investor lenses)
        phase(2, "Seat 3/%d — investor personas" % total)
        pv = personas(PersonaReq(ticker=t, personas=["buffett", "lynch", "marks"],
                                 geminiKey=req.geminiKey))
        ptext = " | ".join(a["text"][:90] for a in pv["analyses"])
        pvotes = [_vote(a["text"]) for a in pv["analyses"]]
        seats.append({"seat": "personas", "label": "Investor Personas",
                      "text": ptext, "vote": max(set(pvotes), key=pvotes.count), "independent": False})

        # Seat 4 — Aeon quant engines: deterministic, free, no LLM
        phase(3, "Seat 4/%d — quant engines (Monte Carlo + DCF)" % total)
        try:
            mc = montecarlo(t, sims=5000)
            base = dcf(t)["scenarios"]["base"]
            q_vote = ("BUY" if mc["probUp"] > 60 and base["upside"] > -10
                      else "SELL" if mc["probUp"] < 45 and base["upside"] < -25
                      else "HOLD")
            seats.append({
                "seat": "quant", "label": "Quant Engines (Monte Carlo + DCF)",
                "text": f"Monte Carlo P(up 1Y) = {mc['probUp']}% (σ {mc['annualVol']}%); "
                        f"base-case DCF fair value ${base['fairValue']} "
                        f"({base['upside']:+.1f}% vs price). Mechanical rule → {q_vote}.",
                "vote": q_vote, "independent": True})
        except HTTPException:
            pass

        # Seat 5 — the real TradingAgents LangGraph (optional, slow)
        if req.includeDebate:
            phase(4, "Seat 5/5 — full multi-agent debate (3-10 min)")
            r = http.post(f"{TA_SERVICE}/run", timeout=15, json={
                "ticker": t, "provider": "google", "apiKey": req.geminiKey})
            ta_id = r.json()["jobId"]
            import time
            for _ in range(150):          # up to ~12.5 min
                time.sleep(5)
                j = http.get(f"{TA_SERVICE}/job/{ta_id}", timeout=10).json()
                if j["status"] != "running":
                    break
            if j.get("status") == "done":
                seats.append({"seat": "tradingagents",
                              "label": "Multi-Agent Debate",
                              "text": (j.get("decision") or "")[:1500],
                              "vote": _vote(j.get("decision") or ""), "independent": True})

        # Meta-verdict: votes + agreement + final synthesis
        COUNCIL_JOBS[job_id].update(phase="Chair synthesizing ruling", progress=0.95)
        votes = [s["vote"] for s in seats]
        tally = {v: votes.count(v) for v in ("BUY", "HOLD", "SELL")}
        agreement = f(100 * max(tally.values()) / len(votes))
        meta = gemini(req.geminiKey,
                      f"You chair an investment council on {t}. Seat conclusions:\n"
                      + "\n".join(f"[{s['label']} → {s['vote']}]: {s['text'][:300]}" for s in seats)
                      + f"\nVote tally: {tally}. Write the chair's final ruling: where the seats "
                        "agree, where they clash and why, and the single actionable call. Max 150 words.")
        COUNCIL_JOBS[job_id].update(
            status="done", seats=seats, tally=tally,
            agreement=agreement, verdict=max(tally, key=tally.get),
            chairRuling=meta.strip(), snapshot=snap,
            independenceNote=(
                "Seats 1-3 (Market Analyst, Hierarchical Research Team, Investor Personas) are "
                "LLM readings of the same shallow snapshot() data pull — different prompts, same "
                "inputs, so their agreement reflects prompt diversity more than independent evidence. "
                "Seat 4 (Quant Engines) is a deterministic rule over Monte Carlo + DCF, methodologically "
                "independent of the LLM seats. Seat 5 (Multi-Agent Debate), when included, runs the "
                "separate TradingAgents service end-to-end and is also independent. Weight agreement "
                "between seats 1-3 accordingly — treat it as one vote, not three."))
    except Exception as e:  # noqa: BLE001
        COUNCIL_JOBS[job_id].update(status="error", error=str(e)[:1500])


@app.post("/fusion/council")
def council(req: CouncilReq):
    if not req.geminiKey:
        raise HTTPException(400, "council needs a Gemini key — all seats are real LLM runs")
    job_id = __import__("uuid").uuid4().hex[:12]
    # Keep memory bounded: drop the oldest finished jobs beyond the last 50.
    finished = [k for k, v in COUNCIL_JOBS.items() if v.get("status") != "running"]
    for k in finished[:-50]:
        COUNCIL_JOBS.pop(k, None)
    COUNCIL_JOBS[job_id] = {"status": "running", "phase": "seats deliberating", "ticker": check(req.ticker)}
    threading.Thread(target=_council, args=(job_id, req), daemon=True).start()
    return {"jobId": job_id}


@app.get("/fusion/council/{job_id}")
def council_job(job_id: str):
    j = COUNCIL_JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "unknown job")
    return j


# ── Houston / Research-ops endpoints ─────────────────────────────────────────

HOUSTON_PY   = os.path.expanduser("~/AeonNimbus/houston.py")
HOUSTON_VENV = os.path.expanduser(
    "~/AeonNimbus/AeonNimbus_Platform/Platform_Source_Code/.venv/bin/python"
)
GATES_DIR    = os.path.expanduser("~/AeonNimbus/outputs/thesis_gates")
PLATFORM_DB  = os.path.expanduser(
    "~/AeonNimbus/AeonNimbus_Platform/Platform_Source_Code/data/platform.db"
)


def _native_brief(day: str) -> str:
    """Morning brief built from what this service already knows — used wherever
    the research-workstation houston.py isn't installed (e.g. a cloud deploy)."""
    from datetime import date, timedelta
    lines = [f"# Aeon Morning Brief — {day}", "",
             "_Built by Aeon Analysis from your events, alerts, watchlists and thesis gates._", ""]

    today = date.today()
    with get_db() as conn:
        events = conn.execute(
            "SELECT title, event_date, affected_assets FROM market_events "
            "WHERE date(event_date) BETWEEN date(?) AND date(?) ORDER BY event_date ASC",
            (today.isoformat(), (today + timedelta(days=7)).isoformat())).fetchall()
        alerts = conn.execute("SELECT ticker, condition_type, threshold FROM alerts WHERE is_active = 1").fetchall()
        wl = conn.execute("SELECT name, tickers_json FROM watchlists ORDER BY updated_at DESC LIMIT 3").fetchall()

    lines.append("## Next 7 days")
    if events:
        for e in events:
            d = (date.fromisoformat(e["event_date"][:10]) - today).days
            assets = ", ".join(json.loads(e["affected_assets"] or "[]"))
            lines.append(f"- **D-{d}** · {e['event_date'][:10]} — {e['title']}" + (f" ({assets})" if assets else ""))
    else:
        lines.append("- No scheduled events in the next week.")
    lines.append("")

    tickers = []
    for w in wl:
        tickers += [t for t in json.loads(w["tickers_json"]) if t not in tickers]
    if tickers:
        lines.append("## Watchlist")
        for tk in tickers[:12]:
            try:
                q = quote(tk)
                chg = q.get("changePercent")
                lines.append(f"- **{tk}** ${q['price']}" + (f" ({chg:+.2f}%)" if chg is not None else ""))
            except Exception:
                lines.append(f"- **{tk}** — quote unavailable")
        lines.append("")

    if alerts:
        lines.append("## Active alerts")
        labels = {"price_above": "price above", "price_below": "price below", "pe_above": "P/E above", "pe_below": "P/E below"}
        for a in alerts:
            lines.append(f"- {a['ticker']}: {labels.get(a['condition_type'], a['condition_type'])} {a['threshold']}")
        lines.append("")

    gates = houston_gates()["gates"]
    lines.append("## Thesis gates")
    if gates:
        for g in gates[-8:]:
            parts = [f"entry {g['entry']}" if g.get("entry") else "", f"target {g['target']}" if g.get("target") else "",
                     f"stop {g['stop']}" if g.get("stop") else ""]
            lines.append(f"- **{g['ticker']}** " + " · ".join(p for p in parts if p))
    else:
        lines.append("- No thesis gates yet — write one before sizing a position.")
    return "\n".join(lines) + "\n"


@app.post("/houston/run")
def houston_run():
    """Run houston.py and return the saved brief as text. Without the research
    workstation's houston.py, build the native brief instead of failing."""
    import subprocess, datetime
    day = datetime.date.today().isoformat()
    if not (os.path.exists(HOUSTON_PY) and os.path.exists(HOUSTON_VENV)):
        return {"ok": True, "day": day, "brief": _native_brief(day), "native": True}
    result = subprocess.run(
        [HOUSTON_VENV, HOUSTON_PY],
        capture_output=True, text=True, timeout=60,
        cwd=os.path.expanduser("~/AeonNimbus"),
    )
    brief_path = os.path.expanduser(f"~/AeonNimbus/outputs/{day}/houston-{day}.md")
    if os.path.exists(brief_path):
        return {"ok": True, "day": day, "brief": open(brief_path).read()}
    if result.returncode != 0:
        raise HTTPException(500, result.stderr[:500] or "houston.py failed")
    return {"ok": True, "day": day, "brief": result.stdout}


@app.get("/houston/brief")
def houston_brief():
    """Return today's already-saved brief (no re-run)."""
    import datetime
    day = datetime.date.today().isoformat()
    brief_path = os.path.expanduser(f"~/AeonNimbus/outputs/{day}/houston-{day}.md")
    if not os.path.exists(brief_path):
        return {"ok": False, "brief": None, "day": day}
    return {"ok": True, "day": day, "brief": open(brief_path).read()}


@app.get("/houston/gates")
def houston_gates():
    """List all thesis gates."""
    import glob, re
    gates = []
    for path in sorted(glob.glob(os.path.join(GATES_DIR, "*.md"))):
        text = open(path, encoding="utf-8", errors="ignore").read()
        fname = os.path.basename(path)
        ticker = fname.split("-")[0].upper()
        g = {"ticker": ticker, "file": fname, "raw": text}
        for line in text.splitlines():
            if "|" in line and any(k in line.lower() for k in ("entry", "target", "stop")):
                parts = {p.split()[0].lower(): p.split()[-1]
                         for p in line.split("|") if p.strip() and len(p.split()) >= 2}
                g.update({k: parts[k] for k in ("entry","target","stop","size") if k in parts})
            if "kill condition" in line.lower() or "line 4" in line.lower():
                g["_next_is_kill"] = True
                continue
            if g.pop("_next_is_kill", False) and line.strip() and not line.startswith("#"):
                g["kill"] = line.strip()
        gates.append(g)
    return {"gates": gates}


class GateIn(BaseModel):
    ticker: str
    edge: str
    catalyst: str
    entry: str
    target: str
    stop: str
    size: str
    kill: str


@app.post("/houston/gates")
def houston_save_gate(g: GateIn):
    """Write a new thesis gate file."""
    import datetime
    tk = check(g.ticker)  # also keeps the filename inside GATES_DIR
    os.makedirs(GATES_DIR, exist_ok=True)
    day = datetime.date.today().isoformat()
    fname = f"{tk}-{day}.md"
    path = os.path.join(GATES_DIR, fname)
    content = f"""# Thesis Gate — {tk} — {day}

**Analyst:** LiJie Guo
**Status:** APPROVED

LINE 1 — EDGE
{g.edge}

LINE 2 — CATALYST
{g.catalyst}

LINE 3 — NUMBERS
Entry {g.entry} | Target {g.target} | Stop {g.stop} | Size {g.size}

LINE 4 — KILL CONDITION
{g.kill}

---
*Gate approved at {datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}. Research may proceed.*
"""
    open(path, "w", encoding="utf-8").write(content)
    return {"ok": True, "file": fname}


@app.get("/houston/notes")
def houston_notes(ticker: str = ""):
    """List research notes from the platform DB."""
    if not os.path.exists(PLATFORM_DB):
        return {"notes": []}
    import sqlite3
    conn = sqlite3.connect(PLATFORM_DB)
    try:
        q = "SELECT id,date,task,tickers,finding,created_at FROM research_notes ORDER BY created_at DESC LIMIT 50"
        rows = conn.execute(q).fetchall()
    except Exception:
        return {"notes": []}
    finally:
        conn.close()
    notes = [{"id":r[0],"date":r[1],"task":r[2],"tickers":r[3],"finding":r[4],"created_at":r[5]} for r in rows]
    if ticker:
        notes = [n for n in notes if n["tickers"] and ticker.upper() in n["tickers"].upper()]
    return {"notes": notes}


class NoteIn(BaseModel):
    date: str = ""
    task: str = ""
    tickers: str = ""
    finding: str


@app.post("/houston/notes")
def houston_save_note(n: NoteIn):
    """Save a research note to the platform DB."""
    if not os.path.exists(PLATFORM_DB):
        raise HTTPException(503, "Platform DB not found — is the platform running?")
    import sqlite3, datetime
    conn = sqlite3.connect(PLATFORM_DB)
    conn.execute(
        "INSERT INTO research_notes (date,task,tickers,finding,created_at) VALUES (?,?,?,?,?)",
        (n.date or datetime.date.today().isoformat(), n.task or None,
         n.tickers or None, n.finding,
         datetime.datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


# ─── Market Sentiment & Event Analysis ─────────────────────────────────────

@app.get("/api/market-events")
def get_market_events(limit: int = 100, category: Optional[str] = None, include_past: bool = False):
    """Market events with sentiment analysis — upcoming ones (and yesterday's) by
    default, so long-past events don't crowd out what's next."""
    from database import get_db
    where, args = [], []
    if category:
        where.append("category = ?")
        args.append(category)
    if not include_past:
        where.append("date(event_date) >= date('now', '-1 day')")
    sql = "SELECT * FROM market_events" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY event_date ASC LIMIT ?"
    with get_db() as conn:
        rows = conn.execute(sql, (*args, limit)).fetchall()

        events = []
        for row in rows:
            event = dict(row)
            # Parse JSON fields
            if event.get('affected_assets'):
                event['affected_assets'] = json.loads(event['affected_assets'])
            if event.get('analysis_json'):
                event['analysis'] = json.loads(event['analysis_json'])
            events.append(event)

        return {"events": events}


@app.post("/api/market-events")
def create_market_event(event: dict):
    """Create new market event"""
    from database import get_db
    missing = [k for k in ("title", "category", "event_date") if not event.get(k)]
    if missing:
        raise HTTPException(422, f"missing required field(s): {', '.join(missing)}")
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO market_events (title, category, event_date, affected_assets, raw_text)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event['title'],
            event['category'],
            event['event_date'],
            json.dumps(event.get('affected_assets', [])),
            event.get('raw_text', event['title'])
        ))
        event_id = cursor.lastrowid

        # Trigger automatic analysis
        analysis = analyze_market_event(event_id)

        return {"id": event_id, "analysis": analysis}


@app.delete("/api/market-events/{event_id}")
def delete_market_event(event_id: int):
    from database import get_db
    with get_db() as conn:
        cur = conn.execute("DELETE FROM market_events WHERE id = ?", (event_id,))
    if not cur.rowcount:
        raise HTTPException(404, "Event not found")
    return {"status": "deleted"}


@app.get("/api/market-events/{event_id}/analyze")
def analyze_event(event_id: int):
    """Analyze specific event with sentiment & impact scanning"""
    analysis = analyze_market_event(event_id)
    return {"analysis": analysis}


@app.get("/api/sentiment/scan")
def sentiment_scan(timeframe: str = "week"):
    """Scan all upcoming events and aggregate sentiment by timeframe"""
    from database import get_db
    from datetime import datetime, timedelta

    # Calculate timeframe window
    today = datetime.now().date()
    if timeframe == "day":
        end_date = today + timedelta(days=1)
    elif timeframe == "week":
        end_date = today + timedelta(days=7)
    elif timeframe == "month":
        end_date = today + timedelta(days=30)
    else:
        end_date = today + timedelta(days=7)

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM market_events
            WHERE date(event_date) BETWEEN date('now') AND date(?)
            ORDER BY event_date ASC
        """, (end_date.isoformat(),)).fetchall()

        # Aggregate sentiment by asset
        asset_sentiment = {}
        events_list = []

        for row in rows:
            event = dict(row)

            # Analyze if not yet analyzed
            if not event['analysis_json']:
                analysis = analyze_market_event(event['id'])
            else:
                analysis = json.loads(event['analysis_json'])

            events_list.append({
                **event,
                'analysis': analysis
            })

            # Aggregate by asset
            for asset_info in analysis.get('affected_assets', []):
                ticker = asset_info['ticker']
                if ticker not in asset_sentiment:
                    asset_sentiment[ticker] = {
                        'ticker': ticker,
                        'total_sentiment': 0,
                        'event_count': 0,
                        'events': []
                    }

                asset_sentiment[ticker]['total_sentiment'] += analysis['sentiment_score']
                asset_sentiment[ticker]['event_count'] += 1
                asset_sentiment[ticker]['events'].append(event['title'])

        # Calculate average sentiment per asset
        for ticker in asset_sentiment:
            count = asset_sentiment[ticker]['event_count']
            asset_sentiment[ticker]['avg_sentiment'] = asset_sentiment[ticker]['total_sentiment'] / count

        return {
            'timeframe': timeframe,
            'total_events': len(events_list),
            'events': events_list,
            'asset_sentiment': list(asset_sentiment.values()),
        }


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("AEON_ANALYTICS_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("AEON_ANALYTICS_PORT", "8000")))
    uvicorn.run(app, host=host, port=port)
