"""
Market Sentiment & Impact Analyzer
Scans event text for keyword/ticker matches and known market-timing
heuristics — a deterministic rule engine, not an LLM. No model call is
made here; "reasoning" below means a templated explanation of which
rules fired, not model-generated inference.
"""
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yfinance as yf
from database import get_db


def _has_word(text_lower: str, phrase: str) -> bool:
    """Whole-word match — plain substring tests made 'ev' (Tesla) match 'event'
    and 'every', 'eth' match 'whether', 'mac' match 'macro' and so on."""
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text_lower) is not None


class SentimentAnalyzer:
    def __init__(self):
        self.asset_keywords = self._load_asset_mappings()
        self.sector_mappings = self._load_sector_mappings()

    def _load_asset_mappings(self) -> Dict[str, List[str]]:
        """Map keywords to tradeable assets"""
        return {
            'AAPL': ['apple', 'iphone', 'ipad', 'mac', 'ios'],
            'MSFT': ['microsoft', 'windows', 'azure', 'microsoft 365', 'xbox'],
            'NVDA': ['nvidia', 'gpu', 'ai chip', 'graphics card'],
            'TSLA': ['tesla', 'elon musk', 'electric vehicle', 'ev'],
            'META': ['meta', 'facebook', 'instagram', 'whatsapp', 'metaverse'],
            'GOOGL': ['google', 'alphabet', 'youtube', 'android', 'google search'],
            'AMZN': ['amazon', 'aws', 'prime video', 'e-commerce'],
            'SPY': ['s&p 500', 'stock market', 'broad market', 'stock index'],
            'QQQ': ['nasdaq', 'tech stocks', 'technology'],
            'GLD': ['gold', 'precious metals', 'safe haven'],
            'USO': ['oil', 'crude', 'petroleum', 'energy'],
            'TLT': ['bonds', 'treasury', 'yields', 'fixed income'],
            'UUP': ['dollar', 'usd', 'currency', 'forex'],
            'BTC-USD': ['bitcoin', 'btc', 'crypto', 'cryptocurrency'],
            'ETH-USD': ['ethereum', 'eth', 'smart contracts'],
        }

    def _load_sector_mappings(self) -> Dict[str, List[str]]:
        """Map sectors to representative ETFs"""
        return {
            'Technology': ['XLK', 'VGT'],
            'Finance': ['XLF', 'VFH'],
            'Energy': ['XLE', 'VDE'],
            'Healthcare': ['XLV', 'VHT'],
            'Consumer': ['XLY', 'VCR'],
            'Industrials': ['XLI', 'VIS'],
            'Materials': ['XLB', 'VAW'],
            'Utilities': ['XLU', 'VPU'],
            'RealEstate': ['XLRE', 'VNQ'],
        }

    def analyze_event(self, event_text: str, event_date: str, category: str) -> Dict[str, Any]:
        """Full analysis: sentiment, affected assets, reasoning, countdown"""

        # 1. Identify affected assets
        affected_assets = self._scan_affected_assets(event_text)

        # 2. Calculate temporal phases
        days_remaining = self._calculate_days_remaining(event_date)
        phase_info = self._get_phase_analysis(days_remaining)

        # 3. Fetch current market data
        market_data = self._fetch_market_data(affected_assets)

        # 4. Generate sentiment score
        sentiment = self._calculate_sentiment(event_text, category, days_remaining)

        # 5. Rule-based reasoning summary (keyword counts + phase heuristics —
        #    not a model call; see module docstring)
        reasoning = self._generate_reasoning(
            event_text, category, affected_assets,
            days_remaining, sentiment, market_data
        )

        # 6. Impact projection by timeframe
        impact_projection = self._project_impact(
            affected_assets, days_remaining, sentiment
        )

        return {
            'sentiment_score': sentiment['score'],
            'sentiment_label': sentiment['label'],
            'affected_assets': affected_assets,
            'market_data': market_data,
            'days_remaining': days_remaining,
            'phase': phase_info,
            'reasoning': reasoning,
            'impact_projection': impact_projection,
            'recommended_action': self._get_recommendation(days_remaining, sentiment),
            'methodology': 'Deterministic keyword/rule engine (no LLM) — sentiment is a '
                            'weighted keyword count, phase/impact come from fixed day-count '
                            'thresholds.',
        }

    def _scan_affected_assets(self, text: str) -> List[Dict[str, Any]]:
        """Scan text and identify which assets will be impacted"""
        affected = []
        text_lower = text.lower()

        # Direct ticker mentions
        ticker_matches = re.findall(r'\$?([A-Z]{2,5})\b', text)
        for ticker in ticker_matches:
            if ticker in self.asset_keywords:
                affected.append({
                    'ticker': ticker,
                    'confidence': 0.95,
                    'match_type': 'direct',
                })

        # Keyword-based detection
        for ticker, keywords in self.asset_keywords.items():
            for keyword in keywords:
                if _has_word(text_lower, keyword):
                    if not any(a['ticker'] == ticker for a in affected):
                        affected.append({
                            'ticker': ticker,
                            'confidence': 0.75,
                            'match_type': 'keyword',
                        })
                    break

        # Sector-level impact
        for sector, etfs in self.sector_mappings.items():
            if _has_word(text_lower, sector.lower()):
                for etf in etfs[:1]:  # Add primary ETF
                    if not any(a['ticker'] == etf for a in affected):
                        affected.append({
                            'ticker': etf,
                            'confidence': 0.60,
                            'match_type': 'sector',
                        })

        return affected

    def _calculate_days_remaining(self, event_date: str) -> int:
        """Calculate days until event"""
        try:
            event_dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
            today = datetime.now()
            return (event_dt.date() - today.date()).days
        except:
            return 999  # Unknown date

    def _get_phase_analysis(self, days: int) -> Dict[str, Any]:
        """Analyze which phase we're in"""
        if days > 20:
            return {
                'name': 'Pre-Rumor',
                'description': 'Too early - market not pricing event yet',
                'color': '#6b7280',
                'action': 'Monitor for rumor emergence',
            }
        elif days > 9:
            return {
                'name': 'Accumulation Phase',
                'description': 'Smart money positioning - ideal entry window',
                'color': '#10b981',
                'action': 'BUY THE RUMOR',
            }
        elif days > 2:
            return {
                'name': 'Mass Participation',
                'description': 'Retail entering late - momentum peaking',
                'color': '#f59e0b',
                'action': 'Prepare exit strategy',
            }
        elif days >= 0:
            return {
                'name': 'Danger Zone',
                'description': 'Event imminent - sell pressure building',
                'color': '#ef4444',
                'action': 'SELL THE NEWS',
            }
        else:
            return {
                'name': 'Post-Event',
                'description': 'Event passed - assess reaction',
                'color': '#8b5cf6',
                'action': 'Analyze outcome vs expectations',
            }

    def _fetch_market_data(self, assets: List[Dict]) -> Dict[str, Any]:
        """Get current prices and momentum for affected assets"""
        market_data = {}

        for asset in assets:
            ticker = asset['ticker']
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='5d')

                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    change_5d = ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100

                    market_data[ticker] = {
                        'price': round(current_price, 2),
                        'change_5d': round(change_5d, 2),
                        'volume': int(hist['Volume'].iloc[-1]),
                        'momentum': 'bullish' if change_5d > 0 else 'bearish',
                    }
            except:
                market_data[ticker] = {'error': 'Data unavailable'}

        return market_data

    def _calculate_sentiment(self, text: str, category: str, days: int) -> Dict[str, Any]:
        """Calculate sentiment score (-100 to +100)"""
        score = 0

        # Keyword-based sentiment
        positive_words = ['growth', 'beat', 'exceed', 'strong', 'positive', 'bullish', 'rally', 'surge']
        negative_words = ['decline', 'miss', 'weak', 'negative', 'bearish', 'drop', 'fall', 'crisis']

        text_lower = text.lower()
        score += sum(10 for word in positive_words if _has_word(text_lower, word))
        score -= sum(10 for word in negative_words if _has_word(text_lower, word))

        # Category-based adjustment
        if category == 'geopolitical':
            score -= 20  # Geopolitical = uncertainty = negative
        elif category == 'earnings':
            score += 5  # Earnings = opportunity

        # Time-based adjustment (closer to event = more uncertainty)
        if days <= 2:
            score -= 15

        score = max(-100, min(100, score))

        if score > 30:
            label = 'Very Bullish'
        elif score > 10:
            label = 'Bullish'
        elif score > -10:
            label = 'Neutral'
        elif score > -30:
            label = 'Bearish'
        else:
            label = 'Very Bearish'

        return {'score': score, 'label': label}

    def _generate_reasoning(self, text: str, category: str, assets: List,
                          days: int, sentiment: Dict, market_data: Dict) -> str:
        """Render a templated explanation of which keyword/phase rules fired —
        not model-generated; see module docstring."""

        phase = self._get_phase_analysis(days)

        reasoning_parts = []

        # Event context
        reasoning_parts.append(f"Event Category: {category.upper()}")
        reasoning_parts.append(f"Timeline: D-{days} ({phase['name']})")

        # Affected assets
        tickers = [a['ticker'] for a in assets[:5]]
        reasoning_parts.append(f"Primary Impact: {', '.join(tickers)}")

        # Sentiment analysis
        reasoning_parts.append(f"Market Sentiment: {sentiment['label']} ({sentiment['score']:+d})")

        # Phase-specific reasoning
        if days > 9:
            reasoning_parts.append(
                "TACTICAL ADVANTAGE: Currently in accumulation phase. "
                "Institutional money is likely positioning before retail awareness peaks. "
                "Entry window open for 'rumor' positioning."
            )
        elif days > 2:
            reasoning_parts.append(
                "CAUTION: Mass participation phase. Media coverage increasing, "
                "retail entering late. Risk/reward deteriorating. "
                "Consider taking partial profits."
            )
        elif days >= 0:
            reasoning_parts.append(
                "DANGER ZONE: Event imminent. Historical pattern shows profit-taking "
                "accelerates in final 48 hours. 'Sell the news' window approaching. "
                "Exit or hedge recommended."
            )

        # Market momentum check
        bullish_count = sum(1 for data in market_data.values()
                           if isinstance(data, dict) and data.get('momentum') == 'bullish')
        total_count = len([d for d in market_data.values() if isinstance(d, dict)])

        if total_count > 0:
            momentum_pct = (bullish_count / total_count) * 100
            reasoning_parts.append(
                f"Current Momentum: {bullish_count}/{total_count} assets bullish ({momentum_pct:.0f}%)"
            )

        return " | ".join(reasoning_parts)

    def _project_impact(self, assets: List, days: int, sentiment: Dict) -> Dict[str, str]:
        """Project impact by timeframe"""
        base_direction = "UP" if sentiment['score'] > 0 else "DOWN"

        if days < 0:
            return {'today': "Event has passed", 'this_week': "Watch the post-event reaction",
                    'until_event': "n/a"}
        return {
            'today': f"Minimal - event still {days} days away",
            'this_week': f"Building momentum - expect gradual move {base_direction}",
            'until_event': f"Peak impact at D-2 to D-1, then reversal risk HIGH",
        }

    def _get_recommendation(self, days: int, sentiment: Dict) -> str:
        """Get actionable recommendation"""
        if days > 20:
            return "⏳ WAIT - Too early to position"
        elif days > 9:
            if sentiment['score'] > 20:
                return "🟢 BUY - Strong accumulation phase"
            elif sentiment['score'] < -20:
                return "🔴 SHORT - Negative catalyst, early positioning"
            else:
                return "⚪ WATCH - Monitor for clearer signals"
        elif days > 2:
            return "⚠️ REDUCE - Take profits, trim exposure"
        elif days >= 0:
            return "🚨 EXIT - Sell the news NOW"
        else:
            return "📊 ASSESS - Review outcome vs expectations"


# API endpoint integration
def analyze_market_event(event_id: int) -> Dict[str, Any]:
    """Analyze a market event from database"""
    analyzer = SentimentAnalyzer()

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM market_events WHERE id = ?",
            (event_id,)
        ).fetchone()

        if not row:
            return {'error': 'Event not found'}

        analysis = analyzer.analyze_event(
            event_text=row['raw_text'] or row['title'],
            event_date=row['event_date'],
            category=row['category']
        )

        # Save analysis back to DB
        conn.execute("""
            UPDATE market_events
            SET analysis_json = ?, sentiment_score = ?, analyzed_at = ?
            WHERE id = ?
        """, (
            json.dumps(analysis),
            analysis['sentiment_score'],
            datetime.now().isoformat(),
            event_id
        ))

        return analysis
