"""Alpha engine on synthetic prices — rules, windows, stats, paper trading."""
from datetime import date, timedelta

import pytest

import alpha_engine as ae


def bars(start: str, closes, lows=None):
    d = date.fromisoformat(start)
    out = []
    for i, c in enumerate(closes):
        while d.weekday() >= 5:
            d += timedelta(days=1)
        lo = lows[i] if lows else c * 0.99
        out.append({"date": d.isoformat(), "open": c, "high": c * 1.01, "low": lo, "close": c})
        d += timedelta(days=1)
    return out


SPY = bars("2026-01-05", [100.0] * 120)  # flat benchmark: excess == raw return


def test_summarize_verdicts():
    few = [{"excess_pct": 5.0, "return_pct": 5.0}] * 5
    assert ae.summarize(few)["verdict"].startswith("only 5 events")
    strong = [{"excess_pct": 3.0 + (i % 3), "return_pct": 4.0} for i in range(30)]
    s = ae.summarize(strong)
    assert s["edge"] and s["t_stat"] >= 2 and s["win_rate"] == 100.0
    weak = [{"excess_pct": x, "return_pct": x} for x in [-3, 4, -2, 3, -1, 2] * 5]
    assert not ae.summarize(weak)["edge"]


def test_insider_backtest_enters_after_filing_and_filters():
    stock = bars("2026-01-05", [10 + 0.1 * i for i in range(80)])
    clusters = [
        {"ticker": "ABC", "filing_date": "2026-01-09", "insiders": 3, "value": 500_000, "price": 10.4, "trade_type": "P - Purchase"},
        {"ticker": "ABC", "filing_date": "2026-01-09", "insiders": 1, "value": 500_000, "price": 10.4, "trade_type": "P - Purchase"},
        {"ticker": "ABC", "filing_date": "2026-01-09", "insiders": 2, "value": 50_000, "price": 10.4, "trade_type": "P - Purchase"},
    ]
    ev = ae.backtest_insider(clusters, lambda t: stock, SPY, hold=20)
    assert len(ev) == 1
    assert ev[0]["entry_date"] == "2026-01-12"  # first session after the Friday filing
    assert ev[0]["excess_pct"] > 0


def test_runup_window_exits_before_the_release():
    b = bars("2026-01-05", [100 + i for i in range(40)])
    report = b[20]["date"]
    pre = ae.runup_window(b, {"date": report, "time": "pre"})
    after = ae.runup_window(b, {"date": report, "time": "after"})
    assert pre == (10, 19) and after == (11, 20)


def test_pead_needs_a_beat_and_a_positive_reaction():
    up = bars("2026-01-05", [50] * 10 + [55] + [56 + i * 0.2 for i in range(40)])
    down = bars("2026-01-05", [50] * 10 + [45] + [45] * 40)
    row = {"symbol": "X", "date": up[10]["date"], "time": "pre", "surprise_pct": 25, "eps_forecast": 1.0, "market_cap": 5e9}
    assert len(ae.backtest_pead([row], lambda t: up, SPY)) == 1
    assert ae.backtest_pead([row], lambda t: down, SPY) == []
    assert ae.backtest_pead([{**row, "surprise_pct": 4}], lambda t: up, SPY) == []


def test_fear_rebound_counts_crossings_only():
    spy = bars("2026-01-05", [100 + i * 0.5 for i in range(80)])
    hist = [{"date": spy[i]["date"], "value": v} for i, v in enumerate([40, 30, 22, 20, 21, 35, 24, 50] + [50] * 20)]
    ev = ae.backtest_fear(hist, spy, hold=20)
    assert [e["event_date"] for e in ev] == [spy[2]["date"], spy[6]["date"]]


def test_live_signals_and_levels():
    today = date(2026, 3, 2)
    stock = bars("2025-11-03", [20 + 0.05 * i for i in range(85)])
    clusters = [{"ticker": "ABC", "company": "Abc Corp", "filing_date": "2026-02-27", "insiders": 4,
                 "value": 2_000_000, "price": 24.0, "trade_type": "P - Purchase"}]
    bt = {"insider_cluster": {"n": 40, "win_rate": 62.0, "edge": True, "avg_win_pct": 9.0}}
    sigs = ae.live_signals(lambda t: stock, bt, today, clusters=clusters)
    assert len(sigs) == 1
    s = sigs[0]
    assert s["ticker"] == "ABC" and s["confidence"] == 62.0 and s["backtest_edge"]
    assert s["stop"] < s["entry_price"] < s["target"]
    assert s["exit_date"] == ae.add_trading_days(today, 20).isoformat()
    stale = [{**clusters[0], "filing_date": "2026-01-15"}]
    assert ae.live_signals(lambda t: stock, bt, today, clusters=stale) == []


def test_insider_skips_funds():
    assert ae._operating_company({"company": "Northern Trust Corp"})
    assert not ae._operating_company({"company": "First Trust High Yield Opportunities 2027 Term Fund"})


def test_runup_signal_requires_uptrend():
    today = date(2026, 3, 2)
    rising = bars("2025-11-03", [100.0 + 0.2 * i for i in range(85)])
    falling = bars("2025-11-03", [100.0 - 0.2 * i for i in range(85)])
    report = ae.add_trading_days(today, 10).isoformat()
    rows = [{"symbol": "BIG", "name": "Big Co", "date": report, "time": "after", "market_cap": 50e9}]
    beats = lambda t: [{"surprise_pct": 5}, {"surprise_pct": 2}, {"surprise_pct": 1}, {"surprise_pct": -1}]
    sig = ae.live_signals(lambda t: rising, {}, today, upcoming_rows=rows, surprises=beats)
    assert [s["ticker"] for s in sig] == ["BIG"] and sig[0]["exit_date"] == report
    assert "3 of the last 4" in sig[0]["reason"]
    assert sig[0]["confidence"] is None  # no proven backtest yet -> no confidence claimed
    assert ae.live_signals(lambda t: falling, {}, today, upcoming_rows=rows, surprises=beats) == []


def test_edge_needs_both_halves_positive():
    def ev(i, x):
        return {"event_date": f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}", "excess_pct": x, "return_pct": x}
    steady = [ev(i, 2.0 + (i % 3)) for i in range(40)]
    lopsided = [ev(i, 9.0 + (i % 3)) for i in range(20)] + [ev(20 + i, -1.0 + (i % 3) * 0.5) for i in range(20)]
    a, b = ae.summarize(steady), ae.summarize(lopsided)
    assert a["edge"] and a["stable"]
    assert b["t_stat"] >= 2 and not b["stable"] and not b["edge"] and "one half" in b["verdict"]


def test_unproven_strategies_are_capped_and_unrated():
    today = date(2026, 3, 2)
    stock = bars("2025-11-03", [100.0 + 0.2 * i for i in range(85)])
    report = ae.add_trading_days(today, 10).isoformat()
    rows = [{"symbol": f"T{i}", "date": report, "time": "pre", "market_cap": 50e9 + i} for i in range(12)]
    beats = lambda t: [{"surprise_pct": 5}] * 4
    weak = {"earnings_runup": {"n": 150, "win_rate": 56.7, "edge": False}}
    sig = ae.live_signals(lambda t: stock, weak, today, upcoming_rows=rows, surprises=beats)
    assert len(sig) == ae.WATCH_CAP and all(s["confidence"] is None and s["tier"] == "watch" for s in sig)
    proven = {"earnings_runup": {"n": 150, "win_rate": 60.0, "edge": True}}
    sig = ae.live_signals(lambda t: stock, proven, today, upcoming_rows=rows, surprises=beats)
    assert len(sig) == 12 and all(s["confidence"] == 60.0 and s["tier"] == "trade" for s in sig)


def test_paper_positions_close_on_stop_or_time():
    ae.init_portfolio()
    closes = [100.0] * 60
    lows = [99.0] * 60
    lows[45] = 80.0  # stop hit on bar 45
    stopper = bars("2026-01-05", closes, lows)
    steady = bars("2026-01-05", [100 + i * 0.5 for i in range(60)])
    spy = bars("2026-01-05", [100.0] * 60)
    px = {"STOP": stopper, "RUN": steady, "SPY": spy}
    entry_day = stopper[40]["date"]
    sigs = [
        {"key": "t:STOP:1", "strategy": "pead", "ticker": "STOP", "entry_date": entry_day, "entry_price": 100.0,
         "exit_date": stopper[55]["date"], "stop": 90.0, "target": 110.0, "reason": "test"},
        {"key": "t:RUN:1", "strategy": "pead", "ticker": "RUN", "entry_date": steady[40]["date"], "entry_price": steady[40]["close"],
         "exit_date": steady[50]["date"], "stop": 50.0, "target": 999.0, "reason": "test"},
    ]
    assert ae.open_positions_from(sigs, 100.0) == 2
    assert ae.open_positions_from(sigs, 100.0) == 0  # idempotent per signal
    assert ae.resolve_positions(lambda t: px[t], today=date.fromisoformat(steady[59]["date"])) == 2
    book = ae.portfolio()
    closed = {r["ticker"]: r for r in book["closed"] if r["signal_key"].startswith("t:")}
    assert closed["STOP"]["exit_reason"] == "stop" and closed["STOP"]["return_pct"] == -10.0
    assert closed["RUN"]["exit_reason"] == "time" and closed["RUN"]["excess_pct"] > 0
    assert book["stats"]["closed"] >= 2 and book["equity"]
