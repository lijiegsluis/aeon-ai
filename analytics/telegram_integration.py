"""
Telegram Breaking News Integration for Aeon Nimbus Terminal
Connects to @Tradeul_Breaking_News channel and feeds real-time events
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from telethon import TelegramClient, events
from database import get_db
import json

# Telegram API credentials
API_ID = 37634302
API_HASH = "d3657dff2652c4251b3d3ff2f1d10f04"
PHONE_NUMBER = "+447440101737"
CHANNEL_USERNAME = "Tradeul_Breaking_News"

class TelegramNewsMonitor:
    def __init__(self, api_id: int, api_hash: str):
        self.client = TelegramClient('aeon_terminal_session', api_id, api_hash)
        self.event_patterns = self._load_patterns()

    def _load_patterns(self):
        """NLP patterns to extract events from messages"""
        return {
            'earnings': re.compile(r'(earnings|results|Q\d|quarterly)', re.IGNORECASE),
            'macro': re.compile(r'(CPI|NFP|GDP|Fed|inflation|interest rate|FOMC)', re.IGNORECASE),
            'geopolitical': re.compile(r'(summit|meeting|sanctions|conflict|treaty|election)', re.IGNORECASE),
            'date': re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|next \w+|in \d+ days)'),
        }

    async def start_monitoring(self):
        """Connect to Telegram and start listening"""
        await self.client.start()

        @self.client.on(events.NewMessage(chats=CHANNEL_USERNAME))
        async def handler(event):
            message = event.message.message
            await self._process_message(message, event.date)

        print(f"✓ Monitoring {CHANNEL_USERNAME} for breaking news...")
        await self.client.run_until_disconnected()

    async def _process_message(self, text: str, timestamp: datetime):
        """Extract event from message and save to database"""
        category = self._classify_event(text)
        if not category:
            return

        date_str = self._extract_date(text)
        if not date_str:
            return

        event_date = self._parse_date(date_str)
        affected_assets = self._extract_assets(text)

        # Save to database
        with get_db() as conn:
            conn.execute("""
                INSERT INTO market_events
                (title, category, event_date, source, raw_text, affected_assets, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                text[:200],
                category,
                event_date.isoformat() if event_date else None,
                'telegram_tradeul',
                text,
                json.dumps(affected_assets),
                timestamp.isoformat()
            ))

        # Trigger alert to Terminal users
        await self._notify_terminal_users(category, text, event_date)

    def _classify_event(self, text: str) -> str:
        """Classify event type from message text"""
        for category, pattern in self.event_patterns.items():
            if category != 'date' and pattern.search(text):
                return category
        return 'general'

    def _extract_date(self, text: str) -> str:
        """Extract date string from message"""
        match = self.event_patterns['date'].search(text)
        return match.group(1) if match else None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        # Handle relative dates
        if 'tomorrow' in date_str.lower():
            return datetime.now() + timedelta(days=1)
        elif 'next week' in date_str.lower():
            return datetime.now() + timedelta(days=7)
        elif match := re.search(r'in (\d+) days', date_str):
            return datetime.now() + timedelta(days=int(match.group(1)))

        # Handle absolute dates
        for fmt in ['%m/%d/%Y', '%d-%m-%Y', '%m-%d-%y']:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None

    def _extract_assets(self, text: str) -> List[str]:
        """Extract affected assets/tickers from message"""
        assets = []

        # Common asset mentions
        asset_keywords = {
            'oil': ['oil', 'crude', 'petroleum', 'brent', 'wti'],
            'gold': ['gold', 'xau'],
            'btc': ['bitcoin', 'btc', 'crypto'],
            'nasdaq': ['nasdaq', 'tech stocks', 'qqq'],
            'spy': ['spy', 's&p', 'sp500'],
            'bonds': ['bonds', 'treasury', 'yield'],
        }

        text_lower = text.lower()
        for asset, keywords in asset_keywords.items():
            if any(kw in text_lower for kw in keywords):
                assets.append(asset.upper())

        # Extract explicit tickers (all caps 2-5 letters)
        tickers = re.findall(r'\b[A-Z]{2,5}\b', text)
        assets.extend(tickers)

        return list(set(assets))

    async def _notify_terminal_users(self, category: str, text: str, event_date: datetime):
        """Push notification to Terminal users via WebSocket or polling"""
        # This would integrate with Terminal's alert system
        notification = {
            'type': 'telegram_event',
            'category': category,
            'text': text[:200],
            'event_date': event_date.isoformat() if event_date else None,
            'timestamp': datetime.now().isoformat(),
        }

        # Store for Terminal to poll
        with get_db() as conn:
            conn.execute("""
                INSERT INTO notifications (user_id, type, data, created_at)
                VALUES (?, ?, ?, ?)
            """, (None, 'telegram_event', json.dumps(notification), datetime.now().isoformat()))


# Database schema additions
def init_telegram_tables():
    """Add tables for Telegram integration"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS market_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                event_date TEXT,
                source TEXT DEFAULT 'telegram',
                raw_text TEXT,
                affected_assets TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_events_date ON market_events(event_date);
            CREATE INDEX IF NOT EXISTS idx_events_category ON market_events(category);

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL,
                data TEXT NOT NULL,
                read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, read);
        """)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python telegram_integration.py <api_id> <api_hash>")
        print("Get credentials from https://my.telegram.org")
        sys.exit(1)

    api_id = int(sys.argv[1])
    api_hash = sys.argv[2]

    init_telegram_tables()
    monitor = TelegramNewsMonitor(api_id, api_hash)
    asyncio.run(monitor.start_monitoring())
