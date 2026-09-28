"""
Portfolio Integration - Connect positions with market events
Track risk exposure to upcoming events
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf

DB_PATH = os.path.expanduser("~/.aeon/intelligence.db")

class PortfolioTracker:
    """Track portfolio and match with market events"""

    def __init__(self):
        self.init_portfolio_tables()

    def init_portfolio_tables(self):
        """Create portfolio tracking tables"""
        conn = sqlite3.connect(DB_PATH)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS portfolio_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                ticker TEXT NOT NULL,
                shares REAL NOT NULL,
                avg_cost REAL NOT NULL,
                current_price REAL,
                position_value REAL,
                unrealized_pnl REAL,
                added_at TEXT NOT NULL,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS event_exposure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                event_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                shares REAL NOT NULL,
                position_value REAL,
                risk_level TEXT,
                calculated_at TEXT,
                FOREIGN KEY (event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS risk_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                ticker TEXT NOT NULL,
                event_id INTEGER,
                risk_type TEXT,
                risk_level TEXT,
                message TEXT,
                triggered_at TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                FOREIGN KEY (event_id) REFERENCES events(id)
            );

            CREATE INDEX IF NOT EXISTS idx_portfolio_ticker ON portfolio_positions(ticker);
            CREATE INDEX IF NOT EXISTS idx_exposure_event ON event_exposure(event_id);
        """)
        conn.commit()
        conn.close()

    def add_position(self, ticker: str, shares: float, avg_cost: float):
        """Add position to portfolio"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get current price
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice', avg_cost)
        except:
            current_price = avg_cost

        position_value = shares * current_price
        unrealized_pnl = (current_price - avg_cost) * shares

        cursor.execute("""
            INSERT INTO portfolio_positions
            (ticker, shares, avg_cost, current_price, position_value, unrealized_pnl, added_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ticker, shares, avg_cost, current_price, position_value, unrealized_pnl,
              datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        position_id = cursor.lastrowid
        conn.close()

        # Check for event exposure
        self.check_event_exposure(ticker)

        return position_id

    def check_event_exposure(self, ticker: str):
        """Check if position has exposure to upcoming events"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Get position
        position = conn.execute("""
            SELECT * FROM portfolio_positions WHERE ticker = ? ORDER BY added_at DESC LIMIT 1
        """, (ticker,)).fetchone()

        if not position:
            conn.close()
            return

        # Find events affecting this ticker (next 30 days)
        end_date = (datetime.now() + timedelta(days=30)).date().isoformat()

        events = conn.execute("""
            SELECT * FROM events
            WHERE date(event_date) BETWEEN date('now') AND date(?)
            AND affected_assets LIKE ?
        """, (end_date, f'%{ticker}%')).fetchall()

        cursor = conn.cursor()

        for event in events:
            event_date = datetime.fromisoformat(event['event_date'])
            days_until = (event_date.date() - datetime.now().date()).days

            # Calculate risk level based on phase
            if days_until <= 2:
                risk_level = 'HIGH'
            elif days_until <= 9:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'

            # Record exposure
            cursor.execute("""
                INSERT INTO event_exposure
                (event_id, ticker, shares, position_value, risk_level, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event['id'], ticker, position['shares'], position['position_value'],
                  risk_level, datetime.now().isoformat()))

            # Create risk alert if HIGH risk
            if risk_level == 'HIGH':
                message = f"⚠️ {ticker}: {event['title']} in D-{days_until} (DANGER ZONE)"
                cursor.execute("""
                    INSERT INTO risk_alerts
                    (ticker, event_id, risk_type, risk_level, message, triggered_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ticker, event['id'], 'event_proximity', risk_level, message,
                      datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_portfolio_summary(self):
        """Get portfolio with event exposure"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        positions = conn.execute("""
            SELECT * FROM portfolio_positions ORDER BY position_value DESC
        """).fetchall()

        summary = {
            'positions': [],
            'total_value': 0,
            'total_pnl': 0,
            'high_risk_positions': 0
        }

        for pos in positions:
            # Get event exposure
            exposures = conn.execute("""
                SELECT e.*, ev.title, ev.event_date, ev.category
                FROM event_exposure e
                JOIN events ev ON e.event_id = ev.id
                WHERE e.ticker = ?
                ORDER BY ev.event_date ASC
            """, (pos['ticker'],)).fetchall()

            high_risk = any(exp['risk_level'] == 'HIGH' for exp in exposures)
            if high_risk:
                summary['high_risk_positions'] += 1

            summary['positions'].append({
                'ticker': pos['ticker'],
                'shares': pos['shares'],
                'avg_cost': pos['avg_cost'],
                'current_price': pos['current_price'],
                'position_value': pos['position_value'],
                'unrealized_pnl': pos['unrealized_pnl'],
                'event_count': len(exposures),
                'high_risk': high_risk,
                'upcoming_events': [dict(e) for e in exposures[:3]]
            })

            summary['total_value'] += pos['position_value'] or 0
            summary['total_pnl'] += pos['unrealized_pnl'] or 0

        conn.close()
        return summary

    def get_risk_alerts(self, acknowledged: bool = False):
        """Get active risk alerts"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        alerts = conn.execute("""
            SELECT r.*, e.title as event_title, e.event_date, e.category
            FROM risk_alerts r
            LEFT JOIN events e ON r.event_id = e.id
            WHERE r.acknowledged = ?
            ORDER BY r.triggered_at DESC
        """, (1 if acknowledged else 0,)).fetchall()

        conn.close()
        return [dict(a) for a in alerts]

# ═══════════════════════════════════════════════════════════
# DEMO DATA
# ═══════════════════════════════════════════════════════════

def seed_demo_portfolio():
    """Add demo portfolio for testing"""
    tracker = PortfolioTracker()

    positions = [
        ("AAPL", 50, 172.50),
        ("MSFT", 30, 365.00),
        ("NVDA", 20, 450.00),
        ("TSLA", 15, 245.00),
        ("SPY", 100, 425.00),
        ("QQQ", 50, 385.00),
    ]

    print("Adding demo portfolio positions...")
    for ticker, shares, cost in positions:
        tracker.add_position(ticker, shares, cost)
        print(f"✓ Added {shares} shares of {ticker} @ ${cost}")

    print("\nChecking event exposure...")
    summary = tracker.get_portfolio_summary()
    print(f"✓ Total portfolio value: ${summary['total_value']:,.2f}")
    print(f"✓ Total P&L: ${summary['total_pnl']:,.2f}")
    print(f"✓ High risk positions: {summary['high_risk_positions']}")

if __name__ == "__main__":
    seed_demo_portfolio()
