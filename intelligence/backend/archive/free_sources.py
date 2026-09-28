"""
Aeon Nimbus Intelligence - Free Data Sources Strategy
Complete implementation using free tiers, public APIs, RSS feeds, and web scraping
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FreeDataSource:
    name: str
    method: str  # api, rss, scrape, public_data
    endpoint: str
    frequency: int  # seconds
    description: str
    implementation_notes: str

# FREE DATA SOURCES - NO PAYMENT REQUIRED
FREE_SOURCES: Dict[str, FreeDataSource] = {

    # ECONOMIC DATA - FREE GOVERNMENT SOURCES
    "fred": FreeDataSource(
        name="FRED API",
        method="api",
        endpoint="https://api.stlouisfed.org/fred",
        frequency=3600,
        description="Free economic data from St. Louis Fed",
        implementation_notes="Free API key from https://fred.stlouisfed.org/docs/api/api_key.html"
    ),
    "bls_public": FreeDataSource(
        name="BLS Public Data",
        method="api",
        endpoint="https://api.bls.gov/publicAPI/v2",
        frequency=86400,
        description="Employment, CPI data - 25 requests/day free tier",
        implementation_notes="Register for free at https://www.bls.gov/developers/home.htm"
    ),
    "census": FreeDataSource(
        name="Census Bureau",
        method="api",
        endpoint="https://api.census.gov/data",
        frequency=86400,
        description="Economic indicators, retail sales",
        implementation_notes="Free API key from https://api.census.gov/data/key_signup.html"
    ),
    "ecb_sdw": FreeDataSource(
        name="ECB Statistical Data Warehouse",
        method="api",
        endpoint="https://sdw-wsrest.ecb.europa.eu/service",
        frequency=3600,
        description="ECB economic data - completely free",
        implementation_notes="No API key required"
    ),
    "worldbank": FreeDataSource(
        name="World Bank API",
        method="api",
        endpoint="https://api.worldbank.org/v2",
        frequency=86400,
        description="Global economic indicators",
        implementation_notes="No registration required"
    ),
    "imf_data": FreeDataSource(
        name="IMF Data API",
        method="api",
        endpoint="http://dataservices.imf.org/REST/SDMX_JSON.svc",
        frequency=86400,
        description="Global economic data",
        implementation_notes="Free, no API key"
    ),

    # NEWS - FREE RSS FEEDS & SCRAPING
    "reuters_rss": FreeDataSource(
        name="Reuters RSS",
        method="rss",
        endpoint="https://www.reutersagency.com/feed/",
        frequency=300,
        description="Free Reuters news feed",
        implementation_notes="Parse RSS feed with feedparser"
    ),
    "bloomberg_rss": FreeDataSource(
        name="Bloomberg Markets RSS",
        method="rss",
        endpoint="https://www.bloomberg.com/feed/podcast/etf-report.xml",
        frequency=300,
        description="Bloomberg podcasts and some market data",
        implementation_notes="Multiple Bloomberg RSS feeds available"
    ),
    "cnbc_rss": FreeDataSource(
        name="CNBC RSS",
        method="rss",
        endpoint="https://www.cnbc.com/id/100003114/device/rss/rss.html",
        frequency=300,
        description="CNBC top news",
        implementation_notes="Multiple CNBC RSS feeds"
    ),
    "marketwatch_rss": FreeDataSource(
        name="MarketWatch RSS",
        method="rss",
        endpoint="http://feeds.marketwatch.com/marketwatch/topstories/",
        frequency=300,
        description="MarketWatch news feed",
        implementation_notes="Free RSS"
    ),
    "seeking_alpha_free": FreeDataSource(
        name="Seeking Alpha Market News",
        method="scrape",
        endpoint="https://seekingalpha.com/market-news",
        frequency=600,
        description="Scrape headlines from public pages",
        implementation_notes="Use BeautifulSoup, respect robots.txt"
    ),
    "yahoo_finance_rss": FreeDataSource(
        name="Yahoo Finance RSS",
        method="rss",
        endpoint="https://finance.yahoo.com/news/rssindex",
        frequency=300,
        description="Yahoo Finance news",
        implementation_notes="Free RSS feeds"
    ),

    # EARNINGS & CORPORATE - FREE SOURCES
    "sec_edgar": FreeDataSource(
        name="SEC EDGAR",
        method="api",
        endpoint="https://data.sec.gov/submissions/",
        frequency=3600,
        description="All SEC filings completely free",
        implementation_notes="No API key, add User-Agent header"
    ),
    "yahoo_finance_api": FreeDataSource(
        name="Yahoo Finance API",
        method="api",
        endpoint="https://query1.finance.yahoo.com/v8/finance/chart/",
        frequency=300,
        description="Free stock data, earnings dates",
        implementation_notes="No API key required, public endpoint"
    ),
    "finnhub_free": FreeDataSource(
        name="Finnhub Free Tier",
        method="api",
        endpoint="https://finnhub.io/api/v1",
        frequency=600,
        description="60 API calls/minute free",
        implementation_notes="Free API key from https://finnhub.io/"
    ),
    "alphavantage_free": FreeDataSource(
        name="Alpha Vantage Free",
        method="api",
        endpoint="https://www.alphavantage.co/query",
        frequency=3600,
        description="5 API calls/minute, 500/day free",
        implementation_notes="Free key from https://www.alphavantage.co/support/#api-key"
    ),

    # CRYPTO - FREE APIS
    "coingecko_free": FreeDataSource(
        name="CoinGecko Free API",
        method="api",
        endpoint="https://api.coingecko.com/api/v3",
        frequency=60,
        description="Completely free crypto data",
        implementation_notes="10-50 calls/minute free tier"
    ),
    "coinpaprika_free": FreeDataSource(
        name="CoinPaprika Free",
        method="api",
        endpoint="https://api.coinpaprika.com/v1",
        frequency=60,
        description="Free crypto market data",
        implementation_notes="No API key required"
    ),
    "blockchain_info": FreeDataSource(
        name="Blockchain.info API",
        method="api",
        endpoint="https://blockchain.info",
        frequency=300,
        description="Free Bitcoin data",
        implementation_notes="No registration required"
    ),

    # SENTIMENT - FREE SOURCES
    "fear_greed_scrape": FreeDataSource(
        name="CNN Fear & Greed",
        method="scrape",
        endpoint="https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        frequency=3600,
        description="Free JSON endpoint for Fear & Greed",
        implementation_notes="Public JSON endpoint"
    ),
    "reddit_free": FreeDataSource(
        name="Reddit JSON",
        method="api",
        endpoint="https://www.reddit.com/r/wallstreetbets.json",
        frequency=600,
        description="Reddit public JSON feeds",
        implementation_notes="No API key needed for public data"
    ),
    "twitter_nitter": FreeDataSource(
        name="Nitter (Twitter Mirror)",
        method="scrape",
        endpoint="https://nitter.net",
        frequency=300,
        description="Scrape Twitter via Nitter mirrors",
        implementation_notes="Public Twitter data via Nitter instances"
    ),
    "stocktwits_free": FreeDataSource(
        name="StockTwits Public",
        method="scrape",
        endpoint="https://stocktwits.com/symbol/",
        frequency=300,
        description="Public StockTwits sentiment",
        implementation_notes="Scrape public pages"
    ),

    # OPTIONS & TECHNICAL
    "cboe_free": FreeDataSource(
        name="CBOE Public Data",
        method="scrape",
        endpoint="https://www.cboe.com/us/options/market_statistics/",
        frequency=300,
        description="Free VIX and put/call ratio data",
        implementation_notes="Scrape public CBOE pages"
    ),
    "finviz_screener": FreeDataSource(
        name="Finviz Screener",
        method="scrape",
        endpoint="https://finviz.com/screener.ashx",
        frequency=600,
        description="Free stock screener data",
        implementation_notes="Scrape with rate limiting"
    ),
    "nasdaq_public": FreeDataSource(
        name="NASDAQ Public Data",
        method="scrape",
        endpoint="https://www.nasdaq.com/market-activity",
        frequency=300,
        description="Free market data from NASDAQ",
        implementation_notes="Public web data"
    ),

    # GEOPOLITICAL - FREE NEWS FEEDS
    "un_news_rss": FreeDataSource(
        name="UN News RSS",
        method="rss",
        endpoint="https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        frequency=3600,
        description="UN news feed",
        implementation_notes="Free RSS"
    ),
    "nato_news": FreeDataSource(
        name="NATO News",
        method="rss",
        endpoint="https://www.nato.int/cps/en/natohq/news.rss",
        frequency=3600,
        description="NATO announcements",
        implementation_notes="Free RSS"
    ),
    "opec_bulletin": FreeDataSource(
        name="OPEC Bulletin",
        method="scrape",
        endpoint="https://www.opec.org/opec_web/en/press_room/",
        frequency=86400,
        description="OPEC press releases",
        implementation_notes="Scrape public pages"
    ),

    # SECTOR SPECIFIC
    "eia_free": FreeDataSource(
        name="EIA Open Data",
        method="api",
        endpoint="https://api.eia.gov/v2",
        frequency=3600,
        description="Free energy data API",
        implementation_notes="Free registration at https://www.eia.gov/opendata/register.php"
    ),
    "baker_hughes": FreeDataSource(
        name="Baker Hughes Rig Count",
        method="scrape",
        endpoint="https://rigcount.bakerhughes.com/",
        frequency=604800,
        description="Weekly rig count data",
        implementation_notes="Public web data"
    ),
    "usda_free": FreeDataSource(
        name="USDA NASS API",
        method="api",
        endpoint="https://quickstats.nass.usda.gov/api",
        frequency=86400,
        description="Agricultural data",
        implementation_notes="Free API key"
    ),

    # REGULATORY
    "sec_press": FreeDataSource(
        name="SEC Press Releases",
        method="rss",
        endpoint="https://www.sec.gov/news/pressreleases.rss",
        frequency=3600,
        description="SEC announcements",
        implementation_notes="Free RSS"
    ),
    "fda_rss": FreeDataSource(
        name="FDA Press Releases",
        method="rss",
        endpoint="https://www.fda.gov/about-fda/contact-fda/stay-connected/rss-feeds",
        frequency=86400,
        description="FDA approvals and news",
        implementation_notes="Multiple RSS feeds"
    ),
    "ftc_news": FreeDataSource(
        name="FTC Press Releases",
        method="rss",
        endpoint="https://www.ftc.gov/feeds/press-release.xml",
        frequency=86400,
        description="FTC antitrust actions",
        implementation_notes="Free RSS"
    ),

    # ECONOMIC CALENDARS - FREE
    "investing_com_calendar": FreeDataSource(
        name="Investing.com Calendar",
        method="scrape",
        endpoint="https://www.investing.com/economic-calendar/",
        frequency=3600,
        description="Free economic calendar",
        implementation_notes="Scrape with Selenium/Playwright"
    ),
    "forexfactory_calendar": FreeDataSource(
        name="Forex Factory Calendar",
        method="scrape",
        endpoint="https://www.forexfactory.com/calendar",
        frequency=3600,
        description="Free forex economic calendar",
        implementation_notes="Simple HTML scraping"
    ),
    "tradingeconomics_free": FreeDataSource(
        name="Trading Economics Public",
        method="scrape",
        endpoint="https://tradingeconomics.com/calendar",
        frequency=3600,
        description="Economic calendar - public data",
        implementation_notes="Scrape public pages"
    ),
}

# IMPLEMENTATION LIBRARIES NEEDED
REQUIRED_PACKAGES = [
    "feedparser",  # RSS feed parsing
    "beautifulsoup4",  # Web scraping
    "selenium",  # Dynamic content scraping
    "playwright",  # Modern web scraping
    "requests",  # HTTP requests
    "aiohttp",  # Async HTTP
    "pandas",  # Data processing
    "python-dotenv",  # Environment variables
]

# SCRAPING BEST PRACTICES
SCRAPING_GUIDELINES = """
1. Always respect robots.txt
2. Add delays between requests (1-5 seconds)
3. Use proper User-Agent headers
4. Cache responses to minimize requests
5. Handle rate limits gracefully
6. Don't scrape during peak hours
7. Use official APIs when available
8. Consider using proxies for heavy scraping
9. Implement exponential backoff on errors
10. Store raw data for later processing
"""

# API KEY REGISTRATION LINKS
FREE_API_KEYS = {
    "FRED": "https://fred.stlouisfed.org/docs/api/api_key.html",
    "BLS": "https://www.bls.gov/developers/home.htm",
    "Census": "https://api.census.gov/data/key_signup.html",
    "EIA": "https://www.eia.gov/opendata/register.php",
    "Finnhub": "https://finnhub.io/register",
    "Alpha Vantage": "https://www.alphavantage.co/support/#api-key",
}

def get_free_sources_summary():
    """Get summary of all free data sources"""
    by_method = {}
    for source in FREE_SOURCES.values():
        if source.method not in by_method:
            by_method[source.method] = []
        by_method[source.method].append(source.name)

    return {
        "total_free_sources": len(FREE_SOURCES),
        "by_method": {k: len(v) for k, v in by_method.items()},
        "sources_by_method": by_method,
        "required_packages": REQUIRED_PACKAGES,
        "api_keys_needed": list(FREE_API_KEYS.keys())
    }
