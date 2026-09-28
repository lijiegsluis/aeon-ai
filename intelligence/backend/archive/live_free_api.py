"""
Aeon Nimbus Intelligence - Live Free Data API
Integrates real free data sources into the backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

# Import free collectors
from free_collectors import FreeDataAggregator
from free_sources import FREE_SOURCES, get_free_sources_summary

# Global aggregator instance
aggregator: Optional[FreeDataAggregator] = None
cached_data: Dict[str, Any] = {}
last_update: Dict[str, datetime] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global aggregator
    aggregator = FreeDataAggregator()
    print("✓ Free data collectors initialized")

    # Start background data collection
    asyncio.create_task(background_data_collection())

    yield

    # Cleanup
    if aggregator:
        await aggregator.close_all()
    print("✓ Collectors closed")

app = FastAPI(
    title="Aeon Nimbus Intelligence - Free Data API",
    version="5.0.0",
    description="Market intelligence from 40+ free data sources",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background data collection task
async def background_data_collection():
    """Collect data from all free sources every 5 minutes"""
    global cached_data, last_update

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Collecting data from free sources...")

            data = await aggregator.collect_all()
            cached_data = data
            last_update['timestamp'] = datetime.now()

            active_sources = sum(1 for v in data.values() if v is not None)
            print(f"✓ Collected from {active_sources}/{len(data)} sources")

        except Exception as e:
            print(f"✗ Collection error: {e}")

        # Wait 5 minutes
        await asyncio.sleep(300)

# Data Models
class EconomicRelease(BaseModel):
    id: int
    name: str
    date: str
    time: str
    country: str
    category: str
    previous: Optional[str]
    forecast: Optional[str]
    actual: Optional[str]
    impact: str
    source: str

class NewsItem(BaseModel):
    id: int
    title: str
    published_at: str
    source: str
    sentiment: str
    summary: str
    url: str

class CryptoData(BaseModel):
    symbol: str
    price: float
    change_24h: float
    market_cap: float
    source: str

class SentimentIndicator(BaseModel):
    name: str
    value: float
    interpretation: str
    source: str
    timestamp: str

@app.get("/")
async def root():
    return {
        "service": "Aeon Nimbus Intelligence",
        "version": "5.0.0",
        "status": "operational",
        "data_sources": "40+ free sources",
        "last_update": last_update.get('timestamp', datetime.now()).isoformat(),
        "sources_active": sum(1 for v in cached_data.values() if v is not None)
    }

@app.get("/api/sources")
async def get_sources():
    """Get all configured free data sources"""
    summary = get_free_sources_summary()

    return {
        "sources": [
            {
                "name": source.name,
                "method": source.method,
                "frequency": source.frequency,
                "description": source.description,
                "status": "active" if cached_data.get(source.name.lower().replace(" ", "_")) else "pending"
            }
            for source in FREE_SOURCES.values()
        ],
        "summary": summary,
        "last_update": last_update.get('timestamp', datetime.now()).isoformat()
    }

@app.get("/api/dashboard")
async def get_dashboard():
    """Main dashboard with live free data"""

    # Process news feeds
    news_data = cached_data.get('news_feeds', [])
    processed_news = []
    for idx, article in enumerate(news_data[:50]):
        processed_news.append({
            "id": idx + 1,
            "title": article.get('title', ''),
            "published_at": article.get('published', datetime.now().isoformat()),
            "source": article.get('source', 'Unknown'),
            "sentiment": "neutral",
            "summary": article.get('summary', '')[:200],
            "url": article.get('link', ''),
            "tickers": ""
        })

    # Process economic calendar
    calendar_data = cached_data.get('forexfactory_calendar', [])
    economic_releases = []
    for idx, event in enumerate(calendar_data[:20]):
        economic_releases.append({
            "id": idx + 1,
            "name": event.get('event', ''),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": event.get('time', 'TBD'),
            "country": event.get('currency', 'US'),
            "category": "economic",
            "previous": event.get('previous', ''),
            "forecast": event.get('forecast', ''),
            "actual": event.get('actual', ''),
            "impact": "high" if event.get('event', '').upper() in ['CPI', 'NFP', 'GDP', 'FOMC'] else "medium",
            "source": "Forex Factory"
        })

    # Process crypto data
    crypto_prices = cached_data.get('crypto_prices', {})
    crypto_data = []
    for idx, (symbol, data) in enumerate(crypto_prices.items() if crypto_prices else []):
        crypto_data.append({
            "symbol": symbol.upper(),
            "price": data.get('usd', 0),
            "change_24h": data.get('usd_24h_change', 0),
            "market_cap": data.get('usd_market_cap', 0),
            "source": "CoinGecko"
        })

    # Process sentiment
    fear_greed = cached_data.get('fear_greed', {})
    reddit_data = cached_data.get('reddit_sentiment', [])

    sentiment_indicators = []

    if fear_greed:
        sentiment_indicators.append({
            "name": "Fear & Greed Index",
            "value": fear_greed.get('value', 50),
            "interpretation": fear_greed.get('rating', 'Neutral'),
            "source": "CNN",
            "timestamp": fear_greed.get('timestamp', datetime.now().isoformat())
        })

    if reddit_data:
        avg_sentiment = sum(p.get('upvote_ratio', 0.5) for p in reddit_data) / len(reddit_data) * 100
        sentiment_indicators.append({
            "name": "Reddit Sentiment",
            "value": avg_sentiment,
            "interpretation": "Bullish" if avg_sentiment > 60 else "Bearish" if avg_sentiment < 40 else "Neutral",
            "source": "r/wallstreetbets",
            "timestamp": datetime.now().isoformat()
        })

    # VIX data
    vix_data = cached_data.get('vix', {})
    if vix_data:
        sentiment_indicators.append({
            "name": "VIX",
            "value": vix_data.get('vix', 20),
            "interpretation": "High volatility" if vix_data.get('vix', 20) > 25 else "Low volatility",
            "source": "CBOE",
            "timestamp": vix_data.get('timestamp', datetime.now().isoformat())
        })

    return {
        "news": processed_news,
        "economic_releases": economic_releases,
        "crypto": crypto_data,
        "sentiment": sentiment_indicators,
        "last_update": last_update.get('timestamp', datetime.now()).isoformat(),
        "sources_active": sum(1 for v in cached_data.values() if v is not None),
        "total_sources": len(FREE_SOURCES)
    }

@app.get("/api/news/all")
async def get_all_news():
    """All news from free RSS feeds"""
    news_data = cached_data.get('news_feeds', [])

    processed_news = []
    for idx, article in enumerate(news_data):
        processed_news.append({
            "id": idx + 1,
            "title": article.get('title', ''),
            "published_at": article.get('published', datetime.now().isoformat()),
            "source": article.get('source', 'Unknown'),
            "sentiment": "neutral",
            "summary": article.get('summary', ''),
            "url": article.get('link', ''),
            "tickers": "",
            "urgency": "medium"
        })

    return {
        "news": processed_news,
        "total": len(processed_news),
        "sources": list(set(n.get('source', '') for n in news_data)),
        "last_update": last_update.get('timestamp', datetime.now()).isoformat()
    }

@app.get("/api/economic-calendar")
async def get_economic_calendar():
    """Economic calendar from free sources"""
    calendar_data = cached_data.get('forexfactory_calendar', [])

    releases = []
    for idx, event in enumerate(calendar_data):
        releases.append({
            "id": idx + 1,
            "name": event.get('event', ''),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": event.get('time', 'TBD'),
            "country": event.get('currency', 'US'),
            "category": "economic",
            "previous": event.get('previous', ''),
            "forecast": event.get('forecast', ''),
            "actual": event.get('actual', ''),
            "impact": "high",
            "source": "Forex Factory",
            "affected_markets": "SPY,QQQ,DXY"
        })

    return {
        "releases": releases,
        "total": len(releases),
        "sources": ["Forex Factory", "Trading Economics"],
        "last_update": last_update.get('timestamp', datetime.now()).isoformat()
    }

@app.get("/api/crypto")
async def get_crypto():
    """Crypto data from free APIs"""
    crypto_prices = cached_data.get('crypto_prices', {})
    crypto_trending = cached_data.get('crypto_trending', {})

    metrics = []
    for idx, (symbol, data) in enumerate(crypto_prices.items() if crypto_prices else []):
        metrics.append({
            "id": idx + 1,
            "symbol": symbol.upper(),
            "price": data.get('usd', 0),
            "change_24h": data.get('usd_24h_change', 0),
            "market_cap": data.get('usd_market_cap', 0),
            "volume_24h": 0,
            "source": "CoinGecko",
            "timestamp": datetime.now().isoformat()
        })

    return {
        "metrics": metrics,
        "trending": crypto_trending,
        "total": len(metrics),
        "sources": ["CoinGecko", "CoinPaprika"],
        "last_update": last_update.get('timestamp', datetime.now()).isoformat()
    }

@app.get("/api/sentiment")
async def get_sentiment():
    """Sentiment indicators from free sources"""
    fear_greed = cached_data.get('fear_greed', {})
    reddit_data = cached_data.get('reddit_sentiment', [])
    vix_data = cached_data.get('vix', {})

    indicators = []

    if fear_greed:
        indicators.append({
            "id": 1,
            "source": "CNN Fear & Greed Index",
            "timestamp": fear_greed.get('timestamp', datetime.now().isoformat()),
            "indicator_name": "Fear & Greed",
            "value": fear_greed.get('value', 50),
            "interpretation": fear_greed.get('rating', 'Neutral'),
            "affected_markets": "SPY,QQQ,DIA"
        })

    if reddit_data:
        avg_sentiment = sum(p.get('upvote_ratio', 0.5) for p in reddit_data) / len(reddit_data) * 100
        indicators.append({
            "id": 2,
            "source": "Reddit",
            "timestamp": datetime.now().isoformat(),
            "indicator_name": "Social Sentiment",
            "value": avg_sentiment,
            "interpretation": "Bullish" if avg_sentiment > 60 else "Bearish" if avg_sentiment < 40 else "Neutral",
            "affected_markets": "Meme stocks"
        })

    if vix_data:
        indicators.append({
            "id": 3,
            "source": "CBOE",
            "timestamp": vix_data.get('timestamp', datetime.now().isoformat()),
            "indicator_name": "VIX",
            "value": vix_data.get('vix', 20),
            "interpretation": "High volatility" if vix_data.get('vix', 20) > 25 else "Low volatility",
            "affected_markets": "SPY,QQQ,VIX"
        })

    return {
        "indicators": indicators,
        "total": len(indicators),
        "sources": list(set(i['source'] for i in indicators)),
        "last_update": last_update.get('timestamp', datetime.now()).isoformat()
    }

# Legacy compatibility endpoints
@app.get("/api/events/live")
async def get_events_legacy():
    """Legacy endpoint - market events"""
    now = datetime.now()

    # Generate some mock events for compatibility
    events = []
    companies = [
        {"ticker": "AAPL", "name": "Apple"},
        {"ticker": "MSFT", "name": "Microsoft"},
        {"ticker": "GOOGL", "name": "Alphabet"},
        {"ticker": "NVDA", "name": "NVIDIA"},
    ]

    for idx, company in enumerate(companies):
        days = (idx + 1) * 3
        event_date = now + timedelta(days=days)
        phase = "DANGER" if days <= 2 else ("EUFORIA" if days <= 9 else "ACCUMULATION")

        events.append({
            "id": idx + 1,
            "title": f"{company['name']} Earnings",
            "date": event_date.strftime("%Y-%m-%d"),
            "event_type": "earnings",
            "description": f"{company['name']} quarterly earnings",
            "impact_score": 8.5,
            "affected_tickers": company['ticker'],
            "phase": phase,
            "days_away": days,
            "recommendation": f"Watch {company['ticker']} - {phase} phase"
        })

    return events

@app.get("/api/news/live")
async def get_news_legacy():
    """Legacy endpoint - returns news in old format"""
    news_data = cached_data.get('news_feeds', [])

    return [
        {
            "id": idx + 1,
            "title": article.get('title', ''),
            "published_at": article.get('published', datetime.now().isoformat()),
            "source": article.get('source', 'Unknown'),
            "sentiment": "neutral",
            "summary": article.get('summary', ''),
            "tickers": "",
            "url": article.get('link', '')
        }
        for idx, article in enumerate(news_data[:100])
    ]

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "5.0.0",
        "sources_active": sum(1 for v in cached_data.values() if v is not None),
        "sources_total": len(FREE_SOURCES),
        "last_update": last_update.get('timestamp', datetime.now()).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
