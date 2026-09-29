"""
Aeon Intelligence - rule-based daily brief and predictions.

Used whenever no LLM key is configured (or the LLM call fails). Everything is
assembled from real inputs that are already in memory — alpha-engine signals and
their backtests, the dated event calendar, Fear & Greed / VIX readings and insider
activity — so a brief is never placeholder text. Output matches the LLM shapes the
frontend renders; `mode` is "rules".
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

STRATEGY_TIMEFRAME = {"insider_cluster": "20 trading days", "pead": "20 trading days",
                      "earnings_runup": "until the day before the report", "fear_rebound": "20 trading days"}


def _reading(sentiment: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    return next((s for s in sentiment or [] if s.get("indicator_name") == name), None)


def market_regime(sentiment) -> str:
    fg, vix = _reading(sentiment, "Fear & Greed"), _reading(sentiment, "VIX")
    parts = []
    if fg:
        v = fg["value"]
        parts.append(f"Fear & Greed {v:.0f} ({fg['interpretation']})")
    if vix:
        parts.append(f"VIX {vix['value']:.1f} ({vix['interpretation'].lower()})")
    if not parts:
        return "Sentiment readings unavailable right now"
    tone = ""
    if fg and vix:
        if fg["value"] <= 25 and vix["value"] >= 25:
            tone = " — capitulation-style fear: historically a better time to add risk than to cut it"
        elif fg["value"] >= 75 and vix["value"] < 15:
            tone = " — complacent greed: tighten stops, avoid chasing"
        elif fg["value"] < 45:
            tone = " — risk-off lean"
        elif fg["value"] > 55:
            tone = " — risk-on lean"
        else:
            tone = " — neutral tape"
    return " · ".join(parts) + tone


def _play(sig: Dict[str, Any], strategies: Dict[str, Any]) -> Dict[str, Any]:
    bt = strategies.get(sig["strategy"]) or {}
    evidence = (f"Backtest: {bt['n']} events, {bt['win_rate']}% beat the S&P 500, avg excess {bt['avg_excess_pct']:+.2f}% "
                f"(t={bt['t_stat']}) — {bt['verdict']}" if bt.get("n") else "No historical sample yet for this strategy")
    return {
        "ticker": sig["ticker"],
        "market_cap": "—",
        "action": f"BUY — {sig['strategy_name']}",
        "target": f"${sig['target']}",
        "stop": f"${sig['stop']}",
        "confidence": f"{sig['confidence']:.0f}%" if sig.get("confidence") is not None else "unproven",
        "timeframe": f"exit {sig['exit_date']} ({STRATEGY_TIMEFRAME.get(sig['strategy'], '')})",
        "rationale": sig["reason"],
        "risks": f"Stop at ${sig['stop']} (2× ATR below ${sig['entry_price']}). {evidence}.",
        "catalyst": sig["reason"],
        "smart_money_signal": sig["reason"] if sig["strategy"] == "insider_cluster" else "—",
        "technical_setup": f"Entry ${sig['entry_price']}, stop ${sig['stop']}, target ${sig['target']}, "
                           f"reward/risk {sig.get('risk_reward') or '—'}",
        "risk_factor": evidence,
        "data_sources": ["alpha_engine", {"insider_cluster": "sec_form4", "pead": "earnings_calendar",
                                          "earnings_runup": "earnings_calendar", "fear_rebound": "cnn_fear_greed"}
                         .get(sig["strategy"], "market_data")],
    }


def daily_brief(context: Dict[str, Any], alpha: Dict[str, Any]) -> Dict[str, Any]:
    signals = alpha.get("signals") or []
    strategies = alpha.get("strategies") or {}
    events = context.get("upcoming_events") or []
    sentiment = context.get("sentiment") or []
    insiders = context.get("insider_trades") or []

    plays = [_play(s, strategies) for s in signals]
    proven = [p for p, s in zip(plays, signals) if s.get("backtest_edge")]
    top = (proven or plays)[:5]

    soon = [e for e in events if e.get("days_until", 99) <= 7]
    def when(d):
        return "today" if d <= 0 else "tomorrow" if d == 1 else f"in {d} days"

    catalyst = (f"{soon[0]['title']} {when(soon[0]['days_until'])}" if soon else
                f"{events[0]['title']} {when(events[0]['days_until'])}" if events else
                "No dated macro or earnings catalyst in the next three weeks")

    buys = [t for t in insiders if t.get("transaction_type") == "BUY"]
    sells = [t for t in insiders if t.get("transaction_type") == "SELL"]
    clusters = [s for s in signals if s["strategy"] == "insider_cluster"]
    edge_lines = [f"{v.get('name', k)}: {v.get('verdict')} ({v['n']} events, avg excess {v.get('avg_excess_pct', 0):+.2f}%)"
                  for k, v in strategies.items() if v.get("n")]

    fg = _reading(sentiment, "Fear & Greed")
    vix = _reading(sentiment, "VIX")
    return {
        "market_regime": market_regime(sentiment),
        "primary_catalyst": catalyst,
        "top_recommendations": top,
        "mega_cap_plays": [],
        "large_cap_plays": [],
        "mid_cap_opportunities": [p for p, s in zip(plays, signals) if s["strategy"] == "insider_cluster"][:5],
        "event_driven_plays": [p for p, s in zip(plays, signals) if s["strategy"] in ("pead", "earnings_runup")][:8],
        "sector_plays": [],
        "market_context": {
            "key_events_today": [f"D-{e['days_until']} · {e['title']}" for e in events[:8]],
            "macro_regime": market_regime(sentiment),
            "sector_rotation": "Not derived — no sector-flow source is connected.",
            "volatility_setup": (f"VIX {vix['value']:.1f}: {vix['interpretation']}" if vix else "VIX unavailable"),
            "sentiment": (f"CNN Fear & Greed {fg['value']:.0f} — {fg['interpretation']}" if fg else "Fear & Greed unavailable"),
        },
        "smart_money_activity": {
            "insider_trades_summary": (f"{len(buys)} open-market insider buys and {len(sells)} sales in the latest SEC "
                                       "Form 4 batch." if insiders else "No Form 4 batch loaded yet."),
            "congressional_trades": "Not tracked in Intelligence.",
            "institutional_flow": "Not tracked — no free institutional-flow source.",
            "cluster_buying_alerts": ("; ".join(f"{s['ticker']}: {s['reason']}" for s in clusters[:4])
                                      or "No cluster buys filed in the last week."),
        },
        "action_plan": {
            "immediate": [f"{s['ticker']}: enter near ${s['entry_price']}, stop ${s['stop']}, exit {s['exit_date']}"
                          for s in signals if s.get("backtest_edge")][:5]
                         or ["No signal with a proven backtest edge today — stay patient."],
            "this_week": [f"{e['title']} (D-{e['days_until']})" for e in soon][:6],
            "this_month": edge_lines[:4],
        },
        "risk_management": {
            "market_risks": market_regime(sentiment),
            "position_sizing": "Size so a stop-out costs at most 1% of capital: shares = 1% × capital ÷ (entry − stop).",
            "hedging": ("VIX is elevated — smaller size or index puts." if vix and vix["value"] >= 25
                        else "No hedge signal from volatility right now."),
            "watch_levels": "; ".join(f"{s['ticker']} stop ${s['stop']}" for s in signals[:6]) or "—",
        },
        "data_edge": ("Rule-based brief (no LLM configured): every line comes from the alpha engine's live signals and "
                      "their backtests, the dated event calendar, CNN Fear & Greed, VIX and SEC Form 4 data. "
                      "Set GROQ_API_KEY or GEMINI_API_KEY for an LLM-written brief on the same data."),
    }


def predictions(context: Dict[str, Any], alpha: Dict[str, Any]) -> Dict[str, Any]:
    signals = alpha.get("signals") or []
    strategies = alpha.get("strategies") or {}
    sentiment = context.get("sentiment") or []

    def pred(s, i, kind):
        bt = strategies.get(s["strategy"]) or {}
        conf = (s["confidence"] / 100) if s.get("confidence") is not None else 0.5
        return {
            "prediction_id": f"R-{s['strategy'][:3].upper()}-{s['ticker']}-{i}",
            "type" if kind == "high" else "pattern_type": s["strategy_name"],
            "ticker": s["ticker"],
            "direction": "bullish",
            "prediction": f"{s['ticker']} outperforms the S&P 500 by {s['exit_date']}",
            "confidence": round(conf, 2),
            "timeframe": f"{max(1, (datetime.fromisoformat(s['exit_date']) - datetime.now()).days)} days",
            "supporting_signals": [s["reason"]],
            "supporting_data": [s["reason"]],
            "historical_precedent": (f"{bt['n']} past events: {bt['win_rate']}% beat SPY, avg excess {bt['avg_excess_pct']:+.2f}%"
                                     if bt.get("n") else "No historical sample yet"),
            "predicted_move": f"target ${s['target']} / stop ${s['stop']}",
            "grounded_in": f"alpha_engine.{s['strategy']}",
            "reasoning": bt.get("thesis", ""),
            "action": f"BUY near ${s['entry_price']}, stop ${s['stop']}, target ${s['target']}, exit {s['exit_date']}",
        }

    high = [pred(s, i, "high") for i, s in enumerate(signals) if s.get("backtest_edge")]
    pattern = [pred(s, i, "pattern") for i, s in enumerate(signals) if not s.get("backtest_edge")]

    contrarian, black_swan = [], []
    fg, vix = _reading(sentiment, "Fear & Greed"), _reading(sentiment, "VIX")
    fear_bt = strategies.get("fear_rebound") or {}
    if fg and fg["value"] <= 25:
        contrarian.append({
            "prediction_id": "R-CON-FEAR", "contrarian_view": "Crowd fear is extreme",
            "prediction": "The S&P 500 is higher in 20 trading days", "direction": "bullish", "ticker": "SPY",
            "confidence": round((fear_bt.get("win_rate") or 55) / 100, 2), "timeframe": "20 days",
            "reasoning": f"Fear & Greed {fg['value']:.0f}. " + (fear_bt.get("verdict") or ""),
            "supporting_data": [f"CNN Fear & Greed {fg['value']:.0f}"], "grounded_in": "sentiment",
            "predicted_outcome": "Mean reversion from extreme fear", "action": "Scale into SPY"})
    elif fg and fg["value"] >= 80:
        contrarian.append({
            "prediction_id": "R-CON-GREED", "contrarian_view": "Crowd greed is extreme",
            "prediction": "Upside is limited over the next month", "direction": "neutral", "ticker": "SPY",
            "confidence": 0.55, "timeframe": "20 days",
            "reasoning": f"Fear & Greed {fg['value']:.0f} — extreme greed readings have preceded weaker forward returns.",
            "supporting_data": [f"CNN Fear & Greed {fg['value']:.0f}"], "grounded_in": "sentiment",
            "predicted_outcome": "Choppier, lower-return month", "action": "Tighten stops; avoid new leverage"})
    if vix:
        black_swan.append({
            "risk_id": "R-VOL", "risk_type": "Volatility regime",
            "scenario": ("Volatility spike from an elevated base" if vix["value"] >= 25 else
                         "Complacency: low implied volatility can snap higher quickly"),
            "probability": None,
            "impact_if_occurs": "Correlations rise and stops get hit together",
            "early_warning_indicators": [f"VIX now {vix['value']:.1f}", "VIX term structure inverting",
                                         "High-yield spreads widening"],
            "hedge": "Keep position sizes to the 1%-risk rule; index puts when VIX is below 15 are cheap insurance",
        })
    return {
        "high_confidence_predictions": high,
        "pattern_based_predictions": pattern,
        "causal_predictions": [],
        "contrarian_predictions": contrarian,
        "black_swan_monitors": black_swan,
    }
