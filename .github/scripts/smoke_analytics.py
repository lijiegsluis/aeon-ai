"""Exercise the analytics market-data fallbacks against the real upstreams."""
import traceback

import market_data as md


def check(label, fn):
    try:
        print(f"OK   {label}: {fn()}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {label}: {type(e).__name__}: {e}")
        traceback.print_exc(limit=1)


for name, fn in (("yfinance", md._yf_history), ("yahoo-chart", md._chart_history), ("stooq", md._stooq_history)):
    check(f"history via {name}", lambda fn=fn: f"{len(fn('AAPL', '1y', '1d'))} rows")
check("history (with fallbacks)", lambda: f"{len(md.history('MSFT', '6mo'))} rows via {md.LAST_SOURCE.get('history')}")
check("info", lambda: {k: md.info("NVDA").get(k) for k in ("currentPrice", "regularMarketPrice", "trailingPE", "_source")})
check("chart-only quote", lambda: md._info_from_chart("SPY"))
print("fallback errors:", md.LAST_ERROR)

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402

client = TestClient(main.app)
for path in ("/market/quote/AAPL", "/quant/dcf/AAPL", "/fusion/valuation/AAPL", "/fusion/quote/AAPL",
             "/market/compare?tickers=AAPL,SPY", "/research/snapshot/AAPL"):
    check(path, lambda path=path: (lambda r: f"{r.status_code} {r.text[:240]}")(client.get(path)))
