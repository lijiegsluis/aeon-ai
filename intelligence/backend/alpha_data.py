"""
Aeon Intelligence - data feeds for the alpha engine.

Every source here is keyless and was verified reachable from cloud hosts (GitHub
runners) with a browser TLS fingerprint:

  Nasdaq earnings calendar   market-wide, per day: reported EPS + % surprise for past
                             days, consensus forecast + report time for future days
  Nasdaq earnings date       next report date per ticker (Zacks-derived)
  Nasdaq earnings surprise   last 4 quarters of EPS vs consensus per ticker
  OpenInsider                market-wide insider cluster buys (parsed SEC Form 4s)
  CNN Fear & Greed           one year of daily index history
  Yahoo chart                daily OHLC price history

Past earnings days never change, so they are cached on disk forever; everything
else has a short TTL. Every fetch fails soft (None / []) and is recorded in
real_data's per-source status, which the Data Sources tab shows.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import real_data

_CACHE_DIR = Path(os.environ.get("AEON_INTEL_DB_PATH", str(Path.home() / ".aeon" / "intelligence.db"))).parent / "alpha_cache"
_MEM: Dict[str, tuple] = {}
_LOCK = threading.Lock()

NASDAQ_HEADERS = {"Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com",
                  "Referer": "https://www.nasdaq.com/"}


# ─── small parsing helpers ──────────────────────────────────────────

def _num(s: Any) -> Optional[float]:
    """'$1,234.5' -> 1234.5, '($0.04)' -> -0.04, 'N/A'/'' -> None."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).strip()
    neg = t.startswith("(") and t.endswith(")")
    t = re.sub(r"[^0-9.\-]", "", t)
    if t in ("", "-", "."):
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    return -abs(v) if neg else v


def _cached(key: str, ttl: float, fn, disk: bool = False):
    now = time.time()
    with _LOCK:
        hit = _MEM.get(key)
    if hit and (ttl is None or now - hit[0] < ttl):
        return hit[1]
    path = _CACHE_DIR / (re.sub(r"[^A-Za-z0-9_.-]", "_", key) + ".json")
    if disk and path.exists():
        try:
            payload = json.loads(path.read_text())
            if ttl is None or now - payload["t"] < ttl:
                with _LOCK:
                    _MEM[key] = (payload["t"], payload["v"])
                return payload["v"]
        except Exception:
            pass
    val = fn()
    if val is None:
        return hit[1] if hit else None  # keep the last good value on a failed refresh
    with _LOCK:
        _MEM[key] = (now, val)
    if disk:
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"t": now, "v": val}))
        except Exception as e:
            print(f"[alpha_data] cache write failed for {key}: {e}")
    return val


# ─── earnings ───────────────────────────────────────────────────────

_TIME = {"time-pre-market": "pre", "time-after-hours": "after"}


def _fetch_calendar(day: date) -> Optional[List[Dict[str, Any]]]:
    resp = real_data._get("https://api.nasdaq.com/api/calendar/earnings", headers=NASDAQ_HEADERS,
                          params={"date": day.isoformat()}, timeout=15, source_name="Nasdaq earnings calendar")
    if not resp:
        return None
    try:
        rows = ((resp.json().get("data") or {}).get("rows")) or []
    except Exception as e:
        print(f"[alpha_data] calendar parse error {day}: {e}")
        return None
    out = []
    for r in rows:
        sym = (r.get("symbol") or "").strip().upper()
        if not sym:
            continue
        out.append({
            "symbol": sym,
            "name": r.get("name"),
            "date": day.isoformat(),
            "time": _TIME.get(r.get("time"), "unknown"),
            "market_cap": _num(r.get("marketCap")),
            "eps_forecast": _num(r.get("epsForecast")),
            "eps_actual": _num(r.get("eps")),
            "surprise_pct": _num(r.get("surprise")),
            "num_estimates": _num(r.get("noOfEsts")),
            "fiscal_quarter": r.get("fiscalQuarterEnding"),
        })
    return out


def earnings_calendar(day: date) -> List[Dict[str, Any]]:
    """All companies reporting on `day`. Past days (already reported) are cached forever."""
    if day.weekday() >= 5:
        return []
    past = day < date.today() - timedelta(days=2)  # give late EPS updates two days to settle
    return _cached(f"cal_{day.isoformat()}", None if past else 6 * 3600,
                   lambda: _fetch_calendar(day), disk=True) or []


def earnings_between(start: date, end: date, pause: float = 0.25) -> List[Dict[str, Any]]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            key = f"cal_{d.isoformat()}"
            fresh = key not in _MEM and not (_CACHE_DIR / f"{key}.json").exists()
            out.extend(earnings_calendar(d))
            if fresh:
                time.sleep(pause)  # be polite on uncached fetches
        d += timedelta(days=1)
    return out


def next_earnings(ticker: str) -> Optional[Dict[str, Any]]:
    """{date, estimated} from Nasdaq's per-ticker earnings-date page. `estimated` is
    True while the date is Zacks' algorithmic projection rather than a company-confirmed one."""
    def fetch():
        resp = real_data._get(f"https://api.nasdaq.com/api/analyst/{ticker.upper()}/earnings-date",
                              headers=NASDAQ_HEADERS, timeout=12, source_name="Nasdaq earnings date")
        if not resp:
            return None
        try:
            data = resp.json().get("data") or {}
            text = data.get("announcement") or ""
            m = re.search(r"([A-Z][a-z]{2}) (\d{1,2}), (\d{4})", text)
            if not m:
                return None
            d = datetime.strptime(" ".join(m.groups()), "%b %d %Y").date().isoformat()
            return {"date": d, "estimated": "estimated" in (data.get("reportText") or "").lower()}
        except Exception:
            return None
    return _cached(f"nextearn_{ticker.upper()}", 12 * 3600, fetch)


def earnings_surprises(ticker: str) -> List[Dict[str, Any]]:
    """Last four quarters: report date, EPS, consensus, % surprise."""
    def fetch():
        resp = real_data._get(f"https://api.nasdaq.com/api/company/{ticker.upper()}/earnings-surprise",
                              headers=NASDAQ_HEADERS, timeout=12, source_name="Nasdaq earnings surprise")
        if not resp:
            return None
        try:
            rows = (((resp.json().get("data") or {}).get("earningsSurpriseTable") or {}).get("rows")) or []
            out = []
            for r in rows:
                d = datetime.strptime(r["dateReported"], "%m/%d/%Y").date().isoformat()
                out.append({"date": d, "eps": _num(r.get("eps")), "forecast": _num(r.get("consensusForecast")),
                            "surprise_pct": _num(r.get("percentageSurprise"))})
            return out
        except Exception:
            return None
    return _cached(f"surprise_{ticker.upper()}", 24 * 3600, fetch, disk=True) or []


# ─── insiders ───────────────────────────────────────────────────────

def _parse_openinsider(html: str) -> List[Dict[str, Any]]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="tinytable")
    if table is None:
        return []
    heads = [th.get_text(" ", strip=True).replace("\xa0", " ") for th in table.find("thead").find_all("th")]

    def col(name):
        for i, h in enumerate(heads):
            if h.lower().startswith(name.lower()):
                return i
        return None

    ix = {k: col(k) for k in ("Filing", "Trade Date", "Ticker", "Company", "Industry", "Ins", "Trade Type",
                              "Price", "Qty", "Owned", "ΔOwn", "Value")}
    out = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]

        def get(k):
            i = ix.get(k)
            return cells[i] if i is not None and i < len(cells) else None

        ticker = (get("Ticker") or "").upper()
        filed, traded = (get("Filing") or "")[:10], (get("Trade Date") or "")[:10]
        if not ticker or not re.match(r"\d{4}-\d{2}-\d{2}", filed or ""):
            continue
        out.append({
            "ticker": ticker, "company": get("Company"), "industry": get("Industry"),
            "filing_date": filed, "trade_date": traded or filed,
            "insiders": int(_num(get("Ins")) or 0), "trade_type": get("Trade Type"),
            "price": _num(get("Price")), "qty": _num(get("Qty")), "owned_change_pct": _num(get("ΔOwn")),
            "value": _num(get("Value")),
        })
    return out


def insider_cluster_buys() -> List[Dict[str, Any]]:
    """Latest market-wide cluster buys (2+ insiders, open-market purchases)."""
    def fetch():
        resp = real_data._get("http://openinsider.com/latest-cluster-buys", timeout=20,
                              source_name="OpenInsider cluster buys")
        if not resp:
            return None
        try:
            rows = _parse_openinsider(resp.text)
            return rows or None
        except Exception as e:
            print(f"[alpha_data] openinsider parse error: {e}")
            return None
    return _cached("oi_clusters", 3 * 3600, fetch, disk=True) or []


# ─── sentiment ──────────────────────────────────────────────────────

def fear_greed_history() -> List[Dict[str, Any]]:
    """[{date, value}] for the last year of CNN Fear & Greed readings."""
    def fetch():
        resp = real_data._get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                              headers={"Accept": "application/json", "Referer": "https://www.cnn.com/markets/fear-and-greed"},
                              timeout=15, source_name="CNN Fear & Greed history")
        if not resp:
            return None
        try:
            pts = (resp.json().get("fear_and_greed_historical") or {}).get("data") or []
            by_day = {datetime.utcfromtimestamp(p["x"] / 1000).date().isoformat(): round(float(p["y"]), 1) for p in pts}
            return [{"date": d, "value": v} for d, v in sorted(by_day.items())] or None
        except Exception:
            return None
    return _cached("fg_hist", 6 * 3600, fetch, disk=True) or []


# ─── prices ─────────────────────────────────────────────────────────

def price_history(ticker: str, rng: str = "2y") -> List[Dict[str, Any]]:
    """Daily bars [{date, open, high, low, close}] oldest first, via Yahoo's chart API."""
    tk = ticker.upper()

    def fetch():
        for host in ("query2", "query1"):
            resp = real_data._get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{tk}",
                                  params={"range": rng, "interval": "1d"}, timeout=15,
                                  source_name="Yahoo Finance price history")
            if not resp:
                continue
            try:
                res = resp.json()["chart"]["result"][0]
                q = res["indicators"]["quote"][0]
                bars = []
                for i, ts in enumerate(res.get("timestamp") or []):
                    c = q["close"][i]
                    if c is None:
                        continue
                    bars.append({"date": datetime.utcfromtimestamp(ts).date().isoformat(), "open": q["open"][i],
                                 "high": q["high"][i], "low": q["low"][i], "close": round(c, 4)})
                # the last bar can repeat today's date during the session — keep the latest
                dedup = {b["date"]: b for b in bars}
                return [dedup[d] for d in sorted(dedup)] or None
            except Exception:
                continue
        return None
    # one fetch per ticker per ~6h is plenty for daily-bar strategies
    return _cached(f"px_{tk}_{rng}", 6 * 3600, fetch, disk=True) or []
