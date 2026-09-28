"""
Aeon Nimbus Intelligence - Enhanced Production API
Economic data, historical events, live updates with expected vs actual results
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
from collections import defaultdict
import random

app = FastAPI(title="Aeon Nimbus Intelligence API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced Data Models
class EconomicRelease(BaseModel):
    id: int
    name: str
    date: str
    time: str
    country: str
    category: str  # macro, geopolitical, earnings, commodity
    previous: Optional[float] = None
    forecast: Optional[float] = None
    actual: Optional[float] = None
    impact: str  # high, medium, low
    affected_markets: str
    source: str
    is_historical: bool
    volatility_score: float
    countdown_hours: Optional[int] = None

class LiveUpdate(BaseModel):
    id: int
    timestamp: str
    source: str  # tradeul, investing, bloomberg, reuters, telegram
    title: str
    content: str
    category: str
    affected_tickers: str
    sentiment: str
    urgency: str  # breaking, high, medium, low

class MarketEvent(BaseModel):
    id: int
    title: str
    date: str
    event_type: str
    description: str
    impact_score: float
    affected_tickers: str
    phase: str
    days_away: int
    countdown_hours: int
    has_earnings: bool
    expected_eps: Optional[float] = None
    actual_eps: Optional[float] = None
    volatility_expected: float
    recommendation: str

# In-memory storage
economic_releases_db: List[EconomicRelease] = []
live_updates_db: List[LiveUpdate] = []
market_events_db: List[MarketEvent] = []

# Initialize enhanced data
def initialize_enhanced_data():
    global economic_releases_db, live_updates_db, market_events_db

    now = datetime.now()

    # Historical economic data (last 7 days)
    economic_releases_db = []

    # Historical releases with actual results
    historical_data = [
        {
            "name": "Non-Farm Payrolls",
            "category": "macro",
            "country": "US",
            "previous": 177000,
            "forecast": 185000,
            "actual": 199000,
            "impact": "high",
            "affected_markets": "SPY,QQQ,DXY,GLD",
            "days_ago": 2,
            "volatility_score": 9.2
        },
        {
            "name": "CPI (Consumer Price Index)",
            "category": "macro",
            "country": "US",
            "previous": 3.2,
            "forecast": 3.1,
            "actual": 3.4,
            "impact": "high",
            "affected_markets": "SPY,TLT,DXY,GLD",
            "days_ago": 5,
            "volatility_score": 9.5
        },
        {
            "name": "Federal Funds Rate Decision",
            "category": "macro",
            "country": "US",
            "previous": 5.50,
            "forecast": 5.50,
            "actual": 5.50,
            "impact": "high",
            "affected_markets": "SPY,QQQ,TLT,DXY",
            "days_ago": 7,
            "volatility_score": 9.8
        },
        {
            "name": "ECB Interest Rate Decision",
            "category": "macro",
            "country": "EU",
            "previous": 4.50,
            "forecast": 4.25,
            "actual": 4.25,
            "impact": "high",
            "affected_markets": "EURUSD,DXY,SPY",
            "days_ago": 4,
            "volatility_score": 8.5
        },
        {
            "name": "China GDP Growth",
            "category": "macro",
            "country": "CN",
            "previous": 4.9,
            "forecast": 5.0,
            "actual": 4.6,
            "impact": "high",
            "affected_markets": "FXI,AAPL,TSLA,NVDA",
            "days_ago": 6,
            "volatility_score": 8.8
        },
        {
            "name": "Retail Sales",
            "category": "macro",
            "country": "US",
            "previous": 0.4,
            "forecast": 0.3,
            "actual": 0.7,
            "impact": "medium",
            "affected_markets": "SPY,XRT,AMZN,WMT",
            "days_ago": 3,
            "volatility_score": 7.2
        },
        {
            "name": "Unemployment Rate",
            "category": "macro",
            "country": "US",
            "previous": 3.8,
            "forecast": 3.8,
            "actual": 3.7,
            "impact": "medium",
            "affected_markets": "SPY,QQQ,DXY",
            "days_ago": 2,
            "volatility_score": 6.5
        }
    ]

    for idx, data in enumerate(historical_data):
        release_date = now - timedelta(days=data["days_ago"])
        economic_releases_db.append(EconomicRelease(
            id=idx + 1,
            name=data["name"],
            date=release_date.strftime("%Y-%m-%d"),
            time="08:30" if data["country"] == "US" else "13:45",
            country=data["country"],
            category=data["category"],
            previous=data["previous"],
            forecast=data["forecast"],
            actual=data["actual"],
            impact=data["impact"],
            affected_markets=data["affected_markets"],
            source="Investing.com",
            is_historical=True,
            volatility_score=data["volatility_score"],
            countdown_hours=None
        ))

    # Upcoming releases with forecasts
    upcoming_data = [
        {
            "name": "CPI (Consumer Price Index)",
            "category": "macro",
            "country": "US",
            "previous": 3.4,
            "forecast": 3.3,
            "impact": "high",
            "affected_markets": "SPY,TLT,DXY,GLD",
            "days_ahead": 2,
            "hours": 8,
            "volatility_score": 9.5
        },
        {
            "name": "Federal Funds Rate Decision",
            "category": "macro",
            "country": "US",
            "previous": 5.50,
            "forecast": 5.25,
            "impact": "high",
            "affected_markets": "SPY,QQQ,TLT,DXY,GLD",
            "days_ahead": 5,
            "hours": 14,
            "volatility_score": 9.8
        },
        {
            "name": "Non-Farm Payrolls",
            "category": "macro",
            "country": "US",
            "previous": 199000,
            "forecast": 180000,
            "impact": "high",
            "affected_markets": "SPY,QQQ,DXY,GLD",
            "days_ahead": 6,
            "hours": 8,
            "volatility_score": 9.2
        },
        {
            "name": "PPI (Producer Price Index)",
            "category": "macro",
            "country": "US",
            "previous": 2.3,
            "forecast": 2.2,
            "impact": "medium",
            "affected_markets": "SPY,QQQ,DXY",
            "days_ahead": 3,
            "hours": 8,
            "volatility_score": 7.8
        },
        {
            "name": "EIA Crude Oil Inventories",
            "category": "commodity",
            "country": "US",
            "previous": -2.2,
            "forecast": -1.5,
            "impact": "medium",
            "affected_markets": "USO,XLE,CVX,XOM",
            "days_ahead": 1,
            "hours": 10,
            "volatility_score": 6.5
        },
        {
            "name": "ECB Press Conference",
            "category": "macro",
            "country": "EU",
            "previous": None,
            "forecast": None,
            "impact": "high",
            "affected_markets": "EURUSD,DXY,SPY",
            "days_ahead": 7,
            "hours": 13,
            "volatility_score": 8.5
        }
    ]

    for idx, data in enumerate(upcoming_data):
        release_date = now + timedelta(days=data["days_ahead"])
        countdown = data["days_ahead"] * 24 + data["hours"]
        economic_releases_db.append(EconomicRelease(
            id=len(economic_releases_db) + 1,
            name=data["name"],
            date=release_date.strftime("%Y-%m-%d"),
            time=f"{data['hours']:02d}:30",
            country=data["country"],
            category=data["category"],
            previous=data["previous"],
            forecast=data["forecast"],
            actual=None,
            impact=data["impact"],
            affected_markets=data["affected_markets"],
            source="Investing.com",
            is_historical=False,
            volatility_score=data["volatility_score"],
            countdown_hours=countdown
        ))

    # Live updates (simulated from multiple sources)
    live_updates_db = []
    sources = ["Tradeul", "Bloomberg", "Reuters", "Investing.com", "WSJ", "CNBC"]
    sentiments = ["positive", "negative", "neutral"]
    urgencies = ["breaking", "high", "medium", "low"]
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN", "SPY", "QQQ"]

    for i in range(50):
        hours_ago = random.randint(0, 168)  # Last 7 days
        timestamp = now - timedelta(hours=hours_ago)

        live_updates_db.append(LiveUpdate(
            id=i + 1,
            timestamp=timestamp.isoformat(),
            source=random.choice(sources),
            title=generate_news_title(random.choice(tickers), random.choice(sentiments)),
            content=generate_news_content(random.choice(tickers), random.choice(sentiments)),
            category=random.choice(["earnings", "macro", "geopolitical", "market"]),
            affected_tickers=",".join(random.sample(tickers, random.randint(1, 3))),
            sentiment=random.choice(sentiments),
            urgency=random.choice(urgencies)
        ))

    # Sort by timestamp descending
    live_updates_db.sort(key=lambda x: x.timestamp, reverse=True)

    # Market events with earnings and volatility
    market_events_db = []
    companies = [
        {"ticker": "AAPL", "name": "Apple", "expected_eps": 1.52},
        {"ticker": "MSFT", "name": "Microsoft", "expected_eps": 2.65},
        {"ticker": "GOOGL", "name": "Alphabet", "expected_eps": 1.45},
        {"ticker": "NVDA", "name": "NVIDIA", "expected_eps": 5.28},
        {"ticker": "TSLA", "name": "Tesla", "expected_eps": 0.73},
        {"ticker": "META", "name": "Meta", "expected_eps": 4.82},
        {"ticker": "AMZN", "name": "Amazon", "expected_eps": 0.98}
    ]

    for idx, company in enumerate(companies):
        days = random.randint(1, 20)
        event_date = now + timedelta(days=days)
        countdown = days * 24 + 16  # 4PM ET

        market_events_db.append(MarketEvent(
            id=idx + 1,
            title=f"{company['name']} Q4 Earnings",
            date=event_date.strftime("%Y-%m-%d"),
            event_type="earnings",
            description=f"{company['name']} reports quarterly earnings. Expected EPS: ${company['expected_eps']:.2f}",
            impact_score=8.0 + random.uniform(0, 1.5),
            affected_tickers=company['ticker'],
            phase="ACCUMULATION" if 10 <= days <= 20 else "EUFORIA" if days < 10 else "PRE-RUMOR",
            days_away=days,
            countdown_hours=countdown,
            has_earnings=True,
            expected_eps=company['expected_eps'],
            actual_eps=None,
            volatility_expected=random.uniform(6.5, 9.5),
            recommendation=f"Watch closely. Expected EPS: ${company['expected_eps']:.2f}. Options IV elevated."
        ))

def generate_news_title(ticker: str, sentiment: str) -> str:
    if sentiment == "positive":
        templates = [
            f"{ticker} surges on strong earnings beat",
            f"{ticker} announces breakthrough product innovation",
            f"Analysts upgrade {ticker} citing robust fundamentals",
            f"{ticker} secures major partnership deal"
        ]
    elif sentiment == "negative":
        templates = [
            f"{ticker} faces regulatory pressure",
            f"{ticker} misses revenue expectations",
            f"Concerns grow over {ticker}'s market position",
            f"{ticker} announces restructuring plans"
        ]
    else:
        templates = [
            f"{ticker} trading steady ahead of earnings",
            f"{ticker} maintains guidance for fiscal year",
            f"Mixed analyst views on {ticker} outlook",
            f"{ticker} in consolidation pattern"
        ]
    return random.choice(templates)

def generate_news_content(ticker: str, sentiment: str) -> str:
    if sentiment == "positive":
        return f"{ticker} demonstrated exceptional performance with strong growth metrics exceeding market expectations. Institutional buying accelerating."
    elif sentiment == "negative":
        return f"{ticker} facing headwinds as recent developments raise concerns. Analysts adjusting price targets pending further clarity on strategic direction."
    else:
        return f"{ticker} trading within established ranges. Investors awaiting next catalyst. Volume moderate with no clear directional bias."

@app.on_event("startup")
async def startup_event():
    initialize_enhanced_data()
    print("✓ Aeon Nimbus Intelligence Enhanced API initialized")
    print(f"✓ Loaded {len(economic_releases_db)} economic releases")
    print(f"✓ Loaded {len(live_updates_db)} live updates")
    print(f"✓ Loaded {len(market_events_db)} market events")

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "Aeon Nimbus Intelligence Enhanced API",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/api/economic-calendar")
async def get_economic_calendar():
    """Get economic releases with expected vs actual results"""
    return {
        "releases": economic_releases_db,
        "total": len(economic_releases_db),
        "upcoming": len([r for r in economic_releases_db if not r.is_historical]),
        "historical": len([r for r in economic_releases_db if r.is_historical])
    }

@app.get("/api/economic-calendar/upcoming")
async def get_upcoming_releases():
    """Get only upcoming economic releases"""
    upcoming = [r for r in economic_releases_db if not r.is_historical]
    upcoming.sort(key=lambda x: x.countdown_hours if x.countdown_hours else 999999)
    return {"releases": upcoming, "total": len(upcoming)}

@app.get("/api/economic-calendar/historical")
async def get_historical_releases():
    """Get historical releases with actual results"""
    historical = [r for r in economic_releases_db if r.is_historical]
    historical.sort(key=lambda x: x.date, reverse=True)
    return {"releases": historical, "total": len(historical)}

@app.get("/api/live-updates")
async def get_live_updates():
    """Get live updates from all sources"""
    return {
        "updates": live_updates_db,
        "total": len(live_updates_db),
        "sources": list(set([u.source for u in live_updates_db]))
    }

@app.get("/api/live-updates/recent")
async def get_recent_updates():
    """Get most recent updates (last 24 hours)"""
    now = datetime.now()
    recent = [
        u for u in live_updates_db
        if (now - datetime.fromisoformat(u.timestamp)).total_seconds() < 86400
    ]
    return {"updates": recent, "total": len(recent)}

@app.get("/api/live-updates/breaking")
async def get_breaking_updates():
    """Get breaking news only"""
    breaking = [u for u in live_updates_db if u.urgency == "breaking"]
    return {"updates": breaking, "total": len(breaking)}

@app.get("/api/market-events")
async def get_market_events():
    """Get market events with earnings and volatility data"""
    return {
        "events": market_events_db,
        "total": len(market_events_db)
    }

@app.get("/api/market-events/earnings")
async def get_earnings_events():
    """Get only earnings events"""
    earnings = [e for e in market_events_db if e.has_earnings]
    earnings.sort(key=lambda x: x.countdown_hours)
    return {"events": earnings, "total": len(earnings)}

@app.get("/api/volatility-watch")
async def get_volatility_watch():
    """Get events likely to cause volatility"""
    high_vol_releases = [r for r in economic_releases_db if r.volatility_score >= 8.0]
    high_vol_events = [e for e in market_events_db if e.volatility_expected >= 8.0]

    return {
        "economic_releases": high_vol_releases,
        "market_events": high_vol_events,
        "total_count": len(high_vol_releases) + len(high_vol_events)
    }

@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get all data for main dashboard"""
    now = datetime.now()

    # Upcoming high-impact releases
    upcoming_releases = [
        r for r in economic_releases_db
        if not r.is_historical and r.impact == "high"
    ][:5]

    # Recent updates
    recent_updates = live_updates_db[:10]

    # Upcoming earnings
    upcoming_earnings = [
        e for e in market_events_db
        if e.has_earnings and e.days_away <= 7
    ][:5]

    return {
        "upcoming_releases": upcoming_releases,
        "recent_updates": recent_updates,
        "upcoming_earnings": upcoming_earnings,
        "total_events_tracked": len(economic_releases_db) + len(market_events_db),
        "breaking_news_count": len([u for u in live_updates_db if u.urgency == "breaking"])
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": {
            "economic_releases": len(economic_releases_db),
            "live_updates": len(live_updates_db),
            "market_events": len(market_events_db)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
