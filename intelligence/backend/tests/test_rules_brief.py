import prediction_engine
import rules_brief

SIG = {"key": "pead:NVDA:2026-09-20", "strategy": "pead", "strategy_name": "Post-earnings drift", "ticker": "NVDA",
       "entry_price": 100.0, "entry_date": "2026-09-28", "stop": 92.0, "target": 109.0, "exit_date": "2026-10-26",
       "risk_reward": 1.12, "confidence": 61.0, "backtest_edge": True, "reason": "EPS +18% surprise, up 4% on the day"}
ALPHA = {"signals": [SIG], "strategies": {"pead": {"n": 44, "win_rate": 61.0, "avg_excess_pct": 2.1, "t_stat": 2.3,
                                                  "verdict": "positive edge", "thesis": "drift"}}}
CTX = {"alpha": ALPHA,
       "sentiment": [{"indicator_name": "Fear & Greed", "value": 22, "interpretation": "Extreme Fear"},
                     {"indicator_name": "VIX", "value": 27.5, "interpretation": "High volatility"}],
       "upcoming_events": [{"title": "CPI", "days_until": 3}], "insider_trades": []}


def test_brief_is_built_from_real_inputs(monkeypatch):
    monkeypatch.setattr(prediction_engine.ai_engine, "available", lambda: False)
    b = prediction_engine.generate_daily_brief(CTX)
    assert b["mode"] == "rules"
    assert b["top_recommendations"][0]["ticker"] == "NVDA"
    assert b["top_recommendations"][0]["stop"] == "$92.0" and b["top_recommendations"][0]["confidence"] == "61%"
    assert "capitulation" in b["market_regime"] and b["primary_catalyst"] == "CPI in 3 days"
    assert all(isinstance(p["data_sources"], list) for p in b["event_driven_plays"])


def test_predictions_are_gradeable(monkeypatch):
    monkeypatch.setattr(prediction_engine.ai_engine, "available", lambda: False)
    p = prediction_engine.generate_ai_predictions(CTX)
    assert p["meta"]["mode"] == "rules"
    hc = p["high_confidence_predictions"][0]
    assert hc["ticker"] == "NVDA" and hc["direction"] == "bullish" and hc["confidence"] == 0.61
    assert p["contrarian_predictions"][0]["ticker"] == "SPY"  # extreme fear
    assert p["black_swan_monitors"][0]["probability"] is None  # no invented probabilities


def test_empty_inputs_still_honest():
    b = rules_brief.daily_brief({}, {})
    assert b["top_recommendations"] == [] and "unavailable" in b["market_regime"]
    assert b["action_plan"]["immediate"] == ["No signal with a proven backtest edge today — stay patient."]
