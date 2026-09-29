"""Run the alpha engine end to end on real data and print what it finds."""
import json
import time
from datetime import date, timedelta

import alpha_data
import alpha_engine as ae


def check(label, fn):
    try:
        print(f"OK   {label}: {fn()}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {label}: {type(e).__name__}: {e}")


today = date.today()
check("cluster buys", lambda: [(r["ticker"], r["filing_date"], r["insiders"], r["value"]) for r in alpha_data.insider_cluster_buys()[:5]])
check("calendar -30d", lambda: [(r["symbol"], r["surprise_pct"]) for r in alpha_data.earnings_calendar(today - timedelta(days=30))[:5]])
check("next earnings NVDA", lambda: alpha_data.next_earnings("NVDA"))
check("surprises MSFT", lambda: alpha_data.earnings_surprises("MSFT"))
check("fear & greed history", lambda: (len(alpha_data.fear_greed_history()), alpha_data.fear_greed_history()[-1:]))
check("SPY bars", lambda: (len(alpha_data.price_history("SPY")), alpha_data.price_history("SPY")[-1]))

t0 = time.time()
bt = ae.run_backtests()
print(f"\nBACKTESTS ({time.time() - t0:.0f}s)")
for k, v in bt.items():
    print(k, json.dumps({x: v.get(x) for x in ("n", "win_rate", "avg_return_pct", "avg_excess_pct",
                                                "median_excess_pct", "t_stat", "verdict")}))
ae.init_portfolio()
ae._state["backtests"] = bt
ae.refresh(full=False)
st = ae.get_state()
print("\nLIVE SIGNALS", len(st["signals"]), "errors", st["errors"])
for s in st["signals"][:12]:
    print(" ", s["strategy"], s["ticker"], s["entry_price"], "stop", s["stop"], "target", s["target"],
          "exit", s["exit_date"], "conf", s["confidence"], "|", s["reason"][:90])
print("portfolio stats", ae.portfolio()["stats"])
