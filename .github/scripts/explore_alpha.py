"""Variant study for the alpha strategies on real data (economically motivated
variants only), with a first-half / second-half stability check."""
import statistics
from datetime import date, timedelta

import alpha_data
import alpha_engine as ae

today = date.today()
spy = alpha_data.price_history("SPY")
px = alpha_data.price_history
past = alpha_data.earnings_between(today - timedelta(days=330), today - timedelta(days=15))
print("earnings rows", len(past))


def line(label, ev):
    s = ae.summarize(ev)
    if not ev:
        print(f"{label:48s} n=0")
        return
    ev = sorted(ev, key=lambda e: e["event_date"])
    h = len(ev) // 2
    a = statistics.fmean(e["excess_pct"] for e in ev[:h]) if h else float("nan")
    b = statistics.fmean(e["excess_pct"] for e in ev[h:]) if len(ev) - h else float("nan")
    print(f"{label:48s} n={s['n']:4d} win={s['win_rate']:5.1f} avg_ex={s['avg_excess_pct']:+6.2f} "
          f"med={s['median_excess_pct']:+6.2f} t={s['t_stat']:+5.2f} | 1st half {a:+6.2f} 2nd half {b:+6.2f}")


print("\n== EARNINGS RUN-UP ==")
for lead in (5, 10, 15):
    for trend in (False, True):
        for mcap in (10e9, 50e9):
            line(f"lead={lead} trend={trend} mcap>={mcap/1e9:.0f}B",
                 ae.backtest_runup(past, px, spy, limit=250, lead=lead, min_mcap=mcap, trend=trend))

print("\n== POST-EARNINGS DRIFT ==")
for sur in (5, 10, 20):
    for react in (0, 3):
        for hold in (10, 20, 40, 60):
            line(f"surprise>={sur}% reaction>={react}% hold={hold}",
                 ae.backtest_pead(past, px, spy, hold=hold, limit=250, min_surprise=sur, min_reaction=react))

print("\n== INSIDER CLUSTERS ==")
clusters = alpha_data.insider_cluster_buys()
print("cluster rows", len(clusters), "span", min(c["filing_date"] for c in clusters), max(c["filing_date"] for c in clusters))
for hold in (5, 10, 20, 40):
    for mv in (100e3, 1e6):
        for mp in (2, 10):
            line(f"hold={hold} value>={mv/1e3:.0f}K price>={mp}",
                 ae.backtest_insider(clusters, px, spy, hold=hold, min_value=mv, min_price=mp))

print("\n== FEAR REBOUND ==")
fg = alpha_data.fear_greed_history()
for thr in (25, 30, 40):
    for hold in (10, 20, 40):
        line(f"threshold<={thr} hold={hold}", ae.backtest_fear(fg, spy, hold=hold, threshold=thr))
