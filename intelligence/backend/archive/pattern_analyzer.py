"""
Pattern Recognition & Historical Analysis
Learn from past events to predict market reactions
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
from collections import defaultdict

DB_PATH = os.path.expanduser("~/.aeon/intelligence.db")

class PatternAnalyzer:
    """Analyze historical patterns around market events"""

    def __init__(self):
        self.init_pattern_tables()

    def init_pattern_tables(self):
        """Create pattern analysis tables"""
        conn = sqlite3.connect(DB_PATH)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS historical_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_title TEXT NOT NULL,
                ticker TEXT NOT NULL,
                days_before INTEGER NOT NULL,
                price_change_pct REAL NOT NULL,
                volume_ratio REAL,
                event_date TEXT NOT NULL,
                analyzed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pattern_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                prediction_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                expected_move_pct REAL,
                reasoning TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS backtesting_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                win_rate REAL NOT NULL,
                avg_return_pct REAL NOT NULL,
                sharpe_ratio REAL,
                max_drawdown_pct REAL,
                tested_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_patterns_ticker ON historical_patterns(ticker);
            CREATE INDEX IF NOT EXISTS idx_patterns_type ON historical_patterns(event_type);
        """)
        conn.commit()
        conn.close()

    def analyze_historical_pattern(self, event_type: str, ticker: str, lookback_days: int = 365):
        """Analyze historical price movements around similar events"""
        try:
            stock = yf.Ticker(ticker)

            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            hist = stock.history(start=start_date, end=end_date)

            if hist.empty:
                return None

            # Find similar events in the past
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row

            past_events = conn.execute("""
                SELECT * FROM events
                WHERE category = ?
                AND affected_assets LIKE ?
                AND date(event_date) < date('now')
                AND date(event_date) >= date('now', '-1 year')
            """, (event_type, f'%{ticker}%')).fetchall()

            patterns = []

            for event in past_events:
                event_date = datetime.fromisoformat(event['event_date'])

                # Analyze price action D-20 to D+5
                for days_before in [20, 15, 10, 7, 5, 3, 2, 1, 0, -1, -2, -3, -5]:
                    target_date = event_date - timedelta(days=days_before)

                    # Find closest trading day
                    closest_idx = hist.index.get_indexer([target_date], method='nearest')[0]
                    if closest_idx == -1:
                        continue

                    # Calculate price change from event date
                    event_idx = hist.index.get_indexer([event_date], method='nearest')[0]
                    if event_idx == -1:
                        continue

                    price_at_target = hist.iloc[closest_idx]['Close']
                    price_at_event = hist.iloc[event_idx]['Close']
                    price_change_pct = ((price_at_target - price_at_event) / price_at_event) * 100

                    # Volume ratio
                    avg_volume = hist['Volume'].rolling(20).mean().iloc[closest_idx]
                    volume_ratio = hist.iloc[closest_idx]['Volume'] / avg_volume if avg_volume > 0 else 1.0

                    patterns.append({
                        'event_type': event_type,
                        'event_title': event['title'],
                        'ticker': ticker,
                        'days_before': days_before,
                        'price_change_pct': price_change_pct,
                        'volume_ratio': volume_ratio,
                        'event_date': event['event_date']
                    })

            # Store patterns
            cursor = conn.cursor()
            for pattern in patterns:
                cursor.execute("""
                    INSERT INTO historical_patterns
                    (event_type, event_title, ticker, days_before, price_change_pct, volume_ratio, event_date, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (pattern['event_type'], pattern['event_title'], pattern['ticker'],
                      pattern['days_before'], pattern['price_change_pct'], pattern['volume_ratio'],
                      pattern['event_date'], datetime.now().isoformat()))

            conn.commit()
            conn.close()

            return patterns

        except Exception as e:
            print(f"Error analyzing pattern for {ticker}: {e}")
            return None

    def get_pattern_summary(self, event_type: str, ticker: str) -> Dict:
        """Get statistical summary of historical patterns"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        patterns = conn.execute("""
            SELECT * FROM historical_patterns
            WHERE event_type = ? AND ticker = ?
        """, (event_type, ticker)).fetchall()

        if not patterns:
            conn.close()
            return {}

        # Group by days_before
        by_period = defaultdict(list)
        for p in patterns:
            by_period[p['days_before']].append(p['price_change_pct'])

        summary = {}
        for days, changes in by_period.items():
            avg_change = sum(changes) / len(changes)
            positive_count = sum(1 for c in changes if c > 0)
            win_rate = (positive_count / len(changes)) * 100

            summary[f"D{days}"] = {
                'avg_change': round(avg_change, 2),
                'win_rate': round(win_rate, 1),
                'sample_size': len(changes),
                'max_gain': round(max(changes), 2),
                'max_loss': round(min(changes), 2)
            }

        conn.close()
        return summary

    def predict_event_impact(self, event_id: int):
        """Generate predictions for upcoming event based on patterns"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        event = conn.execute("""
            SELECT * FROM events WHERE id = ?
        """, (event_id,)).fetchone()

        if not event:
            conn.close()
            return None

        affected_assets = json.loads(event['affected_assets']) if event['affected_assets'] else []

        predictions = []

        for ticker in affected_assets[:5]:  # Analyze top 5 assets
            # Get historical pattern summary
            summary = self.get_pattern_summary(event['category'], ticker)

            if not summary:
                continue

            # Current phase
            days_until = event['days_until']
            phase_key = None

            # Find closest historical period
            for key in summary.keys():
                try:
                    period = int(key.replace('D', ''))
                    if abs(period - days_until) <= 2:
                        phase_key = key
                        break
                except:
                    continue

            if not phase_key:
                continue

            pattern_data = summary[phase_key]

            # Generate prediction
            confidence = min(pattern_data['sample_size'] * 10, 90)  # More samples = higher confidence

            reasoning = f"Based on {pattern_data['sample_size']} similar {event['category']} events: " \
                       f"Average {pattern_data['avg_change']:+.2f}% move at D-{days_until}, " \
                       f"{pattern_data['win_rate']:.0f}% positive outcomes"

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pattern_predictions
                (event_id, ticker, prediction_type, confidence, expected_move_pct, reasoning, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_id, ticker, 'pattern_based', confidence, pattern_data['avg_change'],
                  reasoning, datetime.now().isoformat()))

            predictions.append({
                'ticker': ticker,
                'expected_move': pattern_data['avg_change'],
                'confidence': confidence,
                'reasoning': reasoning
            })

        conn.commit()
        conn.close()

        return predictions

    def backtest_strategy(self, strategy_name: str, event_type: str):
        """Backtest a trading strategy around events"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Get all patterns for this event type
        patterns = conn.execute("""
            SELECT * FROM historical_patterns
            WHERE event_type = ?
        """, (event_type,)).fetchall()

        if not patterns:
            conn.close()
            return None

        # Simple strategy: Buy at D-10, Sell at D-1
        trades = defaultdict(list)

        for pattern in patterns:
            if pattern['days_before'] == 10:
                # Entry point
                trades[f"{pattern['ticker']}_{pattern['event_date']}"].append({
                    'type': 'entry',
                    'price_change': 0  # Normalized entry
                })
            elif pattern['days_before'] == 1:
                # Exit point
                trades[f"{pattern['ticker']}_{pattern['event_date']}"].append({
                    'type': 'exit',
                    'price_change': pattern['price_change_pct']
                })

        # Calculate performance
        returns = []
        for trade_key, events in trades.items():
            if len(events) == 2:  # Complete trade
                exit_event = next((e for e in events if e['type'] == 'exit'), None)
                if exit_event:
                    returns.append(exit_event['price_change'])

        if not returns:
            conn.close()
            return None

        total_trades = len(returns)
        winning_trades = sum(1 for r in returns if r > 0)
        win_rate = (winning_trades / total_trades) * 100
        avg_return = sum(returns) / len(returns)

        # Sharpe ratio (simplified)
        if len(returns) > 1:
            import statistics
            std_dev = statistics.stdev(returns)
            sharpe_ratio = (avg_return / std_dev) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0

        # Max drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        for ret in returns:
            cumulative += ret
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_dd:
                max_dd = drawdown

        # Store results
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO backtesting_results
            (strategy_name, event_type, total_trades, winning_trades, win_rate, avg_return_pct, sharpe_ratio, max_drawdown_pct, tested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (strategy_name, event_type, total_trades, winning_trades, win_rate, avg_return,
              sharpe_ratio, max_dd, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return {
            'strategy': strategy_name,
            'event_type': event_type,
            'total_trades': total_trades,
            'win_rate': round(win_rate, 1),
            'avg_return': round(avg_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_dd, 2)
        }

# ═══════════════════════════════════════════════════════════
# RUN ANALYSIS
# ═══════════════════════════════════════════════════════════

def run_pattern_analysis():
    """Analyze patterns for major tickers and event types"""
    analyzer = PatternAnalyzer()

    tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'SPY', 'QQQ']
    event_types = ['earnings', 'macro']

    print("Analyzing historical patterns...")
    for ticker in tickers:
        for event_type in event_types:
            print(f"  Analyzing {ticker} {event_type} patterns...")
            analyzer.analyze_historical_pattern(event_type, ticker)

    print("\nBacktesting strategies...")
    for event_type in event_types:
        result = analyzer.backtest_strategy(f"Buy D-10 Sell D-1", event_type)
        if result:
            print(f"  {event_type}: {result['win_rate']}% win rate, {result['avg_return']:+.2f}% avg return")

if __name__ == "__main__":
    run_pattern_analysis()
