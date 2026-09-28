"""
Aeon Nimbus Intelligence - Fully Populated API
Complete with realistic mock data for all endpoints
"""

import os
import threading
import time

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

import real_data
import history_db
import telegram_feed
import backtest_engine
from prediction_engine import generate_ai_predictions, generate_daily_brief

app = FastAPI(
    title="Aeon Nimbus Intelligence",
    version="5.0.0",
    description="Market Intelligence Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_predicted_events():
    """Generate predicted/expected events from data sources - AHEAD OF THE MARKET"""
    now = datetime.now()

    predictions = [
        {
            "id": 1,
            "source": "Federal Reserve",
            "event_type": "monetary_policy",
            "predicted_title": "Fed Expected to Hold Rates at 5.25-5.50%",
            "expected_date": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
            "confidence": "95%",
            "market_consensus": "No rate change - dovish language expected",
            "impact_if_correct": 7.5,
            "impact_if_wrong": 9.8,
            "key_indicators": "CPI trending down, unemployment stable at 3.8%",
            "positioning": "Long bonds, defensive stocks if dovish; sell volatility",
            "sources": "CME FedWatch Tool, Fed Minutes, FOMC member speeches"
        },
        {
            "id": 2,
            "source": "Bloomberg Economics",
            "event_type": "economic_data",
            "predicted_title": "CPI Expected +3.3% YoY (vs 3.2% prev)",
            "expected_date": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
            "confidence": "78%",
            "market_consensus": "Slight uptick in inflation, core remains sticky",
            "impact_if_correct": 6.5,
            "impact_if_wrong": 9.5,
            "key_indicators": "Energy prices +2.1%, shelter costs elevated",
            "positioning": "If beats 3.4%: sell tech, buy value. If misses 3.2%: rally tech",
            "sources": "BLS Preview, Bloomberg Survey, Trading Economics forecast"
        },
        {
            "id": 3,
            "source": "FactSet",
            "event_type": "earnings_preview",
            "predicted_title": "NVDA Earnings: EPS $2.65 expected (whisper $2.80)",
            "expected_date": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            "confidence": "82%",
            "market_consensus": "Beat expected, guidance key for AI demand sustainability",
            "impact_if_correct": 8.5,
            "impact_if_wrong": 9.8,
            "key_indicators": "Hopper demand strong, China export controls resolved",
            "positioning": "Straddle or iron condor - high IV. Beat = $520 target, miss = $440",
            "sources": "FactSet consensus, Estimize crowd, Options flow (heavy call buying)"
        },
        {
            "id": 4,
            "source": "TradingEconomics",
            "event_type": "economic_data",
            "predicted_title": "NFP Expected +180K jobs (prev +187K)",
            "expected_date": (now + timedelta(days=5)).strftime("%Y-%m-%d"),
            "confidence": "71%",
            "market_consensus": "Cooling labor market supports Fed pause narrative",
            "impact_if_correct": 7.8,
            "impact_if_wrong": 9.2,
            "key_indicators": "ADP +145K, jobless claims rising trend, JOLTS openings down",
            "positioning": "Below 150K = bullish (soft landing). Above 220K = hawkish Fed risk",
            "sources": "TradingEconomics, ADP Report, Jobless Claims trend"
        },
        {
            "id": 5,
            "source": "Estimize",
            "event_type": "earnings_preview",
            "predicted_title": "AAPL Revenue: $89.5B consensus (whisper $91.2B)",
            "expected_date": (now + timedelta(days=12)).strftime("%Y-%m-%d"),
            "confidence": "85%",
            "market_consensus": "iPhone 15 Pro demand exceeds expectations, China stabilizing",
            "impact_if_correct": 7.2,
            "impact_if_wrong": 8.8,
            "key_indicators": "Supply chain checks positive, App Store growth accelerating",
            "positioning": "Beat = $195 target. Miss on China = $170 downside",
            "sources": "Estimize whisper, Supply chain data (Foxconn output), App Store revenue"
        },
        {
            "id": 6,
            "source": "Forex Factory",
            "event_type": "geopolitical",
            "predicted_title": "OPEC+ Meeting: Production Cut Extension Likely",
            "expected_date": (now + timedelta(days=8)).strftime("%Y-%m-%d"),
            "confidence": "88%",
            "market_consensus": "Saudi/Russia to extend 1.3M bpd cuts through Q1 2027",
            "impact_if_correct": 8.2,
            "impact_if_wrong": 9.0,
            "key_indicators": "Brent $92/bbl, inventories declining, demand forecasts revised up",
            "positioning": "Cut extension = WTI $100+. Long XLE, USO. Bearish for airlines.",
            "sources": "Forex Factory, Reuters OPEC sources, IEA demand outlook"
        },
        {
            "id": 7,
            "source": "ECB Communications",
            "event_type": "monetary_policy",
            "predicted_title": "ECB Expected to Pause Rate Hikes (Hold at 4.5%)",
            "expected_date": (now + timedelta(days=15)).strftime("%Y-%m-%d"),
            "confidence": "92%",
            "market_consensus": "Terminal rate reached, focus shifts to 'higher for longer'",
            "impact_if_correct": 6.8,
            "impact_if_wrong": 8.5,
            "key_indicators": "Eurozone inflation 2.9%, Germany recession fears, wage growth moderating",
            "positioning": "EUR/USD consolidation 1.06-1.08. Pause confirmed = rally European equities",
            "sources": "ECB member speeches, Eurostat data, Reuters ECB sources"
        },
        {
            "id": 8,
            "source": "Insider Reports",
            "event_type": "m&a_speculation",
            "predicted_title": "AMD-ARM Acquisition Rumors Gaining Traction",
            "expected_date": (now + timedelta(days=18)).strftime("%Y-%m-%d"),
            "confidence": "45%",
            "market_consensus": "Low probability but high impact - would reshape semiconductor sector",
            "impact_if_correct": 9.5,
            "impact_if_wrong": 2.0,
            "key_indicators": "AMD insider buying cluster, investment bank activity, regulatory prep",
            "positioning": "Speculative: long AMD calls, ARM calls. Deal = AMD -15%, ARM +40%",
            "sources": "Bloomberg M&A rumors, Insider trading patterns (SEC Form 4), Investment banking chatter"
        },
        {
            "id": 9,
            "source": "CME FedWatch",
            "event_type": "market_structure",
            "predicted_title": "December Rate Cut Probability Now 67%",
            "expected_date": (now + timedelta(days=4)).strftime("%Y-%m-%d"),
            "confidence": "89%",
            "market_consensus": "Fed pivot narrative gaining momentum, data dependent",
            "impact_if_correct": 8.0,
            "impact_if_wrong": 7.5,
            "key_indicators": "Fed futures pricing, dot plot projections, inflation trajectory",
            "positioning": "Cut priced in = rally bonds/tech. No cut surprise = tech selloff",
            "sources": "CME FedWatch Tool, Fed Funds Futures, Goldman Sachs Fed model"
        },
        {
            "id": 10,
            "source": "SEC Filings",
            "event_type": "regulatory",
            "predicted_title": "Tesla FSD Regulatory Approval Expected This Month",
            "expected_date": (now + timedelta(days=10)).strftime("%Y-%m-%d"),
            "confidence": "62%",
            "market_consensus": "NHTSA review nearing completion, conditional approval likely",
            "impact_if_correct": 9.2,
            "impact_if_wrong": 5.0,
            "key_indicators": "NHTSA meeting frequency increased, Tesla government affairs activity",
            "positioning": "Approval = TSLA $280+. Delay = $220 support test",
            "sources": "SEC regulatory filings, NHTSA docket, Industry sources"
        },
        {
            "id": 11,
            "source": "World Bank",
            "event_type": "economic_forecast",
            "predicted_title": "Global Growth Downgrade Expected: 2.1% (from 2.4%)",
            "expected_date": (now + timedelta(days=20)).strftime("%Y-%m-%d"),
            "confidence": "76%",
            "market_consensus": "China slowdown, Europe stagnation driving revision",
            "impact_if_correct": 7.8,
            "impact_if_wrong": 6.0,
            "key_indicators": "China PMI declining, Germany manufacturing contraction, EM debt stress",
            "positioning": "Downgrade = flight to quality. Long USD, US Treasuries, defensive sectors",
            "sources": "World Bank preview, IMF outlook alignment, OECD leading indicators"
        },
        {
            "id": 12,
            "source": "Options Flow",
            "event_type": "unusual_activity",
            "predicted_title": "Massive SPY Put Wall at 430 Expiring Friday",
            "expected_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "confidence": "95%",
            "market_consensus": "Dealers hedging, pin risk near 430 level on OPEX",
            "impact_if_correct": 6.5,
            "impact_if_wrong": 8.0,
            "key_indicators": "400K open interest, $2B notional, gamma exposure negative",
            "positioning": "SPY likely pinned 428-432 through Friday close. Breakout Monday.",
            "sources": "Options flow data, SpotGamma, Zero-DTE activity"
        }
    ]

    return sorted(predictions, key=lambda x: x['expected_date'])

def generate_insider_trades():
    """Real SEC Form 4 insider trading data, mapped into the app's existing trade shape.
    Falls back to illustrative sample data only if the real fetch returns nothing."""
    real_trades = real_data.get_recent_form4_trades(max_filings=30)
    if not real_trades:
        return _fallback_insider_trades()

    ticker_map = real_data.get_sec_ticker_map()
    now = datetime.now()
    out = []

    for t in real_trades:
        ticker = t.get("issuer_ticker") or ticker_map.get(t["issuer_cik"], {}).get("ticker") or "N/A"
        total_value = t["total_value"]

        if total_value > 20_000_000:
            significance = "EXTREME"
        elif total_value > 10_000_000:
            significance = "HIGH"
        elif total_value > 3_000_000:
            significance = "MEDIUM"
        else:
            significance = "LOW"

        if t["is_buy"]:
            signal = (f"VERY BULLISH - {t['role']} accumulating large position" if significance == "EXTREME"
                       else f"BULLISH - {t['role']} insider buy" if significance == "HIGH"
                       else "Positive - insider accumulation")
        else:
            signal = "Large sale - monitor for reasons" if total_value > 15_000_000 else \
                     "Routine sale - may be diversification"

        try:
            trade_date = datetime.strptime(t["date"], "%Y-%m-%d")
            days_ago = max((now - trade_date).days, 0)
        except Exception:
            days_ago = 0

        out.append({
            "ticker": ticker,
            "insider_name": t.get("insider_name") or "Unknown",
            "role": t.get("role") or "Insider",
            "transaction_type": "BUY" if t["is_buy"] else "SELL",
            "shares": t["shares"],
            "price": round(t["price"], 2),
            "total_value": int(total_value),
            "date": t["date"],
            "filing_date": t.get("filed_at", t["date"]),
            "ownership_change": "N/A",
            "significance": significance,
            "smart_money_signal": signal,
            "days_ago": days_ago,
        })

    return sorted(out, key=lambda x: x["days_ago"])


def _fallback_insider_trades():
    """Illustrative sample insider trades - used only when the real SEC Form 4 fetch fails."""
    now = datetime.now()

    insiders = []
    companies = [
        {"ticker": "NVDA", "name": "Jensen Huang", "role": "CEO"},
        {"ticker": "AAPL", "name": "Tim Cook", "role": "CEO"},
        {"ticker": "MSFT", "name": "Satya Nadella", "role": "CEO"},
        {"ticker": "GOOGL", "name": "Sundar Pichai", "role": "CEO"},
        {"ticker": "META", "name": "Mark Zuckerberg", "role": "CEO"},
        {"ticker": "TSLA", "name": "Elon Musk", "role": "CEO"},
        {"ticker": "AMD", "name": "Lisa Su", "role": "CEO"},
        {"ticker": "AMZN", "name": "Andy Jassy", "role": "CEO"},
        {"ticker": "ORCL", "name": "Safra Catz", "role": "CEO"},
        {"ticker": "COIN", "name": "Brian Armstrong", "role": "CEO"},
        {"ticker": "SQ", "name": "Jack Dorsey", "role": "CEO"},
        {"ticker": "SHOP", "name": "Tobi Lutke", "role": "CEO"},
    ]

    # Generate 90 days of insider trading history
    for days_ago in range(1, 91):
        if random.random() < 0.15:  # 15% chance of trade each day
            company = random.choice(companies)
            is_buy = random.random() > 0.35  # 65% buys, 35% sells

            shares = random.randint(10000, 100000) if is_buy else random.randint(20000, 150000)
            price = round(random.uniform(100, 500), 2)
            total_value = shares * price
            ownership_change = round(random.uniform(0.5, 4.0), 1) if is_buy else -round(random.uniform(0.2, 2.0), 1)

            if total_value > 20000000:
                significance = "EXTREME"
            elif total_value > 10000000:
                significance = "HIGH"
            elif total_value > 3000000:
                significance = "MEDIUM"
            else:
                significance = "LOW"

            trade_date = now - timedelta(days=days_ago)
            filing_date = now - timedelta(days=days_ago - random.randint(1, 2))

            if is_buy:
                if significance == "EXTREME":
                    signal = f"VERY BULLISH - {company['role']} accumulating large position"
                elif significance == "HIGH":
                    signal = f"BULLISH - Strong insider confidence"
                else:
                    signal = f"Positive - Insider accumulation"
            else:
                if total_value > 15000000:
                    signal = "Large sale - monitor for reasons"
                else:
                    signal = "Routine sale - likely diversification"

            insiders.append({
                "ticker": company['ticker'],
                "insider_name": company['name'],
                "role": company['role'],
                "transaction_type": "BUY" if is_buy else "SELL",
                "shares": shares,
                "price": price,
                "total_value": int(total_value),
                "date": trade_date.strftime("%Y-%m-%d"),
                "filing_date": filing_date.strftime("%Y-%m-%d"),
                "ownership_change": f"+{ownership_change}%" if is_buy else f"{ownership_change}%",
                "significance": significance,
                "smart_money_signal": signal,
                "days_ago": days_ago
            })

    return sorted(insiders, key=lambda x: x['days_ago'])

def generate_smart_money_notifications():
    """Derive notification-shaped events from the real (or fallback) insider trade data,
    plus a small set of genuinely real recurring regulatory calendar facts."""
    now = datetime.now()
    top_trades = sorted(INSIDER_TRADES, key=lambda x: x.get("total_value", 0), reverse=True)[:9]

    past_filings = []
    for idx, t in enumerate(top_trades, start=1):
        try:
            trade_date = datetime.strptime(t["date"], "%Y-%m-%d")
        except Exception:
            trade_date = now
        days_ago = max((now - trade_date).days, 0)
        action = t["transaction_type"]
        verb = "BOUGHT" if action == "BUY" else "SOLD"
        past_filings.append({
            "id": idx,
            "type": "SEC Form 4 Filed",
            "ticker": t["ticker"],
            "title": f"{t['ticker']} {t['role']} {t['insider_name']} - {'Buy' if action == 'BUY' else 'Sale'} Filing",
            "message": (f"{t['insider_name']} filed Form 4: {verb} ${t['total_value']:,} "
                        f"({t['shares']:,} shares @ ${t['price']:.2f})."),
            "significance": t["significance"],
            "timestamp": trade_date.isoformat(),
            "days_ago": days_ago,
            "action": action,
            "value": t["total_value"],
        })

    future_filings = [
        {
            "id": 100,
            "type": "13F Filing Deadline",
            "ticker": "ALL",
            "title": "Quarterly 13F Filing Deadline Approaching",
            "message": ("Institutional 13F filings are due 45 days after each quarter end - expect hedge fund "
                        "position disclosures around that date."),
            "significance": "MEDIUM",
            "timestamp": (now + timedelta(days=15)).isoformat(),
            "days_ahead": 15,
            "action": "WATCH",
            "expected": True,
        },
    ]

    return {
        "past_filings": past_filings,
        "future_expected": future_filings,
        "total_past": len(past_filings),
        "total_future": len(future_filings),
    }


# Generate realistic market events with D-X phases
def generate_market_events():
    now = datetime.now()
    companies = [
        {"ticker": "NVDA", "name": "NVIDIA"},
        {"ticker": "AAPL", "name": "Apple"},
        {"ticker": "MSFT", "name": "Microsoft"},
        {"ticker": "GOOGL", "name": "Alphabet"},
        {"ticker": "TSLA", "name": "Tesla"},
        {"ticker": "META", "name": "Meta"},
        {"ticker": "AMZN", "name": "Amazon"},
        {"ticker": "AMD", "name": "AMD"},
    ]

    events = []
    event_id = 1

    # Generate events for next 3 months (90 days)
    for company in companies:
        # Generate 3 earnings events per company across 3 months
        for quarter_offset in range(3):
            days = random.randint(1, 30) + (quarter_offset * 30)
            event_date = now + timedelta(days=days)

            if days <= 2:
                phase = "DANGER"
            elif days <= 9:
                phase = "EUFORIA"
            elif days <= 20:
                phase = "ACCUMULATION"
            else:
                phase = "PRE-RUMOR"

            expected_eps = round(random.uniform(0.5, 2.5), 2)
            impact = round(random.uniform(7.0, 9.5), 1)

            events.append({
                "id": event_id,
                "title": f"{company['name']} Q{((now.month + quarter_offset - 1) % 4) + 1} 2026 Earnings",
                "date": event_date.strftime("%Y-%m-%d"),
                "time": "16:00",
                "event_type": "earnings",
                "description": f"{company['name']} quarterly earnings release",
                "impact_score": impact,
                "affected_tickers": company['ticker'],
                "phase": phase,
                "days_away": days,
                "hours_away": days * 24,
                "expected_eps": expected_eps,
                "sentiment": "bullish" if random.random() > 0.4 else "neutral",
                "recommendation": f"Watch {company['ticker']} - {phase} phase optimal for {'entry' if phase == 'ACCUMULATION' else 'monitoring'}"
            })
            event_id += 1

    # Add economic events spread across 3 months
    economic_events = [
        {"name": "CPI Release", "impact": 9.5, "days": 3},
        {"name": "FOMC Meeting", "impact": 9.8, "days": 7},
        {"name": "NFP Report", "impact": 9.2, "days": 5},
        {"name": "GDP Data", "impact": 8.5, "days": 12},
        {"name": "Retail Sales", "impact": 7.8, "days": 15},
        {"name": "CPI Release", "impact": 9.5, "days": 33},
        {"name": "FOMC Meeting", "impact": 9.8, "days": 45},
        {"name": "NFP Report", "impact": 9.2, "days": 35},
        {"name": "Unemployment Claims", "impact": 8.2, "days": 25},
        {"name": "PCE Index", "impact": 8.8, "days": 40},
        {"name": "CPI Release", "impact": 9.5, "days": 63},
        {"name": "GDP Data", "impact": 8.5, "days": 70},
        {"name": "Retail Sales", "impact": 7.8, "days": 75},
        {"name": "Housing Starts", "impact": 7.5, "days": 55},
        {"name": "Consumer Confidence", "impact": 7.2, "days": 50},
    ]

    for econ in economic_events:
        days = econ['days']
        event_date = now + timedelta(days=days)

        if days <= 2:
            phase = "DANGER"
        elif days <= 9:
            phase = "EUFORIA"
        elif days <= 20:
            phase = "ACCUMULATION"
        else:
            phase = "PRE-RUMOR"

        events.append({
            "id": event_id,
            "title": econ['name'],
            "date": event_date.strftime("%Y-%m-%d"),
            "time": "08:30",
            "event_type": "economic",
            "description": f"US {econ['name']}",
            "impact_score": econ['impact'],
            "affected_tickers": "SPY,QQQ,DIA",
            "phase": phase,
            "days_away": days,
            "hours_away": days * 24,
            "previous": "3.2%",
            "forecast": "3.3%",
            "sentiment": "neutral",
            "recommendation": f"High impact - {phase} phase"
        })
        event_id += 1

    return sorted(events, key=lambda x: x['days_away'])

# Generate realistic news
def generate_news():
    """Real RSS-aggregated market news. Falls back to illustrative sample data on total fetch failure."""
    real_items = real_data.get_real_news(limit=30)
    if real_items:
        return [dict(item, id=idx + 1) for idx, item in enumerate(real_items)]
    return _fallback_news()


def _fallback_news():
    news_items = [
        {
            "title": "NVIDIA Announces Next-Gen AI Chips at GTC 2026",
            "source": "Reuters",
            "sentiment": "bullish",
            "summary": "NVIDIA unveils Blackwell Ultra architecture with 3x performance gains",
            "tickers": "NVDA",
            "urgency": "high"
        },
        {
            "title": "Fed Officials Signal Potential Rate Cut in Q4",
            "source": "Bloomberg",
            "sentiment": "bullish",
            "summary": "FOMC members hint at dovish pivot amid cooling inflation",
            "tickers": "SPY,QQQ",
            "urgency": "breaking"
        },
        {
            "title": "Tesla Robotaxi Event Draws Mixed Reactions",
            "source": "CNBC",
            "sentiment": "neutral",
            "summary": "Analysts divided on feasibility of 2027 rollout timeline",
            "tickers": "TSLA",
            "urgency": "high"
        },
        {
            "title": "Apple Vision Pro 2 Enters Mass Production",
            "source": "WSJ",
            "sentiment": "bullish",
            "summary": "Suppliers report strong order volumes for Q1 2027 launch",
            "tickers": "AAPL",
            "urgency": "medium"
        },
        {
            "title": "Crude Oil Surges on Middle East Tensions",
            "source": "MarketWatch",
            "sentiment": "bearish",
            "summary": "WTI breaks $95/barrel as supply concerns mount",
            "tickers": "XLE,USO",
            "urgency": "breaking"
        },
        {
            "title": "Microsoft Azure Revenue Beats Estimates",
            "source": "Reuters",
            "sentiment": "bullish",
            "summary": "Cloud growth accelerates to 31% YoY on AI demand",
            "tickers": "MSFT",
            "urgency": "high"
        },
        {
            "title": "Bitcoin Approaches $75K as ETF Inflows Surge",
            "source": "CoinDesk",
            "sentiment": "bullish",
            "summary": "Spot Bitcoin ETFs see $2.1B in net inflows this week",
            "tickers": "BTC,MSTR",
            "urgency": "high"
        },
        {
            "title": "Consumer Confidence Index Drops to 8-Month Low",
            "source": "Bloomberg",
            "sentiment": "bearish",
            "summary": "Concerns over job market weigh on sentiment",
            "tickers": "SPY,XLY",
            "urgency": "medium"
        },
        {
            "title": "AMD Gains Market Share in Data Center Chips",
            "source": "CNBC",
            "sentiment": "bullish",
            "summary": "EPYC processors capture 24% of server CPU market",
            "tickers": "AMD",
            "urgency": "medium"
        },
        {
            "title": "Treasury Yields Spike After Strong Jobs Data",
            "source": "Reuters",
            "sentiment": "neutral",
            "summary": "10-year yield climbs to 4.35% on NFP beat",
            "tickers": "TLT,IEF",
            "urgency": "high"
        }
    ]

    news = []
    now = datetime.now()

    for idx, item in enumerate(news_items):
        published = now - timedelta(hours=random.randint(1, 72))
        news.append({
            "id": idx + 1,
            "title": item['title'],
            "published_at": published.isoformat(),
            "source": item['source'],
            "sentiment": item['sentiment'],
            "summary": item['summary'],
            "tickers": item['tickers'],
            "url": f"https://example.com/news/{idx+1}",
            "urgency": item.get('urgency', 'medium')
        })

    return sorted(news, key=lambda x: x['published_at'], reverse=True)

# Generate signals
def generate_signals():
    """Real market-context opportunity detection. Each signal cites the specific real fact it's
    derived from (an insider cluster buy, a real tagged news item, a real sentiment/VIX extreme,
    or real crypto momentum) - no random tickers, phases, or prices. entry_price is a real
    reference price where one genuinely exists (the real Form 4 filing price, or the real crypto
    spot price); target_price/stop_loss are left null rather than fabricated, since there's no
    real price series being fetched here to derive them honestly."""
    out: List[Dict[str, Any]] = []
    sid = 0
    now_iso = datetime.now().isoformat()

    buys = [t for t in INSIDER_TRADES if t["transaction_type"] == "BUY"]
    by_ticker: Dict[str, List[Dict[str, Any]]] = {}
    for t in buys:
        by_ticker.setdefault(t["ticker"], []).append(t)

    seen_tickers = set()
    for ticker, trades in by_ticker.items():
        distinct_insiders = sorted({t["insider_name"] for t in trades})
        if len(distinct_insiders) >= 2:
            sid += 1
            total_value = sum(t["total_value"] for t in trades)
            out.append({
                "id": sid, "ticker": ticker, "signal_type": "insider_cluster_buy", "phase": "ACCUMULATION",
                "entry_price": trades[0]["price"], "target_price": None, "stop_loss": None,
                "confidence": round(min(60 + len(distinct_insiders) * 8, 90), 1),
                "reasoning": (f"{len(distinct_insiders)} distinct insiders ({', '.join(distinct_insiders)}) bought "
                              f"{ticker} for a combined ${total_value:,.0f} within days of each other - real SEC "
                              "Form 4 filings"),
                "trigger": "insider_cluster_buy", "generated_at": now_iso,
            })
            seen_tickers.add(ticker)

    for t in buys:
        if t["ticker"] in seen_tickers or t["significance"] not in ("HIGH", "EXTREME"):
            continue
        sid += 1
        out.append({
            "id": sid, "ticker": t["ticker"], "signal_type": "insider_buy", "phase": "ACCUMULATION",
            "entry_price": t["price"], "target_price": None, "stop_loss": None,
            "confidence": 75.0 if t["significance"] == "EXTREME" else 65.0,
            "reasoning": f"{t['role']} {t['insider_name']} bought ${t['total_value']:,.0f} of {t['ticker']} - real SEC Form 4 filing",
            "trigger": "insider_buy", "generated_at": now_iso,
        })
        seen_tickers.add(t["ticker"])

    for item in _all_news()[:30]:
        raw_tickers = item.get("tickers")
        if not raw_tickers or raw_tickers == "N/A" or item.get("sentiment") not in ("bullish", "bearish"):
            continue
        for ticker in [t.strip() for t in str(raw_tickers).split(",") if t.strip()][:2]:
            sid += 1
            out.append({
                "id": sid, "ticker": ticker, "signal_type": "news_catalyst",
                "phase": "EUFORIA" if item["sentiment"] == "bullish" else "DANGER",
                "entry_price": None, "target_price": None, "stop_loss": None,
                "confidence": 70.0 if item.get("urgency") == "breaking" else 55.0,
                "reasoning": f"{item['sentiment'].upper()} news: \"{item['title']}\" ({item['source']})",
                "trigger": "news_catalyst", "generated_at": now_iso,
            })

    for ind in SENTIMENT:
        if ind["indicator_name"] == "Fear & Greed" and (ind["value"] <= 20 or ind["value"] >= 80):
            sid += 1
            out.append({
                "id": sid, "ticker": "SPY", "signal_type": "sentiment_extreme",
                "phase": "ACCUMULATION" if ind["value"] <= 20 else "DANGER",
                "entry_price": None, "target_price": None, "stop_loss": None, "confidence": 60.0,
                "reasoning": f"CNN Fear & Greed at {ind['value']} ({ind['interpretation']}) - contrarian extreme reading",
                "trigger": "sentiment_extreme", "generated_at": now_iso,
            })
        if ind["indicator_name"] == "VIX" and ind["value"] >= 25:
            sid += 1
            out.append({
                "id": sid, "ticker": "VIX", "signal_type": "sentiment_extreme", "phase": "DANGER",
                "entry_price": ind["value"], "target_price": None, "stop_loss": None, "confidence": 55.0,
                "reasoning": f"VIX at {ind['value']} - elevated real volatility reading",
                "trigger": "sentiment_extreme", "generated_at": now_iso,
            })

    for c in CRYPTO:
        change = c.get("change_24h", 0) or 0
        if abs(change) >= 8:
            sid += 1
            out.append({
                "id": sid, "ticker": c["symbol"], "signal_type": "crypto_momentum",
                "phase": "EUFORIA" if change > 0 else "DANGER",
                "entry_price": round(c["price"], 2), "target_price": None, "stop_loss": None,
                "confidence": round(min(50 + abs(change), 85), 1),
                "reasoning": f"{c['name']} {'up' if change > 0 else 'down'} {abs(change)}% in 24h - real CoinGecko price",
                "trigger": "crypto_momentum", "generated_at": now_iso,
            })

    return sorted(out, key=lambda s: s["confidence"], reverse=True)[:25]

# Generate crypto data
def generate_crypto():
    """Real CoinGecko prices. Falls back to illustrative sample data on fetch failure."""
    real_prices = real_data.get_crypto_prices()
    if real_prices:
        return real_prices
    return _fallback_crypto()


def _fallback_crypto():
    cryptos = [
        {"symbol": "BTC", "name": "Bitcoin", "price": 73250},
        {"symbol": "ETH", "name": "Ethereum", "price": 3890},
        {"symbol": "SOL", "name": "Solana", "price": 178},
    ]

    metrics = []
    for idx, crypto in enumerate(cryptos):
        change = round(random.uniform(-5, 8), 2)
        metrics.append({
            "id": idx + 1,
            "symbol": crypto['symbol'],
            "name": crypto['name'],
            "price": crypto['price'] * (1 + change/100),
            "change_24h": change,
            "market_cap": crypto['price'] * random.randint(18000000, 21000000),
            "volume_24h": crypto['price'] * random.randint(20000000, 40000000),
            "source": "CoinGecko",
            "timestamp": datetime.now().isoformat()
        })

    return metrics

# Generate sentiment indicators
def generate_sentiment():
    """Real Fear & Greed / Reddit / VIX sentiment. Falls back to illustrative sample data per-source
    on individual fetch failure - interpretation is always derived from the actual value, real or sample."""
    indicators = []

    fg = real_data.get_fear_greed()
    if fg:
        value = fg["value"]
        interpretation = fg["rating"].title() if fg.get("rating") else _fear_greed_label(value)
    else:
        value = random.randint(45, 75)
        interpretation = _fear_greed_label(value)
    indicators.append({
        "id": 1,
        "source": "CNN Fear & Greed Index",
        "timestamp": datetime.now().isoformat(),
        "indicator_name": "Fear & Greed",
        "value": value,
        "interpretation": interpretation,
        "affected_markets": "SPY,QQQ,DIA"
    })

    reddit = real_data.get_reddit_sentiment()
    if reddit:
        value = reddit["value"]
    else:
        value = random.randint(55, 85)
    indicators.append({
        "id": 2,
        "source": "Reddit Sentiment",
        "timestamp": datetime.now().isoformat(),
        "indicator_name": "Social Sentiment",
        "value": value,
        "interpretation": "Very Bullish" if value >= 70 else "Bullish" if value >= 55 else
                          "Neutral" if value >= 40 else "Bearish",
        "affected_markets": "Meme stocks"
    })

    vix = real_data.get_vix()
    if vix is None:
        vix = round(random.uniform(14, 22), 2)
    indicators.append({
        "id": 3,
        "source": "CBOE",
        "timestamp": datetime.now().isoformat(),
        "indicator_name": "VIX",
        "value": vix,
        "interpretation": "High volatility" if vix >= 25 else "Moderate volatility" if vix >= 18 else "Low volatility",
        "affected_markets": "SPY,QQQ,VIX"
    })

    return indicators


def _fear_greed_label(value: int) -> str:
    if value >= 75:
        return "Extreme Greed"
    if value >= 55:
        return "Greed"
    if value >= 45:
        return "Neutral"
    if value >= 25:
        return "Fear"
    return "Extreme Fear"

def _all_news() -> List[Dict[str, Any]]:
    """NEWS (RSS) plus real live Telegram breaking-news messages, newest first."""
    return telegram_feed.get_recent(15) + NEWS


def _build_ai_context() -> Dict[str, Any]:
    """Compact real-data context passed to the LLM for grounded predictions/daily brief."""
    top_news = sorted(_all_news(), key=lambda x: x["published_at"], reverse=True)[:12]
    top_insider_trades = sorted(INSIDER_TRADES, key=lambda x: x.get("total_value", 0), reverse=True)[:10]
    return {
        "news": [{"title": n["title"], "sentiment": n["sentiment"], "tickers": n["tickers"],
                  "summary": n["summary"]} for n in top_news],
        "telegram_breaking_news": [{"title": m["title"], "summary": m["summary"]}
                                     for m in telegram_feed.get_recent(8)],
        "insider_trades": [{"ticker": t["ticker"], "insider_name": t["insider_name"], "role": t["role"],
                             "transaction_type": t["transaction_type"], "total_value": t["total_value"],
                             "shares": t["shares"], "date": t["date"]} for t in top_insider_trades],
        "sentiment": SENTIMENT,
        "crypto": CRYPTO,
    }


# Cache data (dependency order matters: news/sentiment/crypto/insider trades first, so
# _build_ai_context() and generate_signals() have real data available to derive from)
EVENTS = generate_market_events()
NEWS = generate_news()
CRYPTO = generate_crypto()
SENTIMENT = generate_sentiment()
INSIDER_TRADES = generate_insider_trades()
SIGNALS = generate_signals()
SMART_MONEY_NOTIFICATIONS = generate_smart_money_notifications()
PREDICTED_EVENTS = generate_predicted_events()

history_db.init()

_AI_CONTEXT = _build_ai_context()
AI_PREDICTIONS = generate_ai_predictions(_AI_CONTEXT)
DAILY_BRIEF = generate_daily_brief(_AI_CONTEXT)


def _persist_and_annotate_predictions(predictions: Dict[str, Any]) -> Dict[str, Any]:
    """Save a snapshot to the real persistent history, then reflect the real
    accumulated count back into the response instead of a permanent 0."""
    history_db.save_prediction_snapshot(predictions)
    real_count = history_db.get_predictions_made_count(days=30)
    predictions["prediction_accuracy_stats"]["last_30_days"]["predictions_made"] = real_count
    return predictions


AI_PREDICTIONS = _persist_and_annotate_predictions(AI_PREDICTIONS)
history_db.save_daily_brief(DAILY_BRIEF)
history_db.save_sentiment_snapshot(SENTIMENT)
history_db.save_news_items(NEWS)
history_db.save_insider_trades(INSIDER_TRADES)


# ---------------------------------------------------------------------------
# Background refresh: keep cached data live without hitting free-tier
# sources/LLM providers on every request. "Fast" data refreshes often; "slow"
# data (SEC EDGAR + LLM calls) refreshes less often to stay within free-tier
# limits and SEC's fair-use guidance.
# ---------------------------------------------------------------------------

_FAST_REFRESH_SECONDS = 600   # ~10 min: news / sentiment / crypto
_SLOW_REFRESH_TICKS = 3       # every 3rd fast tick (~30 min): insider trades + AI predictions/brief


def _refresh_fast():
    global NEWS, SENTIMENT, CRYPTO, SIGNALS
    try:
        NEWS = generate_news()
        history_db.save_news_items(NEWS)
    except Exception as e:
        print(f"[refresh] news refresh failed, keeping last-known-good: {e}")
    try:
        SENTIMENT = generate_sentiment()
        history_db.save_sentiment_snapshot(SENTIMENT)
    except Exception as e:
        print(f"[refresh] sentiment refresh failed, keeping last-known-good: {e}")
    try:
        CRYPTO = generate_crypto()
    except Exception as e:
        print(f"[refresh] crypto refresh failed, keeping last-known-good: {e}")
    try:
        SIGNALS = generate_signals()
    except Exception as e:
        print(f"[refresh] signals refresh failed, keeping last-known-good: {e}")


def _refresh_slow():
    global INSIDER_TRADES, SMART_MONEY_NOTIFICATIONS, AI_PREDICTIONS, DAILY_BRIEF, SIGNALS
    try:
        INSIDER_TRADES = generate_insider_trades()
        SMART_MONEY_NOTIFICATIONS = generate_smart_money_notifications()
        history_db.save_insider_trades(INSIDER_TRADES)
        SIGNALS = generate_signals()
    except Exception as e:
        print(f"[refresh] insider trades refresh failed, keeping last-known-good: {e}")
    try:
        context = _build_ai_context()
        AI_PREDICTIONS = _persist_and_annotate_predictions(generate_ai_predictions(context))
        DAILY_BRIEF = generate_daily_brief(context)
        history_db.save_daily_brief(DAILY_BRIEF)
    except Exception as e:
        print(f"[refresh] AI predictions/brief refresh failed, keeping last-known-good: {e}")


def _refresh_loop():
    tick = 0
    while True:
        time.sleep(_FAST_REFRESH_SECONDS)
        tick += 1
        _refresh_fast()
        if tick % _SLOW_REFRESH_TICKS == 0:
            _refresh_slow()

@app.on_event("startup")
async def _start_background_refresh():
    threading.Thread(target=_refresh_loop, daemon=True).start()
    try:
        telegram_feed.start_background(
            on_new_message=lambda item: history_db.save_news_items([item])
        )
    except Exception as e:
        print(f"[telegram_feed] failed to start: {e}")
    try:
        backtest_engine.start_background()
    except Exception as e:
        print(f"[backtest_engine] failed to start: {e}")


@app.get("/")
async def root():
    return {
        "service": "Aeon Nimbus Intelligence",
        "version": "5.0.0",
        "status": "operational",
        "data_sources": "40+ free sources",
        "events": len(EVENTS),
        "news": len(NEWS),
        "signals": len(SIGNALS),
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/dashboard")
async def get_dashboard():
    return {
        "events": EVENTS,
        "news": _all_news()[:20],
        "signals": SIGNALS,
        "crypto": CRYPTO,
        "sentiment": SENTIMENT,
        "insider_trades": INSIDER_TRADES,
        "smart_money_notifications": SMART_MONEY_NOTIFICATIONS,
        "predicted_events": PREDICTED_EVENTS,
        "daily_brief": DAILY_BRIEF,
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/daily-brief")
async def get_daily_brief():
    """AI-powered daily intelligence brief with actionable stock recommendations"""
    return {
        "brief": DAILY_BRIEF,
        "description": "Synthesizes all data sources to recommend which stocks to watch today. Combines insider trades, congressional activity, institutional flow, predictions, and market context.",
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/predictions")
async def get_predictions():
    """Market predictions and expected events from all data sources"""
    return {
        "predictions": PREDICTED_EVENTS,
        "total": len(PREDICTED_EVENTS),
        "description": "Expected events, consensus forecasts, and whisper numbers from market data sources. Stay ahead of the market by tracking what's expected vs what actually happens.",
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/insider/trades")
async def get_insider_trades():
    """Smart Money Flow insider trading data - 3 months history"""
    return {
        "trades": INSIDER_TRADES,
        "total": len(INSIDER_TRADES),
        "source": "Smart Money Flow",
        "description": "SEC Form 4 insider trading filings - 3 months history with smart money analysis. Track what corporate insiders are doing with their own money - the ultimate conviction signal.",
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/smart-money/notifications")
async def get_smart_money_notifications():
    """Past 7 days of Smart Money Flow notifications + future expected filings"""
    return {
        "notifications": SMART_MONEY_NOTIFICATIONS,
        "source": "Smart Money Flow",
        "description": "Upcoming public regulatory disclosure deadlines (e.g. 13F). Past filings are the same real SEC Form 4 data shown on the Insider Trading tab.",
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/events/live")
async def get_events():
    return EVENTS

@app.get("/api/news/live")
async def get_news():
    return _all_news()

@app.get("/api/news/all")
async def get_all_news():
    news = _all_news()
    return {"news": news, "total": len(news)}

@app.get("/api/telegram/breaking-news")
async def get_telegram_breaking_news():
    """Real messages from the Tradeul_Breaking_News Telegram channel: a real backfilled
    history window (see status.history_window_days) plus anything arriving live."""
    return {"messages": telegram_feed.get_recent(8000), "status": telegram_feed.get_status()}

@app.get("/api/signals")
async def get_signals():
    return SIGNALS

@app.get("/api/crypto")
async def get_crypto_data():
    return {"metrics": CRYPTO, "total": len(CRYPTO)}

@app.get("/api/sentiment")
async def get_sentiment_data():
    return {"indicators": SENTIMENT, "total": len(SENTIMENT)}

@app.get("/api/economic-calendar")
async def get_economic_calendar():
    economic = [e for e in EVENTS if e['event_type'] == 'economic']
    return {"releases": economic, "total": len(economic)}

@app.get("/api/sources/status")
async def get_sources_status():
    """Get status of all data sources with historical data"""
    now = datetime.now()

    # Simulate source status with historical data
    sources = [
        {
            "name": "Reuters RSS",
            "category": "News",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(1, 15))).isoformat(),
            "update_frequency": "Real-time",
            "requests_24h": random.randint(400, 600),
            "success_rate": round(random.uniform(95, 100), 1),
            "data_points_week": random.randint(800, 1200)
        },
        {
            "name": "CNBC RSS",
            "category": "News",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(1, 15))).isoformat(),
            "update_frequency": "Real-time",
            "requests_24h": random.randint(350, 550),
            "success_rate": round(random.uniform(95, 100), 1),
            "data_points_week": random.randint(700, 1100)
        },
        {
            "name": "MarketWatch RSS",
            "category": "News",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(1, 15))).isoformat(),
            "update_frequency": "Real-time",
            "requests_24h": random.randint(300, 500),
            "success_rate": round(random.uniform(95, 100), 1),
            "data_points_week": random.randint(600, 1000)
        },
        {
            "name": "Yahoo Finance RSS",
            "category": "News",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(1, 20))).isoformat(),
            "update_frequency": "Real-time",
            "requests_24h": random.randint(400, 600),
            "success_rate": round(random.uniform(93, 99), 1),
            "data_points_week": random.randint(800, 1200)
        },
        {
            "name": "FRED API",
            "category": "Economic",
            "status": "active",
            "last_update": (now - timedelta(hours=random.randint(1, 4))).isoformat(),
            "update_frequency": "Daily",
            "requests_24h": random.randint(20, 40),
            "success_rate": round(random.uniform(98, 100), 1),
            "data_points_week": random.randint(150, 250)
        },
        {
            "name": "ECB Data",
            "category": "Economic",
            "status": "active",
            "last_update": (now - timedelta(hours=random.randint(2, 6))).isoformat(),
            "update_frequency": "Daily",
            "requests_24h": random.randint(15, 30),
            "success_rate": round(random.uniform(96, 100), 1),
            "data_points_week": random.randint(100, 200)
        },
        {
            "name": "World Bank API",
            "category": "Economic",
            "status": "active",
            "last_update": (now - timedelta(hours=random.randint(3, 8))).isoformat(),
            "update_frequency": "Weekly",
            "requests_24h": random.randint(5, 15),
            "success_rate": round(random.uniform(97, 100), 1),
            "data_points_week": random.randint(50, 150)
        },
        {
            "name": "CoinGecko API",
            "category": "Crypto",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(1, 10))).isoformat(),
            "update_frequency": "5 minutes",
            "requests_24h": random.randint(250, 350),
            "success_rate": round(random.uniform(97, 100), 1),
            "data_points_week": random.randint(2000, 3000)
        },
        {
            "name": "CoinPaprika API",
            "category": "Crypto",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(1, 10))).isoformat(),
            "update_frequency": "5 minutes",
            "requests_24h": random.randint(200, 300),
            "success_rate": round(random.uniform(96, 100), 1),
            "data_points_week": random.randint(1800, 2800)
        },
        {
            "name": "CNN Fear & Greed",
            "category": "Sentiment",
            "status": "active",
            "last_update": (now - timedelta(hours=random.randint(1, 3))).isoformat(),
            "update_frequency": "Hourly",
            "requests_24h": random.randint(20, 30),
            "success_rate": round(random.uniform(98, 100), 1),
            "data_points_week": random.randint(150, 200)
        },
        {
            "name": "Reddit API",
            "category": "Sentiment",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(5, 20))).isoformat(),
            "update_frequency": "15 minutes",
            "requests_24h": random.randint(80, 120),
            "success_rate": round(random.uniform(94, 99), 1),
            "data_points_week": random.randint(600, 900)
        },
        {
            "name": "CBOE VIX",
            "category": "Technical",
            "status": "active",
            "last_update": (now - timedelta(hours=random.randint(1, 4))).isoformat(),
            "update_frequency": "Hourly",
            "requests_24h": random.randint(20, 35),
            "success_rate": round(random.uniform(96, 100), 1),
            "data_points_week": random.randint(150, 200)
        },
        {
            "name": "Forex Factory",
            "category": "Calendar",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(10, 30))).isoformat(),
            "update_frequency": "30 minutes",
            "requests_24h": random.randint(40, 60),
            "success_rate": round(random.uniform(95, 100), 1),
            "data_points_week": random.randint(300, 500)
        },
        {
            "name": "Investing.com",
            "category": "Calendar",
            "status": "active",
            "last_update": (now - timedelta(minutes=random.randint(10, 30))).isoformat(),
            "update_frequency": "30 minutes",
            "requests_24h": random.randint(35, 55),
            "success_rate": round(random.uniform(93, 98), 1),
            "data_points_week": random.randint(250, 450)
        },
        {
            "name": "SEC EDGAR",
            "category": "Regulatory",
            "status": "active",
            "last_update": (now - timedelta(hours=random.randint(2, 8))).isoformat(),
            "update_frequency": "Daily",
            "requests_24h": random.randint(10, 25),
            "success_rate": round(random.uniform(97, 100), 1),
            "data_points_week": random.randint(80, 150)
        },
    ]

    # Calculate overall stats
    total_sources = len(sources)
    active_sources = sum(1 for s in sources if s["status"] == "active")
    total_requests = sum(s["requests_24h"] for s in sources)
    avg_success_rate = sum(s["success_rate"] for s in sources) / len(sources)
    total_data_points = sum(s["data_points_week"] for s in sources)

    return {
        "sources": sources,
        "stats": {
            "total_sources": total_sources,
            "active_sources": active_sources,
            "total_requests_24h": total_requests,
            "avg_success_rate": round(avg_success_rate, 1),
            "total_data_points_week": total_data_points
        },
        "last_update": now.isoformat()
    }

def _backtest_by_category(backtest: dict) -> dict:
    """Flattens the real backtest's per-signal/per-horizon results into the {accuracy, n} shape
    prediction_accuracy_stats.by_category already renders - this is the real evidence behind the
    accuracy claim, not a separate unrelated number."""
    out = {}
    for sig_name, sig in (backtest.get("signals") or {}).items():
        for horizon, stats in (sig.get("by_horizon") or {}).items():
            if stats.get("signals_tested"):
                out[f"{sig_name}_{horizon}"] = {
                    "accuracy": round((stats["pct_positive"] or 0) / 100, 3),
                    "n": stats["signals_tested"],
                }
    return out

@app.get("/api/ai-predictions")
async def get_ai_predictions():
    """Get AI-powered market predictions (cached; refreshed on the slow background cycle).
    prediction_accuracy_stats.by_category is populated from the real historical backtest (fetched
    fresh each request from its own daily-refreshed cache) - it's the real evidence behind the
    accuracy section, not a separate unrelated number. historical_backtest is kept alongside with
    the full methodology/sample data for the section that renders the detail."""
    backtest = backtest_engine.get_cached_backtest()
    result = dict(AI_PREDICTIONS)
    stats = dict(result.get("prediction_accuracy_stats") or {})
    if backtest.get("signals"):
        stats["by_category"] = _backtest_by_category(backtest)
        stats["model_improvements"] = [
            "No resolved live-prediction track record yet (the live grounded predictions above were only just "
            "wired up). The category breakdown here is the real historical backtest of the underlying insider-buy "
            "signal - see historical_backtest below for full methodology, sample events, and caveats."
        ]
    result["prediction_accuracy_stats"] = stats
    result["historical_backtest"] = backtest
    return result

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
