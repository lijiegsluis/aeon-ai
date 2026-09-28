"""
Aeon Nimbus Intelligence - Comprehensive Data Source Integration
All major market intelligence sources consolidated
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

class SourceCategory(Enum):
    ECONOMIC = "economic"
    NEWS = "news"
    EARNINGS = "earnings"
    OPTIONS = "options"
    GEOPOLITICAL = "geopolitical"
    CRYPTO = "crypto"
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"
    REGULATORY = "regulatory"
    SECTOR = "sector"

@dataclass
class DataSource:
    name: str
    category: SourceCategory
    url: Optional[str]
    api_endpoint: Optional[str]
    requires_auth: bool
    update_frequency: int  # seconds
    priority: int  # 1-5, 5 being highest
    description: str

# Complete data source registry
DATA_SOURCES: Dict[str, DataSource] = {
    # ECONOMIC DATA & CENTRAL BANKS
    "fedwatch": DataSource(
        name="CME FedWatch Tool",
        category=SourceCategory.ECONOMIC,
        url="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=5,
        description="Federal Reserve interest rate probabilities"
    ),
    "ecb": DataSource(
        name="European Central Bank",
        category=SourceCategory.ECONOMIC,
        url="https://www.ecb.europa.eu",
        api_endpoint="https://sdw-wsrest.ecb.europa.eu/service",
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="ECB monetary policy and economic data"
    ),
    "boe": DataSource(
        name="Bank of England",
        category=SourceCategory.ECONOMIC,
        url="https://www.bankofengland.co.uk",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="UK monetary policy decisions"
    ),
    "boj": DataSource(
        name="Bank of Japan",
        category=SourceCategory.ECONOMIC,
        url="https://www.boj.or.jp/en",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="Japanese monetary policy"
    ),
    "pboc": DataSource(
        name="People's Bank of China",
        category=SourceCategory.ECONOMIC,
        url="http://www.pbc.gov.cn/en",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="Chinese monetary policy"
    ),
    "treasury": DataSource(
        name="U.S. Treasury",
        category=SourceCategory.ECONOMIC,
        url="https://home.treasury.gov",
        api_endpoint="https://api.fiscaldata.treasury.gov/services/api/fiscal_service",
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="Treasury bonds, yields, auctions"
    ),
    "bls": DataSource(
        name="Bureau of Labor Statistics",
        category=SourceCategory.ECONOMIC,
        url="https://www.bls.gov",
        api_endpoint="https://api.bls.gov/publicAPI/v2",
        requires_auth=True,
        update_frequency=86400,
        priority=5,
        description="Employment data, CPI, inflation"
    ),
    "census": DataSource(
        name="U.S. Census Bureau",
        category=SourceCategory.ECONOMIC,
        url="https://www.census.gov",
        api_endpoint="https://api.census.gov/data",
        requires_auth=True,
        update_frequency=86400,
        priority=4,
        description="Retail sales, housing data"
    ),
    "bea": DataSource(
        name="Bureau of Economic Analysis",
        category=SourceCategory.ECONOMIC,
        url="https://www.bea.gov",
        api_endpoint="https://apps.bea.gov/api/data",
        requires_auth=True,
        update_frequency=86400,
        priority=4,
        description="GDP releases, economic indicators"
    ),
    "ism": DataSource(
        name="Institute for Supply Management",
        category=SourceCategory.ECONOMIC,
        url="https://www.ismworld.org",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=86400,
        priority=4,
        description="Manufacturing and Services PMI"
    ),
    "investing_com": DataSource(
        name="Investing.com",
        category=SourceCategory.ECONOMIC,
        url="https://www.investing.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=300,
        priority=5,
        description="Economic calendar with forecasts"
    ),
    "fred": DataSource(
        name="FRED (St. Louis Fed)",
        category=SourceCategory.ECONOMIC,
        url="https://fred.stlouisfed.org",
        api_endpoint="https://api.stlouisfed.org/fred",
        requires_auth=True,
        update_frequency=3600,
        priority=4,
        description="Economic time series data"
    ),

    # REAL-TIME NEWS & ALERTS
    "tradeul": DataSource(
        name="Tradeul Telegram",
        category=SourceCategory.NEWS,
        url="https://t.me/tradeul",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=10,
        priority=5,
        description="Real-time trading signals and news"
    ),
    "bloomberg": DataSource(
        name="Bloomberg",
        category=SourceCategory.NEWS,
        url="https://www.bloomberg.com",
        api_endpoint="https://api.bloomberg.com",
        requires_auth=True,
        update_frequency=60,
        priority=5,
        description="Financial news and market data"
    ),
    "reuters": DataSource(
        name="Reuters",
        category=SourceCategory.NEWS,
        url="https://www.reuters.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=60,
        priority=5,
        description="Global news wire"
    ),
    "benzinga": DataSource(
        name="Benzinga",
        category=SourceCategory.NEWS,
        url="https://www.benzinga.com",
        api_endpoint="https://api.benzinga.com/api/v2",
        requires_auth=True,
        update_frequency=30,
        priority=4,
        description="Real-time news flow and squawks"
    ),
    "seekingalpha": DataSource(
        name="Seeking Alpha",
        category=SourceCategory.NEWS,
        url="https://seekingalpha.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=300,
        priority=4,
        description="Analysis and earnings transcripts"
    ),
    "marketwatch": DataSource(
        name="MarketWatch",
        category=SourceCategory.NEWS,
        url="https://www.marketwatch.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=120,
        priority=4,
        description="Market news and analysis"
    ),
    "ft": DataSource(
        name="Financial Times",
        category=SourceCategory.NEWS,
        url="https://www.ft.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=300,
        priority=4,
        description="Global financial news"
    ),
    "wsj": DataSource(
        name="Wall Street Journal",
        category=SourceCategory.NEWS,
        url="https://www.wsj.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=300,
        priority=4,
        description="Financial news"
    ),
    "cnbc": DataSource(
        name="CNBC",
        category=SourceCategory.NEWS,
        url="https://www.cnbc.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=120,
        priority=4,
        description="Market news and analysis"
    ),
    "economist": DataSource(
        name="The Economist",
        category=SourceCategory.NEWS,
        url="https://www.economist.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=3600,
        priority=3,
        description="Macro and geopolitical analysis"
    ),

    # SOCIAL & SENTIMENT
    "twitter": DataSource(
        name="Twitter/X API",
        category=SourceCategory.SENTIMENT,
        url="https://twitter.com",
        api_endpoint="https://api.twitter.com/2",
        requires_auth=True,
        update_frequency=60,
        priority=4,
        description="Finance influencers and breaking news"
    ),
    "reddit": DataSource(
        name="Reddit",
        category=SourceCategory.SENTIMENT,
        url="https://www.reddit.com",
        api_endpoint="https://www.reddit.com/api/v1",
        requires_auth=True,
        update_frequency=300,
        priority=3,
        description="r/wallstreetbets, r/stocks sentiment"
    ),
    "stocktwits": DataSource(
        name="StockTwits",
        category=SourceCategory.SENTIMENT,
        url="https://stocktwits.com",
        api_endpoint="https://api.stocktwits.com/api/2",
        requires_auth=True,
        update_frequency=300,
        priority=3,
        description="Social sentiment tracking"
    ),
    "lunarcrush": DataSource(
        name="LunarCrush",
        category=SourceCategory.SENTIMENT,
        url="https://lunarcrush.com",
        api_endpoint="https://api.lunarcrush.com/v2",
        requires_auth=True,
        update_frequency=300,
        priority=3,
        description="Social analytics and sentiment"
    ),

    # EARNINGS & CORPORATE
    "sec_edgar": DataSource(
        name="SEC EDGAR",
        category=SourceCategory.EARNINGS,
        url="https://www.sec.gov/edgar",
        api_endpoint="https://data.sec.gov",
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="10-K, 10-Q, 8-K filings"
    ),
    "earnings_whispers": DataSource(
        name="Earnings Whispers",
        category=SourceCategory.EARNINGS,
        url="https://www.earningswhispers.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="EPS expectations and surprises"
    ),
    "zacks": DataSource(
        name="Zacks",
        category=SourceCategory.EARNINGS,
        url="https://www.zacks.com",
        api_endpoint="https://api.zacks.com",
        requires_auth=True,
        update_frequency=3600,
        priority=4,
        description="Earnings calendar and estimates"
    ),
    "yahoo_finance": DataSource(
        name="Yahoo Finance",
        category=SourceCategory.EARNINGS,
        url="https://finance.yahoo.com",
        api_endpoint="https://query1.finance.yahoo.com",
        requires_auth=False,
        update_frequency=300,
        priority=4,
        description="Earnings dates and results"
    ),
    "tipranks": DataSource(
        name="TipRanks",
        category=SourceCategory.EARNINGS,
        url="https://www.tipranks.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=3600,
        priority=3,
        description="Analyst ratings and price targets"
    ),
    "gurufocus": DataSource(
        name="GuruFocus",
        category=SourceCategory.EARNINGS,
        url="https://www.gurufocus.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=86400,
        priority=3,
        description="Institutional holdings and value metrics"
    ),

    # OPTIONS & DERIVATIVES
    "cboe": DataSource(
        name="CBOE",
        category=SourceCategory.OPTIONS,
        url="https://www.cboe.com",
        api_endpoint="https://api.cboe.com",
        requires_auth=True,
        update_frequency=60,
        priority=5,
        description="VIX, put/call ratios"
    ),
    "unusual_whales": DataSource(
        name="Unusual Whales",
        category=SourceCategory.OPTIONS,
        url="https://unusualwhales.com",
        api_endpoint="https://api.unusualwhales.com",
        requires_auth=True,
        update_frequency=60,
        priority=4,
        description="Options flow and dark pools"
    ),
    "cheddar_flow": DataSource(
        name="Cheddar Flow",
        category=SourceCategory.OPTIONS,
        url="https://cheddarflow.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=60,
        priority=4,
        description="Options flow and dark pool prints"
    ),

    # GEOPOLITICAL & MACRO
    "un_news": DataSource(
        name="UN News",
        category=SourceCategory.GEOPOLITICAL,
        url="https://news.un.org",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=3,
        description="Global conflicts and humanitarian"
    ),
    "nato": DataSource(
        name="NATO",
        category=SourceCategory.GEOPOLITICAL,
        url="https://www.nato.int",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=3,
        description="Security developments"
    ),
    "opec": DataSource(
        name="OPEC",
        category=SourceCategory.GEOPOLITICAL,
        url="https://www.opec.org",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=86400,
        priority=4,
        description="Oil production decisions"
    ),
    "imf": DataSource(
        name="IMF",
        category=SourceCategory.GEOPOLITICAL,
        url="https://www.imf.org",
        api_endpoint="https://www.imf.org/external/datamapper/api",
        requires_auth=False,
        update_frequency=86400,
        priority=3,
        description="Global economic outlook"
    ),
    "worldbank": DataSource(
        name="World Bank",
        category=SourceCategory.GEOPOLITICAL,
        url="https://www.worldbank.org",
        api_endpoint="https://api.worldbank.org/v2",
        requires_auth=False,
        update_frequency=86400,
        priority=3,
        description="Development indicators"
    ),
    "stratfor": DataSource(
        name="Stratfor",
        category=SourceCategory.GEOPOLITICAL,
        url="https://worldview.stratfor.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=3600,
        priority=3,
        description="Geopolitical intelligence"
    ),

    # CRYPTO
    "coingecko": DataSource(
        name="CoinGecko",
        category=SourceCategory.CRYPTO,
        url="https://www.coingecko.com",
        api_endpoint="https://api.coingecko.com/api/v3",
        requires_auth=False,
        update_frequency=60,
        priority=4,
        description="Crypto prices and market data"
    ),
    "glassnode": DataSource(
        name="Glassnode",
        category=SourceCategory.CRYPTO,
        url="https://glassnode.com",
        api_endpoint="https://api.glassnode.com",
        requires_auth=True,
        update_frequency=300,
        priority=4,
        description="On-chain metrics"
    ),
    "cryptoquant": DataSource(
        name="CryptoQuant",
        category=SourceCategory.CRYPTO,
        url="https://cryptoquant.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=300,
        priority=4,
        description="Exchange flows and metrics"
    ),
    "theblock": DataSource(
        name="The Block",
        category=SourceCategory.CRYPTO,
        url="https://www.theblock.co",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=300,
        priority=3,
        description="Crypto news and research"
    ),

    # SENTIMENT & ANALYTICS
    "cnn_fear_greed": DataSource(
        name="CNN Fear & Greed Index",
        category=SourceCategory.SENTIMENT,
        url="https://www.cnn.com/markets/fear-and-greed",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=4,
        description="Market sentiment index"
    ),
    "aaii": DataSource(
        name="AAII Sentiment Survey",
        category=SourceCategory.SENTIMENT,
        url="https://www.aaii.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=604800,
        priority=3,
        description="Retail investor sentiment"
    ),
    "cot": DataSource(
        name="Commitment of Traders (COT)",
        category=SourceCategory.SENTIMENT,
        url="https://www.cftc.gov",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=604800,
        priority=3,
        description="CFTC positioning data"
    ),
    "google_trends": DataSource(
        name="Google Trends",
        category=SourceCategory.SENTIMENT,
        url="https://trends.google.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=3,
        description="Search volume for tickers"
    ),

    # TECHNICAL & MARKET STRUCTURE
    "finra": DataSource(
        name="FINRA",
        category=SourceCategory.TECHNICAL,
        url="https://www.finra.org",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=86400,
        priority=3,
        description="Short interest data"
    ),
    "nyse": DataSource(
        name="NYSE",
        category=SourceCategory.TECHNICAL,
        url="https://www.nyse.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=300,
        priority=4,
        description="Market breadth indicators"
    ),
    "nasdaq": DataSource(
        name="NASDAQ",
        category=SourceCategory.TECHNICAL,
        url="https://www.nasdaq.com",
        api_endpoint="https://api.nasdaq.com",
        requires_auth=False,
        update_frequency=300,
        priority=4,
        description="Market data and listings"
    ),
    "tradingview": DataSource(
        name="TradingView",
        category=SourceCategory.TECHNICAL,
        url="https://www.tradingview.com",
        api_endpoint=None,
        requires_auth=True,
        update_frequency=60,
        priority=4,
        description="Technical signals and charting"
    ),
    "quandl": DataSource(
        name="Quandl",
        category=SourceCategory.TECHNICAL,
        url="https://www.quandl.com",
        api_endpoint="https://data.nasdaq.com/api/v3",
        requires_auth=True,
        update_frequency=3600,
        priority=3,
        description="Financial and economic datasets"
    ),

    # REGULATORY & LEGAL
    "doj": DataSource(
        name="DOJ Press Releases",
        category=SourceCategory.REGULATORY,
        url="https://www.justice.gov",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=3,
        description="Corporate investigations"
    ),
    "ftc": DataSource(
        name="FTC",
        category=SourceCategory.REGULATORY,
        url="https://www.ftc.gov",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=3600,
        priority=3,
        description="Antitrust actions"
    ),
    "fda": DataSource(
        name="FDA Calendar",
        category=SourceCategory.REGULATORY,
        url="https://www.fda.gov",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=86400,
        priority=3,
        description="Drug approvals (biotech)"
    ),
    "uspto": DataSource(
        name="USPTO",
        category=SourceCategory.REGULATORY,
        url="https://www.uspto.gov",
        api_endpoint="https://developer.uspto.gov",
        requires_auth=True,
        update_frequency=86400,
        priority=2,
        description="Patent filings"
    ),

    # SECTOR-SPECIFIC
    "eia": DataSource(
        name="EIA",
        category=SourceCategory.SECTOR,
        url="https://www.eia.gov",
        api_endpoint="https://api.eia.gov",
        requires_auth=True,
        update_frequency=3600,
        priority=4,
        description="Energy data and oil inventories"
    ),
    "baker_hughes": DataSource(
        name="Baker Hughes",
        category=SourceCategory.SECTOR,
        url="https://rigcount.bakerhughes.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=604800,
        priority=3,
        description="Rig count data"
    ),
    "kitco": DataSource(
        name="Kitco",
        category=SourceCategory.SECTOR,
        url="https://www.kitco.com",
        api_endpoint=None,
        requires_auth=False,
        update_frequency=300,
        priority=3,
        description="Precious metals prices"
    ),
}


def get_sources_by_category(category: SourceCategory) -> List[DataSource]:
    """Get all data sources for a specific category"""
    return [s for s in DATA_SOURCES.values() if s.category == category]


def get_high_priority_sources() -> List[DataSource]:
    """Get all high priority (4-5) sources"""
    return [s for s in DATA_SOURCES.values() if s.priority >= 4]


def get_sources_requiring_auth() -> List[DataSource]:
    """Get all sources that require authentication"""
    return [s for s in DATA_SOURCES.values() if s.requires_auth]


def get_realtime_sources() -> List[DataSource]:
    """Get sources with update frequency under 5 minutes"""
    return [s for s in DATA_SOURCES.values() if s.update_frequency <= 300]


# Source status tracking
source_health: Dict[str, Dict[str, Any]] = {}

async def check_source_health(source_name: str) -> bool:
    """Check if a data source is healthy and responding"""
    # Implementation would ping the source and check response
    return True


def get_source_stats() -> Dict[str, Any]:
    """Get statistics about all configured sources"""
    return {
        "total_sources": len(DATA_SOURCES),
        "by_category": {
            cat.value: len(get_sources_by_category(cat))
            for cat in SourceCategory
        },
        "high_priority": len(get_high_priority_sources()),
        "requires_auth": len(get_sources_requiring_auth()),
        "realtime": len(get_realtime_sources()),
    }
