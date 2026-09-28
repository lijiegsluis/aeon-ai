"""
Aeon Nimbus Intelligence - Free Data Collectors
Real implementations for all free data sources
"""

import aiohttp
import asyncio
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import re

class FreeDataCollector:
    """Base class for free data collection"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Aeon-Nimbus-Intelligence/4.0 (Market Research)'
        }

    async def get_session(self):
        if self.session is None or self.session.closed:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(headers=self.headers, connector=connector)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

class EconomicDataCollector(FreeDataCollector):
    """Collect free economic data"""

    async def get_fred_data(self, series_id: str, api_key: str = "demo"):
        """Get data from FRED API"""
        session = await self.get_session()
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': series_id,
            'api_key': api_key,
            'file_type': 'json',
            'limit': 100
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"FRED API error: {e}")
        return None

    async def get_ecb_data(self, key: str):
        """Get ECB data - completely free, no key needed"""
        session = await self.get_session()
        url = f"https://sdw-wsrest.ecb.europa.eu/service/data/{key}"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            print(f"ECB API error: {e}")
        return None

    async def get_worldbank_data(self, indicator: str, country: str = "US"):
        """Get World Bank data - free"""
        session = await self.get_session()
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {'format': 'json', 'per_page': 100}

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"World Bank API error: {e}")
        return None

class NewsCollector(FreeDataCollector):
    """Collect free news from RSS feeds"""

    def parse_rss_feed(self, url: str) -> List[Dict[str, Any]]:
        """Parse RSS feed"""
        try:
            feed = feedparser.parse(url)
            articles = []

            for entry in feed.entries[:50]:
                articles.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', ''),
                    'source': feed.feed.get('title', 'Unknown')
                })

            return articles
        except Exception as e:
            print(f"RSS parse error for {url}: {e}")
            return []

    async def get_reuters_news(self):
        """Get Reuters RSS feed"""
        return self.parse_rss_feed("https://www.reutersagency.com/feed/")

    async def get_cnbc_news(self):
        """Get CNBC RSS feed"""
        return self.parse_rss_feed("https://www.cnbc.com/id/100003114/device/rss/rss.html")

    async def get_marketwatch_news(self):
        """Get MarketWatch RSS feed"""
        return self.parse_rss_feed("http://feeds.marketwatch.com/marketwatch/topstories/")

    async def get_yahoo_finance_news(self):
        """Get Yahoo Finance RSS"""
        return self.parse_rss_feed("https://finance.yahoo.com/news/rssindex")

    async def get_all_news_feeds(self):
        """Get all news from RSS feeds"""
        all_news = []

        feeds = [
            self.get_reuters_news(),
            self.get_cnbc_news(),
            self.get_marketwatch_news(),
            self.get_yahoo_finance_news()
        ]

        results = await asyncio.gather(*feeds, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        return all_news

class CryptoCollector(FreeDataCollector):
    """Collect free crypto data"""

    async def get_coingecko_prices(self, symbols: List[str] = None):
        """CoinGecko - completely free"""
        if symbols is None:
            symbols = ['bitcoin', 'ethereum', 'solana']

        session = await self.get_session()
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ','.join(symbols),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"CoinGecko API error: {e}")
        return None

    async def get_coingecko_trending(self):
        """Get trending cryptos - free"""
        session = await self.get_session()
        url = "https://api.coingecko.com/api/v3/search/trending"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"CoinGecko trending error: {e}")
        return None

    async def get_coinpaprika_data(self, coin_id: str = "btc-bitcoin"):
        """CoinPaprika - free, no key"""
        session = await self.get_session()
        url = f"https://api.coinpaprika.com/v1/tickers/{coin_id}"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"CoinPaprika API error: {e}")
        return None

class SentimentCollector(FreeDataCollector):
    """Collect free sentiment data"""

    async def get_fear_greed_index(self):
        """CNN Fear & Greed - free JSON endpoint"""
        session = await self.get_session()
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'value': data.get('fear_and_greed', {}).get('score', 50),
                        'rating': data.get('fear_and_greed', {}).get('rating', 'Neutral'),
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"Fear & Greed error: {e}")
        return None

    async def get_reddit_sentiment(self, subreddit: str = "wallstreetbets"):
        """Reddit public JSON - no API key needed"""
        session = await self.get_session()
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {'limit': 25}

        try:
            async with session.get(url, params=params, headers={'User-Agent': self.headers['User-Agent']}) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = []

                    for post in data.get('data', {}).get('children', []):
                        post_data = post.get('data', {})
                        posts.append({
                            'title': post_data.get('title', ''),
                            'score': post_data.get('score', 0),
                            'upvote_ratio': post_data.get('upvote_ratio', 0),
                            'num_comments': post_data.get('num_comments', 0),
                            'created': post_data.get('created_utc', 0)
                        })

                    return posts
        except Exception as e:
            print(f"Reddit API error: {e}")
        return []

class EarningsCollector(FreeDataCollector):
    """Collect free earnings data"""

    async def get_yahoo_earnings(self, symbol: str):
        """Yahoo Finance - free, no key"""
        session = await self.get_session()
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
        params = {'modules': 'earningsHistory,calendarEvents'}

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Yahoo Finance error: {e}")
        return None

    async def get_sec_filings(self, cik: str):
        """SEC EDGAR - completely free"""
        session = await self.get_session()
        url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"

        try:
            async with session.get(url, headers={'User-Agent': self.headers['User-Agent']}) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"SEC EDGAR error: {e}")
        return None

class CalendarScraper(FreeDataCollector):
    """Scrape free economic calendars"""

    async def scrape_investing_com_calendar(self):
        """Scrape Investing.com calendar"""
        session = await self.get_session()
        url = "https://www.investing.com/economic-calendar/"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    events = []
                    # Parse calendar events from HTML
                    # This is a simplified example - real implementation needs detailed parsing
                    calendar_rows = soup.find_all('tr', class_='js-event-item')

                    for row in calendar_rows[:20]:
                        try:
                            event = {
                                'time': row.find('td', class_='time').text.strip() if row.find('td', class_='time') else '',
                                'currency': row.find('td', class_='flagCur').text.strip() if row.find('td', class_='flagCur') else '',
                                'event': row.find('td', class_='event').text.strip() if row.find('td', class_='event') else '',
                                'actual': row.find('td', class_='act').text.strip() if row.find('td', class_='act') else '',
                                'forecast': row.find('td', class_='fore').text.strip() if row.find('td', class_='fore') else '',
                                'previous': row.find('td', class_='prev').text.strip() if row.find('td', class_='prev') else ''
                            }
                            events.append(event)
                        except:
                            continue

                    return events
        except Exception as e:
            print(f"Investing.com scrape error: {e}")
        return []

    async def scrape_forexfactory_calendar(self):
        """Scrape Forex Factory calendar - very reliable"""
        session = await self.get_session()
        url = "https://www.forexfactory.com/calendar"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    events = []
                    calendar_rows = soup.find_all('tr', class_='calendar__row')

                    for row in calendar_rows[:20]:
                        try:
                            event = {
                                'time': row.find('td', class_='calendar__time').text.strip() if row.find('td', class_='calendar__time') else '',
                                'currency': row.find('td', class_='calendar__currency').text.strip() if row.find('td', class_='calendar__currency') else '',
                                'event': row.find('span', class_='calendar__event-title').text.strip() if row.find('span', class_='calendar__event-title') else '',
                                'actual': row.find('td', class_='calendar__actual').text.strip() if row.find('td', class_='calendar__actual') else '',
                                'forecast': row.find('td', class_='calendar__forecast').text.strip() if row.find('td', class_='calendar__forecast') else '',
                                'previous': row.find('td', class_='calendar__previous').text.strip() if row.find('td', class_='calendar__previous') else ''
                            }
                            events.append(event)
                        except:
                            continue

                    return events
        except Exception as e:
            print(f"Forex Factory scrape error: {e}")
        return []

class TechnicalDataCollector(FreeDataCollector):
    """Collect free technical/market data"""

    async def get_cboe_vix(self):
        """Scrape CBOE VIX data"""
        session = await self.get_session()
        url = "https://www.cboe.com/tradable_products/vix/"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    # Parse VIX value from page
                    vix_match = re.search(r'"vix":\s*(\d+\.\d+)', html)
                    if vix_match:
                        return {
                            'vix': float(vix_match.group(1)),
                            'timestamp': datetime.now().isoformat()
                        }
        except Exception as e:
            print(f"CBOE VIX error: {e}")
        return None

# Main aggregator
class FreeDataAggregator:
    """Aggregate all free data sources"""

    def __init__(self):
        self.economic = EconomicDataCollector()
        self.news = NewsCollector()
        self.crypto = CryptoCollector()
        self.sentiment = SentimentCollector()
        self.earnings = EarningsCollector()
        self.calendar = CalendarScraper()
        self.technical = TechnicalDataCollector()

    async def collect_all(self):
        """Collect data from all free sources"""
        results = {}

        try:
            # Economic data
            results['fred_unemployment'] = await self.economic.get_fred_data('UNRATE')
            results['worldbank_gdp'] = await self.economic.get_worldbank_data('NY.GDP.MKTP.CD')

            # News
            results['news_feeds'] = await self.news.get_all_news_feeds()

            # Crypto
            results['crypto_prices'] = await self.crypto.get_coingecko_prices()
            results['crypto_trending'] = await self.crypto.get_coingecko_trending()

            # Sentiment
            results['fear_greed'] = await self.sentiment.get_fear_greed_index()
            results['reddit_sentiment'] = await self.sentiment.get_reddit_sentiment()

            # Economic calendar
            results['forexfactory_calendar'] = await self.calendar.scrape_forexfactory_calendar()

            # Technical
            results['vix'] = await self.technical.get_cboe_vix()

        except Exception as e:
            print(f"Collection error: {e}")

        return results

    async def close_all(self):
        """Close all collector sessions"""
        await asyncio.gather(
            self.economic.close(),
            self.news.close(),
            self.crypto.close(),
            self.sentiment.close(),
            self.earnings.close(),
            self.calendar.close(),
            self.technical.close(),
            return_exceptions=True
        )

# Usage example
async def test_free_collectors():
    """Test all free data collectors"""
    aggregator = FreeDataAggregator()

    print("Collecting free data from all sources...")
    data = await aggregator.collect_all()

    print(f"\nCollected data from {len(data)} sources:")
    for source, content in data.items():
        if content:
            print(f"✓ {source}: {type(content).__name__}")
        else:
            print(f"✗ {source}: Failed")

    await aggregator.close_all()

    return data

if __name__ == "__main__":
    asyncio.run(test_free_collectors())
