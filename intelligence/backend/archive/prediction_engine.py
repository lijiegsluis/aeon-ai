"""
Aeon Intelligence - AI Prediction Engine

Tries a real, grounded LLM call (via ai_engine, free-tier Groq/Gemini) using
real market data collected elsewhere in the app. Falls back to a clearly
labeled static/demo generator when no AI key is configured or the live call
fails, so the app never silently presents illustrative content as real.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional

import ai_engine

PREDICTIONS_SYSTEM_PROMPT = """You are a market analyst for Aeon Intelligence. You are given `real_market_data`: \
actual, current facts (real news headlines, real SEC Form 4 insider trades, real sentiment/VIX readings, real \
crypto prices). Follow these rules strictly:

1. Every prediction, ticker, name, and number you write must be traceable to something literally present in \
real_market_data. Never invent a ticker, insider name, dollar amount, or event that is not in the supplied data.
2. If real_market_data does not contain enough information to support a category, return an EMPTY LIST for that \
category. An empty list is the correct, honest answer - never pad it with invented content.
3. Confidence scores must be realistic and conservative (0.5-0.85 range).
4. Every prediction object must include a "grounded_in" field citing the specific real_market_data item(s) it is \
based on (e.g. "news[2]" or "insider_trades[0]").
5. Output strict JSON only, no markdown fences, matching exactly this shape:
{
  "high_confidence_predictions": [{"prediction_id": str, "type": str, "ticker": str, "prediction": str,
     "confidence": float, "timeframe": str, "supporting_signals": [str], "grounded_in": str,
     "reasoning": str, "action": str}],
  "pattern_based_predictions": [{"prediction_id": str, "pattern_type": str, "ticker": str, "prediction": str,
     "confidence": float, "historical_precedent": str, "supporting_data": [str], "grounded_in": str,
     "predicted_move": str, "action": str}],
  "causal_predictions": [{"prediction_id": str, "causal_chain": str, "prediction": str, "confidence": float,
     "reasoning": str, "supporting_data": [str], "grounded_in": str, "predicted_outcome": str, "action": str}],
  "contrarian_predictions": [{"prediction_id": str, "contrarian_view": str, "prediction": str, "confidence": float,
     "reasoning": str, "supporting_data": [str], "grounded_in": str, "predicted_outcome": str, "action": str}],
  "black_swan_monitors": [{"risk_id": str, "risk_type": str, "scenario": str, "probability": float,
     "impact_if_occurs": str, "early_warning_indicators": [str], "hedge": str}]
}
Every list may legitimately be empty. Do not fabricate to fill a category."""

DAILY_BRIEF_SYSTEM_PROMPT = """You are a market analyst for Aeon Intelligence writing today's brief. You are \
given `real_market_data`: real news headlines, real SEC Form 4 insider trades, real sentiment readings, and real \
crypto prices, as of right now. Follow these rules strictly:

1. Only reference tickers, insiders, and numbers literally present in real_market_data. Never invent a specific \
dollar figure, ownership percentage, or executive name that isn't there.
2. If there is not enough real data to justify a recommendation in a section, return an EMPTY LIST for that \
section rather than inventing one.
3. Confidence must be a realistic percentage string like "65%".
4. Every recommendation's "rationale" must name the specific real_market_data item(s) it is based on, and its \
"data_sources" list must name the real_market_data categories used (e.g. ["news", "insider_trades"]).
5. Output strict JSON only, no markdown fences, matching exactly this shape:
{
  "market_regime": str, "primary_catalyst": str,
  "mega_cap_plays": [{"ticker": str, "market_cap": str, "action": str, "target": str, "stop": str,
     "confidence": str, "timeframe": str, "rationale": str, "risks": str, "catalyst": str,
     "smart_money_signal": str, "technical_setup": str, "risk_factor": str, "data_sources": [str]}],
  "large_cap_plays": [ ...same shape as mega_cap_plays... ],
  "mid_cap_opportunities": [ ...same shape... ],
  "event_driven_plays": [ ...same shape... ],
  "sector_plays": [{"sector": str, "tickers": [str], "action": str, "rationale": str, "catalyst": str,
     "smart_money_signal": str, "technical_setup": str, "risk_factor": str, "data_sources": [str]}],
  "top_recommendations": [ ...same shape as mega_cap_plays... ],
  "market_context": {"key_events_today": [str], "macro_regime": str, "sector_rotation": str,
     "volatility_setup": str, "sentiment": str},
  "smart_money_activity": {"insider_trades_summary": str, "congressional_trades": str,
     "institutional_flow": str, "cluster_buying_alerts": str},
  "action_plan": {"immediate": [str], "this_week": [str], "this_month": [str]},
  "risk_management": {"market_risks": str, "position_sizing": str, "hedging": str, "watch_levels": str}
}
Any section with no real supporting data should be an empty list or a generic honest statement - never \
fabricated specifics."""


class AeonPredictionEngine:
    def __init__(self):
        self.confidence_threshold = 0.65
        self.prediction_horizon_days = 30

    def generate_ai_predictions(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        required_keys = ["high_confidence_predictions", "pattern_based_predictions", "causal_predictions",
                          "contrarian_predictions", "black_swan_monitors"]

        live = None
        if ai_engine.available():
            user_prompt = json.dumps({"real_market_data": context or {}}, default=str)
            live = ai_engine.generate_json(PREDICTIONS_SYSTEM_PROMPT, user_prompt)

        if live and all(k in live for k in required_keys):
            predictions = {k: live[k] for k in required_keys}
            mode = "live"
            note = None
        else:
            predictions = {
                "high_confidence_predictions": self._generate_high_confidence(),
                "pattern_based_predictions": self._generate_pattern_based(),
                "causal_predictions": self._generate_causal_chain(),
                "contrarian_predictions": self._generate_contrarian(),
                "black_swan_monitors": self._generate_tail_risk(),
            }
            mode = "demo"
            note = ("No AI provider configured (set GROQ_API_KEY or GEMINI_API_KEY in backend/.env) or the live "
                    "call failed - showing illustrative sample predictions, not live analysis.")

        predictions["meta"] = {
            "generated_at": datetime.now().isoformat(),
            "model_version": "Aeon-live-v1" if mode == "live" else "Aeon-demo-v1",
            "prediction_horizon": "30 days",
            "confidence_calibration": ("Not yet calibrated - no resolved live prediction history yet. See "
                                        "historical_backtest below for a real backtest of the underlying "
                                        "insider-buy signal (not a backtest of these LLM predictions themselves)."
                                        if mode == "live" else "N/A - demo mode"),
            "total_data_sources": self._count_data_sources(context),
            "training_data": ("Grounded in real-time news, real SEC Form 4 insider filings, real sentiment/VIX "
                               "readings, and real crypto prices, reasoned over by a free-tier LLM (Groq/Gemini)"
                               if mode == "live" else
                               "Demo mode - illustrative sample data, not derived from any live model or data feed"),
            "mode": mode,
            "note": note,
        }
        predictions["prediction_accuracy_stats"] = self._get_accuracy_stats()
        return predictions

    def _count_data_sources(self, context: Optional[Dict[str, Any]]) -> int:
        """Honest count of real-data categories actually fed into this prediction, not a fabricated number."""
        if not context:
            return 0
        return sum(1 for key in ("news", "insider_trades", "sentiment", "crypto") if context.get(key))

    def generate_daily_brief(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        now = datetime.now()
        live = None
        if ai_engine.available():
            user_prompt = json.dumps({"real_market_data": context or {}}, default=str)
            live = ai_engine.generate_json(DAILY_BRIEF_SYSTEM_PROMPT, user_prompt)

        if live and isinstance(live, dict) and "top_recommendations" in live:
            brief = self._normalize_brief(live)
            brief["mode"] = "live"
            brief.setdefault("data_edge", "Generated just now from live real data (real news, real SEC Form 4 "
                                           "filings, real sentiment, real crypto prices) via a free-tier LLM.")
        else:
            brief = self._static_daily_brief()
            brief["mode"] = "demo"
            brief["demo_note"] = ("No AI provider configured or the live brief generation failed - showing an "
                                   "illustrative sample brief, not live analysis. Set GROQ_API_KEY or "
                                   "GEMINI_API_KEY in backend/.env to enable live briefs.")

        brief["date"] = now.strftime("%A, %B %d, %Y")
        brief["generated_at"] = now.isoformat()
        return brief

    def _normalize_brief(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """Defensively backfill fields the frontend renders unconditionally (e.g. play.data_sources.join(...))
        in case the LLM's live JSON drifts slightly from the requested schema."""
        for key in ("mega_cap_plays", "large_cap_plays", "mid_cap_opportunities", "event_driven_plays",
                    "top_recommendations", "sector_plays"):
            for item in brief.get(key) or []:
                if isinstance(item, dict) and not isinstance(item.get("data_sources"), list):
                    item["data_sources"] = []
        return brief

    def _generate_high_confidence(self) -> List[Dict]:
        return [
            {
                "prediction_id": "HC001-DEMO",
                "type": "EARNINGS_BEAT",
                "ticker": "NVDA",
                "prediction": "Sample: NVDA earnings beat with guidance raise",
                "confidence": 0.7,
                "timeframe": "48 hours",
                "supporting_signals": ["This is illustrative sample content, not a live prediction"],
                "reasoning": "Demo mode - no AI provider configured or the live call failed.",
                "adversarial_test": "N/A - demo content",
                "action": "Configure GROQ_API_KEY or GEMINI_API_KEY for live predictions"
            }
        ]

    def _generate_pattern_based(self) -> List[Dict]:
        return [
            {
                "prediction_id": "PTN001-DEMO",
                "pattern_type": "SEASONAL",
                "ticker": "Energy Sector (XLE)",
                "prediction": "Sample: seasonal energy sector pattern",
                "confidence": 0.65,
                "historical_precedent": "This is illustrative sample content, not a live prediction",
                "supporting_data": ["Demo mode - configure an AI key for live pattern analysis"],
                "predicted_move": "N/A - demo content",
                "action": "Configure GROQ_API_KEY or GEMINI_API_KEY for live predictions"
            }
        ]

    def _generate_causal_chain(self) -> List[Dict]:
        return [
            {
                "prediction_id": "CAU001-DEMO",
                "causal_chain": "Sample causal chain (demo mode)",
                "prediction": "This is illustrative sample content, not a live prediction",
                "confidence": 0.6,
                "reasoning": "Demo mode - no AI provider configured or the live call failed.",
                "supporting_data": ["Configure GROQ_API_KEY or GEMINI_API_KEY for live analysis"],
                "predicted_outcome": "N/A - demo content",
                "action": "Configure an AI key for live causal predictions"
            }
        ]

    def _generate_contrarian(self) -> List[Dict]:
        return [
            {
                "prediction_id": "CON001-DEMO",
                "contrarian_view": "Sample contrarian view (demo mode)",
                "prediction": "This is illustrative sample content, not a live prediction",
                "confidence": 0.55,
                "reasoning": "Demo mode - no AI provider configured or the live call failed.",
                "supporting_data": ["Configure GROQ_API_KEY or GEMINI_API_KEY for live analysis"],
                "predicted_outcome": "N/A - demo content",
                "action": "Configure an AI key for live contrarian analysis"
            }
        ]

    def _generate_tail_risk(self) -> List[Dict]:
        return [
            {
                "risk_id": "TAIL001",
                "risk_type": "Geopolitical",
                "scenario": "Major geopolitical shock disrupts semiconductor supply chain",
                "probability": 0.08,
                "impact_if_occurs": "Markets could sell off sharply; semiconductor supply chain at risk",
                "early_warning_indicators": [
                    "Military activity near Taiwan Strait (public OSINT sources)",
                    "Sudden changes in Taiwan semiconductor export volumes",
                    "US carrier deployments to Indo-Pacific"
                ],
                "hedge": "Long volatility instruments, diversify away from single-region chip exposure"
            },
            {
                "risk_id": "TAIL002",
                "risk_type": "Systemic Financial",
                "scenario": "Regional bank stress event triggers broader credit contagion",
                "probability": 0.12,
                "impact_if_occurs": "Credit crunch risk, potential recession, forced Fed response",
                "early_warning_indicators": [
                    "Regional bank ETF (KRE) breaking key support levels",
                    "High-yield credit spreads widening sharply",
                    "Reverse repo facility usage dropping fast (liquidity stress)"
                ],
                "hedge": "Long duration treasuries, defensive sector tilt, elevated cash reserves"
            }
        ]

    def _get_accuracy_stats(self) -> Dict:
        return {
            "last_30_days": {
                "predictions_made": 0,
                "predictions_resolved": 0,
                "correct": 0,
                "accuracy": 0.0,
                "avg_confidence": 0.0,
                "calibration_score": 0.0,
            },
            "by_category": {},
            "model_improvements": [
                "No resolved prediction track record yet - live grounded predictions were only just wired up. "
                "This section will populate as predictions are made and later resolved against real outcomes."
            ],
        }

    def _static_daily_brief(self) -> Dict[str, Any]:
        return {
            "market_regime": "Demo mode - not a live assessment",
            "primary_catalyst": "No AI provider configured, or the live brief call failed",
            "mega_cap_plays": [],
            "large_cap_plays": [],
            "mid_cap_opportunities": [],
            "event_driven_plays": [],
            "sector_plays": [],
            "top_recommendations": [],
            "market_context": {
                "key_events_today": [],
                "macro_regime": "N/A - demo mode",
                "sector_rotation": "N/A - demo mode",
                "volatility_setup": "N/A - demo mode",
                "sentiment": "N/A - demo mode",
            },
            "smart_money_activity": {
                "insider_trades_summary": "See the Insider Trading tab for real SEC Form 4 data.",
                "congressional_trades": "N/A - demo mode",
                "institutional_flow": "N/A - demo mode",
                "cluster_buying_alerts": "N/A - demo mode",
            },
            "action_plan": {"immediate": [], "this_week": [], "this_month": []},
            "risk_management": {
                "market_risks": "N/A - demo mode",
                "position_sizing": "N/A - demo mode",
                "hedging": "N/A - demo mode",
                "watch_levels": "N/A - demo mode",
            },
            "data_edge": ("No AI provider is configured (or the live call failed), so this brief is placeholder "
                          "content. Set GROQ_API_KEY or GEMINI_API_KEY in backend/.env for a live, data-grounded "
                          "brief generated from real news, real insider trades, and real sentiment."),
        }


# Global instance
prediction_engine = AeonPredictionEngine()


def generate_ai_predictions(context: Optional[Dict[str, Any]] = None):
    """Main entry point for AI predictions"""
    return prediction_engine.generate_ai_predictions(context)


def generate_daily_brief(context: Optional[Dict[str, Any]] = None):
    """Main entry point for the daily brief"""
    return prediction_engine.generate_daily_brief(context)
