"""
Multi-Source News Aggregator
Integrates: Telegram, Twitter/X, RSS Feeds, and APIs
"""
import asyncio
import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import aiohttp
from telethon import TelegramClient, events

DB_PATH = os.path.expanduser("~/.aeon/intelligence.db")

# ═══════════════════════════════════════════════════════════
# TELEGRAM CHANNELS - Financial News Sources
# ═══════════════════════════════════════════════════════════

TELEGRAM_CHANNELS = [
    "Tradeul_Breaking_News",      # Primary - Market moving news
    "DeItaone",                    # Breaking market news
    "FirstSquawk",                 # Economic data releases
    "unusual_whales",              # Options flow & dark pool
    "fxhedgers",                   # Global macro & FX
    "zerohedge",                   # Alternative perspective
    "WatcherGuru",                 # Crypto & tech news
    "BNBBBBNews",                  # Asian markets
]

# ═══════════════════════════════════════════════════════════
# RSS FEEDS - Traditional News Sources
# ═══════════════════════════════════════════════════════════

RSS_FEEDS = {
    "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
    "reuters_business": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    "cnbc_top": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "wsj_markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "ft_markets": "https://www.ft.com/markets?format=rss",
    "marketwatch": "http://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
    "seeking_alpha": "https://seekingalpha.com/market_currents.xml",
}

# ═══════════════════════════════════════════════════════════
# TWITTER/X ACCOUNTS - Via Nitter RSS
# ═══════════════════════════════════════════════════════════

TWITTER_ACCOUNTS = [
    "DeItaone",
    "FirstSquawk",
    "unusual_whales",
    "Fxhedgers",
    "zerohedge",
    "FinancialJuice",
    "business",
    "markets",
    "CNBCnow",
]

# ═══════════════════════════════════════════════════════════
# NEWS API INTEGRATION
# ═══════════════════════════════════════════════════════════

NEWS_API_KEYWORDS = [
    "Federal Reserve",
    "interest rate",
    "CPI",
    "inflation",
    "earnings",
    "GDP",
    "unemployment",
    "FOMC",
    "stock market",
    "S&P 500",
    "Dow Jones",
    "Nasdaq",
]

class NewsAggregator:
    """Multi-source news aggregation engine"""

    def __init__(self, telegram_api_id: int, telegram_api_hash: str):
        self.telegram_api_id = telegram_api_id
        self.telegram_api_hash = telegram_api_hash
        self.telegram_client = None

    async def start_telegram_monitor(self):
        """Monitor all Telegram channels for breaking news"""
        self.telegram_client = TelegramClient(
            'aeon_intelligence_session',
            self.telegram_api_id,
            self.telegram_api_hash
        )

        await self.telegram_client.start()
        print(f"✓ Telegram monitor connected")
        print(f"✓ Watching {len(TELEGRAM_CHANNELS)} channels")

        @self.telegram_client.on(events.NewMessage(chats=TELEGRAM_CHANNELS))
        async def handle_message(event):
            try:
                channel = await event.get_chat()
                channel_name = channel.username or channel.title
                message_text = event.message.message

                # Store in database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO news_feed (source, channel, message, timestamp, processed)
                    VALUES (?, ?, ?, ?, 0)
                """, ('telegram', channel_name, message_text, datetime.now().isoformat()))
                conn.commit()
                conn.close()

                print(f"📰 [{channel_name}] {message_text[:100]}...")

                # Extract tickers and create event if significant
                await self.process_message(message_text, channel_name)

            except Exception as e:
                print(f"Error processing message: {e}")

        print("✓ Telegram listener active")
        await self.telegram_client.run_until_disconnected()

    async def process_message(self, text: str, source: str):
        """Extract events and tickers from news message"""
        # Simple keyword detection for now
        keywords = {
            'earnings': ['earnings', 'EPS', 'revenue', 'guidance'],
            'macro': ['Fed', 'FOMC', 'CPI', 'NFP', 'GDP', 'rate decision'],
            'geopolitical': ['China', 'Russia', 'war', 'sanctions', 'trade war'],
            'commodity': ['oil', 'gold', 'crude', 'OPEC', 'commodities'],
        }

        detected_category = 'news'
        for category, terms in keywords.items():
            if any(term.lower() in text.lower() for term in terms):
                detected_category = category
                break

        # Extract potential tickers (simple regex would go here)
        # For now, just store as news item

    async def fetch_rss_feeds(self):
        """Fetch all RSS feeds periodically"""
        async with aiohttp.ClientSession() as session:
            while True:
                for feed_name, feed_url in RSS_FEEDS.items():
                    try:
                        async with session.get(feed_url, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                # Parse RSS (would use feedparser library)
                                print(f"✓ Fetched {feed_name}")
                    except Exception as e:
                        print(f"✗ Failed to fetch {feed_name}: {e}")

                await asyncio.sleep(300)  # Every 5 minutes

    async def monitor_twitter_via_nitter(self):
        """Monitor Twitter accounts via Nitter RSS"""
        async with aiohttp.ClientSession() as session:
            while True:
                for account in TWITTER_ACCOUNTS:
                    try:
                        # Nitter RSS feed
                        nitter_url = f"https://nitter.net/{account}/rss"
                        async with session.get(nitter_url, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                # Parse RSS feed
                                print(f"✓ Checked @{account}")
                    except Exception as e:
                        print(f"✗ Failed @{account}: {e}")

                await asyncio.sleep(180)  # Every 3 minutes

    async def run_all(self):
        """Run all aggregators concurrently"""
        tasks = [
            self.start_telegram_monitor(),
            self.fetch_rss_feeds(),
            self.monitor_twitter_via_nitter(),
        ]
        await asyncio.gather(*tasks)

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

async def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🌐 AEON NIMBUS - MULTI-SOURCE NEWS AGGREGATOR")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print(f"📡 Telegram Channels: {len(TELEGRAM_CHANNELS)}")
    print(f"📰 RSS Feeds: {len(RSS_FEEDS)}")
    print(f"🐦 Twitter Accounts: {len(TWITTER_ACCOUNTS)}")
    print("")

    # Load credentials
    API_ID = 37634302
    API_HASH = "d3657dff2652c4251b3d3ff2f1d10f04"

    aggregator = NewsAggregator(API_ID, API_HASH)
    await aggregator.run_all()

if __name__ == "__main__":
    asyncio.run(main())
