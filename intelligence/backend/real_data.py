"""
Aeon Intelligence - Real Data Layer

Synchronous, dependency-light fetchers for free/no-key data sources, used to
replace the mock generators in populated_api.py. Every function fails soft:
on any network/parse error it logs and returns None/[] so a single flaky
source never takes the whole app down. Callers keep last-known-good data.
"""

import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import feedparser
import requests

FRED_BASE = "https://api.stlouisfed.org/fred"

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# SEC requires a descriptive User-Agent with a real contact address for fair-use
# access (sec.gov/os/accessing-edgar-data). Set SEC_CONTACT_EMAIL in production.
SEC_UA = f"AeonIntelligence research {os.environ.get('SEC_CONTACT_EMAIL', 'contact@aeonnimbus.com')}"

_SESSION = requests.Session()

try:  # browser TLS fingerprint for hosts that 403/429 plain HTTP clients from cloud IPs
    from curl_cffi import requests as _browser
except ImportError:  # pragma: no cover
    _browser = None
_BROWSER_HOSTS = ("finance.yahoo.com", "bls.gov", "coingecko.com")

# Real, accumulated-since-process-start per-source call outcomes - never
# randomized or backfilled. Powers /api/sources/status. Keyed by the caller's
# own source_name, not by URL, so multiple RSS feeds etc. show up distinctly.
_SOURCE_STATUS: Dict[str, Dict[str, Any]] = {}


def _record_status(source_name: str, ok: bool, status_code: Optional[int], error: Optional[str] = None) -> None:
    entry = _SOURCE_STATUS.setdefault(source_name, {
        "last_attempt_at": None, "last_success_at": None, "last_status_code": None,
        "last_error": None, "success_count": 0, "fail_count": 0,
    })
    now = datetime.now().isoformat()
    entry["last_attempt_at"] = now
    entry["last_status_code"] = status_code
    if ok:
        entry["last_success_at"] = now
        entry["last_error"] = None
        entry["success_count"] += 1
    else:
        entry["last_error"] = error or f"HTTP {status_code}"
        entry["fail_count"] += 1


def get_source_status() -> Dict[str, Dict[str, Any]]:
    """Real per-source status snapshot, computed from actual call outcomes this process has made."""
    out = {}
    for name, entry in _SOURCE_STATUS.items():
        total = entry["success_count"] + entry["fail_count"]
        success_rate = round(entry["success_count"] / total, 3) if total else None
        if entry["success_count"] and not entry["fail_count"]:
            status = "active"
        elif entry["success_count"]:
            status = "degraded"
        else:
            status = "down"
        out[name] = {**entry, "success_rate": success_rate, "status": status}
    return out


def _get(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None,
          timeout: float = 8.0, source_name: Optional[str] = None) -> Optional[requests.Response]:
    try:
        if _browser is not None and any(h in url for h in _BROWSER_HOSTS):
            # let curl_cffi send a real browser's headers; only keep non-UA extras
            extra = {k: v for k, v in (headers or {}).items() if k.lower() != "user-agent"}
            resp = _browser.get(url, headers=extra or None, params=params, timeout=timeout, impersonate="chrome")
        else:
            resp = _SESSION.get(url, headers=headers, params=params, timeout=timeout)
        if resp.status_code == 200:
            if source_name:
                _record_status(source_name, True, resp.status_code)
            return resp
        print(f"[real_data] GET {url} -> HTTP {resp.status_code}")
        if source_name:
            _record_status(source_name, False, resp.status_code)
    except Exception as e:
        print(f"[real_data] GET {url} failed: {e}")
        if source_name:
            _record_status(source_name, False, None, error=str(e))
    return None


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------

def get_fear_greed() -> Optional[Dict[str, Any]]:
    """CNN Fear & Greed Index. Needs a browser-like UA or CNN returns 418."""
    resp = _get(
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        headers={
            "User-Agent": BROWSER_UA,
            "Accept": "application/json",
            "Referer": "https://www.cnn.com/markets/fear-and-greed",
        },
        source_name="CNN Fear & Greed",
    )
    if not resp:
        return None
    try:
        data = resp.json()
        fg = data.get("fear_and_greed", {})
        return {"value": round(fg.get("score", 50)), "rating": fg.get("rating", "neutral")}
    except Exception as e:
        print(f"[real_data] fear_greed parse error: {e}")
        return None


def get_vix() -> Optional[float]:
    """Real-time VIX via Yahoo Finance chart API. Rate-limited, so callers should cache."""
    resp = _get(
        "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX",
        headers={"User-Agent": BROWSER_UA},
        params={"interval": "1d", "range": "5d"},
        source_name="Yahoo Finance VIX",
    )
    if not resp:
        return None
    try:
        result = resp.json()["chart"]["result"][0]
        closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
        return round(closes[-1], 2) if closes else None
    except Exception as e:
        print(f"[real_data] vix parse error: {e}")
        return None


def _fetch_yahoo_chart(ticker: str, source_name: str = "Yahoo Finance Price") -> Optional[Dict[str, Any]]:
    """Shared single-fetch helper for the Yahoo chart endpoint - used by get_current_price(),
    get_screener_snapshot() and get_fed_funds_futures() so a caller that needs both price and
    the previous close never has to make two network calls for the same ticker."""
    resp = _get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
        headers={"User-Agent": BROWSER_UA},
        params={"interval": "1d", "range": "5d"},
        source_name=source_name,
    )
    if not resp:
        return None
    try:
        return resp.json()["chart"]["result"][0]
    except Exception as e:
        print(f"[real_data] chart parse error for {ticker}: {e}")
        return None


def get_current_price(ticker: str) -> Optional[float]:
    """Real-time last close for any ticker, via the same Yahoo chart API as get_vix()."""
    result = _fetch_yahoo_chart(ticker)
    if not result:
        return None
    try:
        closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
        return round(closes[-1], 2) if closes else None
    except Exception as e:
        print(f"[real_data] price parse error for {ticker}: {e}")
        return None


def get_screener_snapshot(tickers: List[str]) -> List[Dict[str, Any]]:
    """Real current price + change-vs-previous-close for a fixed ticker universe, via one
    Yahoo chart fetch per ticker (same endpoint/UA as get_current_price(), source_name shared
    so this doesn't create a duplicate row in /api/sources/status). Skips any ticker whose
    fetch fails - never fabricates a price or a flat 0% change."""
    out: List[Dict[str, Any]] = []
    for ticker in tickers:
        result = _fetch_yahoo_chart(ticker)
        if not result:
            continue
        try:
            closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
            if not closes:
                continue
            price = round(closes[-1], 2)
            meta = result.get("meta", {}) or {}
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
            if prev_close is None and len(closes) >= 2:
                prev_close = closes[-2]
            change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else None
            out.append({"ticker": ticker, "price": price, "change_pct": change_pct})
        except Exception as e:
            print(f"[real_data] screener parse error for {ticker}: {e}")
            continue
        time.sleep(0.1)
    return out


def get_fed_funds_futures() -> Optional[Dict[str, Any]]:
    """Market-implied Fed Funds rate via CME Fed Funds futures (front-month continuous
    contract ZQ=F), through the same keyless Yahoo chart endpoint as get_vix(). This is the
    real, always-available FedWatch-equivalent - implied rate = 100 - futures price."""
    result = _fetch_yahoo_chart("ZQ=F", source_name="CME Fed Funds Futures")
    if not result:
        return None
    try:
        closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
        if not closes:
            return None
        price = round(closes[-1], 3)
        return {
            "contract": "ZQ=F",
            "price": price,
            "implied_rate_pct": round(100 - price, 3),
            "as_of": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"[real_data] fed funds futures parse error: {e}")
        return None


def get_fed_funds_rate() -> Optional[Dict[str, Any]]:
    """Real Fed Funds target range + effective rate via FRED. Only attempted when
    FRED_API_KEY is set in the environment (boolean presence check only, key value is never
    logged) - same gating pattern as GROQ_API_KEY/GEMINI_API_KEY in ai_engine.py. Absent key
    means this source is simply never called and never appears in /api/sources/status."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return None
    series = {"target_upper": "DFEDTARU", "target_lower": "DFEDTARL", "effective_rate": "EFFR"}
    out: Dict[str, Any] = {}
    for label, series_id in series.items():
        resp = _get(
            f"{FRED_BASE}/series/observations",
            params={"series_id": series_id, "api_key": api_key, "file_type": "json",
                     "sort_order": "desc", "limit": 1},
            source_name="FRED Fed Funds Rate",
        )
        if not resp:
            continue
        try:
            obs = resp.json().get("observations") or []
            if obs and obs[0].get("value") not in (None, "."):
                out[label] = {"value": float(obs[0]["value"]), "date": obs[0]["date"]}
        except Exception as e:
            print(f"[real_data] FRED {series_id} parse error: {e}")
    return out or None


def get_economic_releases() -> Optional[List[Dict[str, Any]]]:
    """Real upcoming US economic release dates (CPI, Employment Situation/NFP, PPI, GDP,
    FOMC) via FRED's releases/dates endpoint, filtered by release name rather than hardcoded
    release IDs (which could silently drift/be wrong). Only attempted when FRED_API_KEY is
    set - same gating as get_fed_funds_rate()."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return None
    today = datetime.now().date().isoformat()
    resp = _get(
        f"{FRED_BASE}/releases/dates",
        params={"api_key": api_key, "file_type": "json", "realtime_start": today,
                 "include_release_dates_with_no_data": "true", "sort_order": "asc", "limit": 1000},
        source_name="FRED Economic Releases",
    )
    if not resp:
        return None
    keywords = ("Consumer Price Index", "Employment Situation", "Producer Price Index",
                "Gross Domestic Product", "Federal Open Market Committee")
    try:
        dates = resp.json().get("release_dates") or []
        out = [{"release": d["release_name"], "date": d["date"]} for d in dates
               if any(k.lower() in d.get("release_name", "").lower() for k in keywords)]
        return out[:20] or None
    except Exception as e:
        print(f"[real_data] FRED releases parse error: {e}")
        return None


def get_investing_economic_calendar() -> Optional[List[Dict[str, Any]]]:
    """Best-effort real fetch of investing.com's public economic calendar page. Confirmed live
    this session that investing.com bot-protects this specific page (HTTP 403 even with full
    browser headers), so this is expected to honestly surface as status 'down' in
    /api/sources/status - attempted anyway per the user's explicit request, never faked."""
    resp = _get(
        "https://www.investing.com/economic-calendar/",
        headers={
            "User-Agent": BROWSER_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        source_name="Investing.com Economic Calendar",
    )
    if not resp:
        return None
    try:
        rows = re.findall(r'event="([^"]+)"[^>]*data-event-datetime="([^"]+)"', resp.text)
        return [{"event": e, "datetime": dt} for e, dt in rows[:30]] or None
    except Exception as e:
        print(f"[real_data] investing.com calendar parse error: {e}")
        return None


def get_earnings_date(ticker: str) -> Optional[str]:
    """Real next-earnings date for a ticker via Yahoo's quoteSummary calendarEvents module.

    This endpoint requires a valid crumb/cookie as of 2026 (confirmed live: a bare
    request returns HTTP 401 "Invalid Crumb", and the cookie+getcrumb dance yahoo's
    own JS flow uses also failed against this endpoint in testing - too unreliable
    to depend on). Kept as a real, honestly-attempted fetch; callers must fall back
    to a clearly-labeled estimate when this returns None, never a silent guess.
    """
    resp = _get(
        f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}",
        headers={"User-Agent": BROWSER_UA},
        params={"modules": "calendarEvents"},
        source_name="Yahoo Finance Earnings Calendar",
    )
    if not resp:
        return None
    try:
        earnings = resp.json()["quoteSummary"]["result"][0]["calendarEvents"]["earnings"]
        dates = earnings.get("earningsDate") or []
        if not dates:
            return None
        return datetime.fromtimestamp(dates[0]["raw"]).isoformat()
    except Exception as e:
        print(f"[real_data] earnings date parse error for {ticker}: {e}")
        return None


def get_reddit_sentiment(subreddit: str = "wallstreetbets", limit: int = 25) -> Optional[Dict[str, Any]]:
    """Public Reddit JSON endpoint - no API key needed. Used as a social-sentiment proxy."""
    resp = _get(
        f"https://www.reddit.com/r/{subreddit}/hot.json",
        headers={"User-Agent": BROWSER_UA},
        params={"limit": limit},
        source_name=f"Reddit r/{subreddit}",
    )
    if not resp:
        return None
    try:
        children = resp.json().get("data", {}).get("children", [])
        posts = [c.get("data", {}) for c in children]
        if not posts:
            return None
        avg_ratio = sum(p.get("upvote_ratio", 0.5) for p in posts) / len(posts)
        total_score = sum(p.get("score", 0) for p in posts)
        # Map avg upvote ratio (0.5-1.0 typical range) onto a 0-100 sentiment score
        value = max(0, min(100, round((avg_ratio - 0.5) * 200)))
        return {"value": value, "avg_upvote_ratio": round(avg_ratio, 3), "total_score": total_score,
                "top_titles": [p.get("title", "") for p in posts[:5]]}
    except Exception as e:
        print(f"[real_data] reddit parse error: {e}")
        return None


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

# Feeds verified reachable with a standard UA (Reuters/CNBC direct feeds 403 without
# a residential IP, so we stick to sources that responded 200 in testing).
NEWS_FEEDS = [
    ("MarketWatch", "http://feeds.marketwatch.com/marketwatch/topstories/"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Investing.com", "https://www.investing.com/rss/news_25.rss"),
    ("Seeking Alpha", "https://seekingalpha.com/market_currents.xml"),
]

_BULLISH_WORDS = {"beat", "beats", "surge", "surges", "rally", "rallies", "soar", "soars", "jump", "jumps",
                   "gain", "gains", "record", "upgrade", "upgraded", "strong", "growth", "raises", "raise",
                   "approval", "approved", "outperform", "bullish"}
_BEARISH_WORDS = {"miss", "misses", "plunge", "plunges", "crash", "crashes", "drop", "drops", "fall", "falls",
                   "downgrade", "downgraded", "weak", "cuts", "cut", "recall", "lawsuit", "probe", "fraud",
                   "bearish", "selloff", "sell-off", "slump", "slumps"}


def _classify_sentiment(text: str) -> str:
    words = set(re.findall(r"[a-z']+", text.lower()))
    bullish = len(words & _BULLISH_WORDS)
    bearish = len(words & _BEARISH_WORDS)
    if bullish > bearish:
        return "bullish"
    if bearish > bullish:
        return "bearish"
    return "neutral"


def _extract_tickers(text: str, watchlist: List[str]) -> str:
    upper = text.upper()
    found = [t for t in watchlist if re.search(rf"\b{re.escape(t)}\b", upper)]
    # No match means the story isn't about a tracked ticker - don't pin it on SPY,
    # or every untagged headline turns into an SPY "signal".
    return ",".join(found)


WATCHLIST = ["NVDA", "AAPL", "MSFT", "GOOGL", "META", "TSLA", "AMD", "AMZN", "ORCL", "COIN", "SQ", "SHOP",
             "SPY", "QQQ", "XLE", "BTC", "ETH"]


def get_real_news(limit: int = 30) -> List[Dict[str, Any]]:
    """Aggregate real RSS feeds into the app's news item shape."""
    items: List[Dict[str, Any]] = []
    seen_titles = set()

    for source, url in NEWS_FEEDS:
        # Fetch via requests (uses certifi's CA bundle) rather than feedparser's own
        # urlopen, which relies on the system SSL store and can fail to verify certs
        # in some Python installs (e.g. python.org builds without Install Certificates run).
        resp = _get(url, headers={"User-Agent": BROWSER_UA}, source_name=f"RSS: {source}")
        if resp is None:
            continue
        try:
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"[real_data] feed parse failed for {source}: {e}")
            continue

        for entry in feed.entries[:20]:
            title = entry.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            summary = re.sub("<[^<]+?>", "", entry.get("summary", ""))[:280]
            full_text = f"{title} {summary}"

            published_at = datetime.now()
            for key in ("published_parsed", "updated_parsed"):
                parsed = entry.get(key)
                if parsed:
                    try:
                        published_at = datetime(*parsed[:6])
                    except Exception:
                        pass
                    break

            items.append({
                "title": title,
                "published_at": published_at.isoformat(),
                "source": source,
                "sentiment": _classify_sentiment(full_text),
                "summary": summary or title,
                "tickers": _extract_tickers(full_text, WATCHLIST),
                "url": entry.get("link", ""),
                "urgency": "high" if _classify_sentiment(full_text) != "neutral" else "medium",
            })

    items.sort(key=lambda x: x["published_at"], reverse=True)
    return items[:limit]


# ---------------------------------------------------------------------------
# Crypto
# ---------------------------------------------------------------------------

_COINS = [("bitcoin", "BTC", "Bitcoin"), ("ethereum", "ETH", "Ethereum"), ("solana", "SOL", "Solana")]


def get_crypto_prices() -> Optional[List[Dict[str, Any]]]:
    ids = ",".join(c[0] for c in _COINS)
    resp = _get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": ids, "vs_currencies": "usd", "include_24hr_change": "true", "include_market_cap": "true",
                "include_24hr_vol": "true"},
        source_name="CoinGecko",
    )
    if not resp:
        return None
    try:
        data = resp.json()
        out = []
        for idx, (coingecko_id, symbol, name) in enumerate(_COINS):
            d = data.get(coingecko_id)
            if not d:
                continue
            out.append({
                "id": idx + 1,
                "symbol": symbol,
                "name": name,
                "price": d.get("usd"),
                "change_24h": round(d.get("usd_24h_change", 0.0), 2),
                "market_cap": d.get("usd_market_cap"),
                "volume_24h": d.get("usd_24h_vol"),
                "source": "CoinGecko",
                "timestamp": datetime.now().isoformat(),
            })
        return out or None
    except Exception as e:
        print(f"[real_data] crypto parse error: {e}")
        return None


# ---------------------------------------------------------------------------
# SEC EDGAR: ticker map + real-time Form 4 insider trading
# ---------------------------------------------------------------------------

_TICKER_MAP_CACHE: Dict[str, Dict[str, str]] = {}


def get_sec_ticker_map() -> Dict[str, Dict[str, str]]:
    """CIK (unpadded str) -> {ticker, name}. Cached in-process; call refresh_ticker_map() to force reload."""
    global _TICKER_MAP_CACHE
    if _TICKER_MAP_CACHE:
        return _TICKER_MAP_CACHE
    resp = _get("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": SEC_UA},
                source_name="SEC EDGAR Ticker Map")
    if not resp:
        return {}
    try:
        data = resp.json()
        mapping = {}
        for entry in data.values():
            cik = str(entry.get("cik_str"))
            mapping[cik] = {"ticker": entry.get("ticker", ""), "name": entry.get("title", "")}
        _TICKER_MAP_CACHE = mapping
        return mapping
    except Exception as e:
        print(f"[real_data] ticker map parse error: {e}")
        return {}


_FORM4_ATOM_URL = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&dateb="
                    "&owner=include&count={count}&output=atom")

_ENTRY_RE = re.compile(
    r"<entry>.*?<title>(?P<title>[^<]*)</title>\s*"
    r"<link rel=\"alternate\" type=\"text/html\" href=\"(?P<href>[^\"]*)\"/>.*?"
    r"<updated>(?P<updated>[^<]*)</updated>.*?</entry>",
    re.DOTALL,
)


def _fetch_form4_index_entries(count: int = 60) -> List[Dict[str, str]]:
    resp = _get(_FORM4_ATOM_URL.format(count=count), headers={"User-Agent": SEC_UA},
                source_name="SEC EDGAR Form 4")
    if not resp:
        return []
    entries = []
    for m in _ENTRY_RE.finditer(resp.text):
        entries.append({"title": m.group("title"), "href": m.group("href"), "updated": m.group("updated")})
    return entries


def _find_form4_xml_url(index_url: str) -> Optional[str]:
    resp = _get(index_url, headers={"User-Agent": SEC_UA}, source_name="SEC EDGAR Form 4")
    if not resp:
        return None
    # The plain (non-xslF345X06) .xml file is the raw ownershipDocument.
    candidates = re.findall(r'href="(/Archives/edgar/data/[^"]*?\.xml)"', resp.text)
    plain = [c for c in candidates if "xslF345X06" not in c]
    if not plain:
        return None
    return "https://www.sec.gov" + plain[0]


def _parse_form4_xml(xml_text: str) -> Optional[Dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except Exception as e:
        print(f"[real_data] form4 xml parse error: {e}")
        return None

    def _text(path: str, node=root) -> str:
        el = node.find(path)
        return el.text.strip() if el is not None and el.text else ""

    issuer_cik = _text("issuer/issuerCik").lstrip("0") or "0"
    issuer_ticker = _text("issuer/issuerTradingSymbol")
    issuer_name = _text("issuer/issuerName")
    owner_name = _text("reportingOwner/reportingOwnerId/rptOwnerName")
    is_officer = _text("reportingOwner/reportingOwnerRelationship/isOfficer") == "true"
    is_director = _text("reportingOwner/reportingOwnerRelationship/isDirector") == "true"
    officer_title = _text("reportingOwner/reportingOwnerRelationship/officerTitle")
    role = officer_title or ("Director" if is_director else ("Officer" if is_officer else "10% Owner"))

    bought_value = 0.0
    bought_shares = 0
    sold_value = 0.0
    sold_shares = 0
    latest_date = ""

    for txn in root.findall(".//nonDerivativeTransaction"):
        # Only open-market trades carry a conviction signal: P = purchase, S = sale.
        # Grants (A), option exercises (M), tax withholding (F), gifts (G) etc. also
        # move shares in or out but say nothing about what the insider thinks.
        code = _text("transactionCoding/transactionCode", txn)
        if code not in ("P", "S"):
            continue
        shares_txt = _text("transactionAmounts/transactionShares/value", txn)
        price_txt = _text("transactionAmounts/transactionPricePerShare/value", txn)
        acq_disp = _text("transactionAmounts/transactionAcquiredDisposedCode/value", txn)
        date_txt = _text("transactionDate/value", txn)
        if date_txt:
            latest_date = max(latest_date, date_txt)
        try:
            shares = float(shares_txt)
            price = float(price_txt) if price_txt else 0.0
        except ValueError:
            continue
        value = shares * price
        if code == "P" and acq_disp != "D":
            bought_shares += int(shares)
            bought_value += value
        elif code == "S" and acq_disp != "A":
            sold_shares += int(shares)
            sold_value += value

    if bought_value == 0 and sold_value == 0:
        return None

    is_buy = bought_value >= sold_value
    return {
        "issuer_cik": issuer_cik,
        "issuer_ticker": issuer_ticker,
        "issuer_name": issuer_name,
        "insider_name": owner_name,
        "role": role,
        "is_buy": is_buy,
        "shares": bought_shares if is_buy else sold_shares,
        "total_value": bought_value if is_buy else sold_value,
        "price": (bought_value / bought_shares) if is_buy and bought_shares else
                 (sold_value / sold_shares if sold_shares else 0.0),
        "date": latest_date or datetime.now().strftime("%Y-%m-%d"),
    }


def get_recent_form4_trades(max_filings: int = 25) -> List[Dict[str, Any]]:
    """Fetch and parse the most recent real SEC Form 4 filings. Network-heavy - call on a slow refresh cycle."""
    entries = _fetch_form4_index_entries(count=max_filings * 2)
    seen_hrefs = set()
    seen_trades = set()
    trades: List[Dict[str, Any]] = []

    for entry in entries:
        href = entry["href"]
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        if len(trades) >= max_filings:
            break

        xml_url = _find_form4_xml_url(href)
        if not xml_url:
            continue
        time.sleep(0.15)  # be gentle with SEC's servers
        xml_resp = _get(xml_url, headers={"User-Agent": SEC_UA}, source_name="SEC EDGAR Form 4")
        if not xml_resp:
            continue
        parsed = _parse_form4_xml(xml_resp.text)
        if parsed:
            parsed["filed_at"] = entry["updated"][:10] if entry.get("updated") else parsed["date"]
            # SEC's real-time Form 4 feed lists a single filing once per named party
            # (issuer + each reporting owner), so the same document can show up under
            # more than one href. Dedup on content, not just href.
            dedup_key = (parsed["issuer_cik"], parsed["insider_name"], parsed["date"],
                         parsed["shares"], round(parsed["total_value"], 2))
            if dedup_key in seen_trades:
                continue
            seen_trades.add(dedup_key)
            trades.append(parsed)
        time.sleep(0.15)

    return trades


# ---------------------------------------------------------------------------
# Official release schedules (keeps the calendar current past the hardcoded year)
# ---------------------------------------------------------------------------

_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]
_MONTH_RE = "|".join(_MONTHS)


def parse_fomc_calendar(html: str) -> Dict[int, List[datetime]]:
    """Decision days (the last day of each meeting) per year from the Fed's
    fomccalendars.htm. Works on the page's visible text, so markup changes don't
    break it: each year's block starts at "<year> FOMC Meetings" and lists meetings
    as "January 27-28", "April/May 30-1" or "March 18*" (asterisk = SEP meeting)."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;|\s+", " ", text)
    blocks = list(re.finditer(r"(20\d\d) FOMC Meetings", text))
    out: Dict[int, List[datetime]] = {}
    for i, m in enumerate(blocks):
        year = int(m.group(1))
        body = text[m.end(): blocks[i + 1].start() if i + 1 < len(blocks) else len(text)]
        dates = []
        # Scheduled meetings are always two-day ranges ("January 27-28"); single dates
        # elsewhere on the page are notation votes, minutes releases and the like.
        pat = rf"\b({_MONTH_RE})(?:\s*/\s*({_MONTH_RE}))?\s+(\d{{1,2}})\s*[-\u2013]\s*(\d{{1,2}})\*?"
        for mm in re.finditer(pat, body):
            start_day = int(mm.group(3))
            day = int(mm.group(4))
            # "April/May 28-29" is all April; only a wrapped range ("October/November 31-1")
            # ends in the second month.
            month = mm.group(2) if mm.group(2) and day < start_day else mm.group(1)
            try:
                dates.append(datetime(year, _MONTHS.index(month) + 1, day, 14, 0))
            except ValueError:
                continue
        dates = sorted(set(dates))
        # A meeting is listed once per year; drop repeats within a week (e.g. a
        # rescheduled meeting shown next to its original date).
        dates = [d for i, d in enumerate(dates) if i == 0 or (d - dates[i - 1]).days > 7]
        if 4 <= len(dates) <= 12:  # anything else means the parse went wrong
            out[year] = dates
    return out


def get_fomc_schedule() -> Dict[int, List[datetime]]:
    resp = _get("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
                headers={"User-Agent": BROWSER_UA}, timeout=15, source_name="Federal Reserve FOMC calendar")
    if resp is None:
        return {}
    try:
        return parse_fomc_calendar(resp.text)
    except Exception as e:
        print(f"[real_data] FOMC calendar parse failed: {e}")
        return {}


_BLS_RELEASES = {
    "Employment Situation": "nfp",
    "Consumer Price Index": "cpi",
    "Producer Price Index": "ppi",
}


def parse_bls_ics(ics: str) -> Dict[str, List[datetime]]:
    """Release datetimes (ET) for NFP / CPI / PPI from BLS's news-release iCalendar."""
    ics = re.sub(r"\r?\n[ \t]", "", ics)  # unfold continued lines
    out: Dict[str, List[datetime]] = {k: [] for k in _BLS_RELEASES.values()}
    for block in ics.split("BEGIN:VEVENT")[1:]:
        summary = re.search(r"^SUMMARY[^:]*:(.*)$", block, re.M)
        start = re.search(r"^DTSTART[^:]*:(\d{8})(?:T(\d{4}))?", block, re.M)
        if not summary or not start:
            continue
        title = summary.group(1).strip()
        for name, key in _BLS_RELEASES.items():
            if title.startswith(name):
                d, t = start.group(1), start.group(2) or "0830"
                out[key].append(datetime(int(d[:4]), int(d[4:6]), int(d[6:8]), int(t[:2]), int(t[2:])))
    return {k: sorted(set(v)) for k, v in out.items() if v}


def get_bls_schedule() -> Dict[str, List[datetime]]:
    resp = _get("https://www.bls.gov/schedule/news_release/bls.ics",
                headers={"User-Agent": BROWSER_UA, "Accept": "text/calendar,*/*"},
                timeout=15, source_name="BLS release calendar")
    if resp is None:
        return {}
    try:
        return parse_bls_ics(resp.text)
    except Exception as e:
        print(f"[real_data] BLS calendar parse failed: {e}")
        return {}
