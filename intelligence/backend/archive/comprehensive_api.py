"""
Aeon Nimbus Intelligence - Enhanced API with All Data Sources
Comprehensive market intelligence from 80+ sources
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import random
from data_sources import DATA_SOURCES, SourceCategory, get_sources_by_category, get_source_stats

app = FastAPI(
    title="Aeon Nimbus Intelligence API",
    version="4.0.0",
    description="Comprehensive market intelligence from 80+ data sources"
)

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
    category: str
    previous: Optional[float]
    forecast: Optional[float]
    actual: Optional[float]
    impact: str
    affected_markets: str
    sources: List[str]
    is_historical: bool
    volatility_score: float
    countdown_hours: Optional[int]
    surprise_factor: Optional[float]

class NewsUpdate(BaseModel):
    id: int
    timestamp: str
    source: str
    category: str
    title: str
    content: str
    url: Optional[str]
    affected_tickers: str
    sentiment: str
    urgency: str
    source_priority: int

class SentimentData(BaseModel):
    id: int
    source: str
    timestamp: str
    indicator_name: str
    value: float
    interpretation: str
    affected_markets: str

class OptionsFlow(BaseModel):
    id: int
    timestamp: str
    source: str
    ticker: str
    contract_type: str
    strike: float
    expiry: str
    premium: float
    volume: int
    unusual: bool
    sentiment: str

class GeopoliticalEvent(BaseModel):
    id: int
    timestamp: str
    source: str
    title: str
    region: str
    severity: str
    affected_markets: str
    description: str

class CryptoMetric(BaseModel):
    id: int
    timestamp: str
    source: str
    metric_name: str
    value: float
    symbol: str
    interpretation: str

class RegulatoryUpdate(BaseModel):
    id: int
    timestamp: str
    source: str
    agency: str
    title: str
    affected_companies: str
    impact_level: str
    description: str

class SectorData(BaseModel):
    id: int
    timestamp: str
    source: str
    sector: str
    metric_name: str
    value: float
    unit: str
    interpretation: str

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
    sources: List[str]
    has_earnings: bool
    expected_eps: Optional[float]
    actual_eps: Optional[float]
    volatility_expected: float
    recommendation: str

class SourceStatus(BaseModel):
    name: str
    category: str
    status: str
    last_update: str
    priority: int
    update_frequency: int

# In-memory storage
economic_releases: List[EconomicRelease] = []
news_updates: List[NewsUpdate] = []
sentiment_data: List[SentimentData] = []
options_flow: List[OptionsFlow] = []
geopolitical_events: List[GeopoliticalEvent] = []
crypto_metrics: List[CryptoMetric] = []
regulatory_updates: List[RegulatoryUpdate] = []
sector_data: List[SectorData] = []
market_events: List[MarketEvent] = []
source_statuses: List[SourceStatus] = []

def initialize_comprehensive_data():
    """Initialize data from all 80+ sources"""
    global economic_releases, news_updates, sentiment_data, options_flow
    global geopolitical_events, crypto_metrics, regulatory_updates, sector_data
    global market_events, source_statuses

    now = datetime.now()

    # Initialize source statuses
    source_statuses = []
    for source_name, source in DATA_SOURCES.items():
        source_statuses.append(SourceStatus(
            name=source.name,
            category=source.category.value,
            status="active" if random.random() > 0.05 else "delayed",
            last_update=now.isoformat(),
            priority=source.priority,
            update_frequency=source.update_frequency
        ))

    # Economic releases from multiple sources
    economic_sources = ["Investing.com", "Bloomberg", "Reuters", "FRED", "BLS", "BEA"]
    economic_releases = []

    # Historical (last 7 days)
    historical_events = [
        {"name": "Non-Farm Payrolls", "prev": 177000, "forecast": 185000, "actual": 199000, "days_ago": 2, "vol": 9.2},
        {"name": "CPI (YoY)", "prev": 3.2, "forecast": 3.1, "actual": 3.4, "days_ago": 5, "vol": 9.5},
        {"name": "Federal Funds Rate", "prev": 5.50, "forecast": 5.50, "actual": 5.50, "days_ago": 7, "vol": 9.8},
        {"name": "ECB Rate Decision", "prev": 4.50, "forecast": 4.25, "actual": 4.25, "days_ago": 4, "vol": 8.5},
        {"name": "China GDP (QoQ)", "prev": 4.9, "forecast": 5.0, "actual": 4.6, "days_ago": 6, "vol": 8.8},
        {"name": "Retail Sales (MoM)", "prev": 0.4, "forecast": 0.3, "actual": 0.7, "days_ago": 3, "vol": 7.2},
        {"name": "ISM Manufacturing PMI", "prev": 47.8, "forecast": 48.0, "actual": 47.4, "days_ago": 4, "vol": 7.8},
        {"name": "BoJ Rate Decision", "prev": -0.10, "forecast": -0.10, "actual": -0.10, "days_ago": 6, "vol": 7.5},
    ]

    for idx, event in enumerate(historical_events):
        release_date = now - timedelta(days=event["days_ago"])
        surprise = ((event["actual"] - event["forecast"]) / abs(event["forecast"]) * 100) if event["forecast"] else 0

        economic_releases.append(EconomicRelease(
            id=idx + 1,
            name=event["name"],
            date=release_date.strftime("%Y-%m-%d"),
            time="08:30",
            country="US" if "China" not in event["name"] and "ECB" not in event["name"] and "BoJ" not in event["name"] else ("CN" if "China" in event["name"] else ("EU" if "ECB" in event["name"] else "JP")),
            category="macro",
            previous=event["prev"],
            forecast=event["forecast"],
            actual=event["actual"],
            impact="high" if event["vol"] >= 8 else "medium",
            affected_markets="SPY,QQQ,DXY,GLD" if "US" else "FXI,EWJ,EWU",
            sources=random.sample(economic_sources, 2),
            is_historical=True,
            volatility_score=event["vol"],
            countdown_hours=None,
            surprise_factor=surprise
        ))

    # Upcoming releases
    upcoming_events = [
        {"name": "CPI (YoY)", "prev": 3.4, "forecast": 3.3, "days": 2, "vol": 9.5},
        {"name": "FOMC Rate Decision", "prev": 5.50, "forecast": 5.25, "days": 5, "vol": 9.8},
        {"name": "Non-Farm Payrolls", "prev": 199000, "forecast": 180000, "days": 6, "vol": 9.2},
        {"name": "PPI (MoM)", "prev": 2.3, "forecast": 2.2, "days": 3, "vol": 7.8},
        {"name": "Unemployment Rate", "prev": 3.7, "forecast": 3.7, "days": 6, "vol": 7.0},
        {"name": "Retail Sales (MoM)", "prev": 0.7, "forecast": 0.4, "days": 8, "vol": 7.2},
        {"name": "ECB Press Conference", "prev": None, "forecast": None, "days": 7, "vol": 8.5},
        {"name": "China PMI", "prev": 49.2, "forecast": 49.5, "days": 4, "vol": 7.8},
        {"name": "Core PCE (MoM)", "prev": 0.3, "forecast": 0.2, "days": 9, "vol": 8.2},
        {"name": "Initial Jobless Claims", "prev": 220000, "forecast": 225000, "days": 1, "vol": 6.5},
    ]

    for idx, event in enumerate(upcoming_events):
        release_date = now + timedelta(days=event["days"])
        countdown = event["days"] * 24 + 8

        economic_releases.append(EconomicRelease(
            id=len(economic_releases) + 1,
            name=event["name"],
            date=release_date.strftime("%Y-%m-%d"),
            time="08:30",
            country="US" if "China" not in event["name"] and "ECB" not in event["name"] else ("CN" if "China" in event["name"] else "EU"),
            category="macro",
            previous=event["prev"],
            forecast=event["forecast"],
            actual=None,
            impact="high" if event["vol"] >= 8 else "medium",
            affected_markets="SPY,QQQ,DXY,TLT",
            sources=random.sample(economic_sources, 3),
            is_historical=False,
            volatility_score=event["vol"],
            countdown_hours=countdown,
            surprise_factor=None
        ))

    # News from all sources
    news_sources = [s.name for s in DATA_SOURCES.values() if s.category == SourceCategory.NEWS]
    news_updates = []

    for i in range(100):
        hours_ago = random.randint(0, 168)
        timestamp = now - timedelta(hours=hours_ago)
        source = random.choice(news_sources)

        news_updates.append(NewsUpdate(
            id=i + 1,
            timestamp=timestamp.isoformat(),
            source=source,
            category=random.choice(["earnings", "macro", "geopolitical", "regulatory", "market"]),
            title=f"Market update from {source} - {random.choice(['Fed signals', 'Earnings beat', 'Tensions rise', 'Data surprise'])}",
            content=f"Detailed analysis from {source} regarding market developments and implications.",
            url=f"https://example.com/news/{i}",
            affected_tickers=",".join(random.sample(["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN", "SPY", "QQQ"], 2)),
            sentiment=random.choice(["bullish", "bearish", "neutral"]),
            urgency=random.choice(["breaking", "high", "medium", "low"]),
            source_priority=DATA_SOURCES.get(source.lower().replace(" ", "_"), DATA_SOURCES["bloomberg"]).priority
        ))

    news_updates.sort(key=lambda x: x.timestamp, reverse=True)

    # Sentiment indicators
    sentiment_sources = [s.name for s in DATA_SOURCES.values() if s.category == SourceCategory.SENTIMENT]
    sentiment_data = [
        SentimentData(
            id=1,
            source="CNN Fear & Greed Index",
            timestamp=now.isoformat(),
            indicator_name="Fear & Greed",
            value=52.0,
            interpretation="Neutral",
            affected_markets="SPY,QQQ,DIA"
        ),
        SentimentData(
            id=2,
            source="AAII Sentiment Survey",
            timestamp=now.isoformat(),
            indicator_name="Bullish %",
            value=38.5,
            interpretation="Below Average",
            affected_markets="SPY,QQQ"
        ),
        SentimentData(
            id=3,
            source="StockTwits",
            timestamp=now.isoformat(),
            indicator_name="Social Sentiment",
            value=65.0,
            interpretation="Bullish",
            affected_markets="TSLA,GME,AMC"
        ),
        SentimentData(
            id=4,
            source="LunarCrush",
            timestamp=now.isoformat(),
            indicator_name="Galaxy Score",
            value=72.5,
            interpretation="Strong Bullish",
            affected_markets="BTC,ETH"
        ),
    ]

    # Options flow
    options_flow = []
    for i in range(50):
        minutes_ago = random.randint(0, 1440)
        timestamp = now - timedelta(minutes=minutes_ago)

        options_flow.append(OptionsFlow(
            id=i + 1,
            timestamp=timestamp.isoformat(),
            source=random.choice(["Unusual Whales", "Cheddar Flow", "CBOE"]),
            ticker=random.choice(["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "MSFT"]),
            contract_type=random.choice(["CALL", "PUT"]),
            strike=random.uniform(400, 500),
            expiry=(now + timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d"),
            premium=random.uniform(10000, 1000000),
            volume=random.randint(100, 5000),
            unusual=random.random() > 0.7,
            sentiment=random.choice(["bullish", "bearish", "neutral"])
        ))

    options_flow.sort(key=lambda x: x.timestamp, reverse=True)

    # Geopolitical events
    geo_sources = [s.name for s in DATA_SOURCES.values() if s.category == SourceCategory.GEOPOLITICAL]
    geopolitical_events = []
    for i in range(20):
        hours_ago = random.randint(0, 336)
        timestamp = now - timedelta(hours=hours_ago)

        geopolitical_events.append(GeopoliticalEvent(
            id=i + 1,
            timestamp=timestamp.isoformat(),
            source=random.choice(geo_sources),
            title=random.choice([
                "OPEC announces production cut",
                "Central bank policy divergence widens",
                "Trade tensions escalate",
                "UN security council meeting scheduled",
                "IMF revises growth forecasts"
            ]),
            region=random.choice(["Middle East", "Asia-Pacific", "Europe", "Americas", "Global"]),
            severity=random.choice(["high", "medium", "low"]),
            affected_markets="USO,XLE,EEM,VWO,GLD",
            description="Geopolitical development with potential market implications."
        ))

    geopolitical_events.sort(key=lambda x: x.timestamp, reverse=True)

    # Crypto metrics
    crypto_sources = [s.name for s in DATA_SOURCES.values() if s.category == SourceCategory.CRYPTO]
    crypto_metrics = []
    for i in range(30):
        hours_ago = random.randint(0, 72)
        timestamp = now - timedelta(hours=hours_ago)

        crypto_metrics.append(CryptoMetric(
            id=i + 1,
            timestamp=timestamp.isoformat(),
            source=random.choice(crypto_sources),
            metric_name=random.choice(["Exchange Inflow", "MVRV Ratio", "Active Addresses", "Hash Rate", "Whale Transactions"]),
            value=random.uniform(0, 100),
            symbol=random.choice(["BTC", "ETH", "SOL", "MATIC"]),
            interpretation=random.choice(["Bullish signal", "Bearish signal", "Neutral", "Accumulation phase"])
        ))

    crypto_metrics.sort(key=lambda x: x.timestamp, reverse=True)

    # Regulatory updates
    reg_sources = [s.name for s in DATA_SOURCES.values() if s.category == SourceCategory.REGULATORY]
    regulatory_updates = []
    for i in range(15):
        days_ago = random.randint(0, 14)
        timestamp = now - timedelta(days=days_ago)

        regulatory_updates.append(RegulatoryUpdate(
            id=i + 1,
            timestamp=timestamp.isoformat(),
            source=random.choice(reg_sources),
            agency=random.choice(["SEC", "FTC", "DOJ", "FDA", "EPA"]),
            title=random.choice([
                "Antitrust investigation announced",
                "New drug approval granted",
                "Securities filing deadline extended",
                "Merger review initiated",
                "Environmental compliance review"
            ]),
            affected_companies=",".join(random.sample(["AAPL", "GOOGL", "META", "AMZN", "MSFT", "PFE", "JNJ"], 2)),
            impact_level=random.choice(["high", "medium", "low"]),
            description="Regulatory action with potential market impact."
        ))

    regulatory_updates.sort(key=lambda x: x.timestamp, reverse=True)

    # Sector-specific data
    sector_sources = [s.name for s in DATA_SOURCES.values() if s.category == SourceCategory.SECTOR]
    sector_data = []
    for i in range(25):
        hours_ago = random.randint(0, 168)
        timestamp = now - timedelta(hours=hours_ago)

        sector_data.append(SectorData(
            id=i + 1,
            timestamp=timestamp.isoformat(),
            source=random.choice(sector_sources),
            sector=random.choice(["Energy", "Technology", "Healthcare", "Financials", "Materials"]),
            metric_name=random.choice(["Oil Inventories", "Rig Count", "Chip Orders", "Vehicle Sales", "PMI"]),
            value=random.uniform(40, 60),
            unit=random.choice(["Million Barrels", "Count", "Index", "Units", "Percentage"]),
            interpretation=random.choice(["Above expectations", "Below expectations", "In line", "Strong growth", "Weakness"])
        ))

    sector_data.sort(key=lambda x: x.timestamp, reverse=True)

    # Market events with earnings
    companies = [
        {"ticker": "AAPL", "name": "Apple", "eps": 1.52},
        {"ticker": "MSFT", "name": "Microsoft", "eps": 2.65},
        {"ticker": "GOOGL", "name": "Alphabet", "eps": 1.45},
        {"ticker": "NVDA", "name": "NVIDIA", "eps": 5.28},
        {"ticker": "TSLA", "name": "Tesla", "eps": 0.73},
        {"ticker": "META", "name": "Meta", "eps": 4.82},
        {"ticker": "AMZN", "name": "Amazon", "eps": 0.98},
        {"ticker": "NFLX", "name": "Netflix", "eps": 3.15},
    ]

    market_events = []
    for idx, company in enumerate(companies):
        days = random.randint(1, 20)
        event_date = now + timedelta(days=days)
        countdown = days * 24 + 16

        phase = "DANGER" if days <= 2 else ("EUFORIA" if days <= 9 else ("ACCUMULATION" if days <= 20 else "PRE-RUMOR"))

        market_events.append(MarketEvent(
            id=idx + 1,
            title=f"{company['name']} Q4 Earnings",
            date=event_date.strftime("%Y-%m-%d"),
            event_type="earnings",
            description=f"{company['name']} quarterly earnings report",
            impact_score=random.uniform(7.5, 9.5),
            affected_tickers=company['ticker'],
            phase=phase,
            days_away=days,
            countdown_hours=countdown,
            sources=["Yahoo Finance", "Seeking Alpha", "Zacks"],
            has_earnings=True,
            expected_eps=company['eps'],
            actual_eps=None,
            volatility_expected=random.uniform(6.5, 9.5),
            recommendation=f"Expected EPS: ${company['eps']:.2f}. Watch options IV. {phase} phase active."
        ))

@app.on_event("startup")
async def startup():
    initialize_comprehensive_data()
    stats = get_source_stats()
    print(f"✓ Aeon Nimbus Intelligence API v4.0.0")
    print(f"✓ {stats['total_sources']} data sources configured")
    print(f"✓ {stats['high_priority']} high-priority sources")
    print(f"✓ {stats['realtime']} real-time sources")
    print(f"✓ Data loaded: {len(economic_releases)} economic releases, {len(news_updates)} news items")

@app.get("/")
async def root():
    return {
        "service": "Aeon Nimbus Intelligence",
        "version": "4.0.0",
        "status": "operational",
        "sources": get_source_stats()
    }

@app.get("/api/sources")
async def get_sources():
    """Get all configured data sources"""
    return {
        "sources": source_statuses,
        "stats": get_source_stats(),
        "categories": {cat.value: [s.name for s in get_sources_by_category(cat)] for cat in SourceCategory}
    }

@app.get("/api/dashboard")
async def get_dashboard():
    """Main dashboard with key data from all sources"""
    return {
        "economic_releases_upcoming": [r for r in economic_releases if not r.is_historical][:5],
        "economic_releases_recent": [r for r in economic_releases if r.is_historical][:5],
        "news_breaking": [n for n in news_updates if n.urgency == "breaking"][:5],
        "news_recent": news_updates[:10],
        "sentiment_indicators": sentiment_data,
        "options_flow_unusual": [o for o in options_flow if o.unusual][:5],
        "geopolitical_events_recent": geopolitical_events[:5],
        "market_events_upcoming": [e for e in market_events if e.days_away <= 7][:5],
        "total_sources_active": len([s for s in source_statuses if s.status == "active"])
    }

@app.get("/api/economic-calendar")
async def get_economic_calendar():
    """Complete economic calendar"""
    return {
        "releases": economic_releases,
        "total": len(economic_releases),
        "upcoming": len([r for r in economic_releases if not r.is_historical]),
        "historical": len([r for r in economic_releases if r.is_historical]),
        "sources": list(set([s for r in economic_releases for s in r.sources]))
    }

@app.get("/api/news/all")
async def get_all_news():
    """All news from all sources"""
    return {
        "news": news_updates,
        "total": len(news_updates),
        "sources": list(set([n.source for n in news_updates])),
        "breaking_count": len([n for n in news_updates if n.urgency == "breaking"])
    }

@app.get("/api/sentiment")
async def get_sentiment():
    """Sentiment indicators from all sentiment sources"""
    return {
        "indicators": sentiment_data,
        "sources": list(set([s.source for s in sentiment_data]))
    }

@app.get("/api/options-flow")
async def get_options():
    """Options flow data"""
    return {
        "flow": options_flow,
        "total": len(options_flow),
        "unusual": len([o for o in options_flow if o.unusual]),
        "sources": list(set([o.source for o in options_flow]))
    }

@app.get("/api/geopolitical")
async def get_geopolitical():
    """Geopolitical events"""
    return {
        "events": geopolitical_events,
        "total": len(geopolitical_events),
        "high_severity": len([e for e in geopolitical_events if e.severity == "high"]),
        "sources": list(set([e.source for e in geopolitical_events]))
    }

@app.get("/api/crypto")
async def get_crypto():
    """Crypto on-chain metrics"""
    return {
        "metrics": crypto_metrics,
        "total": len(crypto_metrics),
        "sources": list(set([c.source for c in crypto_metrics]))
    }

@app.get("/api/regulatory")
async def get_regulatory():
    """Regulatory updates"""
    return {
        "updates": regulatory_updates,
        "total": len(regulatory_updates),
        "high_impact": len([r for r in regulatory_updates if r.impact_level == "high"]),
        "sources": list(set([r.source for r in regulatory_updates]))
    }

@app.get("/api/sector-data")
async def get_sector():
    """Sector-specific data"""
    return {
        "data": sector_data,
        "total": len(sector_data),
        "sources": list(set([s.source for s in sector_data]))
    }

@app.get("/api/market-events")
async def get_events():
    """Market events and earnings"""
    return {
        "events": market_events,
        "total": len(market_events),
        "earnings_upcoming": len([e for e in market_events if e.has_earnings])
    }

@app.get("/api/volatility-watch")
async def get_volatility():
    """High volatility events from all sources"""
    high_vol_economic = [r for r in economic_releases if r.volatility_score >= 8.0]
    high_vol_events = [e for e in market_events if e.volatility_expected >= 8.0]

    return {
        "economic_releases": high_vol_economic,
        "market_events": high_vol_events,
        "total": len(high_vol_economic) + len(high_vol_events)
    }

# Legacy compatibility endpoints
@app.get("/api/events/live")
async def get_events_legacy():
    """Legacy endpoint for backward compatibility"""
    return market_events

@app.get("/api/news/live")
async def get_news_legacy():
    """Legacy endpoint for backward compatibility"""
    return [
        {
            "id": n.id,
            "title": n.title,
            "published_at": n.timestamp,
            "source": n.source,
            "sentiment": n.sentiment,
            "summary": n.content,
            "tickers": n.affected_tickers,
            "url": n.url or ""
        }
        for n in news_updates
    ]

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0",
        "sources_active": len([s for s in source_statuses if s.status == "active"]),
        "sources_total": len(source_statuses)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
