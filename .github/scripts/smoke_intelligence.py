"""Hit every real Intelligence source once and print what came back."""
import real_data as rd


def check(label, fn):
    try:
        print(f"OK   {label}: {fn()}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {label}: {type(e).__name__}: {e}")


check("FOMC schedule", lambda: {y: [d.strftime("%m-%d") for d in ds] for y, ds in rd.get_fomc_schedule().items()})
check("BLS schedule", lambda: {k: [d.strftime("%Y-%m-%d") for d in v][:6] for k, v in rd.get_bls_schedule().items()})
check("news", lambda: [(n["source"], n["title"][:60], n["tickers"]) for n in rd.get_real_news(8)])
check("fear & greed", rd.get_fear_greed)
check("vix", rd.get_vix)
check("crypto", lambda: [(c["symbol"], c["price"], c["source"]) for c in (rd.get_crypto_prices() or [])])
check("crypto via kraken", lambda: [(c["symbol"], c["price"], c["change_24h"]) for c in (rd._kraken_prices() or [])])
check("earnings date AAPL", lambda: rd.get_earnings_date("AAPL"))
check("form 4", lambda: [(t["issuer_ticker"], t["insider_name"], "BUY" if t["is_buy"] else "SELL", round(t["total_value"]))
                         for t in rd.get_recent_form4_trades(max_filings=6)])
print("source status:", {k: v["status"] for k, v in rd.get_source_status().items()})
